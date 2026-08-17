"""State: skip-if-unchanged, --force, --fresh, on-disk persistence."""

from __future__ import annotations

from pathlib import Path

from pipeline.state import State, hash_inputs


def test_skip_if_unchanged(tmp_path: Path) -> None:
    state = State.load(tmp_path)
    h = hash_inputs("a", "b")
    assert state.should_run("detect", h) is True
    state.mark_done("detect", h)
    assert state.should_run("detect", h) is False  # unchanged -> skip


def test_rerun_on_input_change(tmp_path: Path) -> None:
    state = State.load(tmp_path)
    state.mark_done("detect", hash_inputs("v1"))
    assert state.should_run("detect", hash_inputs("v2")) is True


def test_force_reruns_one_step(tmp_path: Path) -> None:
    State.load(tmp_path).mark_done("detect", "h")
    forced = State.load(tmp_path, force=["detect"])
    assert forced.should_run("detect", "h") is True
    assert forced.should_run("lock", "h") is False or forced.get("lock") is None


def test_fresh_ignores_prior_state(tmp_path: Path) -> None:
    State.load(tmp_path).mark_done("detect", "h")
    fresh = State.load(tmp_path, fresh=True)
    assert fresh.should_run("detect", "h") is True


def test_persistence_across_loads(tmp_path: Path) -> None:
    State.load(tmp_path).mark_done("detect", "h")
    assert (tmp_path / "state.json").is_file()
    reloaded = State.load(tmp_path)
    assert reloaded.get("detect")["status"] == "done"


def test_hash_inputs_content_sensitive(tmp_path: Path) -> None:
    f = tmp_path / "f.txt"
    f.write_text("one")
    h1 = hash_inputs(f)
    f.write_text("two")
    assert hash_inputs(f) != h1
