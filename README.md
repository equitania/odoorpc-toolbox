# OdooRPC Toolbox

> **Language / Sprache**: [DE](#deutsche-dokumentation) | [EN](#english-documentation)

---

## Deutsche Dokumentation

### Projektübersicht

Ein Python-Paket mit Hilfsfunktionen und Utilities für die Arbeit mit OdooRPC. Es vereinfacht häufige Odoo-Operationen wie Partner-Verwaltung, Bundesland/Länder-Abfragen, Dateioperationen und Sequenzverwaltung.

**Autor**: Equitania Software GmbH - Pforzheim - Germany
**Lizenz**: GNU Affero General Public License v3
**Python**: >= 3.8

### Funktionen

- Einfache Verbindungsverwaltung mit YAML-Konfiguration
- Hilfsfunktionen für häufige Odoo-Operationen:
  - Partner-Verwaltung (Suchen, Erstellen, Aktualisieren)
  - Bundesland- und Länderabfragen
  - Dateioperationen (Bilder, Anhänge)
  - Sequenzverwaltung
  - Produkt- und Lageroperationen

### Installation

```bash
pip install odoorpc-toolbox
```

### Konfiguration

Erstellen Sie eine YAML-Konfigurationsdatei (z.B. `odoo_config.yaml`):

```yaml
Server:
  url: your.odoo.server.com
  port: 8069
  protocol: jsonrpc
  database: your_database
  user: your_username
  password: your_password
```

### Verwendung

```python
from odoorpc_toolbox import EqOdooConnection

# Verbindung initialisieren
connection = EqOdooConnection('odoo_config.yaml')

# Hilfsfunktionen verwenden
state_id = connection.get_state_id(country_id=21, state_name="Bayern")
partner_id = connection.get_res_partner_id(customerno="KUND001")
```

### Partner-Operationen

```python
# Partner suchen
partner_id = connection.get_res_partner_id(supplierno="LIEF001", customerno="KUND001")

# Partner-Kategorien abrufen oder erstellen
category_id = connection.get_res_partner_category_id("Einzelhandel")

# Partner-Titel abrufen
title_id = connection.get_res_partner_title_id("Herr")
```

### Standort-Operationen

```python
# Bundesland-ID abrufen
state_id = connection.get_state_id(country_id=21, state_name="Bayern")

# Adresse parsen
strasse, hausnr = connection.extract_street_address_part("Hauptstraße 123")
```

### Datei-Operationen

```python
# Bilder laden und kodieren
image_data = connection.get_picture("/pfad/zum/bild.jpg")
```

### Abhängigkeiten

- Python >= 3.8
- OdooRPC >= 0.10.1
- PyYAML >= 5.4.1

---

## English Documentation

### Project Overview

A Python package providing helper functions and utilities for working with OdooRPC. It simplifies common Odoo operations like partner management, state/country lookups, file operations, and sequence management.

**Author**: Equitania Software GmbH - Pforzheim - Germany
**License**: GNU Affero General Public License v3
**Python**: >= 3.8

### Features

- Easy connection management with YAML configuration
- Helper functions for common Odoo operations:
  - Partner management (search, create, update)
  - State and country lookups
  - File operations (images, attachments)
  - Sequence management
  - Product and inventory operations

### Installation

```bash
pip install odoorpc-toolbox
```

### Configuration

Create a YAML configuration file (e.g., `odoo_config.yaml`):

```yaml
Server:
  url: your.odoo.server.com
  port: 8069
  protocol: jsonrpc
  database: your_database
  user: your_username
  password: your_password
```

### Usage

```python
from odoorpc_toolbox import EqOdooConnection

# Initialize connection
connection = EqOdooConnection('odoo_config.yaml')

# Use helper functions
state_id = connection.get_state_id(country_id=21, state_name="California")
partner_id = connection.get_res_partner_id(customerno="CUST001")
```

### Partner Operations

```python
# Search for partners
partner_id = connection.get_res_partner_id(supplierno="SUP001", customerno="CUST001")

# Get or create partner categories
category_id = connection.get_res_partner_category_id("Retail")

# Get partner titles
title_id = connection.get_res_partner_title_id("Mr.")
```

### Location Operations

```python
# Get state/province ID
state_id = connection.get_state_id(country_id=21, state_name="California")

# Parse address
street, house_no = connection.extract_street_address_part("123 Main Street")
```

### File Operations

```python
# Load and encode images
image_data = connection.get_picture("/path/to/image.jpg")
```

### Requirements

- Python >= 3.8
- OdooRPC >= 0.10.1
- PyYAML >= 5.4.1

---

## Contributing / Mitwirken

Contributions are welcome! Please feel free to submit a Pull Request.

Beiträge sind willkommen! Bitte zögern Sie nicht, einen Pull Request einzureichen.

## License / Lizenz

This project is licensed under the GNU Affero General Public License v3 - see the LICENSE.txt file for details.

Dieses Projekt ist unter der GNU Affero General Public License v3 lizenziert - siehe LICENSE.txt für Details.
