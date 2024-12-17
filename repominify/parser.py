"""Parser for Repomix output files.

This module handles parsing of Repomix output files into structured data.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Set, Tuple, Optional, Dict, Any

from .logging import get_logger
from .types import FileEntry
from .exceptions import FileParseError

logger = get_logger(__name__)


class RepomixParser:
    """Parser for Repomix output files.

    This class handles parsing of Repomix output files and extracting code
    structure information.

    Attributes:
        stats: Runtime statistics tracking parsed files and content
    """

    stats: Dict[str, int]

    def __init__(self) -> None:
        """Initialize parser with statistics tracking.

        Examples::
            >>> parser = RepomixParser()
            >>> parser.stats["files_processed"]
            0
        """
        self.stats = {
            "files_processed": 0,
            "total_lines": 0,
            "total_size": 0,
            "parse_time_ms": 0,
        }

    def parse_file(self, file_path: str) -> List[FileEntry]:
        """Parse a Repomix file and extract code content.

        Args:
            file_path: Path to the Repomix output file

        Returns:
            List of FileEntry objects containing file paths and contents

        Raises:
            FileNotFoundError: If the input file doesn't exist
            FileParseError: If the file format is invalid or no entries found
            UnicodeDecodeError: If file encoding is not UTF-8

        Examples::
            >>> parser = RepomixParser()
            >>> entries = parser.parse_file("output.txt")
            >>> len(entries)
            3
        """
        logger.debug(f"Parsing Repomix file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Repomix output file not found: {file_path}"
            ) from e
        except UnicodeDecodeError as e:
            raise FileParseError(f"Invalid file encoding: {e}") from e

        file_entries: List[FileEntry] = []
        current_file: Optional[str] = None
        current_content: List[str] = []

        try:
            for line in content.split("\n"):
                if line.startswith("File: "):
                    if current_file:
                        entry = FileEntry(
                            path=current_file, content="\n".join(current_content)
                        )
                        file_entries.append(entry)
                        logger.debug(f"Parsed {entry}")

                        # Update stats
                        self.stats["files_processed"] += 1
                        self.stats["total_lines"] += entry.line_count
                        self.stats["total_size"] += entry.size

                    current_file = line.replace("File: ", "").strip()
                    current_content = []
                elif current_file and line != "================":
                    current_content.append(line)

            # Handle last file
            if current_file:
                entry = FileEntry(path=current_file, content="\n".join(current_content))
                file_entries.append(entry)
                logger.debug(f"Parsed {entry}")

                # Update stats
                self.stats["files_processed"] += 1
                self.stats["total_lines"] += entry.line_count
                self.stats["total_size"] += entry.size

        except Exception as e:
            raise FileParseError(f"Failed to parse Repomix file: {e}") from e

        if not file_entries:
            raise FileParseError("No valid file entries found in Repomix output")

        logger.info(f"Successfully parsed {len(file_entries)} files")
        return file_entries

    def analyze_imports(self, content: str) -> Set[str]:
        """Extract import statements from code.

        Args:
            content: Python source code content

        Returns:
            Set of imported module names

        Examples::
            >>> parser = RepomixParser()
            >>> imports = parser.analyze_imports("import os\\nfrom typing import List")
            >>> sorted(list(imports))
            ['os', 'typing.List']
        """
        imports: Set[str] = set()
        import_pattern = r"^(?:from\s+(\S+)\s+)?import\s+(.+)$"

        for line in content.split("\n"):
            line = line.strip()
            match = re.match(import_pattern, line)
            if match:
                from_module, imported = match.groups()
                if from_module:
                    imports.add(from_module)
                for item in imported.split(","):
                    item = item.strip().split()[0]  # Handle 'as' aliases
                    if from_module:
                        imports.add(f"{from_module}.{item}")
                    else:
                        imports.add(item)
        return imports

    def extract_classes_and_functions(
        self, content: str
    ) -> Tuple[List[str], List[str]]:
        """Extract class and function definitions from code.

        Args:
            content: Python source code content

        Returns:
            Tuple of (class names, function names)

        Examples::
            >>> parser = RepomixParser()
            >>> classes, funcs = parser.extract_classes_and_functions(
            ...     "class MyClass:\\n    def my_func():\\n        pass"
            ... )
            >>> classes
            ['MyClass']
            >>> funcs
            ['my_func']
        """
        classes: List[str] = []
        functions: List[str] = []

        class_pattern = r"^\s*class\s+([^\(:]+)"
        function_pattern = r"^\s*def\s+([^\(:]+)"

        for line in content.split("\n"):
            class_match = re.match(class_pattern, line)
            if class_match:
                classes.append(class_match[1].strip())
                continue

            func_match = re.match(function_pattern, line)
            if func_match:
                functions.append(func_match[1].strip())

        return classes, functions
