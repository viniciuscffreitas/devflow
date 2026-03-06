"""
Stop hook — bloqueia encerramento se spec ativa esta IMPLEMENTING, PENDING ou in_progress.
Also cleans up the discovery-ran marker so no future session inherits stale state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import get_state_dir, hook_block


def _has_active_spec() -> tuple[bool, str]:
    state_dir = get_state_dir()
    active_file = state_dir / "active-spec.json"
    if active_file.exists():
        try:
            data = json.loads(active_file.read_text())
            status = data.get("status", "")
            if status in ("IMPLEMENTING", "PENDING", "in_progress"):
                plan_path = data.get("plan_path", "unknown")
                return True, f"{plan_path} ({status})"
        except (json.JSONDecodeError, OSError) as e:
            # Fail closed: if file exists but is corrupt, assume spec is active
            print(f"[devflow] WARNING: could not read active-spec, assuming active: {e}", file=sys.stderr)
            return True, "unknown (corrupt state file)"
    return False, ""


def _cleanup_discovery_marker() -> None:
    state_dir = get_state_dir()
    marker = state_dir / "discovery-ran"
    try:
        marker.unlink(missing_ok=True)
    except OSError:
        pass


def main() -> int:
    active, description = _has_active_spec()
    if active:
        reason = (
            f"[devflow] Spec ativa detectada: {description}\n"
            f"Conclua ou use /pause para pausar explicitamente.\n"
            f"Apos /pause, o encerramento sera liberado."
        )
        print(hook_block(reason))

    _cleanup_discovery_marker()
    return 0


if __name__ == "__main__":
    sys.exit(main())
