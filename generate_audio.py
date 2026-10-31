from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

VOICE_IDS = {
    "Nam Minh": "vi-VN-NamMinhNeural",
    "Hoài My": "vi-VN-HoaiMyNeural",
    "vi-VN-NamMinhNeural": "vi-VN-NamMinhNeural",
    "vi-VN-HoaiMyNeural": "vi-VN-HoaiMyNeural",
}


def rate_percent(rate: str) -> str:
    value = float(rate)
    if value < 0.5 or value > 2.0:
        raise ValueError("Tốc độ cần nằm trong khoảng 0.5 đến 2.0.")
    return f"{round((value - 1.0) * 100):+d}%"


async def generate(text: str, voice: str, rate: str, output: Path, attempts: int) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("Chưa cài edge-tts. Hãy cài requirements.txt.") from exc

    voice_id = VOICE_IDS.get(voice)
    if not voice_id:
        raise ValueError(f"Giọng đọc không được hỗ trợ: {voice}")

    if not text.strip():
        raise ValueError("Nội dung truyện đang trống.")
    if attempts < 1 or attempts > 5:
        raise ValueError("Số lần thử phải nằm trong khoảng 1 đến 5.")

    rate_value = rate_percent(rate)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.stem + ".partial" + output.suffix)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        partial.unlink(missing_ok=True)
        try:
            # One complete text request produces one MP3 for the chapter.
            communicator = edge_tts.Communicate(
                text=text,
                voice=voice_id,
                rate=rate_value,
            )
            await communicator.save(str(partial))

            if not partial.is_file() or partial.stat().st_size < 128:
                raise RuntimeError(
                    "Edge-TTS không tạo ra file MP3 hợp lệ hoặc không trả về audio."
                )

            os.replace(partial, output)
            return
        except Exception as exc:
            last_error = exc
            partial.unlink(missing_ok=True)
            print(
                f"[RETRY] Lần thử {attempt}/{attempts}: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )
            if attempt < attempts:
                await asyncio.sleep(5 * attempt)

    raise RuntimeError(
        f"Tạo audio thất bại sau {attempts} lần thử. "
        f"Lỗi cuối: {type(last_error).__name__}: {last_error}"
    ) from last_error


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tạo một file MP3 từ toàn bộ văn bản bằng Edge-TTS."
    )
    parser.add_argument("--input", required=True, help="File TXT đầu vào")
    parser.add_argument("--output", required=True, help="Đường dẫn MP3 đầu ra")
    parser.add_argument("--voice", default="Nam Minh")
    parser.add_argument("--rate", default="1.0")
    parser.add_argument("--attempts", type=int, default=1)
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)
    try:
        text = source.read_text(encoding="utf-8-sig").strip()
        asyncio.run(generate(text, args.voice, args.rate, output, args.attempts))
        print(f"[SUCCESS] {output} ({output.stat().st_size} bytes)", flush=True)
        return 0
    except Exception as exc:
        print(
            f"[ERROR] {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
