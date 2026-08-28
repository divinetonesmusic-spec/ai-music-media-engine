"""Small filesystem helpers shared by the config and knowledge loaders.

Persistence in V1 is YAML + Markdown (with YAML front matter) + JSON (I10). These
helpers centralise reading them and raise a single, clear error type.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Tuple

import yaml


class LoadError(Exception):
    """A required input file is missing, unreadable, or malformed."""


def read_text(path: Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise LoadError(f"file not found: {path}") from e
    except OSError as e:  # pragma: no cover - unusual
        raise LoadError(f"cannot read {path}: {e}") from e


def read_yaml(path: Path) -> Any:
    text = read_text(path)
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise LoadError(f"invalid YAML in {path}: {e}") from e


def read_json(path: Path) -> Any:
    text = read_text(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LoadError(f"invalid JSON in {path}: {e}") from e


def read_yaml_front_matter(path: Path) -> Tuple[dict, str]:
    """Split a Markdown file into (front_matter_dict, body).

    The front matter is a leading ``---`` / ``---`` fenced YAML block. A file with
    no front matter yields ``({}, whole_text)``.
    """
    text = read_text(path)
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n", 1)
    rest = parts[1] if len(parts) > 1 else ""
    end = rest.find("\n---")
    if end == -1:
        raise LoadError(f"unterminated YAML front matter in {path}")
    fm_text = rest[:end]
    body = rest[end + len("\n---"):].lstrip("\n")
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        raise LoadError(f"invalid front matter in {path}: {e}") from e
    if not isinstance(fm, dict):
        raise LoadError(f"front matter in {path} is not a mapping")
    return fm, body


def extract_yaml_blocks(markdown: str) -> list:
    """Return the parsed contents of every ```yaml fenced block in a Markdown string."""
    blocks = []
    lines = markdown.splitlines()
    buf: list = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if not in_block and stripped.startswith("```") and stripped[3:].strip().lower() == "yaml":
            in_block = True
            buf = []
        elif in_block and stripped.startswith("```"):
            in_block = False
            try:
                blocks.append(yaml.safe_load("\n".join(buf)))
            except yaml.YAMLError as e:
                raise LoadError(f"invalid ```yaml block: {e}") from e
        elif in_block:
            buf.append(line)
    return blocks
