"""
Pipeline to clean dataset_reader output (CONFORMITY.md Preprocessing).
Uses a chainable workflow of steps; reads JSONL, runs workflow per event, writes cleaned JSONL.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional

from preprocessing.workflow import Workflow, default_workflow

logger = logging.getLogger(__name__)


def clean_jsonl_file(
    workflow: Workflow,
    input_path: Path,
    output_path: Path,
) -> tuple[int, int]:
    """Read JSONL from input_path, run workflow on each event, write kept events to output_path. Returns (read_count, written_count)."""
    read_count = 0
    written_count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(input_path, "r", encoding="utf-8") as f_in:
        with open(output_path, "w", encoding="utf-8") as f_out:
            for line in f_in:
                line = line.strip()
                if not line:
                    continue
                read_count += 1
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cleaned = workflow.run(event)
                if cleaned is not None:
                    json.dump(cleaned, f_out, ensure_ascii=False)
                    f_out.write("\n")
                    written_count += 1
    return read_count, written_count


class CleanerPipeline:
    """Run a preprocessing workflow on all JSONL files in a directory (output of dataset.py)."""

    def __init__(self, input_dir: str, output_dir: str, workflow: Optional[Workflow] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.workflow = workflow if workflow is not None else default_workflow()

    def run(self) -> List[tuple[str, int, int]]:
        """
        Find all .jsonl files in input_dir (ignore .meta.json), run workflow on each event, write to output_dir.
        Returns list of (filename, read_count, written_count).
        """
        results = []
        files = sorted(self.input_dir.glob("*.jsonl"))
        for path in files:
            if path.name.endswith(".meta.json"):
                continue
            out_path = self.output_dir / path.name
            read_count, written_count = clean_jsonl_file(self.workflow, path, out_path)
            results.append((path.name, read_count, written_count))
            logger.info(
                "%s: read %s, kept %s",
                path.name,
                read_count,
                written_count,
            )
        return results
