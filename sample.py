"""
Draw a deterministic stratified sample from the cleaned table and write it to the samples table.
Pipeline step 3: runs after preprocess.py, before judge.py.
See sampling/README.md for design rationale and sampling/pipeline.py for implementation.
"""
import logging
from pathlib import Path

from project_config import DATA_DIR
from sampling.pipeline import SamplingPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    data_dir = Path(DATA_DIR)
    if not data_dir.is_dir():
        logger.error("Data directory does not exist: %s (set DATA_DIR in project_config.py)", data_dir)
        return 1

    pipeline = SamplingPipeline(str(data_dir))
    stats = pipeline.run()

    if not stats:
        logger.warning("No events.db found in %s", data_dir)
        return 0

    logger.info("Done. %d comments sampled across %d strata.", stats["total"], len(stats["strata"]))
    return 0


if __name__ == "__main__":
    exit(main())
