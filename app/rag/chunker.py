# BASIC CODE CHUNKER
# Simple approach: file content into fixed number of lines chunks


CHUNK_SIZE = 80
CHUNK_OVERLAP = 10


def chunk_code(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    lines = content.splitlines()

    chunks = []
    start = 0

    while start < len(lines):
        end = start + chunk_size

        chunk_lines = lines[start:end]

        if not chunk_lines:
            break

        chunks.append({
            "start_line": start + 1,
            "end_line": min(end, len(lines)),
            "content": "\n".join(chunk_lines),
        })

        start += chunk_size - overlap

    return chunks