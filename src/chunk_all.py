import json
import re
import sys
import statistics
import time
from pathlib import Path
from collections import Counter
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.stdout.reconfigure(encoding='utf-8')

PARSED  = Path(r"D:\14 days challenge\4\data\parsed")
OUTPUT  = Path(r"D:\14 days challenge\4\data\chunks.jsonl")

# === Cleaners ===
img_re = re.compile(r'<img[^>]*/>')
empty_div_re = re.compile(r'<div[^>]*>\s*</div>')
div_open_re = re.compile(r'<div[^>]*>')
ws_re = re.compile(r'\s+')
style_attr_re = re.compile(r"\s+style\s*=\s*'[^']*'")
style_attr_re2 = re.compile(r'\s+style\s*=\s*"[^"]*"')
border_attr_re = re.compile(r'\s+border\s*=\s*"[^"]*"')

def strip_css(html):
    html = style_attr_re.sub('', html)
    html = style_attr_re2.sub('', html)
    html = border_attr_re.sub('', html)
    return html

def clean_text(t):
    t = img_re.sub('', t)
    prev = None
    while prev != t:
        prev = t
        t = empty_div_re.sub('', t)
    t = div_open_re.sub('', t)
    t = t.replace('</div>', '')
    t = ws_re.sub(' ', t).strip()
    return t

splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000, chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)

def split_table(html_table, max_chars=1800):
    inner = re.search(r'<table[^>]*>(.*?)</table>', html_table, re.DOTALL)
    if not inner:
        return [html_table]
    rows = re.findall(r'<tr.*?</tr>', inner.group(1), re.DOTALL)
    if len(rows) <= 1 or len(html_table) <= max_chars:
        return [html_table]
    table_open = re.match(r'<table[^>]*>', html_table).group(0)
    header, body = rows[0], rows[1:]
    parts, cur = [], [header]
    cur_len = len(table_open) + len(header) + len('</table>')
    for r in body:
        if cur_len + len(r) > max_chars and len(cur) > 1:
            parts.append(table_open + ''.join(cur) + '</table>')
            cur = [header, r]
            cur_len = len(table_open) + len(header) + len(r) + len('</table>')
        else:
            cur.append(r)
            cur_len += len(r)
    if cur:
        parts.append(table_open + ''.join(cur) + '</table>')
    return parts


def chunk_one_file(json_path):
    """Return list of chunks for 1 file"""
    file_stem = json_path.stem  # "HPG", "ACBS_DPM_..."
    data = json.load(open(json_path, encoding='utf-8'))
    chunks = []

    def flush(buf, blocks_meta, page_idx):
        if not buf: return
        full = "\n\n".join(buf)
        if len(full.strip()) < 50: return
        for i, sp in enumerate(splitter.split_text(full)):
            if len(sp.strip()) < 50: continue
            chunks.append({
                "text": sp,
                "source": file_stem,
                "page": page_idx,
                "block_type": "text",
                "block_ids": [b['block_id'] for b in blocks_meta],
                "split_idx": i,
            })

    for page_idx, page in enumerate(data, start=1):
        try:
            blocks = page['prunedResult']['parsing_res_list']
        except (KeyError, TypeError):
            continue
        text_buf, text_meta = [], []
        for blk in blocks:
            label = blk.get('block_label', 'unknown')
            raw = (blk.get('block_content') or '').strip()
            if not raw: continue
            if label == 'table':
                flush(text_buf, text_meta, page_idx)
                text_buf, text_meta = [], []
                cleaned_table = strip_css(raw)
                for part_idx, part in enumerate(split_table(cleaned_table)):
                    chunks.append({
                        "text": part,
                        "source": file_stem,
                        "page": page_idx,
                        "block_type": "table",
                        "block_id": blk.get('block_id'),
                        "table_part": part_idx,
                        "bbox": blk.get('block_bbox'),
                    })
            else:
                cleaned = clean_text(raw)
                if cleaned:
                    text_buf.append(cleaned)
                    text_meta.append(blk)
        flush(text_buf, text_meta, page_idx)

    return chunks


# === Run on all 40 files ===
all_chunks = []
per_file_stats = []
errors = []

json_files = sorted(PARSED.glob("*.json"))
print(f"Processing {len(json_files)} files...\n")

t0 = time.time()
for jp in json_files:
    try:
        chunks = chunk_one_file(jp)
        all_chunks.extend(chunks)
        n_table = sum(1 for c in chunks if c['block_type'] == 'table')
        n_text = sum(1 for c in chunks if c['block_type'] == 'text')
        per_file_stats.append((jp.stem, len(chunks), n_table, n_text))
        print(f"  {jp.stem:60s} {len(chunks):4d} chunks ({n_table} tbl, {n_text} txt)")
    except Exception as e:
        errors.append((jp.stem, str(e)))
        print(f"  [ERROR] {jp.stem}: {e}")

elapsed = time.time() - t0

# === Save JSONL ===
with open(OUTPUT, 'w', encoding='utf-8') as f:
    for c in all_chunks:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')

# === Summary ===
print(f"\n{'='*70}")
print(f"DONE in {elapsed:.1f}s")
print(f"  Files OK : {len(per_file_stats)}/{len(json_files)}")
print(f"  Errors   : {len(errors)}")
print(f"  Tổng chunks: {len(all_chunks)}")
print(f"    Table : {sum(1 for c in all_chunks if c['block_type'] == 'table')}")
print(f"    Text  : {sum(1 for c in all_chunks if c['block_type'] == 'text')}")
L = [len(c['text']) for c in all_chunks]
print(f"  Chunk chars: min={min(L)} med={int(statistics.median(L))} max={max(L)} mean={int(statistics.mean(L))}")
print(f"\nĐã lưu vào: {OUTPUT}")
print(f"  Size: {OUTPUT.stat().st_size / 1024:.1f} KB")

if errors:
    print("\n=== ERRORS ===")
    for f, e in errors:
        print(f"  {f}: {e}")