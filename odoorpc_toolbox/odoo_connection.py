# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoorpc
import yaml
import urllib
import sys

class OdooConnection:
    def __init__(self,eq_yaml_path):
        with open(eq_yaml_path, "r") as stream:
            data = yaml.safe_load(stream)
        connection_data = data['Server']
        self.odoo_address = connection_data.get('url','0.0.0.0')
        self.odoo_port = connection_data.get('port',8069)
        self.user = connection_data.get('user','admin')
        self.pw = connection_data.get('password','dbpassword')
        self.db = connection_data.get('database','dbname')
        self.protocol = connection_data.get('protocol','jsonrpc')
        self.odoo_version = 0
        try:
            # Build connection
            self.odoo = self.odoo_connect()
        except urllib.error.URLError as ex:
            print("ERROR: Please check your parameters and your connection" + " " + str(ex))
            sys.exit(0)


    def odoo_connect(self):
        """
            Prepare the connection to the server
            :return:
        """
        odoo_address = self.odoo_address
        protocol = self.protocol
        odoo_port = self.odoo_port
        if odoo_address.startswith('https'):
            ssl = True
            odoo_address = odoo_address.replace('https:', '')
            protocol = 'jsonrpc+ssl'
            if odoo_port <= 0:
                odoo_port = 443
        elif odoo_address.startswith('http:'):
            odoo_address = odoo_address.replace('http:', '')
            protocol = 'jsonrpc'

        while odoo_address and odoo_address.startswith('/'):
            odoo_address = odoo_address[1:]

        while odoo_address and odoo_address.endswith('/'):
            odoo_address = odoo_address[:-1]

        while odoo_address and odoo_address.endswith('\\'):
            odoo_address = odoo_address[:-1]

        odoo_con = odoorpc.ODOO(odoo_address, port=odoo_port, protocol=protocol)
        self.odoo_version = int(odoo_con.version.split(".")[0])
        odoo_con.login(self.db, self.user, self.pw)

        odoo_con.config['auto_commit'] = True  # No need for manual commits
        odoo_con.env.context['active_test'] = False  # Show inactive articles
        odoo_con.env.context['tracking_disable'] = True
        return odoo_con