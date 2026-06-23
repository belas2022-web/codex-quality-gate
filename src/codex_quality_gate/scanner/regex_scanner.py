from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RegexMatch:
    line: int
    column: int
    text: str


def find_regex(pattern: str, text: str) -> list[RegexMatch]:
    compiled = re.compile(pattern)
    matches: list[RegexMatch] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = compiled.search(line)
        if match is not None:
            matches.append(
                RegexMatch(line=line_number, column=match.start() + 1, text=line.strip())
            )
    return matches
