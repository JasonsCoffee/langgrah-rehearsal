"""Offline Unity/C# structural checks; editor execution arrives in Phase 6."""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal

from tree_sitter import Language, Node, Parser
import tree_sitter_c_sharp

from ...core.contracts import Interface
from ...core.evidence import CompileResult, CostProfile, TestResult, Violation


def _text(node: Node | None) -> str:
    return node.text.decode("utf-8", errors="replace") if node is not None and node.text is not None else ""


def _canonical(text: str) -> str:
    # Preserve whitespace inside literal default values while ignoring formatting.
    return "".join(re.findall(r'@"(?:[^"]|"")*"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\S', text))


def _walk(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


@dataclass(frozen=True)
class _Declaration:
    file: str
    symbol: str
    signatures: tuple[str, ...]


def _declarations(node: Node, file: str, scope: tuple[str, ...] = ()) -> Iterator[_Declaration]:
    current = scope
    if node.type in ("namespace_declaration", "class_declaration", "struct_declaration", "interface_declaration", "record_declaration"):
        name = _text(node.child_by_field_name("name"))
        current = scope + (name,)
        if node.type != "namespace_declaration":
            kind = node.type.removesuffix("_declaration")
            yield _Declaration(file, ".".join(current), (_canonical(f"{kind} {name}"),))
    if node.type in ("method_declaration", "constructor_declaration"):
        name = _text(node.child_by_field_name("name"))
        parameters = _text(node.child_by_field_name("parameters"))
        generics = next((_text(c) for c in node.named_children if c.type == "type_parameter_list"), "")
        signature = name + generics + parameters
        returns = _text(node.child_by_field_name("returns"))
        yield _Declaration(file, ".".join(scope + (name,)),
                           (_canonical(signature), _canonical(returns + " " + signature)))
        return  # Local methods/body text cannot satisfy a component interface.
    if node.type == "field_declaration":
        attributes = "".join(_text(c) for c in node.named_children if c.type == "attribute_list")
        for declaration in node.named_children:
            if declaration.type != "variable_declaration":
                continue
            type_name = _text(declaration.child_by_field_name("type"))
            for variable in declaration.named_children:
                if variable.type == "variable_declarator":
                    name = _text(variable.child_by_field_name("name"))
                    yield _Declaration(file, ".".join(scope + (name,)),
                                       (_canonical(attributes + type_name + " " + name),))
        return
    for child in node.named_children:
        if child.type == "file_scoped_namespace_declaration":
            current = scope + (_text(child.child_by_field_name("name")),)
        else:
            yield from _declarations(child, file, current)


class UnityAdapter:
    def __init__(self, *, case_sensitive: bool = False,
                 test_symbols: Mapping[str, tuple[str, str]] | None = None) -> None:
        self.case_sensitive = case_sensitive
        self._language = Language(tree_sitter_c_sharp.language())
        self._test_symbols = dict(test_symbols or {})

    def normalise_path(self, path: str) -> str:
        normalized = path.replace("\\", "/")
        return normalized if self.case_sensitive else normalized.casefold()

    def is_generated(self, path: str) -> bool:
        normalized = self.normalise_path(path)
        return ("obj" in normalized.split("/") or normalized.endswith((".meta", ".g.cs"))
                or "_generated." in normalized.rsplit("/", 1)[-1])

    def parse_check(self, files: Mapping[str, str | bytes]) -> tuple[Violation, ...]:
        violations: list[Violation] = []
        for file, source in files.items():
            if not self.normalise_path(file).endswith(".cs"):
                continue
            tree = Parser(self._language).parse(source.encode("utf-8") if isinstance(source, str) else source)
            for node in _walk(tree.root_node):
                if node.is_error or node.is_missing:
                    violations.append(Violation("syntax", file, "", f"Invalid {node.type} at line {node.start_point.row + 1}"))
        return tuple(violations)

    def check_interfaces(self, files: Mapping[str, str | bytes], interfaces: tuple[Interface, ...]) -> tuple[Violation, ...]:
        declarations: list[_Declaration] = []
        sources = [f for f in files if self.normalise_path(f).endswith(".cs")]
        for file in sources:
            source = files[file]
            tree = Parser(self._language).parse(source.encode("utf-8") if isinstance(source, str) else source)
            declarations.extend(_declarations(tree.root_node, file))
        violations: list[Violation] = []
        for interface in interfaces:
            matches = [d for d in declarations if d.symbol == interface.symbol or d.symbol.endswith("." + interface.symbol)]
            signature = _canonical(interface.signature)
            if any(signature in d.signatures for d in matches):
                continue
            related = interface.symbol.rsplit(".", 1)[0]
            context = next((d.file for d in declarations if d.symbol == related or d.symbol.endswith("." + related)), "")
            file = matches[0].file if matches else context or (sources[0] if len(sources) == 1 else "")
            violations.append(Violation("interface", file, interface.symbol,
                                        f"Missing or incompatible declaration: {interface.signature}"))
        return tuple(violations)

    def compile(self, project_root: Path) -> CompileResult:
        return CompileResult(False, operational_error="Compile transport is not configured")

    def run_tests(self, project_root: Path) -> TestResult:
        return TestResult((), (), (), (), operational_error="Test transport is not configured")

    def resolve_test_symbol(self, test_id: str) -> tuple[str, str]:
        try:
            return self._test_symbols[test_id]
        except KeyError as exc:
            raise ValueError(f"Undiscovered test symbol: {test_id}") from exc

    def lock_scope(self, project_root: Path) -> Literal["project"]:
        return "project"

    def cost_profile(self) -> CostProfile:
        return CostProfile(10.0, 90.0)
