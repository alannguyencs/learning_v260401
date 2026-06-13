#!/usr/bin/env python3
"""Smoke-test the V2V Over Mode WebSocket protocol against a recorded WAV.

Drives one press-to-talk turn end-to-end against a *running* backend, with no
browser: connects, waits for ``session_ready``, streams a 16 kHz mono WAV as
binary PCM, sends ``activity_end``, then collects the model's audio reply +
transcripts until ``turn_complete``. Writes the reply audio to a WAV so you can
listen, and prints the input/output transcripts and any tool calls observed.

This is the Stage 3 acceptance gate — it exercises the real Gemini Live session
(so it needs GEMINI_API_KEY, network, and the native-audio model to accept the
two function tools). It is a manual tool, not part of the pytest suite.

Usage:
    # start the backend first (./start_app.sh), then:
    python scripts/sync_terminology_notes.py          # ensure notes are indexed
    python scripts/smoke_v2v_over.py path/to/16k_mono.wav \
        --url ws://localhost:8999/api/voice/v2v-over \
        --token "$WEBAPP_ACCESS_TOKEN" --voice Kore --out reply.wav

The WAV must be 16 kHz, mono, 16-bit PCM. A reply WAV is written at 24 kHz.
"""

import argparse
import asyncio
import json
import os
import sys
import wave
from pathlib import Path

import websockets

PROJECT_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

_FRAME_BYTES = 3200  # 100 ms of 16 kHz 16-bit mono PCM


def _read_wav_pcm(path: str) -> bytes:
    with wave.open(path, "rb") as w:
        if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
            print(
                f"WARNING: expected 16 kHz mono 16-bit; got "
                f"{w.getframerate()} Hz, {w.getnchannels()} ch, {w.getsampwidth()*8}-bit"
            )
        return w.readframes(w.getnframes())


def _write_wav(path: str, pcm: bytes, rate: int = 24000) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


async def _run(args) -> int:
    pcm = _read_wav_pcm(args.wav)
    headers = {"Cookie": f"access_token={args.token}"} if args.token else {}
    url = f"{args.url}?voice={args.voice}"
    print(f"connecting: {url}")
    reply = bytearray()
    in_tr, out_tr = [], []
    async with websockets.connect(url, additional_headers=headers, max_size=None) as ws:
        await ws.send(json.dumps({"type": "activity_start"}))
        # Wait for session_ready before streaming audio.
        while True:
            msg = await ws.recv()
            if isinstance(msg, str) and json.loads(msg).get("type") == "session_ready":
                break
        print("session_ready — streaming audio")
        for i in range(0, len(pcm), _FRAME_BYTES):
            await ws.send(pcm[i : i + _FRAME_BYTES])
            await asyncio.sleep(0.02)
        await ws.send(json.dumps({"type": "activity_end"}))
        print("activity_end — awaiting reply")
        while True:
            msg = await ws.recv()
            if isinstance(msg, bytes):
                reply.extend(msg)
                continue
            event = json.loads(msg)
            etype = event.get("type")
            if etype == "input_transcript":
                in_tr.append(event["text"])
            elif etype == "output_transcript":
                out_tr.append(event["text"])
            elif etype in ("turn_complete", "end", "error"):
                print(f"event: {event}")
                if etype != "turn_complete":
                    return 1
                break
    print(f"\nUSER said:  {''.join(in_tr).strip()!r}")
    print(f"BOT said:   {''.join(out_tr).strip()!r}")
    print(f"reply audio: {len(reply)} bytes")
    if reply:
        _write_wav(args.out, bytes(reply))
        print(f"wrote {args.out}")
    return 0


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Smoke-test V2V Over Mode.")
    parser.add_argument("wav", help="path to a 16 kHz mono 16-bit WAV")
    parser.add_argument("--url", default="ws://localhost:8999/api/voice/v2v-over")
    parser.add_argument("--token", default=os.getenv("WEBAPP_ACCESS_TOKEN", ""))
    parser.add_argument("--voice", default=os.getenv("VOICE_DEFAULT_NAME", "Kore"))
    parser.add_argument("--out", default="reply.wav")
    args = parser.parse_args(argv)
    sys.exit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
