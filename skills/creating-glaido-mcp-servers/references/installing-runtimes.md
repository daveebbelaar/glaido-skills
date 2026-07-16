# Installing runtimes (uv, Node, Python)

A local MCP server only runs if the launcher named in `mcp.json` (`uv`, `node`, `npx`,
`python3`, …) is actually installed. Many people building their first Glaido tool won't have
these yet. Check first, install only what's needed, and confirm before scaffolding.

## Check what's already there

```bash
command -v uv      && uv --version        # Python servers (recommended launcher)
command -v node    && node --version      # TypeScript servers
command -v npx     && npx --version       # running published servers / TypeScript
command -v python3 && python3 --version   # only if not using uv
```

If a check prints nothing, that tool isn't on PATH and needs installing.

## uv — recommended for Python

**Why uv (and why it solves the venv problem):** with plain Python you have to create a virtual
environment, activate it, `pip install` the right packages, and keep the right Python version
around — every time, and it breaks in confusing ways. `uv` removes all of that:

- `uv run server.py` automatically creates an isolated environment and installs the
  dependencies from `pyproject.toml` — no manual `venv`, no `activate`, no global package mess.
- uv **also installs Python for you** if a compatible version isn't present, so the user
  doesn't need a separate Python install at all.
- It's one fast tool instead of `python` + `pip` + `venv` juggling.

That's exactly why the `mcp.json` for a Python server uses `uv --directory <path> run
server.py`: one command, reproducible, isolated.

**Install:**

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or, if Homebrew is present:
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installing, **restart the terminal** (or `source ~/.zshrc`) so `uv` is on PATH, then
verify with `uv --version`. To pre-install a Python version explicitly: `uv python install`
(usually unnecessary — `uv run` fetches one on demand).

## Node.js (node / npm / npx)

Needed for **TypeScript servers** and for **running published servers via `npx`** (a common
way to reuse an existing third-party MCP server).

**Install:**

```bash
# macOS
brew install node
# Any platform: download the LTS installer
#   https://nodejs.org
# Windows (winget)
winget install OpenJS.NodeJS.LTS
```

Prefer **nvm** if the user wants to manage multiple Node versions:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# restart shell, then:
nvm install --lts
```

Verify with `node --version` and `npx --version` (npx ships with Node).

## Plain Python (only if the user declines uv)

If someone insists on system Python instead of uv, they take on the venv work uv would have
handled:

```bash
cd my-server
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

…and the `mcp.json` `command` must then point at that venv's Python (an absolute path to
`.venv/bin/python`), not a bare `python3`. This is more fragile than uv — recommend uv unless
there's a specific reason not to.

## The GUI-PATH gotcha (important for Glaido)

Glaido is a desktop (GUI) app. On macOS especially, GUI apps launched from Finder/Dock **do
not inherit the PATH from your shell config** (`~/.zshrc`, `~/.bashrc`). So a command that
works in your terminal can still fail inside Glaido with "command not found" — even though it's
"installed."

The robust fix: **use the absolute path to the binary in `mcp.json`** rather than a bare name.

```bash
command -v uv     # e.g. /Users/you/.local/bin/uv  → use this full path as "command"
command -v node   # e.g. /opt/homebrew/bin/node
```

```json
{ "command": "/Users/you/.local/bin/uv", "args": ["--directory", "/abs/path", "run", "server.py"] }
```

`scripts/validate_glaido_mcp.py` prints the resolved absolute path when it finds a bare-name
command, so you can paste it straight in if a server connects in the terminal but not in Glaido.

## After installing anything

Restart the terminal **and** Glaido so updated PATHs are picked up, then re-run the validator.
