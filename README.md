# AI Buyers Guide — MCP Server

Model Context Protocol (MCP) server for the [AI Buyers Guide](https://deals.oneheadlightapp.com), providing AI agents with direct tool access to curated Amazon product recommendations.

## Live Endpoint

```
https://mcp.oneheadlightapp.com/sse
```

Connect using any MCP-compatible client (Claude Desktop, Cursor, etc.).

## Available Tools

| Tool | Description |
|------|-------------|
| `search_products` | Search products by keyword, category, or tag |
| `get_product` | Get detailed info for a specific product by ASIN |
| `recommend_products` | Get personalized recommendations based on use case |
| `list_categories` | List all product categories |
| `get_category_products` | Get all products in a category |
| `get_top_products` | Get top-rated picks across categories |
| `list_guides` | List all buying guides |
| `get_guide` | Get a detailed buying guide with product comparisons |

## Quick Start

```bash
pip install fastmcp pyyaml
python server.py --sse
```

The server runs on `http://localhost:8000` with SSE transport.

## About

Part of the [AI Buyers Guide](https://deals.oneheadlightapp.com) — a curated product recommendation site optimized for both humans and AI agents. Browse buying guides, compare products, and find the best deals through our [website](https://deals.oneheadlightapp.com) or connect directly via MCP.

- Website: https://deals.oneheadlightapp.com
- API: https://deals.oneheadlightapp.com/api/products.json
- Agent sitemap: https://deals.oneheadlightapp.com/llms.txt
