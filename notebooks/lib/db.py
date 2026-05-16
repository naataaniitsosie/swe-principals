import sqlite3
import sys
from pathlib import Path


def _repo_root_for_notebook() -> Path:
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        if (p / "project_config.py").is_file():
            return p
    return here


_REPO = _repo_root_for_notebook()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from project_config import DATA_DIR, DB_FILENAME, repo_root

DB_PATH = repo_root() / DATA_DIR / DB_FILENAME


def connect() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH))
