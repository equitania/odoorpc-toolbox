"""Environment class for managing Odoo records.

Wraps data like user ID, context, database name, and provides
access to data model proxies via a registry.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Any

from odoorpc_toolbox import fields as fields_module
from odoorpc_toolbox.model import Model
from odoorpc_toolbox.tools import v

if TYPE_CHECKING:
    from odoorpc_toolbox.odoo import ODOO

FIELDS_RESERVED = ["id", "ids", "__odoo__", "__osv__", "__data__", "env"]


class Environment:
    """An environment wraps data like user ID, context and database name.

    It provides access to data model proxies through the registry.

    Example:
        >>> odoo.env
        Environment(db='mydb', uid=2, context={'lang': 'en_US', ...})
        >>> Partner = odoo.env['res.partner']
    """

    def __init__(
        self,
        odoo: ODOO,
        db: str,
        uid: int,
        context: dict[str, Any],
    ) -> None:
        self._odoo = odoo
        self._db = db
        self._uid = uid
        self._context = context
        self._registry: dict[str, type[Model]] = {}
        self._dirty: weakref.WeakSet = weakref.WeakSet()

    def __repr__(self) -> str:
        return f"Environment(db={self._db!r}, uid={self._uid}, context={self._context})"

    @property
    def dirty(self) -> weakref.WeakSet:
        """Records having local changes. Internal use only."""
        return self._dirty

    @property
    def context(self) -> dict[str, Any]:
        """The context of the connected user."""
        return self._context

    @property
    def db(self) -> str:
        """The database currently used."""
        return self._db

    def commit(self) -> None:
        """Commit dirty records to the server.

        Automatically called when auto_commit is True (default).
        Set auto_commit to False for better performance by batching writes.
        """
        for record in set(self.dirty):
            values = {}
            for field in record._values_to_write:
                if record.id in record._values_to_write[field]:
                    value = record._values_to_write[field].pop(record.id)
                    values[field] = value
                    record.__class__.__dict__[field].store(record, value)
            record.write(values)
            self.dirty.remove(record)

    def batch_commit(self) -> None:
        """Commit dirty records grouped by model for fewer RPC calls.

        Groups all dirty records by their model name and commits each
        record's accumulated changes in a single write() call per record.
        This is more efficient than commit() when many records of the same
        model have been modified.
        """
        grouped: dict[str, list] = {}
        for record in set(self.dirty):
            model_name = record._name
            if model_name not in grouped:
                grouped[model_name] = []
            grouped[model_name].append(record)

        for records in grouped.values():
            for record in records:
                values = {}
                for field in record._values_to_write:
                    if record.id in record._values_to_write[field]:
                        value = record._values_to_write[field].pop(record.id)
                        values[field] = value
                        record.__class__.__dict__[field].store(record, value)
                if values:
                    record.write(values)
                self.dirty.discard(record)

    def invalidate(self) -> None:
        """Invalidate the cache of records."""
        self.dirty.clear()

    @property
    def lang(self) -> str | bool:
        """Return the current language code."""
        return self.context.get("lang", False)

    def ref(self, xml_id: str) -> Model:
        """Return the record corresponding to the given xml_id (external ID).

        Args:
            xml_id: The external ID (e.g., 'base.lang_en').

        Returns:
            A Model instance (recordset).

        Raises:
            RPCError: If no record is found.
        """
        if v(self._odoo.version)[0] < 15:
            self._odoo.execute("ir.model.data", "xmlid_to_res_model_res_id", xml_id, True)
        module, name = xml_id.split(".", 1)
        model, id_ = self._odoo.execute("ir.model.data", "check_object_reference", module, name, True)
        return self[model].browse(id_)

    @property
    def uid(self) -> int:
        """The user ID currently logged."""
        return self._uid

    @property
    def user(self) -> Model:
        """Return the current user as a record."""
        return self["res.users"].browse(self.uid)

    @property
    def registry(self) -> dict[str, type[Model]]:
        """The data model registry mapping model names to their proxies."""
        return self._registry

    def __getitem__(self, model: str) -> type[Model]:
        """Return the model class corresponding to model name.

        Example:
            >>> Partner = odoo.env['res.partner']
        """
        if model not in self.registry:
            self.registry[model] = self._create_model_class(model)
        return self.registry[model]

    def __call__(self, context: dict[str, Any] | None = None) -> Environment:
        """Return an environment based on self with a different user context."""
        context = self.context if context is None else context
        env = Environment(self._odoo, self._db, self._uid, context)
        env._dirty = self._dirty
        env._registry = self._registry
        return env

    def __contains__(self, model: str) -> bool:
        """Check if the given model exists on the server."""
        model_exists = self._odoo.execute("ir.model", "search", [("model", "=", model)])
        return bool(model_exists)

    def _create_model_class(self, model: str) -> type[Model]:
        """Generate the model proxy class dynamically."""
        cls_name = model.replace(".", "_")
        attrs: dict[str, Any] = {
            "_env": self,
            "_odoo": self._odoo,
            "_name": model,
            "_columns": {},
        }
        fields_get = self._odoo.execute(model, "fields_get")
        for field_name, field_data in fields_get.items():
            if field_name not in FIELDS_RESERVED:
                Field = fields_module.generate_field(field_name, field_data)
                attrs["_columns"][field_name] = Field
                attrs[field_name] = Field
        return type(cls_name, (Model,), attrs)
