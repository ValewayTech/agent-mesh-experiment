"""Sample transcripts for manual review:  python scripts/spot_check.py results/<run> --n 12"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from meshexp.cli import main  # noqa: E402

sys.exit(main(["spotcheck", *sys.argv[1:]]))
