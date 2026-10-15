"""Hash a Mulgae live-source identity using its native JSON encoding."""

import argparse
import hashlib
import json
import sys

FIELDS = ("schema_version", "scope", "operand", "base_oid", "head_oid", "empty_base")


def source_identity_digest(identity: object) -> str:
    if not isinstance(identity, dict) or set(identity) != set(FIELDS):
        raise ValueError("expected exactly the six native identity fields")
    if any(type(identity[name]) is not str for name in FIELDS[:-1]):
        raise ValueError("identity text fields must be strings")
    if type(identity["empty_base"]) is not bool:
        raise ValueError("empty_base must be a boolean")
    # Mulgae marshals a Go struct in this order with encoding/json defaults.
    wire = json.dumps(
        {name: identity[name] for name in FIELDS},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    for character, escaped in (
        ("<", "\\u003c"),
        (">", "\\u003e"),
        ("&", "\\u0026"),
        ("\u2028", "\\u2028"),
        ("\u2029", "\\u2029"),
    ):
        wire = wire.replace(character, escaped)
    return "sha256:" + hashlib.sha256(wire.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read a UTF-8 native live-source identity JSON object from stdin and print its metadata digest. Validate its schema separately."
    )
    parser.parse_args()
    try:
        digest = source_identity_digest(
            json.loads(sys.stdin.buffer.read().decode("utf-8"))
        )
    except (ValueError, UnicodeError) as error:
        print(f"Invalid live-source identity: {error}", file=sys.stderr)
        return 2
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
