"""Guard: every tool and argument a ``next_commands`` hint names must exist.

Own tools are checked against the live input schemas; sibling GeneFoundry tools carry
their router-namespaced name and are checked against a PINNED parameter set taken from
the sibling repo's signature (update the pin if the sibling renames).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import mitomap_link

_CROSS_SERVER: dict[str, set[str]] = {
    "gnomad_get_mitochondrial_variant": {"variant_id", "dataset"},
}


def _refs(obj: Any) -> list[tuple[str, set[str]]]:
    out: list[tuple[str, set[str]]] = []
    if isinstance(obj, dict):
        if isinstance(obj.get("tool"), str) and isinstance(obj.get("arguments"), dict):
            out.append((obj["tool"], set(obj["arguments"])))
        for value in obj.values():
            out += _refs(value)
    elif isinstance(obj, list):
        for item in obj:
            out += _refs(item)
    return out


def _source_refs() -> list[tuple[str, set[str]]]:
    """Literal ``cmd("tool", **kwargs)`` templates anywhere in the package."""
    out: list[tuple[str, set[str]]] = []
    for path in Path(mitomap_link.__file__).parent.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "cmd"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                out.append((node.args[0].value, {k.arg for k in node.keywords if k.arg}))
    return out


async def _assert_resolve(facade: Any, refs: list[tuple[str, set[str]]]) -> None:
    own = {t.name: set(t.parameters.get("properties", {})) for t in await facade.list_tools()}
    assert refs, "no hints collected: the walk is broken"
    for tool, args in refs:
        known = own.get(tool, _CROSS_SERVER.get(tool))
        assert known is not None, f"hint names unknown tool {tool!r}"
        assert args <= known, f"{tool}: unknown argument(s) {sorted(args - known)}"


async def test_source_hint_templates_resolve(facade: Any) -> None:
    await _assert_resolve(facade, _source_refs())


async def test_emitted_hints_resolve(facade: Any, structured: Any) -> None:
    calls = [
        ("get_variant", {"variant": "m.3243A>G"}),
        ("get_variant", {"variant": "m.3243A>T"}),
        ("search_variants", {"locus": "MT-TL1"}),
        ("search_variants", {"disease_query": "no such disease"}),
        ("get_diagnostics", {}),
        ("get_variant", {"variant": "not-a-variant"}),
    ]
    refs: list[tuple[str, set[str]]] = []
    for name, args in calls:
        refs += _refs(structured(await facade.call_tool(name, args)))
    await _assert_resolve(facade, refs)
