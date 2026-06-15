#!/usr/bin/env python3
"""Render a self-contained IPA-viewer HTML file from a vocab IPA JSON file.

Usage:
    python build_html.py <input.json> [output.html]

If output.html is omitted, writes to ../html/<same-stem>.html relative to the
JSON's parent's parent (i.e. vocab/json/X.json -> vocab/html/X.html).

The produced HTML:
  * fetches the sibling JSON when served over http(s) (live edits show up), and
  * falls back to an EMBEDDED copy so it also works by double-click (file://).
"""
import json
import sys
from pathlib import Path

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root{
    --bg:#0f1115; --card:#1a1d24; --card2:#212530; --ink:#e8eaf0; --muted:#9aa3b2;
    --accent:#7aa2f7; --ipa:#9ece6a; --line:#2b303b;
  }
  *{box-sizing:border-box}
  body{
    margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    line-height:1.6; padding:0 0 80px;
  }
  .wrap{max-width:820px; margin:0 auto; padding:0 20px}
  header{
    position:sticky; top:0; z-index:5; backdrop-filter:blur(8px);
    background:rgba(15,17,21,.85); border-bottom:1px solid var(--line); padding:18px 0 14px;
  }
  h1{font-size:24px; margin:0 0 6px}
  .sub{color:var(--muted); font-size:13px; margin:0}
  .card{
    background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:18px 20px; margin:16px 0;
  }
  .card.brk{margin-top:34px}
  .en{font-size:19px; font-weight:500; margin:0}
  .ipa{
    font-size:18px; color:var(--ink); margin:10px 0 0;
    font-family:"Charis SIL","Doulos SIL","Gentium Plus","Segoe UI",serif; letter-spacing:.3px;
  }
  details{margin-top:14px; border-top:1px dashed var(--line); padding-top:10px}
  summary{cursor:pointer; font-weight:600; font-size:14px; color:var(--accent); outline:none}
  .nuc-groups{margin-top:12px; display:flex; flex-direction:column; gap:8px}
  .nuc-row{display:flex; flex-wrap:wrap; gap:8px}
  .nuc-row .nuc{flex:1 1 140px; border-left:3px solid var(--g,var(--line))}
  .nuc-row .nuc .sym{color:var(--g,var(--ipa))}
  .nuc{background:var(--card2); border:1px solid var(--line); border-radius:10px; padding:9px 11px}
  .nuc .sym{font-weight:700; color:var(--ipa); font-size:15px}
  .nuc .lbl{color:var(--muted); font-size:12px; margin-left:4px}
  .nuc .w{display:block; margin-top:4px; font-size:13px; color:#cdd3e0}
  .ipa-in{color:var(--ipa); font-family:"Charis SIL","Doulos SIL","Gentium Plus","Segoe UI",serif}
  footer{color:var(--muted); font-size:12px; text-align:center; margin-top:30px}
  code{background:var(--card2); padding:1px 5px; border-radius:5px; font-size:.9em}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1 id="title">__TITLE__</h1>
    <p class="sub" id="subtitle"></p>
  </div>
</header>

<main class="wrap" id="content"></main>
<footer>Generated from <code>vocab/json/__JSON_BASENAME__</code></footer>

<script>
/* ---- Embedded fallback so the file works by double-click (file://). ---- */
/* When served over http(s) it re-fetches the JSON so edits there show live. */
const EMBEDDED = __EMBEDDED__;

function esc(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

/* Color the English word (default) and the /IPA/ syllable differently. */
function fmtWords(s){
  return esc(s).replace(/\/[^\/]*\//g, m=>`<span class="ipa-in">${m}</span>`);
}

/* Display only the binary marked attributes (long, rounded, stressed, r-colored).
   Drop the quoted keyword hint, the unmarked defaults (short, unrounded,
   unstressed, plain non-r) and the category tag (diphthong) — the IPA symbol +
   example words already carry those. */
const HIDE_ATTRS = new Set(["short","unrounded","unstressed","diphthong"]);
function fmtLabel(label){
  const parts = String(label).split(" · ");
  const kept = parts.slice(1).join(", ").split(",")
    .map(s=>s.trim()).filter(a=> a && !HIDE_ATTRS.has(a));
  return kept.join(", ");
}

/* Vowel families — each inner array is rendered as one row (line). A nucleus is
   placed by its bare IPA symbol (slashes stripped). Anything not listed here is
   collected into a trailing "other" row so nothing is dropped. */
const VOWEL_GROUPS = [
  ["eɪ","aɪ","aʊ"],         // diphthongs
  ["ɛ","ɛr","ɪr","æ"],      // front mid-low: eh / air / eer / a
  ["ɪ","iː","i"],           // front high: ih / ee
  ["ə","ər","ɜːr","ʌ"],     // central: uh / er / ur
  ["ɑː","ɑːr","ɔː","ɔːr","oʊ"], // back: ah / ar / aw / or / oh
  ["uː","ʊ","ʊr"],          // back high rounded: oo / uu / oor
];
/* One accent per group row (cycled if there are more rows than colors). */
const GROUP_COLORS = ["#7aa2f7","#f7768e","#9ece6a","#e0af68","#bb9af7","#2ac3de"];
function symOf(ipa){ return String(ipa).replace(/\//g,"").trim(); }
function groupNuclei(nuclei){
  const bySym = new Map(nuclei.map(n=>[symOf(n.ipa), n]));
  const used = new Set(), rows = [];
  VOWEL_GROUPS.forEach(syms=>{
    const row = [];
    syms.forEach(s=>{ if(bySym.has(s)){ row.push(bySym.get(s)); used.add(s); } });
    if(row.length) rows.push(row);
  });
  const leftover = nuclei.filter(n=> !used.has(symOf(n.ipa)));
  if(leftover.length) rows.push(leftover);
  return rows;
}

/* Map each vowel symbol -> its group color, and build a longest-match-first
   regex so the same colors can tint vowels inside the running IPA line. */
const VOWEL_COLOR = {};
VOWEL_GROUPS.forEach((syms,i)=>{
  const c = GROUP_COLORS[i % GROUP_COLORS.length];
  syms.forEach(s=>{ VOWEL_COLOR[s] = c; });
});
const VOWEL_RE = new RegExp(
  Object.keys(VOWEL_COLOR).sort((a,b)=> b.length - a.length)
    .map(s=> s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).join("|"),
  "g"
);
function colorIpa(s){
  return esc(s).replace(VOWEL_RE, m=>`<span style="color:${VOWEL_COLOR[m]}">${m}</span>`);
}

function render(data){
  document.getElementById("title").textContent = data.title;
  document.getElementById("subtitle").textContent = data.subtitle || "";
  document.title = data.title;
  const root = document.getElementById("content");
  root.innerHTML = "";

  data.sections.forEach(sec=>{
    const card = document.createElement("section");
    card.className = "card" + (sec.break ? " brk" : "");
    card.innerHTML =
      `<p class="en">${esc(sec.en)}</p>` +
      `<p class="ipa">${colorIpa(sec.ipa)}</p>`;

    if(sec.nuclei && sec.nuclei.length){
      const d = document.createElement("details"); d.open = true;
      let g = `<summary>&#128068; Nuclei (vowels) in this sentence &mdash; ${sec.nuclei.length}</summary><div class="nuc-groups">`;
      groupNuclei(sec.nuclei).forEach((row,i)=>{
        g += `<div class="nuc-row" style="--g:${GROUP_COLORS[i % GROUP_COLORS.length]}">`;
        row.forEach(n=>{
          g += `<div class="nuc"><span class="sym">${esc(n.ipa)}</span>` +
               `<span class="lbl">${esc(fmtLabel(n.label))}</span><span class="w">${fmtWords(n.words)}</span></div>`;
        });
        g += `</div>`;
      });
      g += `</div>`; d.innerHTML = g; card.appendChild(d);
    }
    root.appendChild(card);
  });
}

/* Prefer the live JSON when served; fall back to embedded for file:// */
fetch("../json/__JSON_BASENAME__")
  .then(r=> r.ok ? r.json() : Promise.reject())
  .then(render)
  .catch(()=> render(EMBEDDED));
</script>
</body>
</html>
"""


def build(json_path: Path, out_path: Path) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    embedded = json.dumps(data, ensure_ascii=False, indent=2)
    title = data.get("title", json_path.stem)
    html = (
        TEMPLATE
        .replace("__EMBEDDED__", embedded)
        .replace("__JSON_BASENAME__", json_path.name)
        .replace("__TITLE__", title)
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    json_path = Path(sys.argv[1]).resolve()
    if not json_path.is_file():
        print(f"error: not a file: {json_path}")
        sys.exit(1)
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2]).resolve()
    else:
        # vocab/json/X.json -> vocab/html/X.html
        out_path = json_path.parent.parent / "html" / (json_path.stem + ".html")
    build(json_path, out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
