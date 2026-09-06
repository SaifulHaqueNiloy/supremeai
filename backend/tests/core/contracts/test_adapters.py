import pytest

from backend.core.contracts.adapters import validate_artifact


def test_artifact_validation_returns_content_metadata():
    content_type, size, digest = validate_artifact("report.json", b"{}")
    assert content_type == "application/json"
    assert size == 2
    assert len(digest) == 64


@pytest.mark.parametrize("name", ["/escape.txt", "../escape.txt", "nested/../../escape.txt"])
def test_artifact_path_escape_is_rejected(name):
    with pytest.raises(ValueError):
        validate_artifact(name, b"x")


def test_artifact_size_limit_is_enforced():
    with pytest.raises(ValueError):
        validate_artifact("large.bin", b"123", max_bytes=2)
