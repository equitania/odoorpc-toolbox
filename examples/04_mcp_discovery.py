#!/usr/bin/env python3
"""MCP Discovery example for odoorpc-toolbox.

This example demonstrates how to use the MCP-compatible method discovery
functionality for integration with AI systems and MCP servers.

Usage:
    python 04_mcp_discovery.py
"""

import json

from odoorpc_toolbox import __version__, get_available_methods, get_method_schema, print_available_methods


def main():
    """Demonstrate MCP discovery functionality."""

    print(f"odoorpc-toolbox v{__version__}")
    print("=" * 60)

    # =========================================
    # 1. Get all available methods
    # =========================================
    print("\n--- All Available Methods ---")

    schema = get_available_methods()

    print(f"Schema version: {schema['schema_version']}")
    print(f"Package: {schema['package']}")
    print(f"Version: {schema['version']}")
    print(f"Total methods: {len(schema['methods'])}")

    print("\nMethod list:")
    for method in schema["methods"]:
        print(f"  - {method['name']}")

    # =========================================
    # 2. Get schema for specific method
    # =========================================
    print("\n--- Method Schema: create_partner ---")

    method_schema = get_method_schema("create_partner")
    print(json.dumps(method_schema, indent=2))

    # =========================================
    # 3. Get schema for search_read
    # =========================================
    print("\n--- Method Schema: search_read ---")

    method_schema = get_method_schema("search_read")
    print(json.dumps(method_schema, indent=2))

    # =========================================
    # 4. Human-readable output
    # =========================================
    print("\n--- Human-Readable Format ---")
    print_available_methods(format="text")

    # =========================================
    # 5. JSON output (for MCP servers)
    # =========================================
    print("\n--- JSON Format (for MCP servers) ---")
    print("Use: print_available_methods(format='json')")
    print("Or:  json.dumps(get_available_methods(), indent=2)")

    # =========================================
    # 6. Filter methods by category
    # =========================================
    print("\n--- Methods by Category ---")

    schema = get_available_methods()

    # Partner methods
    partner_methods = [m for m in schema["methods"] if "partner" in m["name"].lower()]
    print(f"\nPartner methods ({len(partner_methods)}):")
    for m in partner_methods:
        print(f"  - {m['name']}: {m['description'][:50]}...")

    # Product methods
    product_methods = [m for m in schema["methods"] if "product" in m["name"].lower()]
    print(f"\nProduct methods ({len(product_methods)}):")
    for m in product_methods:
        print(f"  - {m['name']}: {m['description'][:50]}...")

    # Country/State methods
    location_methods = [m for m in schema["methods"] if "country" in m["name"].lower() or "state" in m["name"].lower()]
    print(f"\nLocation methods ({len(location_methods)}):")
    for m in location_methods:
        print(f"  - {m['name']}: {m['description'][:50]}...")

    # =========================================
    # 7. Save schema to file
    # =========================================
    print("\n--- Save Schema to File ---")

    output_file = "odoorpc_toolbox_schema.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Schema saved to: {output_file}")


if __name__ == "__main__":
    main()
