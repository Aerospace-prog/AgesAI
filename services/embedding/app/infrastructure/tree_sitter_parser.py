"""Tree-sitter based code parser for extracting AST nodes.

Extracts functions, classes, methods, and other semantic units from source code
using tree-sitter grammars. Designed to be language-agnostic with per-language
node type mappings.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Language-Specific Node Types ──
# Maps tree-sitter node types to our semantic categories for each language.

LANGUAGE_NODE_TYPES: dict[str, dict[str, str]] = {
    "python": {
        "function_definition": "function",
        "class_definition": "class",
    },
    "javascript": {
        "function_declaration": "function",
        "arrow_function": "function",
        "class_declaration": "class",
        "method_definition": "method",
    },
    "typescript": {
        "function_declaration": "function",
        "arrow_function": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "interface_declaration": "interface",
    },
    "tsx": {
        "function_declaration": "function",
        "arrow_function": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "interface_declaration": "interface",
    },
    "go": {
        "function_declaration": "function",
        "method_declaration": "method",
        "type_declaration": "struct",
    },
    "rust": {
        "function_item": "function",
        "impl_item": "class",
        "struct_item": "struct",
        "enum_item": "enum",
        "trait_item": "interface",
    },
    "java": {
        "method_declaration": "method",
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
    },
}


class TreeSitterParser:
    """Parses source code into AST nodes using tree-sitter.

    Falls back to a line-based splitter for unsupported languages.
    """

    def __init__(self) -> None:
        self._parsers: dict[str, Any] = {}
        self._languages: dict[str, Any] = {}

    async def parse(self, content: str, language: str) -> list[dict]:
        """Parse source code and return a list of semantic AST nodes.

        Args:
            content: The raw source code string.
            language: The programming language identifier.

        Returns:
            List of node dictionaries with keys:
                type, name, content, start_line, end_line, signature, parent_name.
        """
        try:
            parser = self._get_parser(language)
            if parser is None:
                # Fallback for unsupported languages: treat entire file as one block
                return self._fallback_parse(content, language)

            tree = parser.parse(content.encode("utf-8"))
            node_types = LANGUAGE_NODE_TYPES.get(language, {})

            nodes = self._extract_nodes(tree.root_node, content, node_types, language)

            if not nodes:
                # If no semantic nodes found, fall back to module-level block
                return self._fallback_parse(content, language)

            return nodes

        except Exception as e:
            logger.warning("Tree-sitter parse failed for %s: %s", language, str(e))
            return self._fallback_parse(content, language)

    def _get_parser(self, language: str) -> Any | None:
        """Get or create a tree-sitter parser for the given language."""
        if language in self._parsers:
            return self._parsers[language]

        try:
            import tree_sitter
            from tree_sitter import Language, Parser

            # tree-sitter 0.23+ uses built-in language loading
            ts_language = Language(self._get_language_lib(language))
            parser = Parser(ts_language)
            self._parsers[language] = parser
            return parser
        except Exception:
            self._parsers[language] = None
            return None

    def _get_language_lib(self, language: str) -> str:
        """Get the tree-sitter language library path.

        Note: In production, tree-sitter language packages are installed
        as Python packages (e.g., tree-sitter-python). This method handles
        the loading indirection.
        """
        lang_package_map = {
            "python": "tree_sitter_python",
            "javascript": "tree_sitter_javascript",
            "typescript": "tree_sitter_typescript",
            "tsx": "tree_sitter_typescript",
            "go": "tree_sitter_go",
            "rust": "tree_sitter_rust",
            "java": "tree_sitter_java",
        }

        pkg_name = lang_package_map.get(language)
        if not pkg_name:
            raise ValueError(f"No tree-sitter grammar for language: {language}")

        import importlib
        mod = importlib.import_module(pkg_name)

        # tree-sitter language packages export a language() function
        if hasattr(mod, "language"):
            return mod.language()

        raise ValueError(f"Language package {pkg_name} has no language() function")

    def _extract_nodes(
        self,
        root_node: Any,
        content: str,
        node_types: dict[str, str],
        language: str,
        parent_name: str | None = None,
    ) -> list[dict]:
        """Recursively extract semantic nodes from the tree-sitter AST."""
        nodes: list[dict] = []
        lines = content.split("\n")

        for child in root_node.children:
            if child.type in node_types:
                semantic_type = node_types[child.type]
                name = self._extract_name(child, language)
                signature = self._extract_signature(child, lines)
                start_line = child.start_point[0] + 1  # 1-indexed
                end_line = child.end_point[0] + 1
                node_content = "\n".join(lines[start_line - 1 : end_line])

                node_dict = {
                    "type": semantic_type,
                    "name": name,
                    "content": node_content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "signature": signature,
                    "parent_name": parent_name,
                }
                nodes.append(node_dict)

                # Recurse into classes to find methods
                if semantic_type in ("class", "struct", "impl"):
                    child_nodes = self._extract_nodes(
                        child, content, node_types, language, parent_name=name
                    )
                    nodes.extend(child_nodes)
            else:
                # Continue recursion into other node types
                child_nodes = self._extract_nodes(
                    child, content, node_types, language, parent_name=parent_name
                )
                nodes.extend(child_nodes)

        return nodes

    def _extract_name(self, node: Any, language: str) -> str:
        """Extract the name identifier from an AST node."""
        for child in node.children:
            if child.type in ("identifier", "property_identifier", "type_identifier"):
                return child.text.decode("utf-8") if isinstance(child.text, bytes) else child.text
        return "anonymous"

    def _extract_signature(self, node: Any, lines: list[str]) -> str | None:
        """Extract the first line as the function/class signature."""
        start = node.start_point[0]
        if start < len(lines):
            return lines[start].strip()
        return None

    def _fallback_parse(self, content: str, language: str) -> list[dict]:
        """Fallback parser for unsupported languages: returns the whole file as a module block."""
        lines = content.split("\n")
        if len(lines) < 3:
            return []

        return [{
            "type": "module",
            "name": "module",
            "content": content,
            "start_line": 1,
            "end_line": len(lines),
            "signature": lines[0].strip() if lines else None,
            "parent_name": None,
        }]
