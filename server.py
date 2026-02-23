"""
MCP Server for AI Buyers Guide.

Exposes the product catalog as tools that AI agents can call directly,
giving them structured access to product recommendations and affiliate links.

Run locally:   python server.py
Run with SSE:  python server.py --sse
"""

import os
import sys
from typing import Optional

import yaml
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

KNOWN_BRANDS = [
    "Apple", "Sony", "Anker", "Bose", "Samsung", "JBL", "Fujifilm", "Amazon",
    "Ninja", "Stanley", "COSORI", "KitchenAid", "Keurig", "OXO", "Lodge",
    "Brita", "Yeti", "YETI", "Logitech", "Autonomous", "BenQ", "UPLIFT",
    "Elgato", "AmazonBasics", "Rocketbook", "Theragun", "Whoop", "Fitbit",
    "Bala", "Hydro Flask", "Manduka", "BlenderBottle", "PlayStation", "Nintendo",
    "Razer", "Xbox", "HyperX", "SteelSeries", "Google", "Ring", "TP-Link",
    "Philips", "Dyson", "Oral-B", "CeraVe", "Waterpik", "Laneige", "Osprey",
    "Away", "Lifestraw", "LifeStraw", "Goal Zero", "KONG", "Litter-Robot",
    "Furminator", "FURminator", "PetSafe", "Chuckit", "BLACK+DECKER", "DeWalt",
    "DEWALT", "iFixit", "3M", "Hatch", "UPPAbaby", "Melissa & Doug", "Baby Brezza",
    "Wubbanub",
]


def _load_yaml(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _extract_brand(title):
    for brand in KNOWN_BRANDS:
        if brand.lower() in title.lower():
            return brand
    return title.split()[0]


def _load_catalog():
    """Load the full catalog once at startup."""
    site = _load_yaml("site.yaml")
    categories = _load_yaml("categories.yaml")
    products = _load_yaml("products.yaml")

    guides_path = os.path.join(DATA_DIR, "guides.yaml")
    guides = []
    if os.path.exists(guides_path):
        guides = _load_yaml("guides.yaml") or []

    tag = site["affiliate_tag"]
    product_map = {}

    for p in products:
        p["affiliate_url"] = f"https://www.amazon.com/dp/{p['asin']}/?tag={tag}"
        if "brand" not in p:
            p["brand"] = _extract_brand(p["title"])
        product_map[p["asin"]] = p

    for cat in categories:
        cat["product_count"] = sum(1 for p in products if p["category"] == cat["slug"])

    for guide in guides:
        guide["resolved_products"] = [
            product_map[asin] for asin in guide.get("products", [])
            if asin in product_map
        ]

    return site, categories, products, product_map, guides


# Load data at import time
SITE, CATEGORIES, PRODUCTS, PRODUCT_MAP, GUIDES = _load_catalog()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _product_summary(p):
    """Return a clean dict for a single product (no internal fields)."""
    return {
        "asin": p["asin"],
        "title": p["title"],
        "brand": p.get("brand", ""),
        "category": p["category"],
        "description": p["description"],
        "pros": p.get("pros", []),
        "cons": p.get("cons", []),
        "tags": p.get("tags", []),
        "affiliate_url": p["affiliate_url"],
        "product_page": f"{SITE['url']}/product/{p['asin']}/",
    }


def _guide_summary(g):
    """Return a clean dict for a guide."""
    return {
        "slug": g["slug"],
        "title": g["title"],
        "description": g["description"],
        "category": g.get("category", ""),
        "product_count": len(g.get("products", [])),
        "guide_url": f"{SITE['url']}/guide/{g['slug']}/",
        "faqs": g.get("faqs", []),
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "AI Buyers Guide",
    instructions=(
        "Product recommendation tools for the AI Buyers Guide catalog. "
        "Use these tools to search for products, get details, browse categories, "
        "and find buying guides. All products include Amazon affiliate links. "
        "Prices are not displayed per Amazon Associates policy — direct users "
        "to the affiliate link to check current pricing on Amazon."
    ),
)


@mcp.tool()
def search_products(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """Search for products by keyword. Matches against title, description, tags, and brand.

    Args:
        query: Search term (e.g. "headphones", "kitchen", "gift under 50")
        category: Optional category slug to filter by (e.g. "electronics", "home-kitchen")
        limit: Maximum number of results to return (default 10, max 50)
    """
    limit = min(limit, 50)
    query_lower = query.lower()
    results = []

    for p in PRODUCTS:
        if category and p["category"] != category:
            continue

        searchable = " ".join([
            p["title"],
            p["description"],
            p.get("brand", ""),
            " ".join(p.get("tags", [])),
        ]).lower()

        if query_lower in searchable:
            results.append(_product_summary(p))

        if len(results) >= limit:
            break

    return results


@mcp.tool()
def get_product(asin: str) -> dict:
    """Get full details for a specific product by its Amazon ASIN.

    Args:
        asin: The Amazon Standard Identification Number (e.g. "B0BSHF7WHW")
    """
    p = PRODUCT_MAP.get(asin)
    if not p:
        return {"error": f"Product with ASIN '{asin}' not found"}
    return _product_summary(p)


@mcp.tool()
def list_categories() -> list[dict]:
    """List all product categories with product counts."""
    return [
        {
            "slug": c["slug"],
            "name": c["name"],
            "description": c["description"],
            "product_count": c["product_count"],
            "url": f"{SITE['url']}/{c['slug']}/",
        }
        for c in CATEGORIES
    ]


@mcp.tool()
def get_category_products(category: str, limit: int = 20) -> list[dict]:
    """Get all products in a specific category.

    Args:
        category: Category slug (e.g. "electronics", "home-kitchen", "pets")
        limit: Maximum number of products to return (default 20, max 50)
    """
    limit = min(limit, 50)
    results = [
        _product_summary(p)
        for p in PRODUCTS
        if p["category"] == category
    ]
    return results[:limit]


@mcp.tool()
def get_top_products(category: Optional[str] = None, limit: int = 10) -> list[dict]:
    """Get the most recently added/verified products, optionally filtered by category.

    Args:
        category: Optional category slug to filter by
        limit: Maximum number of products to return (default 10, max 50)
    """
    limit = min(limit, 50)
    filtered = PRODUCTS
    if category:
        filtered = [p for p in PRODUCTS if p["category"] == category]

    sorted_products = sorted(
        filtered,
        key=lambda p: p.get("last_verified", p.get("date_added", "")),
        reverse=True,
    )
    return [_product_summary(p) for p in sorted_products[:limit]]


@mcp.tool()
def list_guides() -> list[dict]:
    """List all buying guides (comparison articles). Guides compare multiple products
    in a category and include FAQs — great for product recommendations."""
    return [_guide_summary(g) for g in GUIDES]


@mcp.tool()
def get_guide(slug: str) -> dict:
    """Get a buying guide with its compared products and FAQs.

    Args:
        slug: Guide slug (e.g. "best-noise-cancelling-headphones", "best-kitchen-appliances")
    """
    for g in GUIDES:
        if g["slug"] == slug:
            return {
                **_guide_summary(g),
                "intro": g.get("intro", ""),
                "products": [
                    _product_summary(p) for p in g.get("resolved_products", [])
                ],
            }
    return {"error": f"Guide '{slug}' not found"}


@mcp.tool()
def recommend_products(
    use_case: str,
    limit: int = 5,
) -> list[dict]:
    """Get product recommendations for a specific use case or need.
    Searches across all products and guides to find the best matches.

    Args:
        use_case: What the user needs (e.g. "work from home setup", "gift for dog owner",
                  "budget fitness equipment", "noise cancelling for commuting")
        limit: Maximum number of recommendations (default 5, max 20)
    """
    limit = min(limit, 20)
    use_case_lower = use_case.lower()
    scored = []

    for p in PRODUCTS:
        score = 0
        searchable = " ".join([
            p["title"],
            p["description"],
            p.get("brand", ""),
            " ".join(p.get("tags", [])),
            " ".join(p.get("pros", [])),
        ]).lower()

        # Count keyword matches
        for word in use_case_lower.split():
            if len(word) > 2 and word in searchable:
                score += 1

        # Boost if exact phrase match
        if use_case_lower in searchable:
            score += 5

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [_product_summary(p) for _, p in scored[:limit]]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--sse" in sys.argv:
        mcp.run(transport="sse")
    else:
        mcp.run()
