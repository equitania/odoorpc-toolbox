#!/usr/bin/env python3
"""Partner operations example for odoorpc-toolbox.

This example demonstrates various partner-related operations including
searching, creating, and managing partners in Odoo.

Usage:
    python 02_partner_operations.py
"""

from odoorpc_toolbox import EqOdooConnection


def main():
    """Demonstrate partner operations."""

    # Establish connection
    conn = EqOdooConnection("odoo_config.yaml")
    print(f"Connected to Odoo {conn.odoo_version}")

    # =========================================
    # 1. Search for existing partners
    # =========================================
    print("\n--- Searching Partners ---")

    # Search by customer number (requires eq_partner_number module)
    partner_ids = conn.get_res_partner_id(customerno="CUST001")
    print(f"Partners with customer number CUST001: {partner_ids}")

    # Search by supplier number
    partner_ids = conn.get_res_partner_id(supplierno="SUP001")
    print(f"Partners with supplier number SUP001: {partner_ids}")

    # =========================================
    # 2. Check if company exists
    # =========================================
    print("\n--- Checking Company Existence ---")

    company_id = conn.check_if_company_exists(company_name="Musterfirma", zip_code="12345", city="Berlin")
    if company_id:
        print(f"Company found with ID: {company_id}")
    else:
        print("Company not found")

    # =========================================
    # 3. Create a new partner
    # =========================================
    print("\n--- Creating Partner ---")

    # Get country ID first
    germany_id = conn.get_country_id_by_code("DE")
    print(f"Germany country ID: {germany_id}")

    # Create a company
    new_company_id = conn.create_partner(
        name="Test Company GmbH",
        is_company=True,
        email="info@testcompany.de",
        phone="+49 123 456789",
        street="Hauptstraße 1",
        city="München",
        zip_code="80331",
        country_id=germany_id,
        # Additional fields via kwargs
        website="https://www.testcompany.de",
        vat="DE123456789",
    )
    print(f"Created company with ID: {new_company_id}")

    # Create a contact person
    new_contact_id = conn.create_partner(
        name="Max Mustermann",
        is_company=False,
        email="max@testcompany.de",
        phone="+49 123 456790",
        parent_id=new_company_id,  # Link to company
    )
    print(f"Created contact with ID: {new_contact_id}")

    # =========================================
    # 4. Partner categories (tags)
    # =========================================
    print("\n--- Partner Categories ---")

    # Get or create a category
    category_id = conn.get_res_partner_category_id("VIP Customer")
    print(f"Category 'VIP Customer' ID: {category_id}")

    # Get partner title
    title_id = conn.get_res_partner_title_id("Herr")
    print(f"Title 'Herr' ID: {title_id}")

    # =========================================
    # 5. Location helpers
    # =========================================
    print("\n--- Location Helpers ---")

    # Get country by name
    country_id = conn.get_country_id("Germany")
    print(f"Germany ID (by name): {country_id}")

    # Get country by code
    usa_id = conn.get_country_id_by_code("US")
    print(f"USA ID (by code): {usa_id}")

    # Get state/province
    if germany_id:
        bavaria_id = conn.get_state_id(germany_id, "Bayern")
        print(f"Bavaria state ID: {bavaria_id}")

    # =========================================
    # 6. Address parsing
    # =========================================
    print("\n--- Address Parsing ---")

    # German address format
    street, house_no = conn.extract_street_address_part("Hauptstraße 123")
    print(f"German: Street='{street}', House='{house_no}'")

    # Multi-word street
    street, house_no = conn.extract_street_address_part("Am Alten Markt 42")
    print(f"Multi-word: Street='{street}', House='{house_no}'")

    # British format (no number at end)
    street, house_no = conn.extract_street_address_part("Flat 42A Ashburnham Mansions")
    print(f"British: Street='{street}', House='{house_no}'")


if __name__ == "__main__":
    main()
