"""V0.5.1 baseline behavior simulation.

Simulates the old (pre-optimization) code paths to measure
the RPC call reduction achieved by v0.6.0 optimizations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from odoorpc_toolbox.base_helper import EqOdooConnection
    from odoorpc_toolbox.odoo import ODOO


def search_then_read(
    odoo: ODOO,
    model: str,
    domain: list,
    fields: list[str],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """V0.5.1 pattern: search() + read() = 2 RPC calls.

    The old approach required two separate RPC calls where v0.6.0
    uses a single native search_read.

    Args:
        odoo: Connected ODOO instance.
        model: Odoo model name.
        domain: Search domain.
        fields: Fields to read.
        limit: Maximum number of records.

    Returns:
        List of record dictionaries.
    """
    kwargs = {}
    if limit is not None:
        kwargs["limit"] = limit

    # RPC call 1: search
    ids = odoo.execute_kw(model, "search", [domain], kwargs)
    if not ids:
        return []

    # RPC call 2: read
    records = odoo.execute_kw(model, "read", [ids], {"fields": fields})
    return records or []


def get_sequence_old(odoo: ODOO, code: str) -> int | None:
    """V0.5.1 pattern: search + browse + field access = 2-3 RPC calls.

    The old approach used search + browse (which triggers a read) +
    field access instead of a single search_read.

    Args:
        odoo: Connected ODOO instance.
        code: Sequence code.

    Returns:
        The next actual number or None.
    """
    # RPC call 1: search
    seq_ids = odoo.execute_kw(
        "ir.sequence",
        "search",
        [[("code", "=", code)]],
    )
    if not seq_ids:
        return None

    # RPC call 2: read (simulating browse + field access)
    result = odoo.execute_kw(
        "ir.sequence",
        "read",
        [seq_ids[:1]],
        {"fields": ["number_next_actual"]},
    )
    if result:
        return result[0]["number_next_actual"]
    return None


def set_sequence_old(odoo: ODOO, code: str, set_value: int) -> bool:
    """V0.5.1 pattern: search + read + write = 3 RPC calls.

    The old approach used search + browse/read + write instead of
    the optimized search + write (2 calls).

    Args:
        odoo: Connected ODOO instance.
        code: Sequence code.
        set_value: New value for the next actual number.

    Returns:
        True if successful, False otherwise.
    """
    # RPC call 1: search
    seq_ids = odoo.execute_kw(
        "ir.sequence",
        "search",
        [[("code", "=", code)]],
    )
    if not seq_ids:
        return False

    # RPC call 2: read (simulating browse to verify existence)
    result = odoo.execute_kw(
        "ir.sequence",
        "read",
        [seq_ids[:1]],
        {"fields": ["id", "number_next_actual"]},
    )
    if not result:
        return False

    # RPC call 3: write
    odoo.execute_kw(
        "ir.sequence",
        "write",
        [seq_ids[:1], {"number_next_actual": set_value}],
    )
    return True


def get_state_id_uncached(connection: EqOdooConnection, country_id: int, state_name: str) -> int | None:
    """V0.5.1 pattern: always makes an RPC call (no cache).

    The old approach had no TTL cache, so every lookup resulted
    in a separate RPC call.

    Args:
        connection: EqOdooConnection instance.
        country_id: Country ID.
        state_name: State name.

    Returns:
        State ID or None.
    """
    result = connection.odoo.execute_kw(
        "res.country.state",
        "search",
        [[("name", "=", state_name), ("country_id", "=", country_id)]],
    )
    return result[0] if result else None


def write_fields_individually(odoo: ODOO, model: str, record_ids: list[int], field_values: dict) -> int:
    """V0.5.1 pattern: one write() per field = N RPC calls.

    The old approach had no batch_write, so each field assignment
    resulted in a separate write() call.

    Args:
        odoo: Connected ODOO instance.
        model: Odoo model name.
        record_ids: List of record IDs to update.
        field_values: Dictionary of field->value pairs.

    Returns:
        Number of write calls made.
    """
    count = 0
    for field_name, value in field_values.items():
        odoo.execute_kw(model, "write", [record_ids, {field_name: value}])
        count += 1
    return count


def legacy_execute_kw(odoo: ODOO, model: str, method: str, args: list, kwargs: dict | None = None) -> Any:
    """Legacy /jsonrpc execute_kw path, bypassing the JSON-2 routing.

    Used as the baseline for JSON-2 vs legacy comparisons on Odoo 19+,
    where ODOO.execute_kw() would otherwise route through /json/2/.
    Goes through ODOO.json() (the counting() choke-point) with the classic
    [db, uid, credential, model, method, args, kwargs] argument list.

    Args:
        odoo: Connected ODOO instance.
        model: Odoo model name.
        method: Method name.
        args: Positional arguments list.
        kwargs: Keyword arguments dictionary.

    Returns:
        The RPC result.
    """
    data = odoo.json(
        "/jsonrpc",
        {
            "service": "object",
            "method": "execute_kw",
            "args": [odoo.env.db, odoo.env.uid, odoo._rpc_credential, model, method, args, kwargs or {}],
        },
    )
    return data.get("result")
