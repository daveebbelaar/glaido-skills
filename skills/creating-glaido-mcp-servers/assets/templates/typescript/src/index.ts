/**
 * Glaido MCP server (TypeScript + @modelcontextprotocol/sdk).
 *
 * Replace the example tools with your own. Build with `npm run build` and point mcp.json at
 * dist/index.js before importing into Glaido.
 */
import { fileURLToPath } from "node:url";
import path from "node:path";
import { config as loadEnv } from "dotenv";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Load secrets from THIS folder's .env (one level up from dist/ or src/), not the cwd.
const __dirname = path.dirname(fileURLToPath(import.meta.url));
loadEnv({ path: path.join(__dirname, "..", ".env") });

const server = new McpServer({ name: "My Server", version: "0.1.0" });

server.registerTool(
  "search_items",
  {
    description: "Search items by a free-text query. Read-only.",
    inputSchema: { query: z.string(), limit: z.number().optional() },
    annotations: { readOnlyHint: true, openWorldHint: true },
  },
  async ({ query, limit }) => {
    // ... call your API or logic here ...
    const data: unknown[] = [];
    return { content: [{ type: "text", text: JSON.stringify({ status: "ok", data }) }] };
  },
);

server.registerTool(
  "delete_item",
  {
    description: "Delete an item by id. Destructive — Glaido will ask before running.",
    inputSchema: { id: z.string() },
    annotations: { readOnlyHint: false, destructiveHint: true },
  },
  async ({ id }) => {
    // ... perform the deletion ...
    return { content: [{ type: "text", text: JSON.stringify({ status: "ok", deleted: id }) }] };
  },
);

// Never console.log — stdout is the MCP channel. Use console.error for any logging.
const transport = new StdioServerTransport();
await server.connect(transport);
