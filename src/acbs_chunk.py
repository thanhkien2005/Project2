import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

PROC_DIR = Path(r"D:\14 days challenge\4\data\internal_procedures")
CHUNKS_PATH = Path(r"D:\14 days challenge\4\data\chunks.jsonl")


def chunk_procedure_file(md_path: Path) -> list[dict]:
    """Split markdown theo header ### (cấp 3), mỗi section thành 1 chunk."""
    text = md_path.read_text(encoding='utf-8')
    stem_parts = md_path.stem.split('-')
    source = f"{stem_parts[0]}-{stem_parts[1]}"  # "TT-01"
    title = ' '.join(stem_parts[2:]).replace('-', ' ').strip()

    sections = re.split(r'\n### ', text)
    chunks = []

    # Section 0 = header + intro (trước ### đầu tiên)
    intro = sections[0].strip()
    if intro:
        chunks.append({
            "text": intro,
            "source": source,
            "page": 1,
            "block_type": "procedure",
            "section": "Tiêu đề & Metadata",
            "split_idx": 0,
        })

    # Các section còn lại
    for i, sec in enumerate(sections[1:], 1):
        if '\n' in sec:
            section_title = sec.split('\n', 1)[0].strip()
            body = sec.split('\n', 1)[1].strip()
        else:
            section_title = sec.strip()
            body = ""

        # Thêm context "thuộc thông tư nào" vào đầu chunk → giúp retrieval
        chunk_text = f"[Thông tư {source} — {title}]\n\n### {section_title}\n\n{body}"
        chunks.append({
            "text": chunk_text,
            "source": source,
            "page": 1,
            "block_type": "procedure",
            "section": section_title,
            "split_idx": i,
        })

    return chunks


# === Main ===
# Backup chunks.jsonl hiện tại (an toàn)
backup = CHUNKS_PATH.with_suffix(f".jsonl.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
shutil.copy(CHUNKS_PATH, backup)
print(f"Backup → {backup.name}")

# Load chunks hiện có
existing = [json.loads(l) for l in open(CHUNKS_PATH, encoding='utf-8')]
print(f"Chunks hiện có: {len(existing)}")

# Drop procedure chunks cũ (nếu re-run script)
before = len(existing)
existing = [c for c in existing if c.get('block_type') != 'procedure']
if before != len(existing):
    print(f"  Đã xóa {before - len(existing)} procedure chunks cũ")

# Chunk 5 file thông tư
procedure_chunks = []
print("\nChunking 5 file thông tư:")
for md_file in sorted(PROC_DIR.glob("TT-*.md")):
    new_chunks = chunk_procedure_file(md_file)
    procedure_chunks.extend(new_chunks)
    print(f"  {md_file.stem:55s} → {len(new_chunks)} chunks")

print(f"\nTổng procedure chunks: {len(procedure_chunks)}")

# Gộp + ghi lại chunks.jsonl
all_chunks = existing + procedure_chunks
with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
    for c in all_chunks:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')

print(f"\nTotal chunks bây giờ: {len(all_chunks)} (BCTC: {len(existing)}, Procedure: {len(procedure_chunks)})")
print(f"Saved: {CHUNKS_PATH}")
print(f"Size: {CHUNKS_PATH.stat().st_size / 1024:.1f} KB")

# Sample preview
print("\n=== Sample chunk procedure ===")
print(json.dumps(procedure_chunks[5], ensure_ascii=False, indent=2)[:600])