"""
Stratified sampler: repo × event_type strata, per-stratum deterministic seeding.
See sampling/README.md for full design rationale before modifying.
"""
import hashlib
import random
import sqlite3
from typing import Dict, List, NamedTuple

FLOOR = 25   # minimum comments per stratum (informational; take all if below)
CAP = 50     # maximum comments drawn per stratum
BASE_SEED = 42  # change only intentionally; doing so invalidates all existing samples


class SampledRow(NamedTuple):
    id: str
    repo: str
    event_type: str
    stratum_key: str


def stratum_seed(repo: str, event_type: str) -> int:
    """Deterministic per-stratum seed derived from repo, event_type, and BASE_SEED."""
    key = f"{repo}|{event_type}|{BASE_SEED}"
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**31)


def sample_strata(conn: sqlite3.Connection) -> List[SampledRow]:
    """
    Read all (id, repo, event_type) from cleaned, sample per repo × event_type stratum,
    and return the selected rows. Each stratum draws min(count, CAP) rows deterministically.
    Strata with fewer than FLOOR rows take all available (they simply cannot reach the cap).
    """
    cursor = conn.execute(
        "SELECT id, repo, event_type FROM cleaned WHERE repo != '' AND event_type != ''"
    )

    strata: Dict[str, List[str]] = {}
    stratum_meta: Dict[str, tuple] = {}  # stratum_key -> (repo, event_type)

    for row_id, repo, event_type in cursor:
        key = f"{repo}|{event_type}"
        if key not in strata:
            strata[key] = []
            stratum_meta[key] = (repo, event_type)
        strata[key].append(row_id)

    selected: List[SampledRow] = []
    for stratum_key in sorted(strata):
        ids = strata[stratum_key]
        repo, event_type = stratum_meta[stratum_key]
        k = min(len(ids), CAP)
        rng = random.Random(stratum_seed(repo, event_type))
        chosen = rng.sample(ids, k)
        for chosen_id in chosen:
            selected.append(SampledRow(
                id=chosen_id,
                repo=repo,
                event_type=event_type,
                stratum_key=stratum_key,
            ))

    return selected
