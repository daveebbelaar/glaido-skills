#!/usr/bin/env python3
"""Validate that a folder is ready to import into Glaido as a local MCP server.

Checks the things that most commonly block an import or break a server at runtime:
  - mcp.json exists at the folder root and is valid JSON with `mcpServers`
  - each server has a non-empty `command` resolvable on PATH (or an existing absolute path)
  - paths (workingDirectory, --directory, absolute args) are absolute, exist, and are not
    left as the template placeholder
  - secrets aren't sitting unprotected (.env not gitignored) or inlined into mcp.json
  - (best effort) the server process actually launches and doesn't dump to stdout

Usage:
    python3 validate_glaido_mcp.py /absolute/path/to/server-folder [--no-launch] [--timeout 3]

Exit code is non-zero if any check FAILs (WARN/INFO do not fail the run).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PLACEHOLDER = "/ABSOLUTE/PATH/TO"

# Install guidance shown when a server's launcher isn't found on PATH.
INSTALL_HINTS = {
    "uv": "Install uv (recommended for Python - it manages the venv AND installs Python for you):\n"
          "          macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh   (or: brew install uv)\n"
          "          Windows:     powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"",
    "uvx": "uvx ships with uv. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh   (or: brew install uv)",
    "node": "Install Node.js LTS: https://nodejs.org  (or: brew install node, or via nvm)",
    "npx": "npx ships with Node.js. Install Node.js LTS: https://nodejs.org  (or: brew install node)",
    "python3": "Recommended: install uv and run via `uv run` - uv fetches Python for you:\n"
               "          curl -LsSf https://astral.sh/uv/install.sh | sh\n"
               "          Otherwise install Python 3.11+ from https://python.org",
}
INSTALL_HINTS["python"] = INSTALL_HINTS["python3"]

# Patterns that look like real secrets if found inline in mcp.json env values.
SECRET_VALUE_PATTERNS = [
    re.compile(r"^sk-[A-Za-z0-9]"),       # OpenAI-style
    re.compile(r"^gh[pousr]_[A-Za-z0-9]"),  # GitHub tokens
    re.compile(r"^xox[baprs]-"),          # Slack tokens
    re.compile(r"^[A-Za-z0-9_\-]{32,}$"),  # long opaque token
]

failures = 0
warnings = 0


def report(level: str, msg: str) -> None:
    global failures, warnings
    if level == "FAIL":
        failures += 1
    elif level == "WARN":
        warnings += 1
    print(f"[{level}] {msg}")


def looks_like_path(value: str) -> bool:
    return value.startswith("/") or bool(re.match(r"^[A-Za-z]:[\\/]", value))


def check_paths_in_args(args: list, folder: Path) -> None:
    """Validate --directory value and any absolute-looking path args."""
    for i, arg in enumerate(args):
        if not isinstance(arg, str):
            continue
        if PLACEHOLDER in arg:
            report("FAIL", f"args still contains the template placeholder: {arg!r} "
                           f"(replace with the real absolute path, e.g. {folder})")
            continue
        if arg == "--directory" and i + 1 < len(args):
            value = args[i + 1]
            if PLACEHOLDER in value:
                continue  # already reported when the loop reaches the value itself
            if not os.path.isabs(value):
                report("FAIL", f"--directory must be an absolute path, got {value!r}")
            elif not Path(value).is_dir():
                report("FAIL", f"--directory path does not exist: {value}")
        elif looks_like_path(arg) and arg not in ("--directory",):
            if not os.path.isabs(arg):
                report("FAIL", f"path argument is not absolute: {arg!r}")
            elif not Path(arg).exists():
                report("WARN", f"path argument does not exist (build first?): {arg}")


def check_command(command: str, folder: Path) -> None:
    if not command or not command.strip():
        report("FAIL", "server has an empty `command`")
        return
    if PLACEHOLDER in command:
        report("FAIL", f"`command` still contains the template placeholder: {command!r}")
        return
    if looks_like_path(command):
        if not os.path.isabs(command):
            report("FAIL", f"`command` looks like a path but is not absolute: {command!r}")
        elif not Path(command).exists():
            report("FAIL", f"`command` path does not exist: {command}")
        else:
            report("PASS", f"`command` found: {command}")
    else:
        resolved = shutil.which(command)
        if resolved:
            report("PASS", f"`command` {command!r} is on PATH ({resolved})")
            report("INFO", "Glaido is a GUI app and may not inherit your shell PATH. If the "
                           "server launches here but fails in Glaido with 'command not found', "
                           f"set \"command\" to the absolute path: {resolved}")
        else:
            msg = (f"`command` {command!r} not found on PATH - the runtime isn't installed "
                   f"(or isn't on PATH).")
            hint = INSTALL_HINTS.get(command)
            if hint:
                msg += f"\n        → {hint}"
            report("FAIL", msg)


def check_env_block(env: dict) -> None:
    if not isinstance(env, dict):
        report("FAIL", "`env` must be an object")
        return
    for key, value in env.items():
        if not isinstance(value, str):
            report("WARN", f"env value for {key!r} should be a string")
            continue
        if any(p.search(value) for p in SECRET_VALUE_PATTERNS):
            report("WARN", f"env key {key!r} looks like a secret inlined in mcp.json - it will "
                           f"be copied into Glaido's config on import. Prefer a gitignored .env.")


def check_secrets_hygiene(folder: Path) -> None:
    env_file = folder / ".env"
    env_example = folder / ".env.example"
    gitignore = folder / ".gitignore"
    if env_file.exists():
        ignored = gitignore.exists() and any(
            line.strip() in (".env", "/.env", "*.env")
            for line in gitignore.read_text(errors="ignore").splitlines()
        )
        if ignored:
            report("PASS", ".env exists and is gitignored")
        else:
            report("WARN", ".env exists but is not covered by .gitignore - risk of committing secrets")
    elif env_example.exists():
        report("INFO", "no .env yet - remind the user to copy .env.example to .env and fill it in")


def launch_check(command: str, args: list, cwd: Path, timeout: float) -> None:
    """Best effort: start the server and confirm it doesn't crash or write to stdout."""
    exe = command if looks_like_path(command) else shutil.which(command)
    if not exe:
        report("INFO", "skipping launch check (command not resolvable)")
        return
    try:
        proc = subprocess.Popen(
            [exe, *[a for a in args if isinstance(a, str)]],
            cwd=str(cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:  # noqa: BLE001
        report("FAIL", f"could not launch server: {exc}")
        return

    time.sleep(timeout)
    if proc.poll() is not None:
        # Exited on its own - likely a crash or missing dependency.
        out, err = proc.communicate()
        detail = (err or out or b"").decode(errors="replace").strip()
        report("FAIL", f"server exited immediately (code {proc.returncode}). "
                       f"Last output:\n        {detail[:500]}")
        return

    # Still running = good. Stop it and see if it wrote anything to stdout unprompted.
    proc.terminate()
    try:
        out, _err = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _err = proc.communicate()
    if out and out.strip():
        report("WARN", "server wrote to stdout before any request - this corrupts the MCP "
                       "stream in Glaido. Move all logging to stderr. Saw:\n        "
                       + out.decode(errors="replace").strip()[:300])
    else:
        report("PASS", "server launched and stayed up without polluting stdout")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Glaido MCP server folder.")
    parser.add_argument("folder", help="path to the server folder containing mcp.json")
    parser.add_argument("--no-launch", action="store_true", help="skip the launch check")
    parser.add_argument("--timeout", type=float, default=3.0,
                        help="seconds to wait during the launch check (default 3)")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        report("FAIL", f"not a folder: {folder}")
        return 1

    mcp_path = folder / "mcp.json"
    if not mcp_path.exists():
        legacy = folder / ".mcp.json"
        if legacy.exists():
            mcp_path = legacy
            report("WARN", "found legacy .mcp.json - rename it to mcp.json")
        else:
            report("FAIL", f"no mcp.json at the folder root: {folder}")
            return 1

    try:
        config = json.loads(mcp_path.read_text())
    except json.JSONDecodeError as exc:
        report("FAIL", f"mcp.json is not valid JSON: {exc}")
        return 1

    servers = config.get("mcpServers") or config.get("servers")
    if not isinstance(servers, dict) or not servers:
        report("FAIL", "mcp.json must contain a non-empty `mcpServers` object")
        return 1
    report("PASS", f"mcp.json parsed; {len(servers)} server(s) defined")

    for name, server in servers.items():
        print(f"\n--- server: {name} ---")
        if not isinstance(server, dict):
            report("FAIL", f"server {name!r} must be an object")
            continue
        stype = server.get("type", "stdio")
        if stype != "stdio":
            report("INFO", f"type is {stype!r} (not a local stdio server - out of scope here)")
            continue
        command = server.get("command", "")
        srv_args = server.get("args", []) or []
        check_command(command, folder)
        check_paths_in_args(srv_args, folder)
        if "workingDirectory" in server:
            wd = server["workingDirectory"]
            if not os.path.isabs(wd):
                report("FAIL", f"workingDirectory must be absolute: {wd!r}")
            elif not Path(wd).is_dir():
                report("FAIL", f"workingDirectory does not exist: {wd}")
        check_env_block(server.get("env", {}))

        if not args.no_launch and command and not failures:
            wd = server.get("workingDirectory")
            cwd = Path(wd) if wd and os.path.isabs(wd) else folder
            launch_check(command, srv_args, cwd, args.timeout)

    print("\n--- secrets hygiene ---")
    check_secrets_hygiene(folder)

    print()
    if failures:
        print(f"RESULT: {failures} failure(s), {warnings} warning(s) - fix the failures before importing.")
        return 1
    print(f"RESULT: ready to import. {warnings} warning(s) to review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
