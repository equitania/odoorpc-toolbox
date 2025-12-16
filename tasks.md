# Tasks - OdooRPC Toolbox

> **Language / Sprache**: [DE](#deutsche-version) | [EN](#english-version)

---

## Deutsche Version

### Kritische Fehler

- [x] **`__init__.py` erstellen** - Package-Import funktioniert nicht ohne diese Datei ✅
- [x] **Boolean-Bug beheben** - `base_helper.py:247`: `'true'` (String) → `True` (Boolean) ✅
- [x] **`sys.exit(1)` entfernen** - Library wirft jetzt `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅

### Code-Qualität

- [x] **Unbenutzte Variable entfernen** - `odoo_connection.py:85`: `ssl = True` wurde entfernt ✅
- [x] **Return-Typen vereinheitlichen** - `get_res_partner_category_id()` gibt jetzt immer `int` zurück ✅
- [x] **Type Hints vervollständigen** - `tuple` → `Tuple[str, str]` für `extract_street_address_part()` ✅
- [x] **Logging-Konfiguration überarbeiten** - `basicConfig()` entfernt, nur `getLogger(__name__)` ✅

### Neue Funktionen

- [x] **`get_country_id(name)`** - Land-ID anhand des Namens abrufen ✅
- [x] **`get_country_id_by_code(code)`** - Land-ID anhand ISO-Code abrufen ✅
- [x] **`create_partner(data)`** - Partner erstellen mit Validierung ✅
- [x] **`get_product_by_ref(ref)`** - Produkt via interne Referenz suchen ✅
- [x] **`get_product_template_by_ref(ref)`** - Produktvorlage via Referenz suchen ✅
- [x] **`execute_method(model, method, args)`** - Generischer RPC-Methodenaufruf ✅
- [x] **`search_read(model, domain, fields)`** - Suchen und Lesen kombiniert ✅
- [x] **Custom Exception-Klassen** - `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅
- [x] **MCP-Discovery** - `get_available_methods()`, `get_method_schema()` für MCP-Server ✅

### Dokumentation & Tests

- [x] **Unit-Tests erstellen** - 44 pytest-Tests ✅
- [x] **Docstrings überprüfen** - Alle Methoden vollständig dokumentiert ✅
- [x] **Beispiel-Skripte hinzufügen** - 5 Beispiele in `examples/` ✅

---

## English Version

### Critical Bugs

- [x] **Create `__init__.py`** - Package import doesn't work without this file ✅
- [x] **Fix Boolean bug** - `base_helper.py:247`: `'true'` (string) → `True` (boolean) ✅
- [x] **Remove `sys.exit(1)`** - Library now raises `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅

### Code Quality

- [x] **Remove unused variable** - `odoo_connection.py:85`: `ssl = True` removed ✅
- [x] **Unify return types** - `get_res_partner_category_id()` now always returns `int` ✅
- [x] **Complete type hints** - `tuple` → `Tuple[str, str]` for `extract_street_address_part()` ✅
- [x] **Revise logging configuration** - `basicConfig()` removed, only `getLogger(__name__)` ✅

### New Features

- [x] **`get_country_id(name)`** - Get country ID by name ✅
- [x] **`get_country_id_by_code(code)`** - Get country ID by ISO code ✅
- [x] **`create_partner(data)`** - Create partner with validation ✅
- [x] **`get_product_by_ref(ref)`** - Search product by internal reference ✅
- [x] **`get_product_template_by_ref(ref)`** - Search product template by reference ✅
- [x] **`execute_method(model, method, args)`** - Generic RPC method call ✅
- [x] **`search_read(model, domain, fields)`** - Combined search and read ✅
- [x] **Custom exception classes** - `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅
- [x] **MCP Discovery** - `get_available_methods()`, `get_method_schema()` for MCP servers ✅

### Documentation & Tests

- [x] **Create unit tests** - 44 pytest tests ✅
- [x] **Review docstrings** - All methods fully documented ✅
- [x] **Add example scripts** - 5 examples in `examples/` ✅

---

## Priority / Priorität

| Priority | Task | File | Status |
|----------|------|------|--------|
| 🔴 High | Create `__init__.py` | `odoorpc_toolbox/__init__.py` | ✅ Done |
| 🔴 High | Fix Boolean bug | `base_helper.py:247` | ✅ Done |
| 🔴 High | Replace `sys.exit(1)` | `odoo_connection.py` | ✅ Done |
| 🟡 Medium | Fix return types | `base_helper.py` | ✅ Done |
| 🟡 Medium | Remove dead code | `odoo_connection.py:85` | ✅ Done |
| 🟢 Low | Add new helper methods | `base_helper.py` | ✅ Done (7 new methods) |
| 🟢 Low | Create unit tests | `tests/` | ✅ Done (44 tests) |
| 🟢 Low | MCP Discovery | `introspection.py` | ✅ Done |
