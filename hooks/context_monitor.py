"""
PostToolUse hook (broad matcher) — monitora uso do contexto.
Avisa em ~80% e ~90%. Non-blocking.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import (
    AUTOCOMPACT_BUFFER_TOKENS,
    CONTEXT_CAUTION_PCT,
    CONTEXT_WARN_PCT,
    CONTEXT_WINDOW_TOKENS,
    hook_context,
    read_hook_stdin,
)


def tokens_to_pct(tokens_used: int, window: int = CONTEXT_WINDOW_TOKENS) -> float:
    compaction_threshold = window - AUTOCOMPACT_BUFFER_TOKENS
    return min(100.0, (tokens_used / compaction_threshold) * 100)


def main() -> int:
    hook_data = read_hook_stdin()
    tokens_used = hook_data.get("context_tokens_used", 0)
    if not tokens_used:
        sys.exit(0)

    pct = tokens_to_pct(tokens_used)

    if pct >= CONTEXT_CAUTION_PCT:
        msg = (
            f"[devflow] Contexto em {pct:.0f}% — "
            f"Conclua a tarefa atual. Auto-compaction sera disparado em breve."
        )
        print(hook_context(msg))
    elif pct >= CONTEXT_WARN_PCT:
        msg = (
            f"[devflow] Contexto em {pct:.0f}% — "
            f"Considere usar /learn para capturar descobertas importantes."
        )
        print(hook_context(msg))

    sys.exit(0)


if __name__ == "__main__":
    main()
