# odoorpc-toolbox
====================================================================================    
This is a simple python library that extends the functionality of Odoo RPC and contains helper functions.

## Installation

### odoo-fast-report-mapper requires:

- Python (>= 3.6)
- OdooRPC (>= 0.8.0)
- PyYaml (>= 3.12)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install odoorpc-toolbox.

```bash
pip install odoorpc-toolbox
```

---

## Usage

You need to have a Yaml file with the connection parameters.

The library contains two packages:
- odoo_connection with OdooConnection That contains only the connection to the RPC with already setup Parameters.
- base_helper with EqOdooConnection That is an extension of the OdooConnection with useful functions.

## example

```
base_path = os.path.dirname(os.path.abspath(__file__))
helper = base_helper.EqOdooConnection(base_path + '/config.yaml')
odoo = helper.odoo
RES_PARTNER = odoo.env['res.partner']
```

## Options

This project is licensed under the terms of the **AGPLv3** license.