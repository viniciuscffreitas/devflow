import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from _util import check_file_length, detect_toolchain_root, ToolchainKind


def test_file_length_ok(tmp_path):
    f = tmp_path / "small.py"
    f.write_text("\n".join(["line"] * 50))
    warn, critical = check_file_length(f)
    assert not warn and not critical


def test_file_length_warn(tmp_path):
    f = tmp_path / "big.py"
    f.write_text("\n".join(["line"] * 450))
    warn, critical = check_file_length(f)
    assert warn and not critical


def test_file_length_critical(tmp_path):
    f = tmp_path / "huge.py"
    f.write_text("\n".join(["line"] * 650))
    warn, critical = check_file_length(f)
    assert critical


def test_detect_nodejs(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    kind = detect_toolchain_root(tmp_path)
    assert kind == ToolchainKind.NODEJS


def test_detect_flutter(tmp_path):
    (tmp_path / "pubspec.yaml").write_text("name: app")
    kind = detect_toolchain_root(tmp_path)
    assert kind == ToolchainKind.FLUTTER


def test_detect_maven(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    kind = detect_toolchain_root(tmp_path)
    assert kind == ToolchainKind.MAVEN


def test_detect_rust(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[package]")
    kind = detect_toolchain_root(tmp_path)
    assert kind == ToolchainKind.RUST


def test_detect_go(tmp_path):
    (tmp_path / "go.mod").write_text("module app")
    kind = detect_toolchain_root(tmp_path)
    assert kind == ToolchainKind.GO


def test_detect_none(tmp_path):
    kind = detect_toolchain_root(tmp_path)
    assert kind is None


def test_nodejs_priority_over_maven(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "pom.xml").write_text("<project/>")
    kind = detect_toolchain_root(tmp_path)
    assert kind == ToolchainKind.NODEJS
