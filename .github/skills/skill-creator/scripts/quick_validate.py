#!/usr/bin/env python3
"""
Quick validation script for skills - no external dependencies version

Validates SKILL.md frontmatter without requiring PyYAML.
Uses basic string parsing for YAML-like key: value format.
"""

import re
import sys
from pathlib import Path


def _remove_base_indent(lines: list[str]) -> list[str]:
    """Remove base indent from multiline content per YAML spec.

    Determines the indent level from the first non-empty line
    and removes that indent from all lines while preserving
    relative indentation.

    Args:
        lines: List of lines from multiline content

    Returns:
        List of lines with base indent removed
    """
    # Determine base indent from first non-empty line
    base_indent = None
    for line in lines:
        if line.strip():  # Non-empty line
            base_indent = len(line) - len(line.lstrip())
            break

    # Remove base indent from all lines
    if base_indent is not None and base_indent > 0:
        processed = []
        for line in lines:
            if line.strip():  # Non-empty line
                # Remove base indent, preserve relative indent
                processed.append(line[base_indent:] if len(line) >= base_indent else line)
            else:  # Empty line
                processed.append("")
        return processed

    return lines


def _parse_frontmatter_simple(content: str) -> dict | None:
    """
    Simple YAML-like frontmatter parser (no PyYAML required).

    Handles basic key: value format only.
    Returns dict or None if parsing fails.
    """
    if not content.startswith("---"):
        return None

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter_text = match.group(1).strip()
    frontmatter = {}

    # Simple line-by-line parsing
    lines = frontmatter_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue

        # Parse key: value (simple format)
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            # Handle multiline string with |- marker
            if value == "|-":
                multiline = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    # Stop at next key or end
                    if next_line and not next_line[0].isspace():
                        break
                    multiline.append(next_line.rstrip())
                    i += 1

                # Remove trailing empty lines
                while multiline and not multiline[-1].strip():
                    multiline.pop()

                # Apply YAML spec indent removal
                multiline = _remove_base_indent(multiline)

                value = "\n".join(multiline)
                i -= 1  # Adjust because loop will increment
            elif value.startswith('"') and value.endswith('"'):
                # Remove quotes
                value = value[1:-1]

            frontmatter[key] = value

        i += 1

    return frontmatter if frontmatter else None


def _validate_frontmatter(content: str) -> tuple[bool, str | dict]:
    """Validate and extract frontmatter from SKILL.md content."""
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter = _parse_frontmatter_simple(content)
    if frontmatter is None:
        return False, "Failed to parse frontmatter"

    return True, frontmatter


def _validate_properties(frontmatter: dict) -> tuple[bool, str]:
    """Validate frontmatter properties."""
    allowed_properties = {"name", "description", "license", "allowed-tools", "metadata"}
    unexpected_keys = set(frontmatter.keys()) - allowed_properties
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(allowed_properties))}"
        )
    return True, ""


def _validate_name(frontmatter: dict) -> tuple[bool, str]:
    """Validate name field."""
    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"

    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        if not re.match(r"^[a-z0-9-]+$", name):
            return False, f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)"
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."
    return True, ""


def _validate_description(frontmatter: dict) -> tuple[bool, str]:
    """Validate description field."""
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."
    return True, ""


def validate_skill(skill_path: str) -> tuple[bool, str]:
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text(encoding="utf-8")
    valid, result = _validate_frontmatter(content)
    if not valid:
        return False, result

    frontmatter = result

    # Validate properties
    valid, message = _validate_properties(frontmatter)
    if not valid:
        return False, message

    # Validate name
    valid, message = _validate_name(frontmatter)
    if not valid:
        return False, message

    # Validate description
    valid, message = _validate_description(frontmatter)
    if not valid:
        return False, message

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python .github/skills/skill-creator/scripts/quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
