"""Vitalux four-component versions: .0 ... .9, then bump the third component.

Examples:
    v0.9.4.0 -> v0.9.4.1
    v0.9.4.9 -> v0.9.5.0

Only approved GitHub Releases consume a version. Ordinary commits do not.
"""
import re
import sys

VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)\.(\d+)$")


def parse(version):
    match = VERSION_RE.fullmatch(str(version).strip())
    if not match:
        raise ValueError(f"Expected a four-component Vitalux version: {version!r}")
    major, minor, patch, build = map(int, match.groups())
    if not 0 <= build <= 9:
        raise ValueError(f"Vitalux release suffix must be between 0 and 9: {version!r}")
    return major, minor, patch, build


def next_version(version):
    major, minor, patch, build = parse(version)
    if build == 9:
        return f"{major}.{minor}.{patch + 1}.0"
    return f"{major}.{minor}.{patch}.{build + 1}"


def verify_successor(previous, proposed):
    expected = next_version(previous)
    normalized = ".".join(map(str, parse(proposed)))
    if normalized != expected:
        raise ValueError(
            f"Version after v{str(previous).removeprefix('v')} must be v{expected}, "
            f"not v{normalized}."
        )
    return normalized


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "next":
            print(next_version(sys.argv[2]))
        elif len(sys.argv) == 4 and sys.argv[1] == "verify":
            print(f"Version transition valid: "
                  f"v{sys.argv[2].removeprefix('v')} -> v"
                  f"{verify_successor(sys.argv[2], sys.argv[3])}")
        else:
            raise ValueError("Usage: versioning.py next VERSION | verify PREVIOUS PROPOSED")
    except ValueError as exc:
        raise SystemExit(str(exc))
