#!/usr/bin/env python3
"""Generic operations example for odoorpc-toolbox.

This example demonstrates generic RPC operations that can be used
for any Odoo model and method.

Usage:
    python 05_generic_operations.py
"""

from odoorpc_toolbox import EqOdooConnection


def main():
    """Demonstrate generic operations."""

    # Establish connection
    conn = EqOdooConnection("odoo_config.yaml")
    print(f"Connected to Odoo {conn.odoo_version}")

    # =========================================
    # 1. search_read - Flexible data retrieval
    # =========================================
    print("\n--- search_read Examples ---")

    # Get all companies
    companies = conn.search_read(
        model="res.partner",
        domain=[("is_company", "=", True)],
        fields=["name", "email", "city", "country_id"],
        limit=10,
        order="name asc",
    )
    print("\nTop 10 companies:")
    for company in companies:
        country = company.get("country_id", [None, "N/A"])
        country_name = country[1] if isinstance(country, list) else "N/A"
        print(f"  - {company['name']} ({company.get('city', 'N/A')}, {country_name})")

    # Get recent sales orders
    orders = conn.search_read(
        model="sale.order",
        domain=[("state", "in", ["sale", "done"])],
        fields=["name", "partner_id", "amount_total", "date_order"],
        limit=5,
        order="date_order desc",
    )
    print("\nRecent 5 confirmed orders:")
    for order in orders:
        partner = order.get("partner_id", [None, "Unknown"])
        partner_name = partner[1] if isinstance(partner, list) else "Unknown"
        print(f"  - {order['name']}: {partner_name} - {order['amount_total']:.2f}")

    # =========================================
    # 2. execute_method - Call any Odoo method
    # =========================================
    print("\n--- execute_method Examples ---")

    # Call name_search on res.partner
    result = conn.execute_method(
        model="res.partner",
        method="name_search",
        args=["Test"],  # Search for partners containing 'Test'
        kwargs={"limit": 5},
    )
    print("\nname_search results for 'Test':")
    for partner_id, partner_name in result:
        print(f"  - [{partner_id}] {partner_name}")

    # Call a method on specific records
    partner_ids = [1, 2, 3]  # Admin and first partners
    result = conn.execute_method(model="res.partner", method="read", record_ids=partner_ids, args=[["name", "email"]])
    print("\nReading specific partners:")
    for partner in result:
        print(f"  - {partner['name']}: {partner.get('email', 'N/A')}")

    # =========================================
    # 3. Sequence operations
    # =========================================
    print("\n--- Sequence Operations ---")

    # Get next sequence number for sales orders
    next_so_number = conn.get_ir_sequence_number_next_actual("sale.order")
    print(f"Next SO number: {next_so_number}")

    # Get next sequence number for invoices
    next_inv_number = conn.get_ir_sequence_number_next_actual("account.move")
    print(f"Next Invoice number: {next_inv_number}")

    # =========================================
    # 4. Utility functions
    # =========================================
    print("\n--- Utility Functions ---")

    # Check if string contains numbers
    test_strings = ["ABC123", "Hello", "42", "Test!"]
    for s in test_strings:
        has_numbers = conn.string_contains_numbers(s)
        print(f"  '{s}' contains numbers: {has_numbers}")

    # =========================================
    # 5. Advanced: Custom model operations
    # =========================================
    print("\n--- Custom Model Operations ---")

    # Count records in various models
    models_to_count = [
        ("res.partner", [("is_company", "=", True)], "Companies"),
        ("res.partner", [("is_company", "=", False)], "Contacts"),
        ("product.product", [], "Products"),
        ("sale.order", [("state", "=", "sale")], "Confirmed Orders"),
    ]

    for model, domain, label in models_to_count:
        try:
            records = conn.search_read(model=model, domain=domain, fields=["id"], limit=None)
            print(f"  {label}: {len(records)}")
        except Exception as e:
            print(f"  {label}: Error - {e}")


if __name__ == "__main__":
    main()
