from pathlib import Path

# File extension dekh kar basic programming language detect karenge.

LANGUAGE_MAP = {
    ".py": "python",

    ".js": "javascript",
    ".jsx": "javascript",

    ".ts": "typescript",
    ".tsx": "typescript",

    ".java": "java",

    ".c": "c",
    ".h": "c",

    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",

    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".swift": "swift", 
    ".sql": "sql",
}


def detect_language(file_path: str) -> str | None:
    extension = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(extension)