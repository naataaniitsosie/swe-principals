"""
Sampling pipeline: locate DB, read cleaned table, run stratified sampler, write samples table.
Mirrors preprocessing/pipeline.py in structure. Called by sample.py.
"""
import logging
import sqlite3
from pathlib import Path
from typing import Dict

from dataset_readers.gharchive.storage import DEFAULT_DB_FILENAME
from sampling.sampler import sample_strata
from sampling.storage import create_samples_table, insert_samples, query_strata_counts

logger = logging.getLogger(__name__)


class SamplingPipeline:
    """Draw a stratified sample from cleaned and write to samples in the same DB."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def run(self) -> Dict:
        """
        Run sampling. Returns stats dict with total selected and per-stratum breakdown.
        Drops and recreates the samples table — re-running is always idempotent.
        """
        db_path = self.data_dir / DEFAULT_DB_FILENAME
        if not db_path.exists():
            logger.warning("No %s found in %s", DEFAULT_DB_FILENAME, self.data_dir)
            return {}

        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("DROP TABLE IF EXISTS samples")
            create_samples_table(conn)

            rows = sample_strata(conn)
            insert_samples(conn, [(r.id, r.repo, r.event_type, r.stratum_key) for r in rows])
            conn.commit()

            strata_counts = query_strata_counts(conn)
        finally:
            conn.close()

        total = len(rows)
        logger.info("Sampled %d comments across %d strata", total, len(strata_counts))
        for stratum_key, count in strata_counts:
            logger.info("  %-60s %d", stratum_key, count)

        return {"total": total, "strata": dict(strata_counts)}
