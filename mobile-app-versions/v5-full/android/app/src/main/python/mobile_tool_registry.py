#!/usr/bin/env python3
"""
Tool Registry - Автоматическое обнаружение и каталогизация инструментов
Phase 4.2: Динамическое обнаружение всех Python инструментов
"""

import ast
import inspect
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re


class ToolCategory(str, Enum):
    """Категории инструментов"""
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    INDEXING = "indexing"
    SEARCH = "search"
    GRAPH = "graph"
    METADATA = "metadata"
    EXPORT = "export"
    VALIDATION = "validation"
    STATISTICS = "statistics"
    OTHER = "other"


@dataclass
class ToolParameter:
    """Параметр инструмента"""
    name: str
    type: str
    required: bool = True
    default: Any = None
    description: str = ""
    choices: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class ToolMetadata:
    """Метаданные инструмента"""
    name: str
    display_name: str
    description: str
    category: ToolCategory
    file_path: Path

    # Параметры
    parameters: List[ToolParameter] = field(default_factory=list)

    # Выходные файлы
    output_files: List[str] = field(default_factory=list)
    output_formats: List[str] = field(default_factory=list)

    # Статус
    enabled: bool = True
    tested: bool = False

    # Метрики
    estimated_time: Optional[int] = None  # секунды
    complexity: Optional[str] = None  # low, medium, high

    # Зависимости
    dependencies: List[str] = field(default_factory=list)
    requires_input: bool = False

    # UI hints
    icon: str = "🔧"
    color: str = "#667eea"
    tags: List[str] = field(default_factory=list)


class ToolRegistry:
    """Реестр всех доступных инструментов"""

    def __init__(self, tools_dir: Path = Path("tools")):
        self.tools_dir = Path(tools_dir)
        self.tools: Dict[str, ToolMetadata] = {}
        self.categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}

    def scan_tools(self) -> int:
        """Сканировать директорию tools/ и найти все инструменты"""
        print(f"🔍 Сканирование {self.tools_dir}...")

        if not self.tools_dir.exists():
            print(f"❌ Директория {self.tools_dir} не найдена")
            return 0

        tool_files = sorted(self.tools_dir.glob("*.py"))

        for tool_file in tool_files:
            if tool_file.name.startswith("_"):
                continue

            try:
                metadata = self._analyze_tool(tool_file)
                self.tools[metadata.name] = metadata
                self.categories[metadata.category].append(metadata.name)
                print(f"  ✓ {metadata.name} ({metadata.category.value})")
            except Exception as e:
                print(f"  ⚠ {tool_file.name}: {e}")

        print(f"\n✅ Найдено {len(self.tools)} инструментов")
        return len(self.tools)

    def _analyze_tool(self, file_path: Path) -> ToolMetadata:
        """Анализировать Python файл и извлечь метаданные"""

        name = file_path.stem

        # Читать исходный код
        source = file_path.read_text()

        # Парсить AST
        tree = ast.parse(source)

        # Извлечь docstring модуля
        docstring = ast.get_docstring(tree) or ""

        # Определить категорию
        category = self._categorize_tool(name, docstring)

        # Извлечь параметры из main() или argparse
        parameters = self._extract_parameters(tree, source)

        # Определить выходные файлы
        output_files, output_formats = self._detect_outputs(name, source)

        # Определить UI hints
        icon, color = self._get_ui_hints(category)

        # Извлечь теги
        tags = self._extract_tags(name, docstring)

        # Создать метаданные
        metadata = ToolMetadata(
            name=name,
            display_name=self._make_display_name(name),
            description=self._extract_description(docstring),
            category=category,
            file_path=file_path,
            parameters=parameters,
            output_files=output_files,
            output_formats=output_formats,
            icon=icon,
            color=color,
            tags=tags,
            complexity=self._estimate_complexity(source),
            estimated_time=self._estimate_time(name, source)
        )

        return metadata

    def _categorize_tool(self, name: str, docstring: str) -> ToolCategory:
        """Автоматически определить категорию инструмента"""

        text = (name + " " + docstring).lower()

        if any(k in text for k in ["graph", "network", "link", "relation"]):
            return ToolCategory.GRAPH
        elif any(k in text for k in ["visualiz", "chart", "plot", "render"]):
            return ToolCategory.VISUALIZATION
        elif any(k in text for k in ["index", "catalog", "registry"]):
            return ToolCategory.INDEXING
        elif any(k in text for k in ["search", "find", "query", "filter"]):
            return ToolCategory.SEARCH
        elif any(k in text for k in ["analyze", "analysis", "calculate", "metric"]):
            return ToolCategory.ANALYSIS
        elif any(k in text for k in ["metadata", "tag", "attribute"]):
            return ToolCategory.METADATA
        elif any(k in text for k in ["export", "convert", "generate"]):
            return ToolCategory.EXPORT
        elif any(k in text for k in ["validate", "check", "verify"]):
            return ToolCategory.VALIDATION
        elif any(k in text for k in ["statistic", "stats", "summary"]):
            return ToolCategory.STATISTICS
        else:
            return ToolCategory.OTHER

    def _extract_parameters(self, tree: ast.AST, source: str) -> List[ToolParameter]:
        """Извлечь параметры из argparse или функции main()"""
        parameters = []

        # Поиск argparse.ArgumentParser
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Ищем add_argument вызовы
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == "add_argument"):

                    param = self._parse_argparse_argument(node)
                    if param:
                        parameters.append(param)

        # Если не нашли argparse, ищем параметры в main()
        if not parameters:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "main":
                    parameters = self._extract_function_params(node)
                    break

        return parameters

    def _parse_argparse_argument(self, node: ast.Call) -> Optional[ToolParameter]:
        """Парсить add_argument() вызов"""

        if not node.args:
            return None

        # Первый аргумент - имя параметра
        name_arg = node.args[0]
        if isinstance(name_arg, ast.Constant):
            name = name_arg.value.lstrip("-")
        else:
            return None

        # Извлечь ключевые аргументы
        kwargs = {kw.arg: kw.value for kw in node.keywords}

        # Type
        param_type = "str"
        if "type" in kwargs:
            type_node = kwargs["type"]
            if isinstance(type_node, ast.Name):
                param_type = type_node.id

        # Required
        required = True
        if "required" in kwargs:
            req_node = kwargs["required"]
            if isinstance(req_node, ast.Constant):
                required = req_node.value

        # Default
        default = None
        if "default" in kwargs:
            def_node = kwargs["default"]
            if isinstance(def_node, ast.Constant):
                default = def_node.value
                required = False

        # Help (description)
        description = ""
        if "help" in kwargs:
            help_node = kwargs["help"]
            if isinstance(help_node, ast.Constant):
                description = help_node.value

        # Choices
        choices = None
        if "choices" in kwargs:
            choices_node = kwargs["choices"]
            if isinstance(choices_node, ast.List):
                choices = [
                    elt.value for elt in choices_node.elts
                    if isinstance(elt, ast.Constant)
                ]

        return ToolParameter(
            name=name,
            type=param_type,
            required=required,
            default=default,
            description=description,
            choices=choices
        )

    def _extract_function_params(self, func_node: ast.FunctionDef) -> List[ToolParameter]:
        """Извлечь параметры из функции main()"""
        parameters = []

        for arg in func_node.args.args:
            if arg.arg == "self":
                continue

            param_type = "str"
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_type = arg.annotation.id

            parameters.append(ToolParameter(
                name=arg.arg,
                type=param_type,
                required=True,
                description=f"Parameter {arg.arg}"
            ))

        return parameters

    def _detect_outputs(self, name: str, source: str) -> tuple[List[str], List[str]]:
        """Определить выходные файлы инструмента"""

        output_files = []
        output_formats = set()

        # Паттерны для поиска выходных файлов
        patterns = [
            rf'{name}\.(html|json|csv|txt|md)',
            r'with open\([\'"]([^"\']+)["\']',
            r'\.to_(html|json|csv|excel|markdown)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, source, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]

                if match in ['html', 'json', 'csv', 'txt', 'md', 'excel', 'markdown']:
                    output_formats.add(match)
                elif '.' in match:
                    output_files.append(match)
                    ext = match.split('.')[-1]
                    output_formats.add(ext)

        # Если не нашли, предполагаем стандартные форматы
        if not output_files:
            output_files = [f"{name}.html", f"{name}.json"]
            output_formats = {'html', 'json'}

        return output_files, sorted(output_formats)

    def _extract_description(self, docstring: str) -> str:
        """Извлечь короткое описание из docstring"""
        if not docstring:
            return "No description available"

        # Первая строка или первое предложение
        lines = docstring.strip().split('\n')
        first_line = lines[0].strip()

        # Ограничить длину
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."

        return first_line

    def _make_display_name(self, name: str) -> str:
        """Создать читаемое имя"""
        # build_graph → Build Graph
        # calculate_pagerank → Calculate PageRank

        words = name.split('_')
        return ' '.join(word.capitalize() for word in words)

    def _get_ui_hints(self, category: ToolCategory) -> tuple[str, str]:
        """Получить иконку и цвет для категории"""

        hints = {
            ToolCategory.GRAPH: ("🕸️", "#e74c3c"),
            ToolCategory.VISUALIZATION: ("📊", "#3498db"),
            ToolCategory.INDEXING: ("📇", "#9b59b6"),
            ToolCategory.SEARCH: ("🔍", "#1abc9c"),
            ToolCategory.ANALYSIS: ("📈", "#f39c12"),
            ToolCategory.METADATA: ("🏷️", "#16a085"),
            ToolCategory.EXPORT: ("📤", "#27ae60"),
            ToolCategory.VALIDATION: ("✅", "#2ecc71"),
            ToolCategory.STATISTICS: ("📊", "#e67e22"),
            ToolCategory.OTHER: ("🔧", "#95a5a6"),
        }

        return hints.get(category, ("🔧", "#667eea"))

    def _extract_tags(self, name: str, docstring: str) -> List[str]:
        """Извлечь теги из имени и docstring"""
        tags = []

        # Из имени
        tags.extend(name.split('_'))

        # Ключевые слова из docstring
        keywords = re.findall(r'\b(graph|search|index|analyze|generate|build|calculate|validate|export|visualize)\w*\b',
                             docstring.lower())
        tags.extend(keywords)

        # Уникальные теги
        return list(set(tags))[:5]

    def _estimate_complexity(self, source: str) -> str:
        """Оценить сложность инструмента"""
        lines = len(source.split('\n'))

        if lines < 100:
            return "low"
        elif lines < 300:
            return "medium"
        else:
            return "high"

    def _estimate_time(self, name: str, source: str) -> int:
        """Оценить время выполнения (секунды)"""

        # Эвристики
        if "graph" in name or "network" in name:
            return 30
        elif "index" in name or "search" in name:
            return 20
        elif "analyze" in name or "calculate" in name:
            return 15
        else:
            return 10

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Получить метаданные инструмента по имени"""
        return self.tools.get(name)

    def get_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """Получить инструменты по категории"""
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]

    def search(self, query: str) -> List[ToolMetadata]:
        """Поиск инструментов по названию, описанию или тегам"""
        query = query.lower()
        results = []

        for tool in self.tools.values():
            if (query in tool.name.lower() or
                query in tool.display_name.lower() or
                query in tool.description.lower() or
                any(query in tag for tag in tool.tags)):
                results.append(tool)

        return results

    def to_json(self) -> Dict[str, Any]:
        """Экспортировать реестр в JSON"""
        return {
            "total_tools": len(self.tools),
            "categories": {
                cat.value: len(tools)
                for cat, tools in self.categories.items()
            },
            "tools": {
                name: {
                    "name": tool.name,
                    "display_name": tool.display_name,
                    "description": tool.description,
                    "category": tool.category.value,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "required": p.required,
                            "default": p.default,
                            "description": p.description,
                            "choices": p.choices
                        }
                        for p in tool.parameters
                    ],
                    "output_files": tool.output_files,
                    "output_formats": tool.output_formats,
                    "icon": tool.icon,
                    "color": tool.color,
                    "tags": tool.tags,
                    "complexity": tool.complexity,
                    "estimated_time": tool.estimated_time
                }
                for name, tool in self.tools.items()
            }
        }


# CLI для тестирования
if __name__ == "__main__":
    import json

    registry = ToolRegistry()
    count = registry.scan_tools()

    print("\n" + "="*60)
    print(f"📊 Статистика по категориям:")
    print("="*60)

    for category, tools in registry.categories.items():
        if tools:
            print(f"{category.value:20} {len(tools):3} инструментов")

    # Экспортировать в JSON
    output_file = Path("tool_registry.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(registry.to_json(), f, indent=2, ensure_ascii=False)

    print(f"\n✅ Реестр экспортирован в {output_file}")
