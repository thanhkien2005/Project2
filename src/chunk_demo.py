import json
import re
import sys
import statistics
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.stdout.reconfigure(encoding='utf-8')

PARSED = Path(r"D:\14 days challenge\4\data\parsed")
FILE = "HPG"

# ============== Cleaners ==============
img_re        = re.compile(r'<img[^>]*/>')
empty_div_re  = re.compile(r'<div[^>]*>\s*</div>')
div_open_re   = re.compile(r'<div[^>]*>')
ws_re         = re.compile(r'\s+')

# Strip ALL inline style="..." attributes inside any HTML tag
style_attr_re = re.compile(r"\s+style\s*=\s*'[^']*'")
style_attr_re2 = re.compile(r'\s+style\s*=\s*"[^"]*"')
border_attr_re = re.compile(r'\s+border\s*=\s*"[^"]*"')

def strip_css(html):
    """Strip inline style + border attributes, giữ nguyên cấu trúc <table><tr><td>"""
    html = style_attr_re.sub('', html)
    html = style_attr_re2.sub('', html)
    html = border_attr_re.sub('', html)
    return html

def clean_text(t):
    """Clean text blocks (non-table)"""
    t = img_re.sub('', t)
    prev = None
    while prev != t:
        prev = t
        t = empty_div_re.sub('', t)
    t = div_open_re.sub('', t)
    t = t.replace('</div>', '')
    t = ws_re.sub(' ', t).strip()
    return t

# ============== Splitters ==============
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000, chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)

def split_table(html_table, max_chars=1800):
    """Split big table by rows, KEEP header row in each part"""
    inner_match = re.search(r'<table[^>]*>(.*?)</table>', html_table, re.DOTALL)
    if not inner_match:
        return [html_table]
    rows = re.findall(r'<tr.*?</tr>', inner_match.group(1), re.DOTALL)
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

# ============== Main ==============
data = json.load(open(PARSED / f"{FILE}.json", encoding='utf-8'))
print(f"Loaded {FILE}.json: {len(data)} pages\n")

chunks = []

def flush(buf, blocks_meta, page_idx):
    if not buf: return
    full = "\n\n".join(buf)
    if len(full.strip()) < 50: return
    for i, sp in enumerate(splitter.split_text(full)):
        if len(sp.strip()) < 50: continue
        chunks.append({
            "text": sp, "file": f"{FILE}.md", "page": page_idx,
            "block_type": "text",
            "block_ids": [b['block_id'] for b in blocks_meta],
            "split_idx": i,
        })

for page_idx, page in enumerate(data, start=1):
    blocks = page['prunedResult']['parsing_res_list']
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
                    "text": part, "file": f"{FILE}.md", "page": page_idx,
                    "block_type": "table", "block_id": blk.get('block_id'),
                    "table_part": part_idx, "bbox": blk.get('block_bbox'),
                })
        else:
            cleaned = clean_text(raw)
            if cleaned:
                text_buf.append(cleaned)
                text_meta.append(blk)
    flush(text_buf, text_meta, page_idx)

# ============== Stats ==============
table_chunks = [c for c in chunks if c['block_type'] == 'table']
text_chunks  = [c for c in chunks if c['block_type'] == 'text']
print(f"=== Tổng chunks: {len(chunks)} ===")
print(f"  Table : {len(table_chunks)}")
print(f"  Text  : {len(text_chunks)}")

if text_chunks:
    L = [len(c['text']) for c in text_chunks]
    print(f"\nText chunk chars: min={min(L)} med={int(statistics.median(L))} max={max(L)} mean={int(statistics.mean(L))}")
if table_chunks:
    L = [len(c['text']) for c in table_chunks]
    print(f"Table chunk chars: min={min(L)} med={int(statistics.median(L))} max={max(L)} mean={int(statistics.mean(L))}")
    print(f"  → table chunks > 2000 chars: {sum(1 for x in L if x > 2000)}")

# ============== Samples ==============
print("\n" + "="*70)
print("SAMPLE TEXT CHUNK")
print("="*70)
c = text_chunks[2]
print(f"page={c['page']} | block_ids={c['block_ids']} | len={len(c['text'])}")
print("-"*70)
print(c['text'])

print("\n" + "="*70)
print("SAMPLE TABLE CHUNK (sau strip CSS)")
print("="*70)
c = next((c for c in table_chunks if 'VỐN CHỦ' in c['text'] or 'TỔNG CỘNG' in c['text']), table_chunks[5])
print(f"page={c['page']} | block_id={c['block_id']} | bbox={c['bbox']} | part={c.get('table_part')} | len={len(c['text'])}")
print("-"*70)
print(c['text'][:1500])