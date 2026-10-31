from __future__ import annotations

import asyncio
import os
from pathlib import Path

from generate_audio import generate
from split_text import split_text

MAX_INPUT_CHARS = 60_000
MAX_PARALLEL = 4


async def main() -> None:
    text = os.environ.get("STORY_TEXT", "").strip()
    voice = os.environ.get("STORY_VOICE", "Nam Minh")
    rate = os.environ.get("STORY_RATE", "1.0")
    if not text:
        raise ValueError("Không nhận được nội dung truyện.")
    if len(text) > MAX_INPUT_CHARS:
        raise ValueError(f"Truyện vượt giới hạn {MAX_INPUT_CHARS:,} ký tự của workflow_dispatch.")
    if voice not in ("Nam Minh", "Hoài My"):
        raise ValueError("Giọng đọc không hợp lệ.")

    chunks = split_text(text, target_chars=2800)
    work = Path("output/parts")
    work.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(MAX_PARALLEL)

    async def make_part(index: int, chunk: str) -> Path:
        target = work / f"part_{index:05d}.mp3"
        async with semaphore:
            print(f"[START] Đoạn {index}/{len(chunks)}", flush=True)
            await generate(chunk, voice, rate, target, attempts=3)
            print(f"[DONE] Đoạn {index}/{len(chunks)}", flush=True)
        return target

    parts = await asyncio.gather(
        *(make_part(i, chunk) for i, chunk in enumerate(chunks, 1))
    )

    final = Path("output/audiobook.mp3")
    with final.open("wb") as destination:
        for part in parts:
            with part.open("rb") as source:
                while block := source.read(1024 * 1024):
                    destination.write(block)

    print(f"[SUCCESS] {final} ({final.stat().st_size:,} bytes)", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
