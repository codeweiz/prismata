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
    CodeAnalysisPromptConfig
)


# Default code generation prompt configuration
DEFAULT_CODE_GENERATION_PROMPT = CodeGenerationPromptConfig(
    system_message="""You are an expert programming assistant that specializes in generating high-quality code.
Your task is to generate code based on the user's prompt, considering the provided context and language.
Always provide clean, efficient, and well-documented code that follows best practices for the specified language.
Return your response in JSON format with the following structure:
{
    "code": "the generated code",
    "explanation": "explanation of the code and how it addresses the prompt"
}""",
    user_message_template="""Generate code based on the following information:

Prompt: {prompt}
Language: {language}
Context: {context}
Options: {options}

Please provide the code and an explanation.""",
    examples=[
        {
            "user": """Generate code based on the following information:

Prompt: Create a function that sorts an array of integers in ascending order
Language: python
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

# Default prompt configuration
DEFAULT_PROMPT_CONFIG = PromptConfig(
    code_generation=DEFAULT_CODE_GENERATION_PROMPT,
    code_analysis=DEFAULT_CODE_ANALYSIS_PROMPT
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
