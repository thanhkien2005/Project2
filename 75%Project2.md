# Project 2 — RAG Agent BCTC ACBS — Tiến độ 75%

**Cập nhật:** 09/05/2026
**Hoàn thành:** 8/10 milestones
**Còn lại:** Next.js UI + Dockerize + Deploy

---

## 1. Tổng quan kiến trúc

```
┌──────────────────────────────────────────────────────┐
│  LAYER 3 — APPLICATION (Day 6 sáng)                  │
│  LangGraph ReAct agent + Llama 3.3 70B (Groq)        │
│  3 tools:                                            │
│    - retrieve_document      (RAG tổng quát)          │
│    - extract_financial_metrics (KPI 1 cty)           │
│    - compare_companies       (so sánh 2 cty)         │
└──────────────────────────────────────────────────────┘
                          ↑
┌──────────────────────────────────────────────────────┐
│  LAYER 2 — RETRIEVAL (Day 5 tối)                     │
│  - Hybrid: BM25 + Dense + Ticker boost + RRF fusion  │
│  - Embedding: AITeamVN/Vietnamese_Embedding (1.4GB)  │
│  - Vector DB: ChromaDB persistent (78MB local)       │
│  - Score: 19/20 top-1 đúng nguồn                     │
└──────────────────────────────────────────────────────┘
                          ↑
┌──────────────────────────────────────────────────────┐
│  LAYER 1 — DATA PREP (Day 5 sáng-chiều + Day 6 chiều)│
│  - 40 PDF (31 BCTC + 9 báo cáo phân tích)            │
│  - OCR bằng Baidu PaddleOCR-VL-1.5 (web)             │
│  - Chunking: table tách riêng, text 500 token        │
│  - + 5 file Thông tư nội bộ ACBS giả lập (Day 6)     │
│  - Output: chunks.jsonl (6514 chunks, 7.5MB)         │
└──────────────────────────────────────────────────────┘
                          ↑
┌──────────────────────────────────────────────────────┐
│  LAYER 0 — DEPLOYMENT (Day 7a — vừa xong hôm nay)    │
│  - FastAPI app wrap agent thành HTTP endpoint        │
│  - ngrok tunnel public URL (tạm thời)                │
│  - Verified bằng PowerShell curl.exe                 │
└──────────────────────────────────────────────────────┘
```

---

## 2. Tiến độ từng milestone

| # | Milestone | Status | Ghi chú |
|---|---|---|---|
| 1 | Day 5 sáng — OCR 40 PDF | ✅ | Baidu PaddleOCR-VL-1.5, output 80 file (40 .md + 40 .json) |
| 2 | Day 5 chiều — Chunking thông minh | ✅ | 6487 chunks BCTC (table tách riêng + text 500 token overlap 50) |
| 3 | Day 5 tối — Embedding + ChromaDB | ✅ | AITeamVN/Vietnamese_Embedding với prefix "passage:"/"query:" |
| 4 | Day 5 tối — Hybrid retrieval | ✅ | BM25 + Dense + Ticker boost + RRF, **19/20 top-1** |
| 5 | Day 6 sáng — LangGraph agent + 3 tools | ✅ | Manual ReAct loop với Groq Llama 3.3 70B (do langgraph có bug typo) |
| 6 | Day 6 sáng — Citation format JD ACBS | ✅ | `[BCTC TCB - Trang 47]`, `[Báo cáo ACBS HPG - Trang 2]`, ... |
| 7 | Day 6 chiều — 5 file Thông tư nội bộ | ✅ | TT-01 đến TT-05, integrate vào ChromaDB (6487 → 6514 chunks) |
| 8 | **Day 7a — FastAPI backend + ngrok** | ✅ | **Vừa xong hôm nay 09/05** |
| 9 | Day 7b — Next.js frontend | ⏳ | Bước tiếp theo |
| 10 | Day 7b — Dockerize + Deploy HF Spaces + Vercel | ⏳ | URL vĩnh viễn cuối cùng |

(Đã skip RAGAS evaluation vì decided không cần thiết cho portfolio.)

---

## 3. Cấu trúc file

```
D:\14 days challenge\4\
├── data\
│   ├── *.pdf                    40 PDF gốc
│   ├── parsed\                  80 file Baidu OCR (40 .md + 40 .json)
│   ├── internal_procedures\     5 file Thông tư nội bộ giả lập
│   │   ├── TT-01-Quy-trinh-phan-tich-co-phieu-ngan-hang.md
│   │   ├── TT-02-Quy-trinh-phan-tich-co-phieu-bat-dong-san.md
│   │   ├── TT-03-Quy-trinh-dinh-gia-DCF.md
│   │   ├── TT-04-Tieu-chuan-khuyen-nghi-MUA-BAN-NAM-GIU.md
│   │   └── TT-05-Template-bao-cao-cap-nhat-nhanh.md
│   └── chunks.jsonl             6514 chunks (BCTC + procedure), 7.5MB
├── chromadb\                    78MB vector DB persistent
│   ├── chroma.sqlite3
│   └── <collection-uuid>\
├── src\
│   ├── chunk_demo.py            Demo chunking trên 1 file HPG
│   ├── chunk_all.py             Chunk 40 file BCTC từ JSON Baidu
│   ├── acbs_chunk.py            Chunk 5 file thông tư MD, append vào chunks.jsonl
│   ├── Embedding+ChromaDB.ipynb 7 cells: load + embed + upsert + 2 test
│   └── LangGraph_Agents.ipynb   7+ cells: load state + tools + agent + FastAPI + ngrok
└── 75%Project2.md               File này
```

---

## 4. Stack công nghệ chốt

| Layer | Công nghệ | Lý do chọn |
|---|---|---|
| OCR | Baidu PaddleOCR-VL-1.5 (web) | Tiếng Việt + bảng số liệu chính xác >98% |
| Chunking | Python (regex + langchain-text-splitters) | Table giữ nguyên, text split 500 token |
| Embedding | AITeamVN/Vietnamese_Embedding (568M) | Best Vietnamese embedding 2026, cần prefix E5 |
| Sparse retrieval | rank_bm25 | Bắt chính xác mã ticker (VCB, HPG, VNM...) |
| Vector DB | ChromaDB persistent (file-based) | Không cần Docker, gọn cho demo |
| LLM | Groq Llama 3.3 70B | Free 30 RPM, fast (LPU), Vietnamese OK |
| Agent | LangGraph create_react_agent | Match JD ACBS (modern agent framework) |
| Backend | FastAPI + uvicorn | Nhẹ, async, OpenAPI auto-docs |
| Tunnel (dev) | ngrok | Public URL miễn phí cho test từ máy local |

---

## 5. Cách restart pipeline (nếu Colab disconnect)

### Notebook 1 — `Embedding+ChromaDB.ipynb` (chỉ chạy lại khi data thay đổi)
1. Mount Drive
2. Load `chunks.jsonl` từ `/content/drive/MyDrive/chunks.jsonl`
3. Load model + embed all chunks (3-5 phút trên GPU T4)
4. Upsert ChromaDB → save folder sang Drive

### Notebook 2 — `LangGraph_Agents.ipynb` (chạy mỗi session)
1. Mount Drive + install deps
2. Load chunks + ChromaDB từ Drive (~30s)
3. Load embedding model
4. Setup BM25 + ticker map + hybrid_search
5. Define 3 tools + Groq client + format_citation
6. Build LangGraph agent với SYSTEM prompt
7. Test queries (nếu muốn verify)
8. **Cell FastAPI + ngrok** — start server background, expose URL public

---

## 6. Bí mật cần lưu (Colab Secrets)

| Secret name | Lấy ở đâu | Dùng để |
|---|---|---|
| `GROQ_API_KEY` | https://console.groq.com/keys | LLM agent + tools |
| `NGROK_AUTH_TOKEN` | https://dashboard.ngrok.com/get-started/your-authtoken | Tunnel public URL |

---

## 7. Test endpoint từ PowerShell máy local

```powershell
# Health check
curl.exe -H "ngrok-skip-browser-warning: any" https://<ngrok-url>/health

# Chat
'{"query":"Vốn chủ sở hữu của HPG cuối Q1/2026 là bao nhiêu?"}' | Out-File -FilePath body.json -Encoding utf8

curl.exe -X POST "https://<ngrok-url>/chat" `
  -H "Content-Type: application/json" `
  -H "ngrok-skip-browser-warning: any" `
  --data-binary "@body.json"
```

Response:
```json
{
  "answer": "Vốn chủ sở hữu của HPG vào cuối Q1/2026 là 139.781.792.206.472 VND 【BCTC HPG - Trang 5】.",
  "citations": [],
  "tools_used": ["extract_financial_metrics"]
}
```

⚠️ Lưu ý citation array đang trống vì Llama hay dùng `【】` (Chinese brackets) thay vì `[]`. Sẽ fix ở Bước 4 Day 7b: normalize `【】` → `[]` trước khi regex extract.

---

## 8. Vấn đề đã gặp + cách fix (lessons learned)

| Vấn đề | Root cause | Fix |
|---|---|---|
| PaddleOCR local OOM | RAM 8GB không đủ cho model 1.4GB + render PDF | Chuyển sang Colab GPU |
| PaddleOCR tiếng Việt thiếu dấu | Latin model mobile không phủ hết diacritic | Bỏ PaddleOCR, dùng Baidu web service (PaddleOCR-VL multimodal) |
| Gemini API rate limit + ban project | Free tier hết quota nhanh | Switch sang Groq Llama 3.3 70B |
| `langchain-groq` typo bug `contentt` | Bug nội tại langchain version mới | Dùng `langchain-openai` trỏ vào Groq endpoint (OpenAI-compatible) |
| Embedding sim score thấp 3/10 đúng | E5 model cần prefix `passage:`/`query:` | Re-embed với prefix → 19/20 đúng |
| Hybrid retrieval không phân biệt mã CK | Embedding không discriminate ticker | Thêm BM25 + ticker boost trong RRF |
| ChromaDB "no such table tenants" | pre-created empty dir confused chromadb | Bỏ `os.makedirs`, để chromadb tự init schema |
| ngrok ERR_NGROK_6024 | Free tier hiện trang warning | Header `ngrok-skip-browser-warning: any` |
| PowerShell `curl` lỗi `-X` | Alias của Invoke-WebRequest | Dùng `curl.exe` (real curl) |

---

## 9. Còn lại — Day 7b (1.5 ngày)

| Bước | Task | Time |
|---|---|---|
| 2 | Next.js skeleton (TypeScript + Tailwind) | ~3h |
| 3 | Build chat UI: input + message list + fetch ngrok URL | ~3h |
| 4 | Citation badge inline (fix regex `【】` → `[]`) | ~1h |
| 5 | Streaming response (SSE) | ~2h |
| 6 | Dockerize FastAPI | ~2h |
| 7 | Deploy: HF Spaces (BE) + Vercel (FE) | ~3h |
| + | Viết case study Markdown cho GitHub | ~1h |

**Final URL kỳ vọng:** `https://acbs-rag.vercel.app` → đính kèm CV ACBS.

---

## 10. Tóm 1 câu

**Đã build được toàn bộ "bộ não" RAG agent + wrap thành FastAPI service, test thành công qua PowerShell terminal. Còn 1.5 ngày cho UI Next.js + deploy production.**
