"""Normalize catalog labels without changing their internal whitespace."""


def normalize_label(value: str) -> str:
    return value.strip().casefold()
