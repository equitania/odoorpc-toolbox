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

- [ ] **`get_country_id(name)`** - Land-ID anhand des Namens abrufen
- [ ] **`create_partner(data)`** - Partner erstellen mit Validierung
- [ ] **`get_product_by_ref(ref)`** - Produkt via interne Referenz suchen
- [ ] **`execute_method(model, method, args)`** - Generischer RPC-Methodenaufruf
- [x] **Custom Exception-Klassen** - `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅

### Dokumentation & Tests

- [x] **Unit-Tests erstellen** - 27 pytest-Tests, 66% Coverage ✅
- [ ] **Docstrings überprüfen** - Alle Methoden dokumentiert?
- [ ] **Beispiel-Skripte hinzufügen** - Praktische Anwendungsbeispiele in `examples/`

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

- [ ] **`get_country_id(name)`** - Get country ID by name
- [ ] **`create_partner(data)`** - Create partner with validation
- [ ] **`get_product_by_ref(ref)`** - Search product by internal reference
- [ ] **`execute_method(model, method, args)`** - Generic RPC method call
- [x] **Custom exception classes** - `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅

### Documentation & Tests

- [x] **Create unit tests** - 27 pytest tests, 66% coverage ✅
- [ ] **Review docstrings** - Are all methods documented?
- [ ] **Add example scripts** - Practical usage examples in `examples/`

---

## Priority / Priorität

| Priority | Task | File | Status |
|----------|------|------|--------|
| 🔴 High | Create `__init__.py` | `odoorpc_toolbox/__init__.py` | ✅ Done |
| 🔴 High | Fix Boolean bug | `base_helper.py:247` | ✅ Done |
| 🔴 High | Replace `sys.exit(1)` | `odoo_connection.py` | ✅ Done |
| 🟡 Medium | Fix return types | `base_helper.py` | ✅ Done |
| 🟡 Medium | Remove dead code | `odoo_connection.py:85` | ✅ Done |
| 🟢 Low | Add new helper methods | `base_helper.py` | Pending |
| 🟢 Low | Create unit tests | `tests/` | ✅ Done (27 tests) |
