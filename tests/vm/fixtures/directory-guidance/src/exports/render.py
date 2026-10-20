"""Render already prepared labels as newline-delimited text."""


def render_lines(labels: list[str]) -> str:
    return "".join(f"{label}\n" for label in labels)
