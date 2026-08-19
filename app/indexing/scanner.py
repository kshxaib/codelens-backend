import hashlib
import os
from pathlib import Path
import re

from app.indexing.language import detect_language


# DIRECTORIES WE NEVER WANT TO SCAN
IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
}


# FILES WE DON'T WANT
IGNORED_FILES = {
    ".DS_Store",
}


# BINARY FILE EXTENSIONS
# Images, archives, executables etc. ko source-code index me nahi daalna.
BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",

    ".pdf",

    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",

    ".exe",
    ".dll",
    ".so",
    ".dylib",

    ".class",
    ".pyc",

    ".woff",
    ".woff2",
    ".ttf",
    ".otf",

    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
}


# MINIFIED FILE DETECTION
def is_minified(file_path: str) -> bool:
    name = Path(file_path).name.lower()

    return (
        ".min.js" in name
        or ".min.css" in name
        or ".bundle.js" in name
    )


# BINARY FILE DETECTION
def is_binary(file_path: str) -> bool:
    path = Path(file_path)

    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    try:
        with path.open("rb") as file:
            sample = file.read(8192)

        return b"\x00" in sample

    except OSError:
        return True


# FILE HASH
# Later: old hash != new hash → file changed
def calculate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# SCAN REPOSITORY
# Repository directory ko recursively scan karta hai. return krega source files (ignored files nahi, binary files nahi, minified files nahi)
def scan_repository(repo_path: str):
    repo_path = Path(repo_path)

    files = []

    for root, directories, filenames in os.walk(repo_path):

        # Remove ignored directories
        for directory in directories[:]:
            if directory in IGNORED_DIRECTORIES:
                directories.remove(directory)

        for filename in filenames:

            # Skip ignored files
            if filename in IGNORED_FILES:
                continue

            full_path = Path(root) / filename

            # Skip binary files
            if is_binary(str(full_path)):
                continue

            # Skip minified files
            if is_minified(str(full_path)):
                continue

            # Detect language
            language = detect_language(str(full_path))

            # Skip unknown file types
            if not language:
                continue

            try:
                content = full_path.read_bytes()
                text = content.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Get path relative to repository root
            relative_path = full_path.relative_to(repo_path).as_posix()

            # Store file information
            files.append({
                "file_path": relative_path,
                "language": language,
                "file_size": len(content),
                "line_count": text.count("\n") + 1 if text else 0,
                "file_hash": calculate_hash(content),
                "content": text,
            })

    return files



# BASIC SYMBOL EXTRACTION
def detect_symbol(content: str,start_line: int,end_line: int,language: str | None):
    if not content or not language:
        return None

    lines = content.splitlines()

    # Chunk ke andar lines check karo
    for line in lines:
        stripped = line.strip()

        # Python function
        if language == "python":
            match = re.match(r"def\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if match:
                return match.group(1)

            # Python class
            match = re.match(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if match:
                return match.group(1)


        # JavaScript / TypeScript function
        if language in ("javascript", "typescript"):
            match = re.match(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)",stripped)
            if match:
                return match.group(1)

            # JS/TS class
            match = re.match(r"(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)",stripped)
            if match:
                return match.group(1)

    return None