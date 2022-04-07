# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import base64
from . import odoo_connection


class EqOdooConnection(odoo_connection.OdooConnection):

    def get_state_id(self,_country_id,_state_name):
        """
        Return the state_id (Bundesland)
        :param _country_id: ID des Landes
        :param _state_name: Name des Bundeslandes/Kanton
        :return:
        """
        RES_COUNTRY_STATE = self.odoo.env['res.country.state']
        _state_id = RES_COUNTRY_STATE.search([('name', '=', _state_name), ('country_id', '=', _country_id)])
        if len(_state_id) != 0:
            _get_state_id = _state_id[0]
        else:
            _get_state_id = None

        return _get_state_id

    def get_res_partner_id(self,_supplierno, _customerno):
        """
        res.partner id ermitteln
        :param _supplierno: Lieferantennummer
        :param _customerno: Kundennummer
        :return:
        """
        RES_PARTNER = self.odoo.env['res.partner']
        if _supplierno == None and _customerno != None:
            _partner_id = RES_PARTNER.search([('customer_number', '=', _customerno)])
        elif _supplierno != None and _customerno == None:
            _partner_id = RES_PARTNER.search([('supplier_number', '=', _supplierno)])
        elif _supplierno != None and _customerno != None:
            _partner_id = RES_PARTNER.search([('supplier_number', '=', _supplierno), ('customer_number', '=', _customerno)])

        return _partner_id

    def get_res_partner_category_id(self,_category_name):
        """
        Kategorie / Schlagwörter Kontakte setzen, wenn nicht vorhanden, wird die Kategorie angelegt
        :param _category_name: Name der Kategorie
        :return:
        """
        RES_PARTNER_CATEGORY = self.odoo.env['res.partner.category']
        _category_id = RES_PARTNER_CATEGORY.search([('name', '=', _category_name)])
        if len(_category_id) == 0:
            _category_data = {}
            _category_data['name'] = _category_name
            _category_id = [RES_PARTNER_CATEGORY.create(_category_data)]

        return _category_id

    def get_ir_sequence_number_next_actual(self,_code):
        """
        Ermittelt die nächste Nummer im Zähler von ir.sequence
        :param _code: Bezeichner der Sequenz
        :return:
        """
        IR_SEQUENCE = self.odoo.env['ir.sequence']
        _sequence_id = IR_SEQUENCE.search([('code', '=', _code)])
        if len(_sequence_id) != 0:
            _ir_sequence = IR_SEQUENCE.browse(_sequence_id)
            _number_next_actual = _ir_sequence["number_next_actual"]
        else:
            _number_next_actual = None

        return _number_next_actual

    def get_res_partner_title_id(self,_title):
        """
        Ermittelt die ID der Anrede
        :param _title: Anrede
        :return:
        """
        RES_PARTNER_TITLE = self.odoo.env['res.partner.title']
        _title_id = RES_PARTNER_TITLE.search([('name', '=', _title)])
        if len(_title_id) != 0:
            _get_title_id = _title_id[0]
        else:
            _get_title_id = None

        return _get_title_id

    def set_ir_sequence_number_next_actual(self,_code,_set):
        IR_SEQUENCE = self.odoo.env['ir.sequence']
        _sequence_id = IR_SEQUENCE.search([('code', '=', _code)])
        if len(_sequence_id) != 0:
            _ir_sequence = IR_SEQUENCE.browse(_sequence_id)
            _ir_sequence_data = {'number_next_actual': _set}
            _ir_sequence.write(_ir_sequence_data)
            _done = True
        else:
            _done = False

        return _done

    def set_stock_warehouse_orderpoint(self,_product_id):
        """
        Setzt den Meldebestand für ein Produkt
        :param _product_id: ID des Produktes
        :return:
        """
        STOCK_WAREHOUSE_ORDERPOINT = self.odoo.env['stock.warehouse.orderpoint']
        _stock_warehouse_orderpoint_id = STOCK_WAREHOUSE_ORDERPOINT.search([('product_id', '=', _product_id)])
        if len(_stock_warehouse_orderpoint_id) == 0:
            _orderpoint_data = {
                'product_id': _product_id,
                'product_min_qty': 0,
                'product_max_qty': 0,
                'qty_multiple': 1,
            }
            STOCK_WAREHOUSE_ORDERPOINT.create(_orderpoint_data)
            _done = True
        else:
            _done = False

        return _done

    def get_picture(self,_picturepath):
        """
        Bild von Pfad wird eingeladen und BASE64 codiert um in Odoo eingespielt zu werden.
        :param _picturepath: Pfad zum Bild inkl. Namen
        :return:
        """
        if os.path.exists(_picturepath):
            with open(_picturepath, "rb") as f:
                _img = f.read()
                _return = str(base64.b64encode(_img).decode("utf-8"))
        else:
            return None

        return _return

    def get_product_uom_id(self,_uom):
        """
        Ermittelt die ID der Mengeneinheit
        :param _uom: Mengeneinheit
        :return:
        """
        if self.odoo_version in [10,11,12]:
            PRODUCT_UOM = self.odoo.env['product.uom']
        else:
             PRODUCT_UOM = self.odoo.env['uom.uom']
        _uom_id = PRODUCT_UOM.search([('name', '=', _uom)])

        if len(_uom_id) != 0:
            _get_uom_id = _uom_id[0]
        else:
            _get_uom_id = 1 # Default: Stück

        return _get_uom_id


    def string_contains_numbers(self,source):
        """
        Kontrolle ob String eine Zahl beinhaltet
        :param source: String mit Infos
        :return: True -> String beinhaltet eine Zahl
        """
        return any(i.isdigit() for i in source)

    def extract_street_address_part(self,streetinfos):
        """
        Extrahiert Strasse und Hausnummer aus einem String und liefert beide Infos getrennt zurück
        :param streetinfos: Strasseninfos
        :return: Strasse und Hausnummer
        """
        street = streetinfos
        house_no = ""

        if len(streetinfos) > 0:
            street_parts = streetinfos.split(" ")
            if len(street_parts) == 2:
                street = street_parts[0]
                house_no = street_parts[1]
            elif len(street_parts) > 2:
                street = ""
                part_position = 1
                for part in street_parts:
                    if part_position == len(street_parts):
                        if string_contains_numbers(part):                   # beinhaltet die letzte Position wirklich eine Zahl
                            house_no = part                                 # ja, es ist typische Adresse -> Weiherstrasse 12
                        else:
                            street += part                                  # nein, es ist z.B. eine GB Adresse -> Flat 42A Ashburnham Mansions
                    else:
                        street += part + " "

                    part_position += 1

        street = street.strip()
        house_no = house_no.strip()
        return street, house_no


    def check_if_company_exists(self,company_name, zip, city):
        """
        Kontrolliert ob ein Unternehmen bereits in der Tabelle res_partner vorhanden ist
        :param company_name: Unternehmensname
        :param zip: PLZ
        :param city: Stadt
        :return: ID -> falls das Unternehemen in der Tabelle res_partner vorhanden ist
        """
        RES_PARTNER = self.odoo.env['res.partner']
        record = RES_PARTNER.search([('name', 'like', company_name),
                                    ('zip', '=', zip),
                                    ('city', '=', city),
                                    ('is_company', '=', 'true')])
        if record:
            return record[0]

        return None