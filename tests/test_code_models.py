"""
Tests for Code Models.

This module contains tests for the code models.
"""

import unittest

from shared.models.code import (
    Position,
    Range,
    Symbol,
    SymbolKind,
    CodeAnalysisResult,
    CodeGenerationRequest,
    CodeGenerationResult
)


class TestCodeModels(unittest.TestCase):
    """Tests for the code models."""

    def test_position(self):
        """Test the Position model."""
        # Act
        position = Position(line=10, character=20)
        
        # Assert
        self.assertEqual(position.line, 10)
        self.assertEqual(position.character, 20)
        self.assertEqual(position.model_dump(), {"line": 10, "character": 20})

    def test_range(self):
        """Test the Range model."""
        # Arrange
        start = Position(line=10, character=20)
        end = Position(line=15, character=30)
        
        # Act
        range_obj = Range(start=start, end=end)
        
        # Assert
        self.assertEqual(range_obj.start.line, 10)
        self.assertEqual(range_obj.start.character, 20)
        self.assertEqual(range_obj.end.line, 15)
        self.assertEqual(range_obj.end.character, 30)
        self.assertEqual(range_obj.model_dump(), {
            "start": {"line": 10, "character": 20},
            "end": {"line": 15, "character": 30}
        })

    def test_symbol(self):
        """Test the Symbol model."""
        # Arrange
        start = Position(line=10, character=20)
        end = Position(line=15, character=30)
        range_obj = Range(start=start, end=end)
        
        # Act
        symbol = Symbol(
            name="test_function",
            kind=SymbolKind.FUNCTION,
            range=range_obj,
            selection_range=range_obj,
            detail="A test function"
        )
        
        # Assert
        self.assertEqual(symbol.name, "test_function")
        self.assertEqual(symbol.kind, SymbolKind.FUNCTION)
        self.assertEqual(symbol.range.start.line, 10)
        self.assertEqual(symbol.range.end.line, 15)
        self.assertEqual(symbol.detail, "A test function")
        self.assertIsNone(symbol.children)

    def test_symbol_with_children(self):
        """Test the Symbol model with children."""
        # Arrange
        parent_range = Range(
            start=Position(line=10, character=20),
            end=Position(line=20, character=30)
        )
        
        child_range = Range(
            start=Position(line=12, character=4),
            end=Position(line=14, character=8)
        )
        
        child_symbol = Symbol(
            name="child_function",
            kind=SymbolKind.FUNCTION,
            range=child_range,
            selection_range=child_range,
            detail="A child function"
        )
        
        # Act
        parent_symbol = Symbol(
            name="parent_class",
            kind=SymbolKind.CLASS,
            range=parent_range,
            selection_range=parent_range,
            detail="A parent class",
            children=[child_symbol]
        )
        
        # Assert
        self.assertEqual(parent_symbol.name, "parent_class")
        self.assertEqual(parent_symbol.kind, SymbolKind.CLASS)
        self.assertEqual(len(parent_symbol.children), 1)
        self.assertEqual(parent_symbol.children[0].name, "child_function")
        self.assertEqual(parent_symbol.children[0].kind, SymbolKind.FUNCTION)

    def test_code_analysis_result(self):
        """Test the CodeAnalysisResult model."""
        # Arrange
        symbol_range = Range(
            start=Position(line=10, character=20),
            end=Position(line=15, character=30)
        )
        
        symbol = Symbol(
            name="test_function",
            kind=SymbolKind.FUNCTION,
            range=symbol_range,
            selection_range=symbol_range,
            detail="A test function"
        )
        
        # Act
        result = CodeAnalysisResult(
            file_path="test.py",
            symbols=[symbol],
            imports=["import os", "import sys"],
            dependencies=["os", "sys"],
            language="python",
            errors=[]
        )
        
        # Assert
        self.assertEqual(result.file_path, "test.py")
        self.assertEqual(len(result.symbols), 1)
        self.assertEqual(result.symbols[0].name, "test_function")
        self.assertEqual(len(result.imports), 2)
        self.assertEqual(result.imports[0], "import os")
        self.assertEqual(len(result.dependencies), 2)
        self.assertEqual(result.dependencies[0], "os")
        self.assertEqual(result.language, "python")
        self.assertEqual(len(result.errors), 0)

    def test_code_generation_request(self):
        """Test the CodeGenerationRequest model."""
        # Act
        request = CodeGenerationRequest(
            prompt="Create a function to calculate the factorial of a number",
            context="This is part of a math library",
            language="python",
            file_path="math_utils.py",
            position=Position(line=10, character=0),
            options={"include_tests": True}
        )
        
        # Assert
        self.assertEqual(request.prompt, "Create a function to calculate the factorial of a number")
        self.assertEqual(request.context, "This is part of a math library")
        self.assertEqual(request.language, "python")
        self.assertEqual(request.file_path, "math_utils.py")
        self.assertEqual(request.position.line, 10)
        self.assertEqual(request.position.character, 0)
        self.assertEqual(request.options, {"include_tests": True})

    def test_code_generation_result(self):
        """Test the CodeGenerationResult model."""
        # Act
        result = CodeGenerationResult(
            code="def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)",
            explanation="This is a recursive implementation of factorial",
            alternatives=["def factorial(n):\n    result = 1\n    for i in range(1, n+1):\n        result *= i\n    return result"],
            file_path="math_utils.py",
            position=Position(line=10, character=0)
        )
        
        # Assert
        self.assertEqual(result.code, "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)")
        self.assertEqual(result.explanation, "This is a recursive implementation of factorial")
        self.assertEqual(len(result.alternatives), 1)
        self.assertEqual(result.file_path, "math_utils.py")
        self.assertEqual(result.position.line, 10)
        self.assertEqual(result.position.character, 0)


if __name__ == "__main__":
    unittest.main()
