#!/usr/bin/env python3
"""Product operations example for odoorpc-toolbox.

This example demonstrates product-related operations including
searching products, managing units of measure, and inventory operations.

Usage:
    python 03_product_operations.py
"""

from odoorpc_toolbox import EqOdooConnection


def main():
    """Demonstrate product operations."""

    # Establish connection
    conn = EqOdooConnection('odoo_config.yaml')
    print(f"Connected to Odoo {conn.odoo_version}")

    # =========================================
    # 1. Search products by reference (SKU)
    # =========================================
    print("\n--- Product Search ---")

    # Search for product by internal reference
    product_id = conn.get_product_by_ref("SKU-001")
    if product_id:
        print(f"Product 'SKU-001' found with ID: {product_id}")
    else:
        print("Product 'SKU-001' not found")

    # Search for product template
    template_id = conn.get_product_template_by_ref("SKU-001")
    if template_id:
        print(f"Product template 'SKU-001' found with ID: {template_id}")
    else:
        print("Product template 'SKU-001' not found")

    # =========================================
    # 2. Unit of Measure
    # =========================================
    print("\n--- Units of Measure ---")

    # Get unit of measure ID
    uom_id = conn.get_product_uom_id("Stück")
    print(f"UoM 'Stück' ID: {uom_id}")

    uom_id = conn.get_product_uom_id("kg")
    print(f"UoM 'kg' ID: {uom_id}")

    # Note: Returns 1 (default) if not found
    uom_id = conn.get_product_uom_id("NonexistentUnit")
    print(f"UoM 'NonexistentUnit' ID (default): {uom_id}")

    # =========================================
    # 3. Reorder Points (Warehouse)
    # =========================================
    print("\n--- Warehouse Operations ---")

    if product_id:
        # Set reorder point for product
        success = conn.set_stock_warehouse_orderpoint(product_id)
        if success:
            print(f"Reorder point created for product {product_id}")
        else:
            print(f"Reorder point already exists for product {product_id}")

    # =========================================
    # 4. Generic search_read for products
    # =========================================
    print("\n--- Product Search with search_read ---")

    # Get first 5 products with specific fields
    products = conn.search_read(
        model='product.product',
        domain=[('sale_ok', '=', True)],
        fields=['name', 'default_code', 'list_price', 'qty_available'],
        limit=5,
        order='name asc'
    )

    print(f"Found {len(products)} saleable products:")
    for product in products:
        print(f"  - {product.get('name')} "
              f"[{product.get('default_code', 'N/A')}] "
              f"Price: {product.get('list_price', 0):.2f}")

    # =========================================
    # 5. Product images
    # =========================================
    print("\n--- Product Images ---")

    # Load image from file (BASE64 encoded)
    image_path = "/path/to/product_image.jpg"
    image_base64 = conn.get_picture(image_path)
    if image_base64:
        print(f"Image loaded, size: {len(image_base64)} bytes (base64)")
    else:
        print(f"Image not found at: {image_path}")


if __name__ == '__main__':
    main()
