# Other languages

MCP is language-agnostic. If the user wants Go, Rust, Java, C#, Kotlin, Ruby, or anything
else, the shape of the work is identical to the Python and TypeScript paths — only the SDK and
the `command` change. Use the language's **official MCP SDK** and fetch its current docs
(your training data is likely stale on exact APIs — search the web or use a docs tool).

## Official SDKs

| Language | SDK |
| --- | --- |
| Python | `mcp` (FastMCP) — see [python-fastmcp.md](python-fastmcp.md) |
| TypeScript / Node | `@modelcontextprotocol/sdk` — see [typescript-mcp.md](typescript-mcp.md) |
| Go | `github.com/modelcontextprotocol/go-sdk` |
| Rust | `rmcp` (the official Rust SDK) |
| Java | `io.modelcontextprotocol.sdk` |
| Kotlin | `mcp-kotlin-sdk` |
| C# / .NET | `ModelContextProtocol` (NuGet) |
| Ruby | community `mcp` gem |

Confirm the exact package name and current API from the SDK's own docs before scaffolding.

**Prerequisite:** make sure the language's toolchain/compiler is installed before you start
(`go`, `cargo`, the JDK, `dotnet`, …), the same way you'd check for `uv` or `node`. For Python
and Node specifics, see [installing-runtimes.md](installing-runtimes.md).

## The six things that must be true regardless of language

1. **stdio transport.** Wire the server to MCP over stdin/stdout. Every SDK has a stdio
   transport — use it. This is what Glaido launches for local servers.
2. **stdout is sacred.** Write nothing to stdout but MCP protocol messages. Send all logging to
   stderr. A stray write to stdout breaks the connection — this is the most common failure.
3. **Server-level instructions.** Set the server's `instructions` (every SDK exposes this on
   the server/constructor — it becomes the `instructions` field of the MCP `initialize`
   response). The client passes it to the model as a hint about what the whole server is for
   and when to reach for it, separate from the per-tool descriptions. Write a "use this server
   to…" statement naming the domain and the kinds of actions it covers.
4. **Tools described for an agent.** Each tool needs a clear name and description (what it does,
   when to use it) and a typed input schema. Mark read-only vs destructive tools using the
   SDK's annotation/hint mechanism so Glaido sets sane approval defaults.
5. **Secrets from a local `.env` in the folder**, loaded relative to the binary/source, not the
   working directory. Commit `.env.example`, gitignore `.env`. If the language has no good
   dotenv loader, put non-secret config in the `mcp.json` `env` block and read it from the
   process environment instead.
6. **`mcp.json` with absolute paths and a PATH-resolvable command.** Build/compile first if the
   language needs it, then point `command`/`args` at the runnable artifact.

## mcp.json shape per language

The pattern is always the same — swap `command` and `args` for whatever launches the built
artifact:

```json
{
  "mcpServers": {
    "My Server": {
      "type": "stdio",
      "command": "<launcher>",
      "args": ["<absolute path or args>"],
      "env": {}
    }
  }
}
```

Examples:

- **Go (compiled binary):** `"command": "/ABSOLUTE/PATH/TO/my-server/bin/server"`, `"args": []`
- **Rust (compiled binary):** `"command": "/ABSOLUTE/PATH/TO/target/release/my-server"`
- **Java (jar):** `"command": "java"`, `"args": ["-jar", "/ABSOLUTE/PATH/TO/my-server.jar"]`
- **C# / .NET:** `"command": "dotnet"`, `"args": ["/ABSOLUTE/PATH/TO/MyServer.dll"]`

For compiled languages, **build first** and point at the produced binary/jar/dll. The user
must rebuild after code changes before re-testing in Glaido.

## Validate

Whatever the language, run the bundled checker against the folder before handing off:

```bash
python3 <path-to-this-skill>/scripts/validate_glaido_mcp.py /ABSOLUTE/PATH/TO/my-server
```

It checks the `mcp.json` structure, absolute paths, the command on PATH, committed secrets,
and that the process launches — none of which is language-specific.
