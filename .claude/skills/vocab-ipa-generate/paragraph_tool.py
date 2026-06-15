#!/usr/bin/env python3
"""Incremental paragraph driver for the vocab IPA viewer.

Segments a story into paragraphs (same rule as the skill: drop the leading
"# Title" heading and any horizontal rules, then split on blank lines) and
drives one-paragraph-at-a-time generation against the per-story JSON.

A paragraph is COMPLETE when its section exists in the JSON AND carries a
non-empty `nuclei` list. The "next" paragraph is the first incomplete one — so
each skill run transcribes exactly one paragraph, never the whole article.

Usage:
  python paragraph_tool.py next <story.md> [json] [dict.json]
      Print JSON describing the next paragraph to generate:
        {title, subtitle, total, completed, next_index, next_text,
         found: {word: ipa, ...}, missing: [word, ...]}
      `found`/`missing` are the dictionary lookup for THIS paragraph's words
      only. next_index is null when every paragraph is already complete.

  python paragraph_tool.py set <story.md> <json> <index> <payload.json|->
      Upsert one section at <index> (0-based). payload = {"ipa": "...",
      "nuclei": [...]}. `en` is filled automatically from paragraph[index]
      verbatim, so the English text can never drift. Creates the JSON
      (title + standard subtitle) if it does not exist yet; preserves all
      other sections.

Default json path:  vocab/json/<story-stem>_ipa.json
Default dict path:  vocab/US_IPA.json
"""
import json
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ipa_lookup import tokenize, load_dict, DEFAULT_DICT  # noqa: E402

SUBTITLE = ("Phonemic transcription (General American, rhotic). "
            "ˈ = primary stress · ˌ = secondary stress · ː = long vowel · "
            "ə = schwa. LOT vowel = /ɑː/, THOUGHT/CLOTH = /ɔː/ "
            "(cot–caught kept distinct).")
HR_RE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")


def segment(story_text):
    """Return (title, [paragraph, ...]) using the skill's segmentation rule."""
    title, body_lines, dropped_heading = None, [], False
    for ln in story_text.splitlines():
        s = ln.strip()
        if not dropped_heading and s.startswith("# "):
            title = s[2:].strip()
            dropped_heading = True
            continue
        if HR_RE.match(ln):
            continue
        body_lines.append(ln)
    paras = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(body_lines))
             if p.strip()]
    return title, paras


def default_json_for(story_path):
    stem = os.path.splitext(os.path.basename(story_path))[0]
    return os.path.join("vocab", "json", f"{stem}_ipa.json")


def load_json(path):
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    return None


def is_complete(sec):
    return bool(sec) and bool(sec.get("nuclei"))


def cmd_next(args):
    if not args:
        sys.exit("next: need <story.md>")
    story_path = args[0]
    json_path = args[1] if len(args) > 1 else default_json_for(story_path)
    dict_path = args[2] if len(args) > 2 else DEFAULT_DICT
    with open(story_path, encoding="utf-8") as f:
        title, paras = segment(f.read())
    doc = load_json(json_path) or {}
    sections = doc.get("sections", [])

    next_index = len(paras)
    for i in range(len(paras)):
        if i >= len(sections) or not is_complete(sections[i]):
            next_index = i
            break

    out = OrderedDict()
    out["title"] = (doc.get("title") or
                    (f"{title} — IPA" if title else "Untitled — IPA"))
    out["subtitle"] = doc.get("subtitle", SUBTITLE)
    out["total"] = len(paras)
    out["completed"] = next_index
    if next_index >= len(paras):
        out["next_index"] = None
        out["next_text"] = None
        out["found"] = {}
        out["missing"] = []
    else:
        text = paras[next_index]
        d = load_dict(dict_path)
        found, missing = OrderedDict(), []
        for w in tokenize(text):
            (found.__setitem__(w, d[w]) if w in d else missing.append(w))
        out["next_index"] = next_index
        out["next_text"] = text
        out["found"] = found
        out["missing"] = missing
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_set(args):
    if len(args) < 3:
        sys.exit("set: need <story.md> <json> <index> [payload.json|-]")
    story_path, json_path, index = args[0], args[1], int(args[2])
    payload_path = args[3] if len(args) > 3 else "-"
    with open(story_path, encoding="utf-8") as f:
        _, paras = segment(f.read())
    if not 0 <= index < len(paras):
        sys.exit(f"set: index {index} out of range (0..{len(paras) - 1})")

    raw = sys.stdin.read() if payload_path == "-" else open(
        payload_path, encoding="utf-8").read()
    payload = json.loads(raw)

    doc = load_json(json_path)
    if doc is None:
        title, _ = segment(open(story_path, encoding="utf-8").read())
        doc = OrderedDict([
            ("title", f"{title} — IPA" if title else "Untitled — IPA"),
            ("subtitle", SUBTITLE),
            ("sections", []),
        ])
    sections = doc.setdefault("sections", [])
    while len(sections) <= index:  # pad gaps with text-only placeholders
        j = len(sections)
        sections.append(OrderedDict([("en", paras[j]), ("ipa", ""),
                                     ("nuclei", [])]))
    sections[index] = OrderedDict([
        ("en", paras[index]),
        ("ipa", payload["ipa"]),
        ("nuclei", payload.get("nuclei", [])),
    ])

    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"set paragraph {index + 1}/{len(paras)} in {json_path}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "next":
        cmd_next(sys.argv[2:])
    elif cmd == "set":
        cmd_set(sys.argv[2:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
