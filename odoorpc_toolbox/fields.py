"""Field type descriptors for Odoo model fields.

Each field type is a Python descriptor which defines getter/setter methods
for its related attribute on Model instances.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

from __future__ import annotations

import datetime
from typing import Any


def is_int(value: Any) -> bool:
    """Return True if value is an integer (not a boolean)."""
    if isinstance(value, bool):
        return False
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def is_string(value: Any) -> bool:
    """Return True if value is a string."""
    return isinstance(value, str)


def odoo_tuple_in(iterable: list) -> bool:
    """Return True if iterable contains an Odoo special tuple like (6, 0, IDS).

    Examples:
        >>> odoo_tuple_in([0, 1, 2])
        False
        >>> odoo_tuple_in([(6, 0, [42])])
        True
        >>> odoo_tuple_in([[1, 42]])
        True
    """
    if not iterable:
        return False

    def is_odoo_tuple(elt) -> bool:
        try:
            return elt[:1][0] in [1, 2, 3, 4, 5] or elt[:2] in [
                (6, 0),
                [6, 0],
                (0, 0),
                [0, 0],
            ]
        except (TypeError, IndexError):
            return False

    return any(is_odoo_tuple(elt) for elt in iterable)


def tuples2ids(tuples: list, ids: list[int]) -> list[int]:
    """Update ids according to Odoo special tuples (3, 0, X), (4, 0, X), etc."""
    for value in tuples:
        if value[0] == 6 and value[2]:
            ids = value[2]
        elif value[0] == 5:
            ids[:] = []
        elif value[0] == 4 and value[1] and value[1] not in ids:
            ids.append(value[1])
        elif value[0] == 3 and value[1] and value[1] in ids:
            ids.remove(value[1])
    return ids


def records2ids(iterable) -> list[int]:
    """Replace records contained in iterable with their corresponding IDs."""
    from odoorpc_toolbox.model import Model

    def record2id(elt):
        if isinstance(elt, Model):
            return elt.id
        return elt

    return [record2id(elt) for elt in iterable]


class BaseField:
    """Base field class. All other fields inherit from this.

    Manages common metadata like name, type, string, size, required, readonly.
    """

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        self.name = name
        self.type = data.get("type", False)
        self.string = data.get("string", False)
        self.size = data.get("size", False)
        self.required = data.get("required", False)
        self.readonly = data.get("readonly", False)
        self.help = data.get("help", False)
        self.states = data.get("states", False)

    def __get__(self, instance, owner):
        pass

    def __set__(self, instance, value) -> None:
        """Mark the record as dirty in the environment when modified."""
        instance.env.dirty.add(instance)
        if instance._odoo.config.get("auto_commit"):
            instance.env.commit()

    def __str__(self) -> str:
        attrs = ["string", "relation", "required", "readonly", "size", "domain"]
        attrs_rep = []
        for attr in attrs:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if value:
                    if is_string(value):
                        attrs_rep.append(f"{attr}='{value}'")
                    else:
                        attrs_rep.append(f"{attr}={value}")
        return "{}({})".format(self.type, ", ".join(attrs_rep))

    def check_required(self, value: Any) -> bool:
        """Check the value if the field is required."""
        return bool(value)

    def check_value(self, value: Any) -> Any:
        """Check the validity of a value for the field."""
        if value and self.size:
            if not is_string(value):
                raise ValueError("Value supplied has to be a string")
            if len(value) > self.size:
                raise ValueError(f"Length of the '{self.name}' is limited to {self.size}")
        if self.required and not self.check_required(value):
            raise ValueError(f"'{self.name}' field is required")
        return value

    def store(self, record, value: Any) -> None:
        """Store the value in the record."""
        record._values[self.name][record.id] = value


class Binary(BaseField):
    """Equivalent of Odoo fields.Binary."""

    def __get__(self, instance, owner):
        value = instance._values[self.name][instance.id]
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        return value

    def __set__(self, instance, value) -> None:
        if value is None:
            value = False
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)


class Boolean(BaseField):
    """Equivalent of Odoo fields.Boolean."""

    def __get__(self, instance, owner):
        value = instance._values[self.name][instance.id]
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        return value

    def __set__(self, instance, value) -> None:
        value = bool(value)
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)


class Char(BaseField):
    """Equivalent of Odoo fields.Char."""

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id)
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        return value

    def __set__(self, instance, value) -> None:
        if value is None:
            value = False
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)


class Date(BaseField):
    """Equivalent of Odoo fields.Date."""

    pattern = "%Y-%m-%d"

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id) or False
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        try:
            res = datetime.datetime.strptime(value, self.pattern).date()
        except (ValueError, TypeError):
            res = value
        return res

    def __set__(self, instance, value) -> None:
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def check_value(self, value: Any) -> Any:
        super().check_value(value)
        if isinstance(value, datetime.date):
            value = value.strftime("%Y-%m-%d")
        elif is_string(value):
            datetime.datetime.strptime(value, self.pattern)
        elif isinstance(value, bool) or value is None:
            return value
        else:
            raise ValueError("Expecting a datetime.date object or string")
        return value


class Datetime(BaseField):
    """Equivalent of Odoo fields.Datetime."""

    pattern = "%Y-%m-%d %H:%M:%S"

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id)
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        try:
            res = datetime.datetime.strptime(value, self.pattern)
        except (ValueError, TypeError):
            res = value
        return res

    def __set__(self, instance, value) -> None:
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def check_value(self, value: Any) -> Any:
        super().check_value(value)
        if isinstance(value, datetime.datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        elif is_string(value):
            datetime.datetime.strptime(value, self.pattern)
        elif isinstance(value, bool):
            return value
        else:
            raise ValueError("Expecting a datetime.datetime object or string")
        return value


class Float(BaseField):
    """Equivalent of Odoo fields.Float."""

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id)
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        if value in [None, False]:
            value = 0.0
        return value

    def __set__(self, instance, value) -> None:
        if value is None:
            value = False
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def check_required(self, value: Any) -> bool:
        return super().check_required(value) or value == 0


class Integer(BaseField):
    """Equivalent of Odoo fields.Integer."""

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id)
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        if value in [None, False]:
            value = 0
        return value

    def __set__(self, instance, value) -> None:
        if value is None:
            value = False
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def check_required(self, value: Any) -> bool:
        return super().check_required(value) or value == 0


class Selection(BaseField):
    """Equivalent of Odoo fields.Selection."""

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        super().__init__(name, data)
        self.selection = data.get("selection", False)

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id, False)
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        return value

    def __set__(self, instance, value) -> None:
        if value is None:
            value = False
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def check_value(self, value: Any) -> Any:
        super().check_value(value)
        selection = [val[0] for val in self.selection]
        if value and value not in selection:
            raise ValueError(
                f"The value '{value}' supplied doesn't match with the possible "
                f"values '{selection}' for the '{self.name}' field"
            )
        return value


class Many2many(BaseField):
    """Equivalent of Odoo fields.Many2many."""

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        super().__init__(name, data)
        self.relation = data.get("relation", False)
        self.context = data.get("context", {})
        self.domain = data.get("domain", False)

    def __get__(self, instance, owner):
        """Return a recordset."""
        ids = None
        if instance._values[self.name].get(instance.id):
            ids = instance._values[self.name][instance.id][:]
        if ids is None:
            args = [[instance.id], [self.name]]
            kwargs = {"context": self.context, "load": "_classic_write"}
            orig_ids = instance._odoo.execute_kw(instance._name, "read", args, kwargs)[0][self.name]
            instance._values[self.name][instance.id] = orig_ids
            ids = orig_ids[:] if orig_ids else []
        if instance.id in instance._values_to_write[self.name]:
            values = instance._values_to_write[self.name][instance.id]
            ids = tuples2ids(values, ids or [])
        Relation = instance.env[self.relation]
        env = instance.env
        if self.context:
            context = instance.env.context.copy()
            context.update(self.context)
            env = instance.env(context=context)
        return Relation._browse(env, ids, from_record=(instance, self))

    def __set__(self, instance, value) -> None:
        from odoorpc_toolbox.model import IncrementalRecords

        value = self.check_value(value)
        if isinstance(value, IncrementalRecords):
            value = value.tuples
        else:
            if value and not odoo_tuple_in(value):
                value = [(6, 0, records2ids(value))]
            elif not value:
                value = [(5,)]
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def check_value(self, value: Any) -> Any:
        if value:
            from odoorpc_toolbox.model import IncrementalRecords, Model

            if not isinstance(value, (list, Model, IncrementalRecords)):
                raise ValueError("The value supplied has to be a list, a recordset or 'False'")
        return super().check_value(value)

    def store(self, record, value: Any) -> None:
        if record._values[self.name].get(record.id):
            tuples2ids(value, record._values[self.name][record.id])
        else:
            record._values[self.name][record.id] = tuples2ids(value, [])


class Many2one(BaseField):
    """Equivalent of Odoo fields.Many2one."""

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        super().__init__(name, data)
        self.relation = data.get("relation", False)
        self.context = data.get("context", {})
        self.domain = data.get("domain", False)

    def __get__(self, instance, owner):
        id_ = instance._values[self.name].get(instance.id)
        if instance.id in instance._values_to_write[self.name]:
            id_ = instance._values_to_write[self.name][instance.id]
        if id_ is None:
            args = [[instance.id], [self.name]]
            kwargs = {"context": self.context, "load": "_classic_write"}
            id_ = instance._odoo.execute_kw(instance._name, "read", args, kwargs)[0][self.name]
            instance._values[self.name][instance.id] = id_
        Relation = instance.env[self.relation]
        if id_:
            env = instance.env
            if self.context:
                context = instance.env.context.copy()
                context.update(self.context)
                env = instance.env(context=context)
            return Relation._browse(env, id_, from_record=(instance, self))
        return Relation.browse(False)

    def __set__(self, instance, value) -> None:
        from odoorpc_toolbox.model import Model

        if isinstance(value, Model):
            o_rel = value
        elif is_int(value):
            rel_obj = instance.env[self.relation]
            o_rel = rel_obj.browse(value)
        elif value in [None, False]:
            o_rel = False
        else:
            raise ValueError("Value supplied has to be an integer, a record object or 'None/False'.")
        o_rel = self.check_value(o_rel)
        instance._values_to_write[self.name][instance.id] = o_rel.id if o_rel else False
        super().__set__(instance, value)

    def check_value(self, value: Any) -> Any:
        super().check_value(value)
        if value and value._name != self.relation:
            raise ValueError(
                f"Instance of '{value._name}' supplied doesn't match with the "
                f"relation '{self.relation}' of the '{self.name}' field."
            )
        return value


class One2many(BaseField):
    """Equivalent of Odoo fields.One2many."""

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        super().__init__(name, data)
        self.relation = data.get("relation", False)
        self.context = data.get("context", {})
        self.domain = data.get("domain", False)

    def __get__(self, instance, owner):
        """Return a recordset."""
        ids = None
        if instance._values[self.name].get(instance.id):
            ids = instance._values[self.name][instance.id][:]
        if ids is None:
            args = [[instance.id], [self.name]]
            kwargs = {"context": self.context, "load": "_classic_write"}
            orig_ids = instance._odoo.execute_kw(instance._name, "read", args, kwargs)[0][self.name]
            instance._values[self.name][instance.id] = orig_ids
            ids = orig_ids[:] if orig_ids else []
        if instance.id in instance._values_to_write[self.name]:
            values = instance._values_to_write[self.name][instance.id]
            ids = tuples2ids(values, ids or [])
        Relation = instance.env[self.relation]
        env = instance.env
        if self.context:
            context = instance.env.context.copy()
            context.update(self.context)
            env = instance.env(context=context)
        return Relation._browse(env, ids, from_record=(instance, self))

    def __set__(self, instance, value) -> None:
        from odoorpc_toolbox.model import IncrementalRecords

        value = self.check_value(value)
        if isinstance(value, IncrementalRecords):
            value = value.tuples
        else:
            if value and not odoo_tuple_in(value):
                value = [(6, 0, records2ids(value))]
            elif not value:
                value = [(5,)]
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def check_value(self, value: Any) -> Any:
        if value:
            from odoorpc_toolbox.model import IncrementalRecords, Model

            if not isinstance(value, (list, Model, IncrementalRecords)):
                raise ValueError("The value supplied has to be a list, a recordset or 'False'")
        return super().check_value(value)

    def store(self, record, value: Any) -> None:
        if record._values[self.name].get(record.id):
            tuples2ids(value, record._values[self.name][record.id])
        else:
            record._values[self.name][record.id] = tuples2ids(value, [])


class Reference(BaseField):
    """Equivalent of Odoo fields.Reference."""

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        super().__init__(name, data)
        self.context = data.get("context", {})
        self.domain = data.get("domain", False)
        self.selection = data.get("selection", False)

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id) or False
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        if value is None:
            args = [[instance.id], [self.name]]
            kwargs = {"context": self.context, "load": "_classic_write"}
            value = instance._odoo.execute_kw(instance._name, "read", args, kwargs)[0][self.name]
            instance._values_to_write[self.name][instance.id] = value
        if value:
            parts = value.rpartition(",")
            relation, o_id = parts[0].strip(), parts[2].strip()
            o_id = int(o_id)
            if relation and o_id:
                Relation = instance.env[relation]
                env = instance.env
                if self.context:
                    context = instance.env.context.copy()
                    context.update(self.context)
                    env = instance.env(context=context)
                return Relation._browse(env, o_id, from_record=(instance, self))
        return False

    def __set__(self, instance, value) -> None:
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)

    def _check_relation(self, relation: str) -> str:
        selection = [val[0] for val in self.selection]
        if relation not in selection:
            raise ValueError(
                f"The value '{relation}' supplied doesn't match with the possible "
                f"values '{selection}' for the '{self.name}' field"
            )
        return relation

    def check_value(self, value: Any) -> Any:
        from odoorpc_toolbox.model import Model

        if isinstance(value, Model):
            relation = value.__class__.__osv__["name"]
            self._check_relation(relation)
            value = f"{relation},{value.id}"
            super().check_value(value)
        elif is_string(value):
            super().check_value(value)
            parts = value.rpartition(",")
            relation, o_id = parts[0].strip(), parts[2].strip()
            if not relation or not is_int(o_id):
                raise ValueError("String not well formatted, expecting '{relation},{id}' format")
            self._check_relation(relation)
        else:
            raise ValueError("Value supplied has to be a string or a browse_record object.")
        return value


class Text(BaseField):
    """Equivalent of Odoo fields.Text."""

    def __get__(self, instance, owner):
        value = instance._values[self.name].get(instance.id)
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        return value

    def __set__(self, instance, value) -> None:
        if value is None:
            value = False
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)


class Html(Text):
    """Equivalent of Odoo fields.Html."""

    pass


class Unknown(BaseField):
    """Fallback field for unsupported field types."""

    def __get__(self, instance, owner):
        value = instance._values[self.name][instance.id]
        if instance.id in instance._values_to_write[self.name]:
            value = instance._values_to_write[self.name][instance.id]
        return value

    def __set__(self, instance, value) -> None:
        value = self.check_value(value)
        instance._values_to_write[self.name][instance.id] = value
        super().__set__(instance, value)


TYPES_TO_FIELDS: dict[str, type[BaseField]] = {
    "binary": Binary,
    "boolean": Boolean,
    "char": Char,
    "date": Date,
    "datetime": Datetime,
    "float": Float,
    "html": Html,
    "integer": Integer,
    "many2many": Many2many,
    "many2one": Many2one,
    "one2many": One2many,
    "reference": Reference,
    "selection": Selection,
    "text": Text,
}


def generate_field(name: str, data: dict[str, Any]) -> BaseField:
    """Generate a well-typed field according to the data dictionary.

    The data dictionary is obtained via the 'fields_get' method of any model.
    """
    assert "type" in data
    field = TYPES_TO_FIELDS.get(data["type"], Unknown)(name, data)
    return field
