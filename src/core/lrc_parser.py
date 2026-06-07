"""
LRC Parser — Parse LRC (Lyric) files with timestamps
"""
import re
from typing import List, Tuple, Optional


class LRCLine:
    """Represents a single lyric line with its timestamp."""
    def __init__(self, time_ms: int, text: str):
        self.time_ms = time_ms
        self.text = text

    def __repr__(self):
        return f"[{self.time_ms}ms] {self.text}"


def parse_lrc(lrc_content: str) -> Tuple[List[LRCLine], dict]:
    """
    Parse LRC content into a list of LRCLine objects and metadata dict.
    Returns (lines, metadata)
    """
    if not lrc_content:
        return [], {}

    lines = lrc_content.splitlines()
    parsed_lines: List[LRCLine] = []
    metadata = {}

    # Regex patterns
    timestamp_pattern = re.compile(r"\[(\d{1,2}):(\d{2})\.(\d{2,3})\]")
    metadata_pattern = re.compile(r"\[(\w+):(.*?)\]")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for timestamps
        timestamps = timestamp_pattern.findall(line)
        if timestamps:
            # Remove all timestamps from the line text
            text = timestamp_pattern.sub("", line).strip()
            for m, s, ms_str in timestamps:
                ms = int(m) * 60000 + int(s) * 1000
                if len(ms_str) == 2:
                    ms += int(ms_str) * 10
                elif len(ms_str) == 3:
                    ms += int(ms_str)
                parsed_lines.append(LRCLine(time_ms=ms, text=text))
        else:
            # Check for metadata tags like [ar:Artist], [ti:Title], etc.
            meta_match = metadata_pattern.match(line)
            if meta_match:
                key, value = meta_match.group(1), meta_match.group(2).strip()
                metadata[key] = value

    # Sort by timestamp
    parsed_lines.sort(key=lambda l: l.time_ms)
    return parsed_lines, metadata


def get_current_line_index(lines: List[LRCLine], current_ms: int) -> int:
    """
    Find the index of the current lyric line for the given playback position.
    Returns -1 if before the first line.
    """
    if not lines:
        return -1

    current_idx = -1
    for i, line in enumerate(lines):
        if line.time_ms <= current_ms:
            current_idx = i
        else:
            break
    return current_idx


def lrc_to_plain_text(lrc_content: str) -> str:
    """Convert LRC content to plain text (no timestamps)."""
    lines, _ = parse_lrc(lrc_content)
    return "\n".join(line.text for line in lines if line.text)
