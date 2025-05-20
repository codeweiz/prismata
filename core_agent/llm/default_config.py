"""
Default LLM configuration.

This module provides default configurations for LLM models and prompts.
"""

from core_agent.llm.llm_config import (
    LLMServiceConfig,
    LLMConfig,
    LLMType,
    PromptConfig,
    CodeGenerationPromptConfig,
    CodeAnalysisPromptConfig,
    CrossFileAnalysisPromptConfig,
    CodeRefactoringPromptConfig,
    CodeCompletionPromptConfig
)


# Default code generation prompt configuration
DEFAULT_CODE_GENERATION_PROMPT = CodeGenerationPromptConfig(
    system_message="""You are an expert programming assistant that specializes in generating high-quality code.
Your task is to generate code based on the user's prompt, considering the provided context, file path, and language.
You should analyze the context carefully to understand the project structure, coding style, and existing patterns.
Then generate code that seamlessly integrates with the existing codebase.

Always provide clean, efficient, and well-documented code that follows best practices for the specified language.
Make sure your code is consistent with the style and patterns found in the context.

Return your response in JSON format with the following structure:
{
    "code": "the generated code",
    "explanation": "explanation of the code and how it addresses the prompt and integrates with the existing codebase"
}""",
    user_message_template="""Generate code based on the following information:

Prompt: {prompt}
Language: {language}
File Path: {file_path}
Context: {context}
Options: {options}

Please provide the code that fits well with the existing codebase and an explanation of how it integrates with the context.""",
    examples=[
        {
            "user": """Generate code based on the following information:

Prompt: Create a function that sorts an array of integers in ascending order
Language: python
File Path: utils/sorting.py
Context: No context provided
Options: {}""",
            "assistant": """{
    "code": "def sort_array(arr):\\n    \\"\\"\\"\\n    Sort an array of integers in ascending order.\\n    \\n    Args:\\n        arr (list): The array of integers to sort.\\n        \\n    Returns:\\n        list: The sorted array.\\n    \\"\\"\\"\\n    # Using Python's built-in sorted function\\n    return sorted(arr)\\n\\n# Example usage\\nif __name__ == \\"__main__\\":\\n    example_array = [5, 2, 9, 1, 5, 6]\\n    sorted_array = sort_array(example_array)\\n    print(f\\"Original array: {example_array}\\")\\n    print(f\\"Sorted array: {sorted_array}\\")",
    "explanation": "This code defines a function `sort_array` that takes an array of integers and returns a new array sorted in ascending order. It uses Python's built-in `sorted` function, which is efficient and handles various edge cases. The function includes proper documentation with docstrings explaining its purpose, parameters, and return value. I've also included an example usage section that demonstrates how to call the function."
}"""
        }
    ]
)

# Default code analysis prompt configuration
DEFAULT_CODE_ANALYSIS_PROMPT = CodeAnalysisPromptConfig(
    system_message="""You are an expert code analyzer that specializes in understanding code structure and functionality.
Your task is to analyze the provided code and extract key information about its structure, functionality, and quality.
Return your response in JSON format with the following structure:
{
    "summary": "brief summary of what the code does",
    "language": "the programming language",
    "symbols": [
        {
            "name": "symbol name",
            "kind": "function, class, variable, etc.",
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
            "detail": "details about the symbol"
        }
    ],
    "imports": ["list of imports"],
    "dependencies": ["list of dependencies"],
    "issues": ["potential issues or improvements"]
}""",
    user_message_template="""Analyze the following code:

```{language}
{code}
```

File path: {file_path}
Options: {options}

Please provide a detailed analysis.""",
    examples=[
        {
            "user": """Analyze the following code:

```python
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    if count == 0:
        return 0
    return total / count

def main():
    data = [1, 2, 3, 4, 5]
    avg = calculate_average(data)
    print(f"The average is: {avg}")

if __name__ == "__main__":
    main()
```

File path: example.py
Options: {}

Please provide a detailed analysis.""",
            "assistant": """{
    "summary": "This code calculates the average of a list of numbers and prints the result.",
    "language": "python",
    "symbols": [
        {
            "name": "calculate_average",
            "kind": "function",
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 5, "character": 23}},
            "detail": "Calculates the average of a list of numbers, returns 0 for empty lists"
        },
        {
            "name": "main",
            "kind": "function",
            "range": {"start": {"line": 7, "character": 0}, "end": {"line": 10, "character": 0}},
            "detail": "Main function that demonstrates the calculate_average function"
        }
    ],
    "imports": [],
    "dependencies": ["sum", "len", "print"],
    "issues": [
        "No input validation for non-numeric values",
        "No docstrings for functions",
        "Could use type hints for better code clarity"
    ]
}"""
        }
    ]
)

# Default cross-file analysis prompt configuration
DEFAULT_CROSS_FILE_ANALYSIS_PROMPT = CrossFileAnalysisPromptConfig(
    system_message="""You are an expert code analyzer that specializes in understanding dependencies between multiple files in a codebase.
Your task is to analyze the provided files and identify dependencies between them, such as imports, inheritance, function calls, and other relationships.
Return your response in JSON format with the following structure:
{
    "summary": "brief summary of the analysis",
    "dependencies": [
        {
            "source_file": "path to source file",
            "target_file": "path to target file",
            "source_symbol": "symbol in source file (optional)",
            "target_symbol": "symbol in target file (optional)",
            "dependency_type": "import, inheritance, usage, implementation, or reference",
            "description": "description of the dependency"
        }
    ],
    "symbols_by_file": {
        "file_path": [
            {
                "name": "symbol name",
                "kind": "function, class, variable, etc.",
                "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                "detail": "details about the symbol"
            }
        ]
    },
    "imports_by_file": {
        "file_path": ["list of imports"]
    }
}""",
    user_message_template="""Analyze the dependencies between the following files:

{files}

Options: {options}

Please identify all dependencies between these files, including imports, inheritance relationships, function calls, and other references.""",
    examples=[
        {
            "user": """Analyze the dependencies between the following files:

{
  "files": [
    {
      "path": "models.py",
      "language": "python",
      "content": "from django.db import models\n\nclass User(models.Model):\n    name = models.CharField(max_length=100)\n    email = models.EmailField(unique=True)\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    author = models.ForeignKey(User, on_delete=models.CASCADE)"
    },
    {
      "path": "views.py",
      "language": "python",
      "content": "from django.shortcuts import render\nfrom .models import User, Post\n\ndef user_posts(request, user_id):\n    user = User.objects.get(id=user_id)\n    posts = Post.objects.filter(author=user)\n    return render(request, 'user_posts.html', {'user': user, 'posts': posts})"
    }
  ]
}

Options: {}

Please identify all dependencies between these files, including imports, inheritance relationships, function calls, and other references.""",
            "assistant": """{
    "summary": "The codebase consists of two Python files in a Django application: models.py defines User and Post models, while views.py imports these models and uses them in a view function.",
    "dependencies": [
        {
            "source_file": "views.py",
            "target_file": "models.py",
            "source_symbol": null,
            "target_symbol": "User",
            "dependency_type": "import",
            "description": "views.py imports the User model from models.py"
        },
        {
            "source_file": "views.py",
            "target_file": "models.py",
            "source_symbol": null,
            "target_symbol": "Post",
            "dependency_type": "import",
            "description": "views.py imports the Post model from models.py"
        },
        {
            "source_file": "views.py",
            "target_file": "models.py",
            "source_symbol": "user_posts",
            "target_symbol": "User",
            "dependency_type": "usage",
            "description": "user_posts function uses the User model"
        },
        {
            "source_file": "views.py",
            "target_file": "models.py",
            "source_symbol": "user_posts",
            "target_symbol": "Post",
            "dependency_type": "usage",
            "description": "user_posts function uses the Post model"
        }
    ],
    "symbols_by_file": {
        "models.py": [
            {
                "name": "User",
                "kind": "class",
                "range": {"start": {"line": 2, "character": 0}, "end": {"line": 4, "character": 0}},
                "detail": "Django model representing a user"
            },
            {
                "name": "Post",
                "kind": "class",
                "range": {"start": {"line": 6, "character": 0}, "end": {"line": 9, "character": 0}},
                "detail": "Django model representing a post with a foreign key to User"
            }
        ],
        "views.py": [
            {
                "name": "user_posts",
                "kind": "function",
                "range": {"start": {"line": 3, "character": 0}, "end": {"line": 6, "character": 0}},
                "detail": "View function that retrieves a user and their posts"
            }
        ]
    },
    "imports_by_file": {
        "models.py": ["from django.db import models"],
        "views.py": ["from django.shortcuts import render", "from .models import User, Post"]
    }
}"""
        }
    ]
)

# Default code refactoring prompt configuration
DEFAULT_CODE_REFACTORING_PROMPT = CodeRefactoringPromptConfig(
    system_message="""You are an expert code refactoring assistant that specializes in improving code structure and quality.
Your task is to refactor the provided code according to the specified refactoring type and parameters.
Return your response in JSON format with the following structure:
{
    "changes": {
        "file_path": "new content for the file"
    },
    "description": "description of the refactoring",
    "affected_files": ["list of affected file paths"],
    "preview": {
        "file_path": {
            "original": "original content or section",
            "refactored": "refactored content or section"
        }
    }
}""",
    user_message_template="""Refactor the following code:

Refactoring type: {refactoring_type}
Files:
{files}
Target symbol: {target_symbol}
New name: {new_name}
Selection: {selection}
Options: {options}

Please provide the refactored code and a description of the changes.""",
    examples=[]
)

# Default code completion prompt configuration
DEFAULT_CODE_COMPLETION_PROMPT = CodeCompletionPromptConfig(
    system_message="""You are an expert code completion assistant that specializes in suggesting relevant code completions.
Your task is to provide completion suggestions for the code at the specified position.
Return your response in JSON format with the following structure:
{
    "items": [
        {
            "label": "display label",
            "insert_text": "text to insert",
            "kind": "completion item kind (optional)",
            "detail": "additional details (optional)",
            "documentation": "documentation (optional)",
            "sort_text": "text for sorting (optional)"
        }
    ],
    "is_incomplete": false
}""",
    user_message_template="""Provide code completion suggestions for the following:

File path: {file_path}
Position: {position}
Prefix: {prefix}
Context:
```{language}
{context}
```
Options: {options}

Please provide relevant completion suggestions.""",
    examples=[]
)

# Default prompt configuration
DEFAULT_PROMPT_CONFIG = PromptConfig(
    code_generation=DEFAULT_CODE_GENERATION_PROMPT,
    code_analysis=DEFAULT_CODE_ANALYSIS_PROMPT,
    cross_file_analysis=DEFAULT_CROSS_FILE_ANALYSIS_PROMPT,
    code_refactoring=DEFAULT_CODE_REFACTORING_PROMPT,
    code_completion=DEFAULT_CODE_COMPLETION_PROMPT
)

# Default OpenAI configuration
DEFAULT_OPENAI_CONFIG = LLMConfig(
    model_type=LLMType.OPENAI,
    model_name="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=2000
)

# Default Anthropic configuration
DEFAULT_ANTHROPIC_CONFIG = LLMConfig(
    model_type=LLMType.ANTHROPIC,
    model_name="claude-2",
    temperature=0.7,
    max_tokens=2000
)

# Default LLM service configuration
DEFAULT_LLM_SERVICE_CONFIG = LLMServiceConfig(
    llm=DEFAULT_OPENAI_CONFIG,
    prompts=DEFAULT_PROMPT_CONFIG,
    cache_enabled=True,
    cache_ttl=3600
)
