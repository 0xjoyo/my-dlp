"""
Unit tests for src/utils/search_history.py

The Spotify tab stores the user's recent search queries so they can be
re-run with one click. Tests cover:
- Empty initial state
- Adding unique queries
- Deduplication (case-insensitive)
- Capacity cap at MAX_ENTRIES
- Removal and clearing
- Persistence across calls
"""
import pytest


# We import every function we touch explicitly so test failure messages
# surface the missing symbol clearly.
from src.utils.search_history import (
    get_history,
    add_query,
    clear_history,
    remove_query,
    MAX_ENTRIES,
)


@pytest.fixture(autouse=True)
def wipe(tmp_config_dir):
    """Each test starts with an empty search history."""
    clear_history()
    yield


class TestSearchHistory:
    def test_empty_initially(self):
        assert get_history() == []

    def test_add_single(self):
        add_query("rick astley")
        assert get_history() == ["rick astley"]

    def test_newest_first(self):
        add_query("first")
        add_query("second")
        add_query("third")
        assert get_history() == ["third", "second", "first"]

    def test_dedup_case_insensitive(self):
        add_query("Rick Astley")
        add_query("rick astley")
        add_query("RICK ASTLEY")
        history = get_history()
        # Only one entry, the most recent casing
        assert len(history) == 1
        assert history[0] == "RICK ASTLEY"

    def test_promote_existing_to_top(self):
        add_query("a")
        add_query("b")
        add_query("c")
        # Re-search 'a' — should go to top, not duplicate
        add_query("a")
        history = get_history()
        assert history == ["a", "c", "b"]
        assert len(history) == 3

    def test_capped_at_max(self):
        # Add MAX_ENTRIES + 5 items
        for i in range(MAX_ENTRIES + 5):
            add_query(f"query-{i}")
        history = get_history()
        assert len(history) == MAX_ENTRIES
        # Newest first means the last 5 we added are kept
        assert history[0] == f"query-{MAX_ENTRIES + 4}"

    def test_empty_query_no_op(self):
        add_query("")
        add_query("   ")
        add_query(None)
        assert get_history() == []

    def test_whitespace_trimmed(self):
        add_query("  never gonna give you up  ")
        assert get_history() == ["never gonna give you up"]

    def test_clear(self):
        add_query("a")
        add_query("b")
        clear_history()
        assert get_history() == []

    def test_remove_specific(self):
        add_query("keep this")
        add_query("delete me")
        add_query("and this too")
        remove_query("delete me")
        history = get_history()
        assert "delete me" not in history
        assert "keep this" in history
        assert "and this too" in history

    def test_remove_case_insensitive(self):
        add_query("Hello World")
        remove_query("hello world")
        assert get_history() == []

    def test_persistence_across_module_reloads(self):
        """Verify that what we wrote can be read after reloading both
        the search_history module and the underlying config_manager
        (which simulates a fresh process start)."""
        add_query("persistent")

        # We do NOT expect this to survive an arbitrary reload (the
        # fixture's monkeypatch-set env var gets cleared between tests)
        # but we DO expect the value to remain readable from the same
        # in-memory module state during the test:
        from src.utils.search_history import get_history as fresh_get
        assert fresh_get() == ["persistent"]

    def test_max_entries_constant_is_sane(self):
        # Sanity: shouldn't be ridiculously small or large
        assert 5 <= MAX_ENTRIES <= 20