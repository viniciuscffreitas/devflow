"""
PreCompact hook — salva estado antes do auto-compaction.
Captura: session ID, trigger, spec ativa, e diretorio de trabalho.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import get_session_id, get_state_dir, read_hook_stdin


def _find_active_spec() -> dict | None:
    plans_dir = Path.home() / ".claude" / "plans"
    if not plans_dir.exists():
        return None

    def safe_mtime(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except OSError:
            return 0.0

    plan_files = sorted(plans_dir.glob("*.md"), key=safe_mtime, reverse=True)
    for plan_file in plan_files[:5]:
        try:
            content = plan_file.read_text()
            if "IMPLEMENTING" in content or "in_progress" in content.lower():
                return {"plan_path": str(plan_file), "status": "IMPLEMENTING"}
        except OSError:
            continue
    return None


def main() -> int:
    hook_data = read_hook_stdin()
    state_dir = get_state_dir()

    state = {
        "session_id": get_session_id(),
        "trigger": hook_data.get("trigger", "auto"),
        "active_spec": _find_active_spec(),
        "cwd": os.getcwd(),
    }

    state_file = state_dir / "pre-compact.json"
    try:
        state_file.write_text(json.dumps(state, indent=2))
    except OSError as e:
        print(f"[devflow] ERROR: could not save pre-compact state: {e}", file=sys.stderr)
        return 1

    print("[devflow] Estado salvo antes da compaction", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
