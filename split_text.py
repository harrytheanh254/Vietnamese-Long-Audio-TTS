from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


# Prefer splits after paragraph and sentence boundaries. The fallback splits at
# whitespace, so Vietnamese words and UTF-8 characters are never cut mid-token.
PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n+")
SENTENCE_BREAK = re.compile(r"""[.!?…]+["'”’»)\]]*\s+""")
WHITESPACE_BREAK = re.compile(r"\s+")


def split_text(text: str, target_chars: int = 3000) -> list[str]:
    """Split text into manageable, ordered chunks without losing words.

    The returned chunks are each no longer than target_chars. Whitespace at a
    chunk boundary is normalized by design; punctuation and word order remain.
    """
    if target_chars < 256:
        raise ValueError("target_chars must be at least 256.")
    text = text.strip()
    if not text:
        raise ValueError("Input text is empty.")

    chunks: list[str] = []
    start = 0
    while len(text) - start > target_chars:
        limit = start + target_chars
        min_cut = start + int(target_chars * 0.55)
        window = text[start:limit]

        cut = None
        # Paragraph breaks first.
        for match in PARAGRAPH_BREAK.finditer(window):
            candidate = start + match.end()
            if candidate >= min_cut:
                cut = candidate

        # Then sentence boundaries.
        if cut is None:
            for match in SENTENCE_BREAK.finditer(window):
                candidate = start + match.end()
                if candidate >= min_cut:
                    cut = candidate

        # Then a newline, then any whitespace.
        if cut is None:
            for match in re.finditer(r"\n+", window):
                candidate = start + match.end()
                if candidate >= min_cut:
                    cut = candidate
        if cut is None:
            for match in WHITESPACE_BREAK.finditer(window):
                candidate = start + match.end()
                if candidate >= min_cut:
                    cut = candidate

        # Last resort for a huge unbroken string.
        if cut is None:
            cut = limit

        piece = text[start:cut].strip()
        if piece:
            chunks.append(piece)
        start = cut

    tail = text[start:].strip()
    if tail:
        chunks.append(tail)

    if not chunks:
        raise ValueError("Text splitting produced no chunks.")
    if any(len(chunk) > target_chars for chunk in chunks):
        raise RuntimeError("Internal error: a text chunk exceeds the target size.")
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Split long text at natural boundaries for parallel TTS."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--target-chars", type=int, default=3000)
    parser.add_argument(
        "--github-output",
        help="Optional GitHub Actions GITHUB_OUTPUT path for matrix/count.",
    )
    args = parser.parse_args()

    source = Path(args.input)
    output_dir = Path(args.output_dir)
    text = source.read_text(encoding="utf-8-sig")
    chunks = split_text(text, args.target_chars)

    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("part_*.txt"):
        stale.unlink()

    items = []
    for number, chunk in enumerate(chunks, start=1):
        index = f"{number:05d}"
        filename = f"part_{index}.txt"
        (output_dir / filename).write_text(chunk, encoding="utf-8")
        items.append({"index": index, "file": filename})

    if args.github_output:
        # Single-line compact JSON is required for a GitHub Actions output value.
        matrix = json.dumps({"include": items}, ensure_ascii=False, separators=(",", ":"))
        with Path(args.github_output).open("a", encoding="utf-8") as output:
            output.write(f"matrix={matrix}\n")
            output.write(f"count={len(items)}\n")

    print(
        f"Split text into {len(chunks)} chunks "
        f"(target {args.target_chars:,} characters each).",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
