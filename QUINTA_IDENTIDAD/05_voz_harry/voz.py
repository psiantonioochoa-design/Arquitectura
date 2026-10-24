"""Punto de entrada: python3 -I voz.py <orden> ...   (desde 05_voz_harry; sirve el Python 3.9 del sistema)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from voz_harry.cli import main  # noqa: E402

raise SystemExit(main())
