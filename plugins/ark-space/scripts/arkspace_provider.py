#!/usr/bin/env python3
"""Repository-root wrapper for the provider-manager skill script."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "provider-manager" / "scripts" / "arkspace_provider.py"

sys.path.insert(0, str(SCRIPT.parent))
runpy.run_path(str(SCRIPT), run_name="__main__")
