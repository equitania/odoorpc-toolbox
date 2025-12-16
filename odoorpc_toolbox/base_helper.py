"""Helper functions for OdooRPC operations.

This module extends the base OdooConnection class with helper functions for
common Odoo operations like partner management, state/country lookups, and
file operations.

Typical usage example:
    connection = EqOdooConnection('config.yaml')
    state_id = connection.get_state_id(country_id, state_name)
"""

import os
import base64
from typing import Optional, List, Union
from . import odoo_connection


class EqOdooConnection(odoo_connection.OdooConnection):
    """Extended Odoo connection class with helper functions.
    
    This class inherits from OdooConnection and adds various helper methods
    for common Odoo operations.
    """

    def get_state_id(self, country_id: int, state_name: str) -> Optional[int]:
        """Returns the state ID (Bundesland) for a given country and state name.

        Args:
            country_id: The ID of the country in Odoo.
            state_name: The name of the state/province/bundesland.

        Returns:
            The ID of the state if found, None otherwise.
        """
        RES_COUNTRY_STATE = self.odoo.env['res.country.state']
        state_id = RES_COUNTRY_STATE.search([
            ('name', '=', state_name),
            ('country_id', '=', country_id)
        ])
        return state_id[0] if state_id else None

    def get_res_partner_id(
        self,
        supplierno: Optional[str] = None,
        customerno: Optional[str] = None
    ) -> List[int]:
        """Retrieves partner IDs based on supplier or customer numbers.

        Args:
            supplierno: Optional supplier number to search for.
            customerno: Optional customer number to search for.

        Returns:
            List of matching partner IDs.
        """
        RES_PARTNER = self.odoo.env['res.partner']
        domain = []
        
        if supplierno:
            domain.append(('supplier_number', '=', supplierno))
        if customerno:
            domain.append(('customer_number', '=', customerno))
            
        return RES_PARTNER.search(domain)

    def get_res_partner_category_id(self, category_name: str) -> int:
        """Gets or creates a partner category (tag).

        If the category doesn't exist, it will be created.

        Args:
            category_name: Name of the category/tag.

        Returns:
            ID of the existing or newly created category.
        """
        RES_PARTNER_CATEGORY = self.odoo.env['res.partner.category']
        category_id = RES_PARTNER_CATEGORY.search([('name', '=', category_name)])
        if not category_id:
            category_data = {'name': category_name}
            category_id = RES_PARTNER_CATEGORY.create(category_data)
        return category_id

    def get_ir_sequence_number_next_actual(self, code: str) -> Optional[int]:
        """Returns the next actual number in the sequence.

        Args:
            code: The code of the sequence.

        Returns:
            The next actual number in the sequence if found, None otherwise.
        """
        IR_SEQUENCE = self.odoo.env['ir.sequence']
        sequence_id = IR_SEQUENCE.search([('code', '=', code)])
        if sequence_id:
            sequence = IR_SEQUENCE.browse(sequence_id)
            return sequence["number_next_actual"]
        return None

    def get_res_partner_title_id(self, title: str) -> Optional[int]:
        """Returns the ID of the partner title.

        Args:
            title: The title to search for.

        Returns:
            The ID of the title if found, None otherwise.
        """
        RES_PARTNER_TITLE = self.odoo.env['res.partner.title']
        title_id = RES_PARTNER_TITLE.search([('name', '=', title)])
        return title_id[0] if title_id else None

    def set_ir_sequence_number_next_actual(self, code: str, set_value: int) -> bool:
        """Sets the next actual number in the sequence.

        Args:
            code: The code of the sequence.
            set_value: The new value for the next actual number.

        Returns:
            True if the operation was successful, False otherwise.
        """
        IR_SEQUENCE = self.odoo.env['ir.sequence']
        sequence_id = IR_SEQUENCE.search([('code', '=', code)])
        if sequence_id:
            sequence = IR_SEQUENCE.browse(sequence_id)
            sequence_data = {'number_next_actual': set_value}
            sequence.write(sequence_data)
            return True
        return False

    def set_stock_warehouse_orderpoint(self, product_id: int) -> bool:
        """Sets the reorder point for a product.

        Args:
            product_id: The ID of the product.

        Returns:
            True if the operation was successful, False otherwise.
        """
        STOCK_WAREHOUSE_ORDERPOINT = self.odoo.env['stock.warehouse.orderpoint']
        orderpoint_id = STOCK_WAREHOUSE_ORDERPOINT.search([('product_id', '=', product_id)])
        if not orderpoint_id:
            orderpoint_data = {
                'product_id': product_id,
                'product_min_qty': 0,
                'product_max_qty': 0,
                'qty_multiple': 1,
            }
            STOCK_WAREHOUSE_ORDERPOINT.create(orderpoint_data)
            return True
        return False

    def get_picture(self, picture_path: str) -> Optional[str]:
        """Loads a picture from a file path and encodes it in BASE64.

        Args:
            picture_path: The path to the picture file.

        Returns:
            The BASE64 encoded picture if the file exists, None otherwise.
        """
        if os.path.exists(picture_path):
            with open(picture_path, "rb") as f:
                img = f.read()
                return str(base64.b64encode(img).decode("utf-8"))
        return None

    def get_product_uom_id(self, uom: str) -> int:
        """Returns the ID of the product unit of measure.

        Args:
            uom: The unit of measure to search for.

        Returns:
            The ID of the unit of measure if found, 1 (default) otherwise.
        """
        if self.odoo_version in [10, 11, 12]:
            PRODUCT_UOM = self.odoo.env['product.uom']
        else:
            PRODUCT_UOM = self.odoo.env['uom.uom']
        uom_id = PRODUCT_UOM.search([('name', '=', uom)])
        return uom_id[0] if uom_id else 1

    def string_contains_numbers(self, source: str) -> bool:
        """Checks if a string contains numbers.

        Args:
            source: The string to check.

        Returns:
            True if the string contains numbers, False otherwise.
        """
        return any(i.isdigit() for i in source)

    def extract_street_address_part(self, street_infos: str) -> tuple:
        """Extracts street and house number from a string.

        Args:
            street_infos: The string containing street and house number.

        Returns:
            A tuple containing the street and house number.
        """
        street = street_infos
        house_no = ""

        if len(street_infos) > 0:
            street_parts = street_infos.split(" ")
            if len(street_parts) == 2:
                street = street_parts[0]
                house_no = street_parts[1]
            elif len(street_parts) > 2:
                street = ""
                part_position = 1
                for part in street_parts:
                    if part_position == len(street_parts):
                        if self.string_contains_numbers(part):  # beinhaltet die letzte Position wirklich eine Zahl
                            house_no = part  # ja, es ist typische Adresse -> Weiherstrasse 12
                        else:
                            street += part  # nein, es ist z.B. eine GB Adresse -> Flat 42A Ashburnham Mansions
                    else:
                        street += part + " "

                    part_position += 1

        street = street.strip()
        house_no = house_no.strip()
        return street, house_no

    def check_if_company_exists(self, company_name: str, zip_code: str, city: str) -> Optional[int]:
        """Checks if a company exists in the res_partner table.

        Args:
            company_name: The name of the company.
            zip_code: The zip code of the company.
            city: The city of the company.

        Returns:
            The ID of the company if found, None otherwise.
        """
        RES_PARTNER = self.odoo.env['res.partner']
        record = RES_PARTNER.search([
            ('name', 'like', company_name),
            ('zip', '=', zip_code),
            ('city', '=', city),
            ('is_company', '=', True)
        ])
        return record[0] if record else None