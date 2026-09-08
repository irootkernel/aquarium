#!/usr/bin/env python3
"""Expose the development manager through the official MCP Python SDK."""

from __future__ import annotations

import json
from pathlib import Path

import anyio
from aquarium_dev import error_result, invoke
from dev_contract import PROJECT_IDS
from dev_manager import ManagerError
from jsonschema import ValidationError, validate
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
    ToolAnnotations,
)

INSTRUCTIONS = """Manage the Aquarium development channel only on an explicit user request.
Diagnose the named canonical checkout before effects. Report dirty state, exact SHA,
enrollment and hook ownership. Enrollment, hook changes, builds, and service activation
retain independent user approvals; an approval boolean records consent, it does not grant it.
Show the full service plan and obtain consent to its exact token before service_apply.
Never infer approval from tool availability, a successful build, or a previous token.
Use $aquarium:dev-setup-global for a missing or outdated manager runtime. No tool installs
production tools, configures Codex, authenticates, commits, or changes producer-owned services
except through their native controller. After each effect, diagnose again. If a call is
interrupted, inspect state before retrying: lack of a response does not establish failure.
"""

REPOSITORY = {
    "type": "string",
    "minLength": 1,
    "pattern": "^/",
    "description": "Absolute path of the explicitly selected canonical Git root.",
}
PROJECT = {"type": "string", "enum": sorted(PROJECT_IDS)}


def approval(description: str) -> dict:
    return {"type": "boolean", "default": False, "description": description}


OPERATIONS = {
    "diagnose": (
        "Read-only diagnosis of one explicitly selected Aquarium development checkout, including its SHA, dirty state, enrollment, hook, and selected generations.",
        {"repository": REPOSITORY},
        ["repository"],
    ),
    "enroll": (
        "Enroll the diagnosed checkout and its native post-commit hook after independent user approvals. Migrate an intact recorded legacy hook only with additional re-enrollment approval; preserve other hook content.",
        {
            "repository": REPOSITORY,
            "approve_enrollment": approval(
                "True only after the user approves enrollment metadata for this checkout."
            ),
            "approve_hook": approval(
                "True only after the user approves the displayed native hook change."
            ),
            "approve_reenrollment": approval(
                "True only after the user approves the exact checkout transfer or recorded legacy hook migration."
            ),
        },
        ["repository"],
    ),
    "repair_hook": (
        "Restore the current owned hook after user approval. This does not migrate an older hook; use enroll with re-enrollment approval for that.",
        {
            "repository": REPOSITORY,
            "approve_hook": approval(
                "True only after the user approves restoring the exact owned hook."
            ),
        },
        ["repository"],
    ),
    "rebuild": (
        "Build and publish the diagnosed clean local-main revision after build approval. A managed-service build becomes pending; it does not activate the service.",
        {
            "repository": REPOSITORY,
            "approve_build": approval(
                "True only after the user approves rebuilding this diagnosed checkout."
            ),
        },
        ["repository"],
    ),
    "service_plan": (
        "Read the native controller's status and exact activation plan. Show the full action, active/target SHAs, busy state, and plan token. A deferred busy plan authorizes no apply.",
        {"project_id": PROJECT},
        ["project_id"],
    ),
    "service_apply": (
        "Apply only the exact service plan token independently approved by the user. The native controller must confirm the exact target generation before current advances. Missing or stale tokens are rejected.",
        {
            "project_id": PROJECT,
            "plan_token": {
                "type": "string",
                "minLength": 1,
                "description": "The exact unmodified token returned by service_plan and approved by the user.",
            },
            "approve_service": approval(
                "True only after the user approves this exact service plan token."
            ),
        },
        ["project_id", "plan_token"],
    ),
}


def tool_definitions() -> list[Tool]:
    return [
        Tool(
            name=f"aquarium_dev_{name}",
            description=description,
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            annotations=ToolAnnotations(
                readOnlyHint=name in {"diagnose", "service_plan"},
                destructiveHint=name not in {"diagnose", "service_plan"},
                openWorldHint=False,
            ),
        )
        for name, (description, properties, required) in OPERATIONS.items()
    ]


async def call(name: str, arguments: dict) -> CallToolResult:
    tool = next((item for item in tool_definitions() if item.name == name), None)
    try:
        if tool is None:
            raise ValueError("Unknown Aquarium development tool.")
        validate(arguments, tool.input_schema)
        operation = name.removeprefix("aquarium_dev_")
        argv = [operation.replace("_", "-")]
        for key, value in arguments.items():
            flag = "--" + key.replace("_", "-")
            if isinstance(value, bool):
                if value:
                    argv.append(flag)
            else:
                # Equals keeps a string value from becoming a second CLI option.
                argv.append(f"{flag}={value}")
    except (ValidationError, ValueError) as error:
        payload = error_result(
            ManagerError(
                "invalid_arguments",
                str(error),
                "Use the tool's declared input schema.",
                "arguments",
            )
        )
        exit_code = 2
    else:
        payload, exit_code = await anyio.to_thread.run_sync(invoke, argv)
    return CallToolResult(
        content=[TextContent(text=json.dumps(payload, sort_keys=True))],
        structuredContent=payload,
        isError=exit_code != 0,
    )


def create_server() -> Server:
    async def list_tools(context, params):
        return ListToolsResult(tools=tool_definitions())

    async def call_tool(context, params):
        return await call(params.name, params.arguments or {})

    receipt = Path(__file__).with_name("runtime.json")
    version = (
        json.loads(receipt.read_text())["plugin_version"]
        if receipt.exists()
        else "development"
    )
    return Server(
        "aquarium-dev",
        version=version,
        instructions=INSTRUCTIONS,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def serve() -> None:
    server = create_server()
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def main() -> int:
    anyio.run(serve)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
