# Examples / Beispiele

> **Language / Sprache**: [DE](#deutsche-version) | [EN](#english-version)

---

## English Version

### Prerequisites

1. Install the package:
   ```bash
   pip install odoorpc-toolbox
   ```

2. Create a configuration file `odoo_config.yaml`:
   ```yaml
   Server:
     url: https://your.odoo.server.com
     port: 443
     user: admin
     password: your_password
     database: your_database
     protocol: jsonrpc+ssl
   ```

### Available Examples

| File | Description |
|------|-------------|
| `01_basic_connection.py` | Basic connection and error handling |
| `02_partner_operations.py` | Partner search, create, and management |
| `03_product_operations.py` | Product search, UoM, and inventory |
| `04_mcp_discovery.py` | MCP-compatible method discovery |
| `05_generic_operations.py` | Generic RPC operations |

### Running Examples

```bash
cd examples
python 01_basic_connection.py
python 02_partner_operations.py
python 03_product_operations.py
python 04_mcp_discovery.py
python 05_generic_operations.py
```

---

## Deutsche Version

### Voraussetzungen

1. Paket installieren:
   ```bash
   pip install odoorpc-toolbox
   ```

2. Konfigurationsdatei `odoo_config.yaml` erstellen:
   ```yaml
   Server:
     url: https://ihr.odoo.server.de
     port: 443
     user: admin
     password: ihr_passwort
     database: ihre_datenbank
     protocol: jsonrpc+ssl
   ```

### Verfügbare Beispiele

| Datei | Beschreibung |
|-------|--------------|
| `01_basic_connection.py` | Grundlegende Verbindung und Fehlerbehandlung |
| `02_partner_operations.py` | Partner suchen, erstellen und verwalten |
| `03_product_operations.py` | Produkte suchen, Mengeneinheiten, Lager |
| `04_mcp_discovery.py` | MCP-kompatible Methoden-Erkennung |
| `05_generic_operations.py` | Generische RPC-Operationen |

### Beispiele ausführen

```bash
cd examples
python 01_basic_connection.py
python 02_partner_operations.py
python 03_product_operations.py
python 04_mcp_discovery.py
python 05_generic_operations.py
```
