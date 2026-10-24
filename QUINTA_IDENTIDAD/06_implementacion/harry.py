"""Punto de entrada: python3 -I /Volumes/NOUS/QUINTA_IDENTIDAD/06_implementacion/harry.py <orden> ..."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "codigo"))

from harry_nucleo.cli import main  # noqa: E402

raise SystemExit(main())
