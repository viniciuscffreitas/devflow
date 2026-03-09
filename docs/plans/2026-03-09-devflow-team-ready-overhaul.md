# Devflow Team-Ready Overhaul

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all known devflow bugs, convert everything from Portuguese to English, and make devflow ready for team adoption.

**Architecture:** Each task targets non-overlapping files so all tasks can run in parallel. Every task includes both the functional fix AND the i18n conversion for its files. Tests are updated alongside production code.

**Tech Stack:** Python 3.x (hooks), Markdown (skills/CLAUDE.md), pytest (test suite)

**Test command:** `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/ -v`

**Pre-existing state:** 4 tests failing in `test_file_checker.py` (missing `config` arg). 71 passing.

---

## Task 1: Fix `_util.py` — i18n error messages

**Files:**
- Modify: `hooks/_util.py:128-132` (Portuguese error messages in `run_command`)
- Modify: `hooks/tests/test_util.py:134` (test assertion for Portuguese string)

- [ ] **Step 1: Update `run_command` error messages to English**

In `hooks/_util.py`, change:
```python
# Line 128
return 1, f"timeout após {timeout}s"
# Line 130
return 127, f"comando não encontrado: {cmd[0]}"
```
To:
```python
return 1, f"timeout after {timeout}s"
return 127, f"command not found: {cmd[0]}"
```

- [ ] **Step 2: Update test assertion**

In `hooks/tests/test_util.py`, line 134:
```python
# Old
assert "não encontrado" in msg or "not found" in msg.lower()
# New
assert "not found" in msg.lower()
```

- [ ] **Step 3: Update module docstring to English**

```python
"""Shared utilities for devflow hooks."""
```
(Already in English — verify no other Portuguese strings remain)

- [ ] **Step 4: Run tests**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/test_util.py -v`
Expected: All 22 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/vini/.claude/devflow
git add hooks/_util.py hooks/tests/test_util.py
git commit -m "fix: convert _util.py error messages to English"
```

---

## Task 2: Fix `discovery_scan.py` — learned skills detection + non-project handling + i18n

**Files:**
- Modify: `hooks/discovery_scan.py`

**Bug 1:** `LEARNED_SKILLS=none` even when permanent skills exist in `~/.claude/skills/devflow-learned-*`. The scan only counts dynamically injected symlinks, ignoring permanently installed skills.

**Bug 2:** When not in a project directory, outputs `TOOLCHAIN=unknown` and `TEST_FRAMEWORK=unknown` instead of a clear signal.

- [ ] **Step 1: Add function to count all installed learned skills**

After `_manage_symlinks`, add:
```python
def _count_all_learned_skills() -> list[str]:
    """Return names of ALL installed learned skills (permanent + injected)."""
    installed = []
    if not SKILLS_DIR.is_dir():
        return installed
    for entry in SKILLS_DIR.iterdir():
        if entry.name.startswith("devflow-learned-") and entry.is_dir():
            installed.append(entry.name)
    return sorted(installed)
```

- [ ] **Step 2: Update `main()` to use `_count_all_learned_skills`**

Replace in `main()`:
```python
    # Old: only reports injected (symlinked) skills
    if injected:
        lines.append(f"LEARNED_SKILLS={','.join(injected)}")
    else:
        lines.append("LEARNED_SKILLS=none")
```
With:
```python
    all_learned = _count_all_learned_skills()
    if all_learned:
        lines.append(f"LEARNED_SKILLS={','.join(all_learned)}")
    else:
        lines.append("LEARNED_SKILLS=none")
```

Also update profile dict:
```python
    profile = {
        ...
        "injected_skills": injected,
        "all_learned_skills": all_learned,
    }
```

- [ ] **Step 3: Fix non-project directory handling**

In `main()`, after `toolchain, _ = detect_toolchain(project_root)`, add logic to detect if we're actually in a project:
```python
    # Detect if we found a real project or just fell back to cwd
    in_project = (project_root != cwd) or any(
        (cwd / marker).exists()
        for marker in [".git", "package.json", "pubspec.yaml", "Cargo.toml", "go.mod", "pom.xml"]
    )
```

Then update output:
```python
    tc_label = toolchain.name if toolchain else ("none" if not in_project else "unknown")
    tf_label = test_framework if in_project else ("none" if not in_project else test_framework)
    ...
    lines.append(f"TOOLCHAIN={tc_label}")
    if not in_project:
        lines.append("PROJECT=none (not in a project directory)")
```

- [ ] **Step 4: Update docstring to English**

```python
"""
SessionStart hook — project discovery scan (devflow v2.2).
Detects: issue tracker, toolchain, design system, test framework.
Manages learned skill symlinks based on detected technologies.
Outputs project profile to context.
"""
```
(Already in English — verify)

- [ ] **Step 5: Run tests**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/ -v -k "not test_length_message"`
Expected: All non-file-checker-length tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/vini/.claude/devflow
git add hooks/discovery_scan.py
git commit -m "fix: report all learned skills and handle non-project directories"
```

---

## Task 3: Fix `file_checker.py` — pre-existing test bug + Maven checker + i18n

**Files:**
- Modify: `hooks/file_checker.py:1-4,50-64` (docstring + Portuguese strings + add Maven)
- Modify: `hooks/tests/test_file_checker.py:45-69` (fix missing config arg + add Maven test)

- [ ] **Step 1: Fix failing tests — add config arg**

In `hooks/tests/test_file_checker.py`, update all 4 `get_length_message` calls:
```python
def test_length_message_warn(tmp_path):
    f = tmp_path / "big.py"
    f.write_text("\n".join(["x"] * 450))
    msg = get_length_message(f, {})
    assert "GROWING" in msg
    assert "450" in msg


def test_length_message_critical(tmp_path):
    f = tmp_path / "huge.py"
    f.write_text("\n".join(["x"] * 650))
    msg = get_length_message(f, {})
    assert "TOO LONG" in msg


def test_length_message_ok(tmp_path):
    f = tmp_path / "small.py"
    f.write_text("x\n" * 50)
    msg = get_length_message(f, {})
    assert msg == ""


def test_length_message_missing():
    msg = get_length_message(Path("/nonexistent/file.py"), {})
    assert msg == ""
```

- [ ] **Step 2: Run fixed tests to verify**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/test_file_checker.py -v`
Expected: All 10 tests PASS

- [ ] **Step 3: Convert Portuguese strings to English**

In `hooks/file_checker.py`, update docstring and messages:
```python
"""
PostToolUse hook (Write|Edit|MultiEdit) — language-agnostic quality checker.
Detects toolchain, runs format+lint, warns about file size.
"""
```

Update `get_length_message`:
```python
    if critical:
        return (
            f"FILE TOO LONG: {file_path.name} has {lines} lines "
            f"(critical: {critical_limit}). Must split into smaller modules."
        )
    return (
        f"FILE GROWING: {file_path.name} has {lines} lines "
        f"(warn: {warn_limit}). Consider splitting."
    )
```

- [ ] **Step 4: Add Maven checker**

Add after `_check_rust`:
```python
def _check_maven(file_path: Path, project_root: Path) -> list[str]:
    issues = []
    mvnw = project_root / "mvnw"
    mvn_cmd = str(mvnw) if mvnw.exists() else shutil.which("mvn")
    if not mvn_cmd:
        return issues
    if file_path.suffix == ".java":
        code, output = run_command([mvn_cmd, "compile", "-q"], cwd=project_root, timeout=60)
        if code != 0 and output:
            lines = [l for l in output.splitlines() if "ERROR" in l or "[ERROR]" in l][:5]
            if lines:
                issues.append("Maven compile: " + "\n".join(lines))
    return issues
```

Update `_CHECKERS`:
```python
_CHECKERS = {
    ToolchainKind.NODEJS: _check_nodejs,
    ToolchainKind.FLUTTER: _check_flutter,
    ToolchainKind.GO: _check_go,
    ToolchainKind.RUST: _check_rust,
    ToolchainKind.MAVEN: _check_maven,
}
```

- [ ] **Step 5: Add Maven checker test**

In `hooks/tests/test_file_checker.py`, add:
```python
from file_checker import _check_maven

def test_maven_checker_no_mvn(tmp_path, monkeypatch):
    """When neither mvnw nor mvn exist, returns no issues."""
    monkeypatch.setattr("shutil.which", lambda x: None)
    f = tmp_path / "App.java"
    f.write_text("public class App {}")
    issues = _check_maven(f, tmp_path)
    assert issues == []
```

- [ ] **Step 6: Run all tests**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/test_file_checker.py -v`
Expected: All 11+ tests PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/vini/.claude/devflow
git add hooks/file_checker.py hooks/tests/test_file_checker.py
git commit -m "fix: repair test failures, add Maven checker, convert to English"
```

---

## Task 4: Fix `tdd_enforcer.py` — deeper search + monorepo + i18n

**Files:**
- Modify: `hooks/tdd_enforcer.py:1-4,75-90,106-110`
- Modify: `hooks/tests/test_tdd_enforcer.py` (add monorepo + depth tests)

- [ ] **Step 1: Convert docstring and messages to English**

```python
"""
PostToolUse hook (Write|Edit|MultiEdit) — warns about implementation without tests.
Non-blocking: never blocks, only advises with suggested test path.
"""
```

Update message in `main()`:
```python
        context = (
            f"[devflow TDD] {file_path.name}: implementation without corresponding test.\n"
            f"Suggestion: create `{suggested}`\n"
            f"TDD: RED -> GREEN -> REFACTOR"
        )
```

- [ ] **Step 2: Increase search depth and add monorepo support**

Replace `find_test_file`:
```python
def find_test_file(impl_path: Path, max_depth: int = 5) -> bool:
    stem = impl_path.stem
    root = impl_path.parent

    # Standard test directories
    test_dir_names = ["tests", "test", "__tests__"]

    # Monorepo patterns — check laterally
    monorepo_test_dirs = ["packages/*/test", "packages/*/tests", "apps/*/test", "apps/*/tests"]

    for _ in range(max_depth):
        # Check standard test dirs with targeted glob (not rglob)
        for test_dir in test_dir_names:
            td = root / test_dir
            if td.is_dir():
                # Use targeted patterns instead of rglob for performance
                for pattern in [f"test_{stem}.*", f"{stem}_test.*", f"{stem}.test.*", f"{stem}.spec.*", f"**/test_{stem}.*", f"**/{stem}_test.*", f"**/{stem}.test.*"]:
                    if list(td.glob(pattern)):
                        return True

        # Check sibling test files
        for pattern in [f"test_{stem}", f"{stem}_test", f"{stem}.test", f"{stem}.spec"]:
            for ext in _IMPL_EXTENSIONS:
                if (root / f"{pattern}{ext}").exists():
                    return True

        # Check monorepo patterns from this level
        for mono_pattern in monorepo_test_dirs:
            for td in root.glob(mono_pattern):
                if td.is_dir():
                    for pattern in [f"**/*{stem}*"]:
                        for f in td.glob(pattern):
                            if is_test_file(f):
                                return True

        root = root.parent
        if root == root.parent:
            break

    return False
```

- [ ] **Step 3: Add test for deeper search**

In `hooks/tests/test_tdd_enforcer.py`, add:
```python
def test_find_test_file_deep_nested(tmp_path):
    """Test finds tests 4+ levels up."""
    impl_dir = tmp_path / "src" / "features" / "auth" / "login"
    impl_dir.mkdir(parents=True)
    impl = impl_dir / "service.py"
    impl.write_text("class Service: pass")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_file = tests_dir / "test_service.py"
    test_file.write_text("def test_service(): pass")
    assert find_test_file(impl)


def test_find_test_file_monorepo(tmp_path):
    """Test finds tests in monorepo packages/*/test layout."""
    pkg = tmp_path / "packages" / "auth" / "src"
    pkg.mkdir(parents=True)
    impl = pkg / "handler.py"
    impl.write_text("def handle(): pass")
    test_dir = tmp_path / "packages" / "auth" / "test"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_handler.py"
    test_file.write_text("def test_handle(): pass")
    assert find_test_file(impl)
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/test_tdd_enforcer.py -v`
Expected: All 16 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/vini/.claude/devflow
git add hooks/tdd_enforcer.py hooks/tests/test_tdd_enforcer.py
git commit -m "fix: deepen test search, add monorepo support, convert to English"
```

---

## Task 5: Fix `spec_stop_guard.py` — timestamp expiry + i18n

**Files:**
- Modify: `hooks/spec_stop_guard.py`
- Modify: `hooks/tests/test_spec_stop_guard.py`

- [ ] **Step 1: Convert to English and add timestamp check**

Rewrite `hooks/spec_stop_guard.py`:
```python
"""
Stop hook — blocks session exit if an active spec is IMPLEMENTING, PENDING, or in_progress.
Also cleans up the discovery-ran marker so no future session inherits stale state.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import get_state_dir, hook_block

# Specs older than 24 hours are considered abandoned
SPEC_EXPIRY_SECONDS = 24 * 60 * 60


def _has_active_spec() -> tuple[bool, str]:
    state_dir = get_state_dir()
    active_file = state_dir / "active-spec.json"
    if active_file.exists():
        try:
            data = json.loads(active_file.read_text())
            status = data.get("status", "")
            if status in ("IMPLEMENTING", "PENDING", "in_progress"):
                # Check timestamp — abandon if too old
                started_at = data.get("started_at", 0)
                if started_at and (time.time() - started_at) > SPEC_EXPIRY_SECONDS:
                    return False, ""
                plan_path = data.get("plan_path", "unknown")
                return True, f"{plan_path} ({status})"
        except (json.JSONDecodeError, OSError) as e:
            # Fail-safe: corrupt file should NOT block forever
            # Check file age as fallback
            try:
                file_age = time.time() - active_file.stat().st_mtime
                if file_age > SPEC_EXPIRY_SECONDS:
                    return False, ""
            except OSError:
                pass
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
            f"[devflow] Active spec detected: {description}\n"
            f"Complete it or use /pause to explicitly pause.\n"
            f"After /pause, session exit will be allowed."
        )
        print(hook_block(reason))

    _cleanup_discovery_marker()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Update tests — add timestamp expiry tests**

In `hooks/tests/test_spec_stop_guard.py`, add:
```python
import time

def test_expired_spec_not_active(tmp_path):
    """Spec older than 24h should not block exit."""
    state_dir = _make_state_dir(tmp_path)
    old_time = time.time() - (25 * 60 * 60)  # 25 hours ago
    spec = {"status": "IMPLEMENTING", "plan_path": "/plans/old.md", "started_at": old_time}
    (state_dir / "active-spec.json").write_text(json.dumps(spec))
    with patch("spec_stop_guard.get_state_dir", return_value=state_dir):
        active, desc = _has_active_spec()
    assert not active


def test_recent_spec_still_active(tmp_path):
    """Spec younger than 24h should still block."""
    state_dir = _make_state_dir(tmp_path)
    recent_time = time.time() - (2 * 60 * 60)  # 2 hours ago
    spec = {"status": "IMPLEMENTING", "plan_path": "/plans/wip.md", "started_at": recent_time}
    (state_dir / "active-spec.json").write_text(json.dumps(spec))
    with patch("spec_stop_guard.get_state_dir", return_value=state_dir):
        active, desc = _has_active_spec()
    assert active


def test_corrupt_json_old_file_not_active(tmp_path):
    """Corrupt file older than 24h should NOT block (fail-safe)."""
    state_dir = _make_state_dir(tmp_path)
    spec_file = state_dir / "active-spec.json"
    spec_file.write_text("{invalid json!!!")
    # Make file appear old
    old_time = time.time() - (25 * 60 * 60)
    import os
    os.utime(spec_file, (old_time, old_time))
    with patch("spec_stop_guard.get_state_dir", return_value=state_dir):
        active, desc = _has_active_spec()
    assert not active
```

- [ ] **Step 3: Run tests**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/test_spec_stop_guard.py -v`
Expected: All 10 tests PASS (7 existing + 3 new)

- [ ] **Step 4: Commit**

```bash
cd /Users/vini/.claude/devflow
git add hooks/spec_stop_guard.py hooks/tests/test_spec_stop_guard.py
git commit -m "fix: add 24h expiry for stale specs, fail-safe on corruption, English strings"
```

---

## Task 6: Fix `context_monitor.py` + `pre_compact.py` + `post_compact_restore.py` — i18n

**Files:**
- Modify: `hooks/context_monitor.py` (Portuguese messages)
- Modify: `hooks/pre_compact.py` (Portuguese docstring + stderr message)
- Modify: `hooks/post_compact_restore.py` (Portuguese docstring)

- [ ] **Step 1: Convert `context_monitor.py` messages to English**

```python
"""
PostToolUse hook (broad matcher) — monitors context window usage.
Warns at ~80% and ~90%. Non-blocking.
"""
```

Update messages:
```python
    if pct >= CONTEXT_CAUTION_PCT:
        msg = (
            f"[devflow] Context at {pct:.0f}% — "
            f"Wrap up your current task. Auto-compaction will trigger soon."
        )
    elif pct >= CONTEXT_WARN_PCT:
        msg = (
            f"[devflow] Context at {pct:.0f}% — "
            f"Consider using /learn to capture important discoveries."
        )
```

- [ ] **Step 2: Convert `pre_compact.py` to English**

```python
"""
PreCompact hook — saves state before auto-compaction.
Captures: session ID, trigger, active spec, working directory, and project profile.
"""
```

Update stderr message:
```python
    print("[devflow] State saved before compaction", file=sys.stderr)
```

- [ ] **Step 3: Convert `post_compact_restore.py` to English**

```python
"""
SessionStart(compact) hook — restores context after compaction.
Reads state saved by pre_compact.py and injects into context via stdout.
Includes project profile for immediate continuity.
Output protocol: plain text lines to stdout (SessionStart hooks use text, not JSON).
"""
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/test_context_monitor.py hooks/tests/test_compact_hooks.py -v`
Expected: All 16 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/vini/.claude/devflow
git add hooks/context_monitor.py hooks/pre_compact.py hooks/post_compact_restore.py
git commit -m "fix: convert context_monitor, pre_compact, post_compact_restore to English"
```

---

## Task 7: Convert core skills to English

**Files:**
- Modify: `~/.claude/skills/devflow-spec-driven-dev/SKILL.md`
- Modify: `~/.claude/skills/devflow-behavior-contract/SKILL.md`
- Modify: `~/.claude/skills/devflow-wizard/SKILL.md`
- Modify: `~/.claude/skills/devflow-agent-orchestration/SKILL.md`
- Modify: `~/.claude/skills/devflow-model-routing/SKILL.md`

- [ ] **Step 1: Rewrite `devflow-spec-driven-dev/SKILL.md` in English**

Full rewrite keeping exact same structure but all content in English. Key translations:
- "Deteccao de Tipo" → "Type Detection"
- "funcionalidade nova" → "new functionality"
- "comportamento existente que esta errado" → "existing behavior that is broken"
- "descreva arquitetura" → "describe architecture"
- "apresente ao usuario" → "present to user"
- All TDD cycle, rules, review gate, frontend gate → English
- "NUNCA" → "NEVER"
- "obrigatorio" → "mandatory"

- [ ] **Step 2: Rewrite `devflow-behavior-contract/SKILL.md` in English**

Key translations:
- "Proposito" → "Purpose"
- "MUDA" → "CHANGES" (behavior that will change)
- "NAO MUDA" → "MUST NOT CHANGE" (behavior that must be preserved)
- "PROVA" → "PROOF" (tests that validate the contract)
- "Regras Criticas" → "Critical Rules"
- "PARE, revise contrato" → "STOP, revise contract"
- Example stays same format but with English labels

- [ ] **Step 3: Rewrite `devflow-wizard/SKILL.md` in English**

Key translations:
- "Operacoes Destrutivas" → "Destructive Operations"
- "Proposito" → "Purpose"
- "FASE" → "PHASE"
- "ANALISE" → "ANALYZE"
- "APRESENTACAO" → "PRESENT"
- "PLANO DETALHADO" → "DETAILED PLAN"
- "EXECUCAO" → "EXECUTE"
- "Regras" → "Rules"

- [ ] **Step 4: Rewrite `devflow-agent-orchestration/SKILL.md` in English**

Key translations:
- "Regra Arquitetural Critica" → "Critical Architectural Rule"
- "Padroes" → "Patterns"
- "ordem crescente de complexidade" → "increasing complexity order"
- "Quando" / "Exemplo" → "When" / "Example"
- All pattern descriptions → English
- Decision flowchart → English

- [ ] **Step 5: Rewrite `devflow-model-routing/SKILL.md` with realistic guidance**

Complete rewrite:
- Remove "Tabela de Decisao" → "Decision Table"
- Remove aspirational mid-session switching claims
- Add practical guidance: model selection is relevant for `/model` command between tasks and for subagent dispatching
- Keep model recommendations table but in English
- Add concrete examples of when to use each model
- Add section on subagent model selection (where it actually works)

- [ ] **Step 6: Commit**

```bash
cd /Users/vini/.claude/devflow
git add ~/.claude/skills/devflow-spec-driven-dev/SKILL.md \
        ~/.claude/skills/devflow-behavior-contract/SKILL.md \
        ~/.claude/skills/devflow-wizard/SKILL.md \
        ~/.claude/skills/devflow-agent-orchestration/SKILL.md \
        ~/.claude/skills/devflow-model-routing/SKILL.md
git commit -m "feat: convert all core skills to English"
```

---

## Task 8: Convert learned skills to English

**Files:**
- Modify: `~/.claude/skills/devflow-learned-dart-format-after-merge/SKILL.md`
- Modify: `~/.claude/skills/devflow-learned-ci-optimization/SKILL.md`
- Modify: `~/.claude/skills/devflow-learned-bloc-future-callsites/SKILL.md`
- Modify: `~/.claude/skills/devflow-learned-run-ci-locally/SKILL.md`

- [ ] **Step 1: Rewrite dart-format-after-merge in English**

Keep code blocks identical. Translate all prose:
- "dart format obrigatorio apos merge" → "Mandatory dart format after merge"
- "Trigger" section → English
- "O Problema" → "The Problem"
- "Solucao" → "Solution"
- "Checklist pos-merge" → "Post-merge checklist"

- [ ] **Step 2: Rewrite ci-optimization in English**

Keep all code blocks and YAML identical. Translate prose:
- "Flutter CI Otimizacao — Custo e Tempo" → "Flutter CI Optimization — Cost & Speed"
- "Padrao: Pre-push hook" → "Pattern: Pre-push hook"
- "Armadilhas" → "Pitfalls"
- "Regra de ouro" → "Golden rule"

- [ ] **Step 3: Rewrite bloc-future-callsites in English**

Keep code blocks identical. Most is already partially English. Translate remaining Portuguese.

- [ ] **Step 4: Rewrite run-ci-locally in English**

Keep code blocks identical. Translate prose:
- "Rodar CI Completo Localmente Antes de Push" → "Run Full CI Locally Before Push"
- "Quando usar" → "When to use"
- "Armadilhas comuns" → "Common pitfalls"
- "Regra de ouro" → "Golden rule"

- [ ] **Step 5: Commit**

```bash
cd /Users/vini/.claude/devflow
git add ~/.claude/skills/devflow-learned-dart-format-after-merge/SKILL.md \
        ~/.claude/skills/devflow-learned-ci-optimization/SKILL.md \
        ~/.claude/skills/devflow-learned-bloc-future-callsites/SKILL.md \
        ~/.claude/skills/devflow-learned-run-ci-locally/SKILL.md
git commit -m "feat: convert all learned skills to English"
```

---

## Task 9: Rewrite CLAUDE.md in English

**Files:**
- Modify: `~/.claude/CLAUDE.md`

- [ ] **Step 1: Full rewrite in English**

```markdown
## devflow v2.2 — Workflow & Quality

### When to use /spec
Use `/spec "description"` for any non-trivial task:
- Features that add new behavior
- Bugfixes (auto-detects -> Behavior Contract)
- Refactoring with non-trivial scope

Skip /spec only for trivial 1-2 line changes.

### TDD
- RED: write the test describing behavior -> run -> MUST FAIL
- GREEN: implement minimum to pass -> run -> MUST PASS
- REFACTOR: improve without breaking -> run -> MUST PASS
- COMMIT: atomic commit per behavior

### Verification (mandatory before "done")
1. Lint / static analysis for the project
2. Full build (if applicable)
3. Complete test suite

### Model Routing
- `claude-opus-4-6` -> planning, design, complex trade-offs
- `claude-sonnet-4-6` -> implementation, refactoring, debugging (default)
- `claude-haiku-4-5-20251001` -> search, formatting, simple transformations

### Code Quality
- File length limits configurable via `devflow-config.json` (global: `~/.claude/devflow/`, project: `.devflow-config.json`)
- Default: >400 lines warning, >600 lines mandatory split
- No TODO without associated issue
- Atomic, descriptive commits

### Issue Tracker (agnostic)
- Discovery scan auto-detects the project tracker (Linear, GitHub Issues, Jira, TODO.md)
- `[devflow:project-profile]` is injected each session with `ISSUE_TRACKER_TYPE`
- Review Gate generates tech debt drafts in the tracker's native format
- NEVER create issues automatically — always present drafts for manual approval
- If no tracker detected: plaintext drafts to stdout

### Destructive Operations
Any delete, reset, migration, or irreversible overwrite:
-> Use `devflow:wizard` (explicit confirmation mandatory)

### Frontend & UX
- **Design System first**: always consult existing tokens, components, and patterns before creating new ones
- **Visual silence**: every element on screen must justify its presence — remove noise, don't add it
- **Low cognitive load**: clear hierarchy, one primary action per screen, progressive disclosure
- **WCAG**: minimum AA contrast, don't rely on color alone, keyboard navigation must work
- **Custom states**: replace default browser focus rings with design system visual states
- **Crafted with care**: polished micro-interactions (smooth transitions, tactile feedback, purposeful animations — not decorative)
- **Frontend Gate mandatory**: before coding UI, invoke `frontend-design:frontend-design`

### Review Gate
- Before declaring DONE on any non-trivial task, run `pr-review-toolkit:review-pr`
- Review validates logic, quality, regressions, and design system adherence
- Issues found in review: fix before proceeding

### Learned Skills (single-session focus)
- devflow is single-session: learned skills are injected via global symlinks in `~/.claude/skills/`
- Two simultaneous sessions on different projects cause race conditions on symlinks
- For parallel sessions: set `"learned_skills_auto_inject": false` in `devflow-config.json` or project `.devflow-config.json`
- Skills loaded at session start survive symlink removal — the real risk is only during concurrent compaction

### Subagents
- Subagents DO NOT spawn other subagents
- All delegation flows through the Main Agent
- For independent parallel tasks: `superpowers:dispatching-parallel-agents`
```

- [ ] **Step 2: Commit**

```bash
cd /Users/vini/.claude/devflow
git add ~/.claude/CLAUDE.md
git commit -m "feat: rewrite CLAUDE.md in English for team adoption"
```

---

## Final Verification

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/vini/.claude/devflow && python3 -m pytest hooks/tests/ -v`
Expected: ALL tests PASS (75+ tests, 0 failures)

- [ ] **Step 2: Grep for remaining Portuguese**

Run: `grep -rn "NUNCA\|obrigatorio\|não\|após\|Conclua\|Considere\|implementacao\|Proposito\|Quando\|Solucao" hooks/ ~/.claude/skills/devflow-*/ ~/.claude/CLAUDE.md --include="*.py" --include="*.md" 2>/dev/null`
Expected: No matches (all Portuguese removed)

- [ ] **Step 3: Final commit if any stragglers**

Fix any remaining Portuguese strings found in Step 2.
