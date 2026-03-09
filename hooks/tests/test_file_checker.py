import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_checker import should_skip, get_length_message, _check_maven
import shutil


def test_skip_test_files():
    assert should_skip(Path("tests/test_user.py"))
    assert should_skip(Path("src/user.test.ts"))
    assert should_skip(Path("user_spec.rb"))


def test_skip_config_files():
    assert should_skip(Path("pyproject.toml"))
    assert should_skip(Path(".eslintrc.json"))
    assert should_skip(Path("Dockerfile"))


def test_skip_generated_files():
    assert should_skip(Path("lib/models/user.g.dart"))
    assert should_skip(Path("lib/models/user.freezed.dart"))
    assert should_skip(Path("src/proto/user.generated.ts"))
    assert should_skip(Path("internal/proto/user.pb.go"))
    assert should_skip(Path("src/widget.moc.cpp"))


def test_skip_dirs():
    assert should_skip(Path("node_modules/pkg/index.js"))
    assert should_skip(Path("build/output.js"))
    assert should_skip(Path(".git/hooks/pre-commit"))


def test_no_skip_impl_files():
    assert not should_skip(Path("src/user.py"))
    assert not should_skip(Path("lib/api.ts"))
    assert not should_skip(Path("internal/server.go"))


def test_case_insensitive_skip():
    assert should_skip(Path("src/USER.G.DART"))
    assert should_skip(Path("DOCKERFILE"))


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


def test_maven_checker_no_mvn(tmp_path, monkeypatch):
    """When neither mvnw nor mvn exist, returns no issues."""
    monkeypatch.setattr(shutil, "which", lambda x: None)
    f = tmp_path / "App.java"
    f.write_text("public class App {}")
    issues = _check_maven(f, tmp_path)
    assert issues == []
