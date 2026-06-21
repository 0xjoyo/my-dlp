"""
Unit tests for src/core/lrc_parser.py

The parser is the heart of the Karaoke tab — if it miscounts timestamps,
the highlight drifts and the whole experience feels broken. We cover:
- Standard [mm:ss.xx] and [mm:ss.xxx] formats
- Extended [hh:mm:ss.xx] format used by some long-track providers
- Multiple timestamps on a single line (chorus repeated as one line)
- Empty / garbage input
- has_lrc_timestamps pre-flight check
- lrc_to_plain_text stripping
"""
import pytest

from src.core.lrc_parser import (
    parse_lrc,
    get_current_line_index,
    has_lrc_timestamps,
    lrc_to_plain_text,
)


# ── has_lrc_timestamps ──────────────────────────────────────────────


class TestHasLrcTimestamps:
    def test_empty_string(self):
        assert has_lrc_timestamps("") is False

    def test_none(self):
        assert has_lrc_timestamps(None) is False

    def test_standard_minutes_seconds_2_digit_ms(self):
        assert has_lrc_timestamps("[00:12.50] hello") is True

    def test_standard_minutes_seconds_3_digit_ms(self):
        assert has_lrc_timestamps("[00:12.500] hello") is True

    def test_extended_hours_minutes_seconds(self):
        # Long mixes / podcasts sometimes use [hh:mm:ss.xx]
        assert has_lrc_timestamps("[01:05:30.00] long song") is True

    def test_plain_text_no_timestamps(self):
        assert has_lrc_timestamps("Just some lyrics here") is False

    def test_metadata_only(self):
        # [ar:Artist] is metadata, not a timestamp
        assert has_lrc_timestamps("[ar:Some Artist]\n[ti:Song Title]") is False

    def test_garbage(self):
        assert has_lrc_timestamps("!@#$%^&*()") is False

    def test_timestamp_in_middle_of_text(self):
        # The regex finds it anywhere in the string
        assert has_lrc_timestamps("prefix [00:01.00] suffix") is True

    def test_high_minutes(self):
        assert has_lrc_timestamps("[99:59.99] last second") is True


# ── parse_lrc ───────────────────────────────────────────────────────


class TestParseLrc:
    def test_empty_input(self):
        lines, meta = parse_lrc("")
        assert lines == []
        assert meta == {}

    def test_none_input(self):
        lines, meta = parse_lrc(None)
        assert lines == []
        assert meta == {}

    def test_standard_format(self):
        text = "[00:01.50] first line\n[00:05.00] second line"
        lines, meta = parse_lrc(text)
        assert len(lines) == 2
        assert lines[0].time_ms == 1500
        assert lines[0].text == "first line"
        assert lines[1].time_ms == 5000
        assert lines[1].text == "second line"
        assert meta == {}

    def test_3_digit_ms(self):
        text = "[00:01.500] precise"
        lines, _ = parse_lrc(text)
        assert lines[0].time_ms == 1500

    def test_2_digit_ms(self):
        text = "[00:01.50] precise"
        lines, _ = parse_lrc(text)
        assert lines[0].time_ms == 1500

    def test_extended_format(self):
        # Long mixes: 1 hour 5 minutes 30.5 seconds
        text = "[01:05:30.50] long line"
        lines, _ = parse_lrc(text)
        assert lines[0].time_ms == (1 * 3600 + 5 * 60 + 30) * 1000 + 500
        assert lines[0].text == "long line"

    def test_extended_3_digit_ms(self):
        text = "[01:05:30.500] long line"
        lines, _ = parse_lrc(text)
        assert lines[0].time_ms == (1 * 3600 + 5 * 60 + 30) * 1000 + 500

    def test_metadata_extraction(self):
        text = "[ar:Lana Del Rey]\n[ti:Video Games]\n[al:Video Games EP]\n[00:01.00] hello"
        lines, meta = parse_lrc(text)
        assert meta.get("ar") == "Lana Del Rey"
        assert meta.get("ti") == "Video Games"
        assert meta.get("al") == "Video Games EP"
        assert len(lines) == 1
        assert lines[0].text == "hello"

    def test_multiple_timestamps_same_line(self):
        # Some LRC files repeat a line at different timestamps (e.g. chorus)
        text = "[00:01.00][00:30.00] chorus line"
        lines, _ = parse_lrc(text)
        assert len(lines) == 2
        assert lines[0].time_ms == 1000
        assert lines[1].time_ms == 30000
        # The text after stripping timestamps should be the same
        assert lines[0].text == lines[1].text == "chorus line"

    def test_sorted_by_timestamp(self):
        # Input is out of order — output should be sorted
        text = "[00:05.00] second\n[00:01.00] first"
        lines, _ = parse_lrc(text)
        assert lines[0].time_ms == 1000
        assert lines[1].time_ms == 5000

    def test_blank_lines_ignored(self):
        text = "[00:01.00] one\n\n\n[00:05.00] two\n"
        lines, _ = parse_lrc(text)
        assert len(lines) == 2

    def test_whitespace_stripped(self):
        text = "  [00:01.00]   spaced   "
        lines, _ = parse_lrc(text)
        assert lines[0].text == "spaced"

    def test_unicode_text_preserved(self):
        text = "[00:01.00] مرحبا بالعالم"
        lines, _ = parse_lrc(text)
        assert lines[0].text == "مرحبا بالعالم"

    def test_emoji_text_preserved(self):
        text = "[00:01.00] hello 🎵"
        lines, _ = parse_lrc(text)
        assert lines[0].text == "hello 🎵"

    def test_real_world_lrc(self):
        # Real-world excerpt from a popular song
        text = """[ti:Never Gonna Give You Up]
[ar:Rick Astley]
[al:Whenever You Need Somebody]
[00:00.50] We're no strangers to love
[00:04.00] You know the rules and so do I
[00:07.50] A full commitment's what I'm thinking of"""
        lines, meta = parse_lrc(text)
        assert meta["ar"] == "Rick Astley"
        assert meta["ti"] == "Never Gonna Give You Up"
        assert len(lines) == 3
        assert lines[0].text == "We're no strangers to love"
        assert lines[1].time_ms == 4000
        assert lines[2].text == "A full commitment's what I'm thinking of"


# ── get_current_line_index ──────────────────────────────────────────


class TestGetCurrentLineIndex:
    def make_lines(self):
        return [
            type("L", (), {"time_ms": 1000})(),
            type("L", (), {"time_ms": 5000})(),
            type("L", (), {"time_ms": 10000})(),
        ]

    def test_empty_lines(self):
        assert get_current_line_index([], 5000) == -1

    def test_before_first_line(self):
        lines = self.make_lines()
        assert get_current_line_index(lines, 500) == -1

    def test_on_first_line(self):
        lines = self.make_lines()
        assert get_current_line_index(lines, 1000) == 0

    def test_between_lines(self):
        lines = self.make_lines()
        assert get_current_line_index(lines, 3000) == 0  # still first

    def test_on_second_line(self):
        lines = self.make_lines()
        assert get_current_line_index(lines, 5000) == 1

    def test_at_last_line(self):
        lines = self.make_lines()
        assert get_current_line_index(lines, 10000) == 2

    def test_after_last_line(self):
        lines = self.make_lines()
        assert get_current_line_index(lines, 99999) == 2


# ── lrc_to_plain_text ───────────────────────────────────────────────


class TestLrcToPlainText:
    def test_strips_timestamps(self):
        text = "[00:01.00] line one\n[00:05.00] line two"
        plain = lrc_to_plain_text(text)
        assert "line one" in plain
        assert "line two" in plain
        assert "[" not in plain
        assert "00:01" not in plain

    def test_skips_empty_lines(self):
        text = "[00:01.00] line\n[00:05.00]\n[00:09.00] third"
        plain = lrc_to_plain_text(text)
        lines = [l for l in plain.split("\n") if l]
        assert lines == ["line", "third"]