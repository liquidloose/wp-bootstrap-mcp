from __future__ import annotations

import re
from pathlib import Path

_LINE_RE = re.compile(
    r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P<sep>\s*=\s*)(?P<value>.*)$"
)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _LINE_RE.match(raw_line)
        if not match:
            continue
        values[match.group("key")] = _strip_quotes(match.group("value").rstrip())
    return values


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _format_value(new_value: str, original_value: str) -> str:
    stripped = original_value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        quote = stripped[0]
        return f"{quote}{new_value}{quote}"
    return new_value


def substitute_env_sample(
    sample_text: str,
    replacements: dict[str, str],
) -> str:
    """Replace values for known keys, preserving each line's `KEY=` spacing."""
    out: list[str] = []
    for raw_line in sample_text.splitlines():
        stripped = raw_line.lstrip()
        if stripped.startswith("#") or not stripped:
            out.append(raw_line)
            continue
        match = _LINE_RE.match(raw_line)
        if not match or match.group("key") not in replacements:
            out.append(raw_line)
            continue
        key = match.group("key")
        sep = match.group("sep")
        formatted = _format_value(replacements[key], match.group("value"))
        out.append(f"{key}{sep}{formatted}")
    trailing_newline = sample_text.endswith("\n")
    joined = "\n".join(out)
    return joined + ("\n" if trailing_newline else "")


def write_site_env(
    sample_path: Path,
    dest_path: Path,
    replacements: dict[str, str],
) -> None:
    text = substitute_env_sample(
        sample_path.read_text(encoding="utf-8"), replacements
    )
    dest_path.write_text(text, encoding="utf-8")
