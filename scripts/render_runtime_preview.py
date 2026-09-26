#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

p = Path(__file__).with_name("generate_runtime.py")
spec = importlib.util.spec_from_file_location("generate_runtime", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("# --- service manifest ---")
import json
print(json.dumps(mod.manifest(), indent=2))
print("\n# --- Caddyfile ---")
print(mod.caddyfile())
