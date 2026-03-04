"""Utilitários compartilhados para hooks do devflow."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from enum import Enum, auto
from pathlib import Path
from typing import Optional

# Limites de tamanho de arquivo
FILE_LINES_WARN = 400
FILE_LINES_CRITICAL = 600

# Threshold de contexto
CONTEXT_WINDOW_TOKENS = 200_000
AUTOCOMPACT_BUFFER_TOKENS = 33_000
CONTEXT_WARN_PCT = 80.0
CONTEXT_CAUTION_PCT = 90.0


class ToolchainKind(Enum):
    NODEJS = auto()
    FLUTTER = auto()
    MAVEN = auto()
    RUST = auto()
    GO = auto()


_TOOLCHAIN_FINGERPRINTS: list[tuple[str, ToolchainKind]] = [
    ("package.json", ToolchainKind.NODEJS),
    ("pubspec.yaml", ToolchainKind.FLUTTER),
    ("pom.xml", ToolchainKind.MAVEN),
    ("mvnw", ToolchainKind.MAVEN),
    ("Cargo.toml", ToolchainKind.RUST),
    ("go.mod", ToolchainKind.GO),
]


def detect_toolchain_root(start_dir: Path, max_levels: int = 4) -> Optional[ToolchainKind]:
    current = start_dir
    for _ in range(max_levels):
        for filename, kind in _TOOLCHAIN_FINGERPRINTS:
            if (current / filename).exists():
                return kind
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def check_file_length(file_path: Path) -> tuple[bool, bool]:
    try:
        lines = len(file_path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return False, False
    return lines > FILE_LINES_WARN, lines > FILE_LINES_CRITICAL


def read_hook_stdin() -> dict:
    try:
        content = sys.stdin.read()
        if content.strip():
            return json.loads(content)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def get_edited_file(hook_data: dict) -> Optional[Path]:
    file_path = hook_data.get("tool_input", {}).get("file_path")
    if file_path:
        return Path(file_path)
    return None


def get_session_id() -> str:
    return os.environ.get("CLAUDE_SESSION_ID", "default")


def get_state_dir() -> Path:
    state_dir = Path.home() / ".claude" / "devflow" / "state" / get_session_id()
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def run_command(cmd: list[str], cwd: Optional[Path] = None, timeout: int = 30) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, f"timeout após {timeout}s"
    except FileNotFoundError:
        return 127, f"comando não encontrado: {cmd[0]}"
    except Exception as e:
        return 1, str(e)


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def hook_context(context: str) -> str:
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    })


def hook_block(reason: str) -> str:
    return json.dumps({"decision": "block", "reason": reason})


def hook_deny(reason: str) -> str:
    return json.dumps({"permissionDecision": "deny", "reason": reason})


def hook_stop_block(reason: str) -> str:
    return json.dumps({"decision": "block", "reason": reason})
