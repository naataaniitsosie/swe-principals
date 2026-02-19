"""
Text cleaning for PR comments (CONFORMITY.md: strip code blocks and diff snippets, lowercase, tokenize).
Pattern-based: regex for code blocks and diff lines; simple lowercase and word tokenize.
"""
import re
from typing import List

# Markdown fenced code blocks (```...``` or ```lang\n...\n```)
# Examples
# Example: "```javascript\nconsole.log('Hello, world!');\n```" -> True
# Example: "```javascript\nconsole.log('Hello, world!');\n```" -> True
_CODE_BLOCK_RE = re.compile(r"```[\w]*\n.*?```", re.DOTALL | re.IGNORECASE)

# Diff snippet lines: start with + or - (optional space)
# Examples
# Example: "+ This is a diff snippet" -> True
# Example: "- This is a diff snippet" -> True
# Example: " This is a diff snippet" -> False
_DIFF_LINE_RE = re.compile(r"^[\+\-]\s?.*$", re.MULTILINE)

# Word tokenize: split on non-word chars, keep words
# Examples
# Example: "Hello, world! 123" -> ["Hello", "world", "123"]
# Example: "Hello, world! 123." -> ["Hello", "world", "123"]
# Example: "Hello, world! 123." -> ["Hello", "world", "123"]
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def strip_code_blocks(text: str) -> str:
    """Remove markdown fenced code blocks (```...```)."""
    if not text:
        return ""
    return _CODE_BLOCK_RE.sub(" ", text)


def strip_diff_snippets(text: str) -> str:
    """Remove lines that look like diff snippets (start with + or -)."""
    if not text:
        return ""
    lines = text.splitlines()
    kept = [line for line in lines if not _DIFF_LINE_RE.match(line.strip())]
    return "\n".join(kept)


def lowercase(text: str) -> str:
    """Normalize to lowercase."""
    return (text or "").lower()


def tokenize(text: str) -> List[str]:
    """Tokenize into words (CONFORMITY.md: tokenize). Simple word-boundary split."""
    if not text:
        return []
    return _WORD_RE.findall(text.lower())


def clean_text(text: str) -> str:
    """Full cleaning pipeline: strip code, strip diff, lowercase, collapse whitespace."""
    if not text:
        return ""
    t = strip_code_blocks(text)
    t = strip_diff_snippets(t)
    t = lowercase(t)
    t = " ".join(t.split())
    return t.strip()
