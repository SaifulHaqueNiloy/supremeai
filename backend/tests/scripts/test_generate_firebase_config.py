"""Fail-closed contract tests for scripts/deploy/generate_firebase_config.py.

BACKGROUND (zero-hardcode reconciliation): the generator used to treat a
missing ``/api/**`` rewrite as a WARNING-only condition. A hosting site that
silently drops its API rewrite ships a SPA whose backend calls 404 at the
edge — the exact class of silent-config failure the zero-hardcode plan
forbids. The generator is now fail-closed:

1. All three required API rewrites (/api/**, /api/v1/**, /admin-api/**)
   must exist on every hosting site.
2. Rewrite destinations must share the canonical BACKEND_URL origin
   (foreign destinations rejected).
3. Destinations must pass source-prefix proof (/api/** must route into
   {origin}/api/..., not into a sibling path).
4. The SPA fallback (** -> /index.html) must exist verbatim.
5. All previous fail-fast checks (missing template/env, unresolved
   placeholders, invalid JSON) are preserved.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "deploy" / "generate_firebase_config.py"

_spec = importlib.util.spec_from_file_location("generate_firebase_config", SCRIPT_PATH)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

BACKEND_URL = "https://api.example.com"


def _template(
    *,
    sources: tuple[str, ...] = ("/admin-api/**", "/api/v1/**", "/api/**", "**"),
    destinations: dict[str, str] | None = None,
    spa_destination: str = "/index.html",
    shape: str = "list",
) -> str:
    default_dests = {
        "/admin-api/**": f"{BACKEND_URL}/admin-api/**",
        "/api/v1/**": f"{BACKEND_URL}/api/v1/**",
        "/api/**": f"{BACKEND_URL}/api/**",
        "**": spa_destination,
    }
    dests = {**default_dests, **(destinations or {})}
    rewrites = [{"source": s, "destination": dests[s]} for s in sources if s in dests]
    site = {
        "target": "user",
        "public": "frontend/dist",
        "rewrites": rewrites,
    }
    doc = {"hosting": [site, {**site, "target": "admin"}] if shape == "list" else site}
    return json.dumps(doc)


def _run_generate(
    monkeypatch, tmp_path: Path, template: str | None, env_url: str | None = BACKEND_URL
):
    monkeypatch.chdir(tmp_path)
    if template is not None:
        (tmp_path / "firebase.template.json").write_text(template, encoding="utf-8")
    if env_url is None:
        for var in (
            "BACKEND_URL",
            "VITE_BACKEND_URL",
            "VITE_API_URL",
            "USER_BACKEND_URL",
            "VITE_USER_BACKEND",
        ):
            monkeypatch.delenv(var, raising=False)
    else:
        monkeypatch.setenv("BACKEND_URL", env_url)
    gen.generate_firebase_config()


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_real_repo_template_passes_end_to_end(monkeypatch, tmp_path):
    """The ACTUAL committed template must satisfy the fail-closed contract."""
    real_template = (REPO_ROOT / "firebase.template.json").read_text(encoding="utf-8")
    out_dir = tmp_path / "repo"
    out_dir.mkdir()
    (out_dir / "firebase.template.json").write_text(real_template, encoding="utf-8")
    monkeypatch.chdir(out_dir)
    monkeypatch.setenv("BACKEND_URL", BACKEND_URL)
    gen.generate_firebase_config()
    produced = json.loads((out_dir / "firebase.json").read_text(encoding="utf-8"))
    sites = produced["hosting"]
    assert {s["target"] for s in sites} == {"user", "admin"}
    for site in sites:
        srcs = {rw["source"] for rw in site["rewrites"]}
        assert {"/api/**", "/api/v1/**", "/admin-api/**", "**"} <= srcs


def test_minimal_valid_template_generates_output(monkeypatch, tmp_path):
    _run_generate(monkeypatch, tmp_path, _template())
    produced = json.loads((tmp_path / "firebase.json").read_text(encoding="utf-8"))
    assert produced["hosting"][0]["rewrites"][0]["destination"] == f"{BACKEND_URL}/admin-api/**"


def test_generation_is_deterministic(monkeypatch, tmp_path):
    _run_generate(monkeypatch, tmp_path, _template())
    first = (tmp_path / "firebase.json").read_bytes()
    (tmp_path / "firebase.json").unlink()
    _run_generate(monkeypatch, tmp_path, _template())
    assert (tmp_path / "firebase.json").read_bytes() == first


def test_dict_hosting_shape_still_validated(monkeypatch, tmp_path):
    _run_generate(monkeypatch, tmp_path, _template(shape="dict"))
    assert (tmp_path / "firebase.json").exists()


# ---------------------------------------------------------------------------
# Environment / template fail-fast (pre-existing contract, still enforced)
# ---------------------------------------------------------------------------


def test_missing_backend_url_exits(monkeypatch, tmp_path):
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, _template(), env_url=None)
    assert exc.value.code == 1


def test_missing_template_exits(monkeypatch, tmp_path):
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, None)
    assert exc.value.code == 1


def test_unresolved_placeholders_exits(monkeypatch, tmp_path):
    template = _template().replace("frontend/dist", "frontend/dist/{{UNKNOWN}}")
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, template)
    assert exc.value.code == 1


def test_invalid_json_exits(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "firebase.template.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setenv("BACKEND_URL", BACKEND_URL)
    with pytest.raises(SystemExit) as exc:
        gen.generate_firebase_config()
    assert exc.value.code == 1


def test_relative_backend_url_rejected(monkeypatch, tmp_path):
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, _template(), env_url="api.example.com")
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# Rewrite contract (NEW fail-closed behaviour — was WARNING-only)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing",
    ["/api/**", "/api/v1/**", "/admin-api/**"],
    ids=["api", "api-v1", "admin-api"],
)
def test_missing_required_rewrite_fails_closed(monkeypatch, tmp_path, missing, capsys):
    remaining = tuple(s for s in ("/admin-api/**", "/api/v1/**", "/api/**") if s != missing)
    template = _template(sources=(*remaining, "**"))
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, template)
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert f"missing required rewrite {missing}" in out


def test_foreign_destination_origin_rejected(monkeypatch, tmp_path, capsys):
    template = _template(
        destinations={"/api/**": "https://evil.example.com/api/**"},
    )
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, template)
    assert exc.value.code == 1
    assert "foreign destination rejected" in capsys.readouterr().out


def test_source_prefix_proof_violation_rejected(monkeypatch, tmp_path, capsys):
    # /api/** routed into /admin-api/... on the correct origin: origin matches,
    # but the destination path breaks the source-prefix proof.
    template = _template(destinations={"/api/**": f"{BACKEND_URL}/admin-api/**"})
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, template)
    assert exc.value.code == 1
    assert "source-prefix proof failed" in capsys.readouterr().out


def test_missing_spa_fallback_rejected(monkeypatch, tmp_path, capsys):
    template = _template(sources=("/admin-api/**", "/api/v1/**", "/api/**"))
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, template)
    assert exc.value.code == 1
    assert "SPA fallback" in capsys.readouterr().out


def test_wrong_spa_destination_rejected(monkeypatch, tmp_path):
    template = _template(spa_destination="/app.html")
    with pytest.raises(SystemExit) as exc:
        _run_generate(monkeypatch, tmp_path, template)
    assert exc.value.code == 1
