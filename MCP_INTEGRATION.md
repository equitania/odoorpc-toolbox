# OdooRPC Toolbox v0.3.0 - MCP Integration Guide

> **Language / Sprache**: [DE](#deutsche-version) | [EN](#english-version)

---

## Deutsche Version

Die Python-Bibliothek `odoorpc-toolbox` wurde erweitert und bietet jetzt MCP-kompatible Method-Discovery.

### Installation

```bash
pip install odoorpc-toolbox==0.3.0
```

### MCP-Discovery verwenden

Die Bibliothek kann ihre verfügbaren Methoden als JSON-Schema exportieren:

```python
from odoorpc_toolbox import get_available_methods, get_method_schema
import json

# Vollständiges Schema aller 19 verfügbaren Methoden abrufen
schema = get_available_methods()

# Schema für eine spezifische Methode abrufen
method_schema = get_method_schema('create_partner')
```

### Schema-Format (JSON-Schema kompatibel)

Das zurückgegebene Schema folgt diesem Format:

```json
{
  "schema_version": "1.0",
  "package": "odoorpc-toolbox",
  "version": "0.3.0",
  "description": "Helper functions for OdooRPC operations",
  "methods": [
    {
      "name": "method_name",
      "description": "Beschreibung der Methode",
      "parameters": {
        "type": "object",
        "properties": {
          "param_name": {
            "type": "string|integer|boolean|array|object",
            "description": "Parameter-Beschreibung",
            "nullable": true
          }
        },
        "required": ["required_param_names"]
      },
      "returns": {
        "type": "string|integer|boolean|array|object",
        "nullable": true,
        "description": "Return-Beschreibung"
      }
    }
  ]
}
```

### Verfügbare Methoden (19 Stück)

#### Partner-Operationen
| Methode | Beschreibung |
|---------|--------------|
| `get_res_partner_id(supplierno, customerno)` | Partner suchen |
| `create_partner(name, is_company, email, phone, ...)` | Partner erstellen |
| `get_res_partner_category_id(category_name)` | Kategorie abrufen/erstellen |
| `get_res_partner_title_id(title)` | Titel-ID abrufen |
| `check_if_company_exists(company_name, zip_code, city)` | Firma prüfen |

#### Standort-Operationen
| Methode | Beschreibung |
|---------|--------------|
| `get_country_id(country_name)` | Land-ID via Name |
| `get_country_id_by_code(country_code)` | Land-ID via ISO-Code (DE, US) |
| `get_state_id(country_id, state_name)` | Bundesland-ID abrufen |
| `extract_street_address_part(street_infos)` | Adresse parsen |

#### Produkt-Operationen
| Methode | Beschreibung |
|---------|--------------|
| `get_product_by_ref(default_code)` | Produkt via SKU |
| `get_product_template_by_ref(default_code)` | Produktvorlage via SKU |
| `get_product_uom_id(uom)` | Mengeneinheit-ID |

#### Generische Operationen
| Methode | Beschreibung |
|---------|--------------|
| `execute_method(model, method, record_ids, args, kwargs)` | Beliebige Odoo-Methode aufrufen |
| `search_read(model, domain, fields, limit, offset, order)` | Suchen und Lesen |

#### Sequenz-Operationen
| Methode | Beschreibung |
|---------|--------------|
| `get_ir_sequence_number_next_actual(code)` | Nächste Sequenznummer |
| `set_ir_sequence_number_next_actual(code, set_value)` | Sequenz setzen |

#### Lager-Operationen
| Methode | Beschreibung |
|---------|--------------|
| `set_stock_warehouse_orderpoint(product_id)` | Bestellpunkt setzen |

#### Utility-Operationen
| Methode | Beschreibung |
|---------|--------------|
| `get_picture(picture_path)` | Bild als BASE64 laden |
| `string_contains_numbers(source)` | Prüfen ob String Zahlen enthält |

### Exception-Handling

```python
from odoorpc_toolbox import (
    EqOdooConnection,
    OdooConnectionError,  # Basis-Exception
    OdooConfigError,      # YAML/Konfigurationsfehler
    OdooAuthError,        # Login-Fehler
)

try:
    conn = EqOdooConnection('config.yaml')
except OdooConfigError as e:
    print(f"Konfigurationsfehler: {e}")
except OdooAuthError as e:
    print(f"Authentifizierungsfehler: {e}")
except OdooConnectionError as e:
    print(f"Verbindungsfehler: {e}")
```

### Verwendungsbeispiel

```python
from odoorpc_toolbox import EqOdooConnection

# Verbindung herstellen
conn = EqOdooConnection('odoo_config.yaml')

# Partner erstellen
partner_id = conn.create_partner(
    name="Musterfirma GmbH",
    is_company=True,
    email="info@musterfirma.de",
    city="München",
    country_id=conn.get_country_id_by_code("DE")
)

# Generische Suche
partners = conn.search_read(
    model='res.partner',
    domain=[('is_company', '=', True)],
    fields=['name', 'email', 'city'],
    limit=10
)
```

---

## English Version

The Python library `odoorpc-toolbox` has been extended and now offers MCP-compatible method discovery.

### Installation

```bash
pip install odoorpc-toolbox==0.3.0
```

### Using MCP Discovery

The library can export its available methods as JSON schema:

```python
from odoorpc_toolbox import get_available_methods, get_method_schema
import json

# Get complete schema of all 19 available methods
schema = get_available_methods()

# Get schema for a specific method
method_schema = get_method_schema('create_partner')
```

### Schema Format (JSON Schema compatible)

The returned schema follows this format:

```json
{
  "schema_version": "1.0",
  "package": "odoorpc-toolbox",
  "version": "0.3.0",
  "description": "Helper functions for OdooRPC operations",
  "methods": [
    {
      "name": "method_name",
      "description": "Method description",
      "parameters": {
        "type": "object",
        "properties": {
          "param_name": {
            "type": "string|integer|boolean|array|object",
            "description": "Parameter description",
            "nullable": true
          }
        },
        "required": ["required_param_names"]
      },
      "returns": {
        "type": "string|integer|boolean|array|object",
        "nullable": true,
        "description": "Return description"
      }
    }
  ]
}
```

### Available Methods (19 total)

#### Partner Operations
| Method | Description |
|--------|-------------|
| `get_res_partner_id(supplierno, customerno)` | Search for partners |
| `create_partner(name, is_company, email, phone, ...)` | Create partner |
| `get_res_partner_category_id(category_name)` | Get or create category |
| `get_res_partner_title_id(title)` | Get title ID |
| `check_if_company_exists(company_name, zip_code, city)` | Check if company exists |

#### Location Operations
| Method | Description |
|--------|-------------|
| `get_country_id(country_name)` | Country ID by name |
| `get_country_id_by_code(country_code)` | Country ID by ISO code (DE, US) |
| `get_state_id(country_id, state_name)` | State/province ID |
| `extract_street_address_part(street_infos)` | Parse address |

#### Product Operations
| Method | Description |
|--------|-------------|
| `get_product_by_ref(default_code)` | Product by SKU |
| `get_product_template_by_ref(default_code)` | Product template by SKU |
| `get_product_uom_id(uom)` | Unit of measure ID |

#### Generic Operations
| Method | Description |
|--------|-------------|
| `execute_method(model, method, record_ids, args, kwargs)` | Call any Odoo method |
| `search_read(model, domain, fields, limit, offset, order)` | Search and read |

#### Sequence Operations
| Method | Description |
|--------|-------------|
| `get_ir_sequence_number_next_actual(code)` | Next sequence number |
| `set_ir_sequence_number_next_actual(code, set_value)` | Set sequence |

#### Warehouse Operations
| Method | Description |
|--------|-------------|
| `set_stock_warehouse_orderpoint(product_id)` | Set reorder point |

#### Utility Operations
| Method | Description |
|--------|-------------|
| `get_picture(picture_path)` | Load image as BASE64 |
| `string_contains_numbers(source)` | Check if string contains numbers |

### Exception Handling

```python
from odoorpc_toolbox import (
    EqOdooConnection,
    OdooConnectionError,  # Base exception
    OdooConfigError,      # YAML/configuration errors
    OdooAuthError,        # Login errors
)

try:
    conn = EqOdooConnection('config.yaml')
except OdooConfigError as e:
    print(f"Configuration error: {e}")
except OdooAuthError as e:
    print(f"Authentication error: {e}")
except OdooConnectionError as e:
    print(f"Connection error: {e}")
```

### Usage Example

```python
from odoorpc_toolbox import EqOdooConnection

# Establish connection
conn = EqOdooConnection('odoo_config.yaml')

# Create partner
partner_id = conn.create_partner(
    name="Sample Company Inc",
    is_company=True,
    email="info@sample.com",
    city="New York",
    country_id=conn.get_country_id_by_code("US")
)

# Generic search
partners = conn.search_read(
    model='res.partner',
    domain=[('is_company', '=', True)],
    fields=['name', 'email', 'city'],
    limit=10
)
```

---

## YAML Configuration / YAML-Konfiguration

```yaml
Server:
  url: https://your.odoo.server.com
  port: 443
  user: admin
  password: your_password
  database: your_database
  protocol: jsonrpc+ssl
```
