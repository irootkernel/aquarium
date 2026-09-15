#!/usr/bin/env python3
"""Verify one supported Dolgorae release from official GitHub metadata."""

from __future__ import annotations

import argparse
import http.client
import json
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

SCHEMA_VERSION = "aquarium-dolgorae-release-verification.v1"
API_ROOT = "https://api.github.com/repos/irootkernel/dolgorae"
RELEASE_ROOT = "https://github.com/irootkernel/dolgorae/releases/download"
MAX_RESPONSE_BYTES = 1_048_576
RELEASES_PER_PAGE = 100
MAX_RELEASE_PAGES = 10
SUPPORTED_VERSION = re.compile(r"v0\.1\.(0|[1-9][0-9]*)")
SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
SUPPORTED_VERSION_RANGE = ">=v0.1.2,<v0.2.0"
UNSUPPORTED_VERSION_MESSAGE = "Dolgorae version is outside stable v0.1.2 through v0.1.x"
PINNED_RELEASES = {
    "v0.1.2": {
        "source_commit": "060b569833535a23218cdc6dd45880862853030e",
        "archive_sha256": (
            "513db93e7f09bcb7c2b8e323014d7149c856ab8d342856c1e10d936a817547c4"
        ),
        "executable_sha256": (
            "a8baa962fbc4e08f8aaafd007836dfd01e7022095a1cddefa1d6969896b7cf69"
        ),
    }
}


class ReleaseVerificationError(Exception):
    """A bounded official-release verification failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def failure_result(error: ReleaseVerificationError) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "failed",
        "error": {"code": error.code, "message": str(error)},
    }


def supported_version(tag: str | None) -> bool:
    if not isinstance(tag, str):
        return False
    match = SUPPORTED_VERSION.fullmatch(tag)
    return bool(match and int(match.group(1)) >= 2)


def canonical_supported_tag(version: str | None) -> str | None:
    if not isinstance(version, str):
        return None
    tag = version if version.startswith("v") else f"v{version}"
    return tag if supported_version(tag) else None


def _strict_json(content: bytes) -> Any:
    def object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(content.decode("utf-8"), object_pairs_hook=object_from_pairs)


def fetch_json(url: str, timeout_seconds: float) -> Any:
    parsed = urllib.parse.urlparse(url)
    expected_path = "/repos/irootkernel/dolgorae/"
    if (
        parsed.scheme != "https"
        or parsed.netloc != "api.github.com"
        or not parsed.path.startswith(expected_path)
    ):
        raise ReleaseVerificationError(
            "unexpected_endpoint", "unexpected GitHub API endpoint"
        )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "aquarium-dolgorae-release-verifier/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            final = urllib.parse.urlparse(response.geturl())
            if (
                final.scheme != "https"
                or final.netloc != "api.github.com"
                or not final.path.startswith(expected_path)
            ):
                raise ReleaseVerificationError(
                    "unexpected_endpoint",
                    "GitHub API redirected outside the official endpoint",
                )
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ReleaseVerificationError(
                "release_not_found", "official Dolgorae release metadata was not found"
            ) from error
        raise ReleaseVerificationError(
            "metadata_unavailable", "official Dolgorae release metadata is unavailable"
        ) from error
    except (OSError, urllib.error.URLError, http.client.HTTPException) as error:
        raise ReleaseVerificationError(
            "metadata_unavailable", "official Dolgorae release metadata is unavailable"
        ) from error
    if len(content) > MAX_RESPONSE_BYTES:
        raise ReleaseVerificationError(
            "metadata_too_large", "release metadata exceeds the size limit"
        )
    try:
        return _strict_json(content)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise ReleaseVerificationError(
            "invalid_metadata", "release metadata is not canonical JSON"
        ) from error


def _required_body_digest(body: str, label: str) -> str:
    values: set[str] = set()
    awaiting_continuation = False
    fence = ""
    for raw_line in body.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", raw_line)
        if marker:
            if not fence:
                fence = marker.group(1)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = ""
            awaiting_continuation = False
            continue
        if fence:
            continue
        if awaiting_continuation:
            awaiting_continuation = False
            if raw_line[:1].isspace():
                candidate = (
                    raw_line.strip()
                    .replace("`", "")
                    .replace("*", "")
                    .replace("_", "")
                    .removesuffix(".")
                    .strip()
                )
                if SHA256.fullmatch(candidate):
                    values.add(candidate)
                    continue
        if raw_line.startswith("\t") or re.match(r"^ {4}", raw_line):
            continue
        line = re.sub(r"^ {0,3}[-+*][ \t]+", "", raw_line.strip())
        line = line.replace("`", "").replace("*", "").replace("_", "")
        key, separator, value = line.partition(":")
        if not separator or " ".join(key.split()).casefold() != label.casefold():
            continue
        candidate = value.strip().removesuffix(".").strip()
        if SHA256.fullmatch(candidate):
            values.add(candidate)
        elif not candidate:
            awaiting_continuation = True
    if len(values) != 1:
        raise ReleaseVerificationError(
            "invalid_release_notes", f"missing or conflicting {label} release identity"
        )
    return values.pop()


def _verify_release(
    release: Any,
    timeout_seconds: float,
    fetcher: Callable[[str, float], Any],
) -> dict[str, Any]:
    if not isinstance(release, dict):
        raise ReleaseVerificationError(
            "invalid_metadata", "release metadata must be an object"
        )
    tag = release.get("tag_name")
    if (
        not supported_version(tag)
        or release.get("draft") is not False
        or release.get("prerelease") is not False
    ):
        raise ReleaseVerificationError(
            "unsupported_release", UNSUPPORTED_VERSION_MESSAGE
        )
    body = release.get("body")
    assets = release.get("assets")
    if not isinstance(body, str) or not isinstance(assets, list):
        raise ReleaseVerificationError(
            "invalid_metadata", "release identity fields are malformed"
        )

    archive_name = f"dolgorae-{tag}-aarch64-apple-darwin.tar.gz"
    checksum_name = f"{archive_name}.sha256"
    executable_sha = _required_body_digest(body, "Contained executable SHA-256")

    selected: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("name") not in {
            archive_name,
            checksum_name,
        }:
            continue
        name = asset["name"]
        if name in selected:
            raise ReleaseVerificationError(
                "duplicate_asset", "release contains a duplicate required asset"
            )
        expected_url = f"{RELEASE_ROOT}/{tag}/{name}"
        if asset.get("browser_download_url") != expected_url:
            raise ReleaseVerificationError(
                "invalid_asset", "required asset URL is not canonical"
            )
        selected[name] = asset
    if set(selected) != {archive_name, checksum_name}:
        raise ReleaseVerificationError(
            "missing_asset", "release is missing a required Apple Silicon asset"
        )
    archive_digest = selected[archive_name].get("digest")
    if not isinstance(archive_digest, str) or not re.fullmatch(
        rf"sha256:({SHA256.pattern})", archive_digest
    ):
        raise ReleaseVerificationError(
            "archive_digest_mismatch", "archive digest metadata is invalid"
        )
    archive_sha = archive_digest.removeprefix("sha256:")

    ref = fetcher(f"{API_ROOT}/git/ref/tags/{tag}", timeout_seconds)
    ref_object = ref.get("object") if isinstance(ref, dict) else None
    ref_sha = ref_object.get("sha") if isinstance(ref_object, dict) else None
    if (
        not isinstance(ref_object, dict)
        or ref_object.get("type") != "tag"
        or not isinstance(ref_sha, str)
        or not COMMIT.fullmatch(ref_sha)
    ):
        raise ReleaseVerificationError(
            "invalid_tag", "release tag is not an annotated official tag"
        )
    tag_object = fetcher(f"{API_ROOT}/git/tags/{ref_sha}", timeout_seconds)
    peeled = tag_object.get("object") if isinstance(tag_object, dict) else None
    peeled_sha = peeled.get("sha") if isinstance(peeled, dict) else None
    if (
        not isinstance(peeled, dict)
        or peeled.get("type") != "commit"
        or not isinstance(peeled_sha, str)
        or not COMMIT.fullmatch(peeled_sha)
    ):
        raise ReleaseVerificationError(
            "invalid_tag",
            "annotated tag does not peel to a release commit",
        )
    release_commit = peeled_sha

    pinned = PINNED_RELEASES.get(tag)
    observed_identity = {
        "source_commit": release_commit,
        "archive_sha256": archive_sha,
        "executable_sha256": executable_sha,
    }
    if pinned is not None and observed_identity != pinned:
        raise ReleaseVerificationError(
            "pinned_release_mismatch",
            "release metadata does not match Aquarium's pinned baseline identity",
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "verified",
        "supported_version_range": SUPPORTED_VERSION_RANGE,
        "release": {
            "tag": tag,
            "source_commit": release_commit,
            "archive_name": archive_name,
            "archive_url": selected[archive_name]["browser_download_url"],
            "archive_sha256": archive_sha,
            "checksum_name": checksum_name,
            "checksum_url": selected[checksum_name]["browser_download_url"],
            "executable_sha256": executable_sha,
        },
    }


def verify_release(
    version: str | None,
    timeout_seconds: float,
    fetcher: Callable[[str, float], Any] = fetch_json,
) -> dict[str, Any]:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ReleaseVerificationError(
            "invalid_timeout", "timeout_seconds must be a positive finite number"
        )
    if version is not None:
        tag = canonical_supported_tag(version)
        if tag is None:
            raise ReleaseVerificationError(
                "unsupported_version",
                UNSUPPORTED_VERSION_MESSAGE,
            )
        release = fetcher(f"{API_ROOT}/releases/tags/{tag}", timeout_seconds)
    else:
        releases = []
        listing_complete = False
        for page in range(1, MAX_RELEASE_PAGES + 1):
            batch = fetcher(
                f"{API_ROOT}/releases?per_page={RELEASES_PER_PAGE}&page={page}",
                timeout_seconds,
            )
            if not isinstance(batch, list):
                raise ReleaseVerificationError(
                    "invalid_metadata", "release listing must be an array"
                )
            releases.extend(batch)
            if len(batch) < RELEASES_PER_PAGE:
                listing_complete = True
                break
        if not listing_complete:
            raise ReleaseVerificationError(
                "release_listing_limit",
                "release listing exceeds the bounded setup-recommendation limit",
            )
        candidates = [
            item
            for item in releases
            if isinstance(item, dict)
            and supported_version(item.get("tag_name"))
            and item.get("draft") is False
            and item.get("prerelease") is False
        ]
        if not candidates:
            raise ReleaseVerificationError(
                "release_not_found", "no supported stable Dolgorae release was found"
            )
        release = max(
            candidates, key=lambda item: int(item["tag_name"].rsplit(".", 1)[1])
        )
    return _verify_release(release, timeout_seconds, fetcher)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    arguments = parser.parse_args()
    try:
        result = verify_release(arguments.version, arguments.timeout_seconds)
    except ReleaseVerificationError as error:
        result = failure_result(error)
        exit_code = 1
    else:
        exit_code = 0
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
