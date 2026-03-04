"""
PostToolUse hook (Write|Edit|MultiEdit) — quality checker agnóstico de linguagem.
Detecta toolchain, roda format+lint, avisa sobre tamanho de arquivo.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import (
    ToolchainKind,
    check_file_length,
    detect_toolchain_root,
    get_edited_file,
    hook_context,
    read_hook_stdin,
    run_command,
    which,
    FILE_LINES_WARN,
    FILE_LINES_CRITICAL,
)

_SKIP_PATTERNS = {
    "test_", "_test.", ".test.", "_spec.", ".spec.",
    "conftest.", "fixture", "mock",
}
_SKIP_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".md", ".txt", ".env", ".lock", ".gitignore",
}
_SKIP_NAMES = {"Dockerfile", "Makefile", "Procfile"}
_GENERATED_PATTERNS = {
    ".g.dart", ".freezed.dart",
    ".generated.ts", ".generated.js",
    ".pb.go", ".pb.ts", ".pb.py",
    ".moc.cpp",
    ".designer.cs",
}
_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".dart_tool", "build", "dist"}


def should_skip(file_path: Path) -> bool:
    name = file_path.name.lower()
    for part in file_path.parts:
        if part in _SKIP_DIRS:
            return True
    if file_path.suffix in _SKIP_EXTENSIONS or file_path.name in _SKIP_NAMES:
        return True
    if any(name.endswith(pattern) for pattern in _GENERATED_PATTERNS):
        return True
    if any(pattern in name for pattern in _SKIP_PATTERNS):
        return True
    return False


def get_length_message(file_path: Path) -> str:
    warn, critical = check_file_length(file_path)
    try:
        lines = len(file_path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return ""
    if critical:
        return (
            f"FILE TOO LONG: {file_path.name} tem {lines} linhas "
            f"(critico: {FILE_LINES_CRITICAL}). Split obrigatorio em modulos menores."
        )
    if warn:
        return (
            f"FILE GROWING: {file_path.name} tem {lines} linhas "
            f"(aviso: {FILE_LINES_WARN}). Considere dividir."
        )
    return ""


def _find_project_root(file_path: Path, toolchain: ToolchainKind) -> Path:
    fingerprints = {
        ToolchainKind.NODEJS: "package.json",
        ToolchainKind.FLUTTER: "pubspec.yaml",
        ToolchainKind.GO: "go.mod",
        ToolchainKind.RUST: "Cargo.toml",
        ToolchainKind.MAVEN: "pom.xml",
    }
    fp = fingerprints.get(toolchain)
    current = file_path.parent
    for _ in range(4):
        if fp and (current / fp).exists():
            return current
        current = current.parent
    return file_path.parent


def _check_nodejs(file_path: Path, project_root: Path) -> list[str]:
    issues = []
    prettier = which("prettier")
    if not prettier:
        local = project_root / "node_modules" / ".bin" / "prettier"
        if local.exists():
            prettier = str(local)
    if prettier:
        run_command([prettier, "--write", str(file_path)], cwd=project_root)
    eslint = which("eslint")
    if not eslint:
        local = project_root / "node_modules" / ".bin" / "eslint"
        if local.exists():
            eslint = str(local)
    if eslint:
        code, output = run_command([eslint, str(file_path)], cwd=project_root)
        if code != 0 and output:
            issues.append(f"ESLint: {output[:400]}")
    return issues


def _check_flutter(file_path: Path, project_root: Path) -> list[str]:
    issues = []
    tool = which("dart")
    if not tool:
        return issues
    code, output = run_command(["dart", "analyze", str(file_path)], cwd=project_root, timeout=30)
    if code != 0 and output:
        lines = [l for l in output.splitlines() if "error" in l.lower() or "warning" in l.lower()]
        if lines:
            issues.append("Dart: " + "\n".join(lines[:10]))
    return issues


def _check_go(file_path: Path, project_root: Path) -> list[str]:
    issues = []
    if which("gofmt"):
        run_command(["gofmt", "-w", str(file_path)])
    if which("go"):
        code, output = run_command(["go", "vet", str(file_path)], cwd=project_root)
        if code != 0 and output:
            issues.append(f"go vet: {output[:300]}")
    return issues


def _check_rust(file_path: Path, project_root: Path) -> list[str]:
    issues = []
    if which("cargo"):
        code, output = run_command(["cargo", "check"], cwd=project_root, timeout=60)
        if code != 0 and output:
            lines = [l for l in output.splitlines() if "error" in l.lower()][:5]
            if lines:
                issues.append("cargo check: " + "\n".join(lines))
    return issues


_CHECKERS = {
    ToolchainKind.NODEJS: _check_nodejs,
    ToolchainKind.FLUTTER: _check_flutter,
    ToolchainKind.GO: _check_go,
    ToolchainKind.RUST: _check_rust,
}


def main() -> int:
    hook_data = read_hook_stdin()
    file_path = get_edited_file(hook_data)

    if not file_path or not file_path.exists():
        sys.exit(0)

    if should_skip(file_path):
        sys.exit(0)

    toolchain = detect_toolchain_root(file_path.parent)
    length_msg = get_length_message(file_path)

    issues: list[str] = []

    if toolchain and toolchain in _CHECKERS:
        project_root = _find_project_root(file_path, toolchain)
        issues = _CHECKERS[toolchain](file_path, project_root)

    if issues or length_msg:
        parts = []
        if issues:
            parts.extend(issues)
        if length_msg:
            parts.append(length_msg)
        context = "\n".join(parts)
        print(hook_context(f"[devflow quality]\n{context}"))

    sys.exit(0)


if __name__ == "__main__":
    main()
