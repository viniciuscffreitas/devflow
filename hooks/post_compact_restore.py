"""
SessionStart(compact) hook — restaura contexto apos compaction.
Le estado salvo pelo pre_compact.py e injeta no contexto via stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import get_state_dir


def main() -> int:
    state_dir = get_state_dir()
    state_file = state_dir / "pre-compact.json"

    if not state_file.exists():
        sys.exit(0)

    try:
        state = json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    lines = ["[devflow Context Restored After Compaction]"]

    active_spec = state.get("active_spec")
    if active_spec:
        plan_path = active_spec.get("plan_path", "Unknown")
        status = active_spec.get("status", "Unknown")
        lines.append(f"Active Spec: {plan_path} (Status: {status})")
        lines.append("Resume from where you left off using the plan above.")
    else:
        lines.append("No active spec was in progress.")

    cwd = state.get("cwd")
    if cwd:
        lines.append(f"Working directory: {cwd}")

    try:
        state_file.unlink()
    except OSError:
        pass

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
