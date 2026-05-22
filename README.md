# 🤖 ACBS RAG Agent — Báo cáo Tài chính Việt Nam

> **End-to-end Retrieval-Augmented Generation system** cho phân tích Báo cáo Tài chính (BCTC) và báo cáo phân tích VN30. Crawl 40 PDF → OCR → Chunk → Embed → Hybrid Retrieval → LangGraph Agent với 3 tool + citation chuẩn ACBS.

[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.9-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5.9-F09433)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20gpt--oss--120b-F55036)](https://groq.com/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?logo=vercel&logoColor=white)](https://vercel.com/)
[![HF Spaces](https://img.shields.io/badge/Backend-HF%20Spaces-FFD21E?logo=huggingface)](https://huggingface.co/spaces)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## 🌐 Live Demo

### 🎥 Video walkthrough

<!-- DEMO_VIDEO_URL -->
> *Video demo sẽ được embed tại đây sau khi upload (placeholder).*

### 🔗 Live services

| Layer | URL | Host |
|---|---|---|
| 💬 **Chat UI** | https://project2-delta-lake.vercel.app/ | Vercel |
| ⚙️ **Backend API** | https://lovingtk5-acbs-rag-agent.hf.space/ | Hugging Face Spaces |
| 📑 **Swagger Docs** | https://lovingtk5-acbs-rag-agent.hf.space/docs | Auto-generated |
| 📦 **Source code** | https://github.com/thanhkien2005/Project2 | GitHub |
| 🤗 **HF Space repo** | https://huggingface.co/spaces/lovingTK5/acbs-rag-agent | HF |

---

## 🎯 TL;DR

RAG Agent chuyên biệt phân tích BCTC và báo cáo VN30, **match 1-1 với JD ACBS AI Engineer** ("trả kết quả tìm kiếm bao gồm citation, các bước và template theo quy trình nội bộ"):

- **OCR** 40 PDF (32 BCTC + 5 ACBS + 3 BSC + 3 VCSC) qua **PaddleOCR** trên https://aistudio.baidu.com/paddleocr
- **Chunk** tách `text` và `table` riêng → 6514 chunks (BCTC 6487 + thông tư nội bộ 27)
- **Embed** bằng `AITeamVN/Vietnamese_Embedding` (568M params, dim 1024)
- **Retrieval** hybrid: BM25 + Dense + RRF (Reciprocal Rank Fusion) + ticker source boost
- **Agent** LangGraph ReAct với 3 tool: `retrieve_document`, `extract_financial_metrics`, `compare_companies`
- **LLM** Groq `openai/gpt-oss-120b` (LPU inference, latency ~1s)
- **Citation** chuẩn ACBS: `[BCTC HPG - Trang 5]`, `[Báo cáo ACBS VCB Q1/2026 - Trang 2]`
- **Deploy** 2-tier: Frontend Next.js trên Vercel + Backend Docker trên HF Spaces
- **Retrieval metric**: top-1 hit **19/20** trên test set 20 câu hỏi mẫu

---

## 🏗️ Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER (Browser)                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTPS — Vercel CDN edge
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FRONTEND — Next.js 16 + TypeScript + Tailwind CSS                      │
│  Host: Vercel (Hobby, free, global CDN)                                 │
│  URL : project2-delta-lake.vercel.app                                   │
│                                                                         │
│  ─ app/page.tsx     : Chat UI (useState messages, fetch backend)        │
│  ─ Auto-scroll, Enter to send, Shift+Enter newline                      │
│  ─ Citation badge màu vàng + tools_used inline                          │
│  ─ Env var NEXT_PUBLIC_API_URL → backend HF Spaces                      │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTPS POST /chat
                                  │ {"query": "..."}
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND — FastAPI + LangGraph (Docker container)                       │
│  Host: Hugging Face Spaces (CPU basic, 16GB RAM, 2 vCPU, free)          │
│  URL : lovingtk5-acbs-rag-agent.hf.space                                │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  1. Request validation (Pydantic ChatRequest)                    │   │
│  │     ↓                                                            │   │
│  │  2. LangGraph ReAct Agent (create_react_agent)                   │   │
│  │     ┌─────────────────────────────────────────────────────┐      │   │
│  │     │  System prompt → quy tắc chọn tool + format citation │     │   │
│  │     ▼                                                     │      │   │
│  │     LLM (Groq) ──→ chọn tool ──→ gọi tool ──→ tổng hợp    │      │   │
│  │                  ↑                ↓                       │      │   │
│  │                  └─── loop ◄──────┘ (multi-step ReAct)    │      │   │
│  │     └─────────────────────────────────────────────────────┘      │   │
│  │     ↓                                                            │   │
│  │  3. Citation regex extract ──→ ChatResponse(answer, citations)   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  3 tools sẵn có cho Agent:                                              │
│    • retrieve_document(query, top_k)                                    │
│    • extract_financial_metrics(ticker, metric)                          │
│    • compare_companies(ticker_a, ticker_b, metric)                      │
└─────────────────────────────────────────────────────────────────────────┘
            │                            │                      │
            │ embedding query            │ keyword search       │ LLM call
            ▼                            ▼                      ▼
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────┐
│  DENSE RETRIEVAL     │   │  SPARSE RETRIEVAL    │   │  GROQ LLM        │
│                      │   │                      │   │                  │
│  AITeamVN/           │   │  rank-bm25 0.2.2     │   │  Model:          │
│  Vietnamese_         │   │                      │   │  openai/         │
│  Embedding           │   │  Tokenize text       │   │  gpt-oss-120b    │
│  (568M params,       │   │  với regex tiếng     │   │                  │
│   dim 1024)          │   │  Việt có dấu         │   │  LPU inference   │
│                      │   │                      │   │  ~1s latency     │
│  ChromaDB persistent │   │  BM25Okapi(k1=1.5,   │   │  Temperature=0   │
│  cosine similarity   │   │           b=0.75)    │   │                  │
└──────────────────────┘   └──────────────────────┘   └──────────────────┘
            │                            │
            └────────────┬───────────────┘
                         ▼
            ┌─────────────────────────────┐
            │  Reciprocal Rank Fusion     │
            │  + Ticker source boost 2.0x │
            │  → top_k chunks             │
            └─────────────────────────────┘
                         ▲
                         │ retrieve from
                         │
            ┌─────────────────────────────────────────────────────┐
            │  KNOWLEDGE BASE — 6514 chunks                       │
            │                                                     │
            │  • 6487 BCTC + analyst reports (text + table)       │
            │  • 27 thông tư nội bộ ACBS (5 file markdown)        │
            │                                                     │
            │  Storage: ChromaDB persistent (~78MB sqlite + bin)  │
            │  Metadata: source, page, block_type, block_id       │
            └─────────────────────────────────────────────────────┘
```

**Triết lý kiến trúc — 2-tier separation**:
- **Vercel** chuyên frontend (CDN edge, auto SSL, GitHub auto-deploy) → tối ưu UX
- **HF Spaces** chuyên backend (Docker 16GB RAM cho embedding model 1.4GB, có HF cache pre-warm) → tối ưu inference

Tách 2 tier giúp: bảo mật API key (Groq key chỉ tồn tại trên HF Secrets), scale độc lập, mỗi platform tối ưu cho stack tương ứng.

---

## 🛠️ Tech Stack

| Layer | Công nghệ | Version | Lý do chọn |
|---|---|---|---|
| **Frontend framework** | Next.js | 16.2.6 (Turbopack) | JD ACBS yêu cầu TypeScript, Next.js show được FE engineering |
| Frontend language | TypeScript | latest | Strict typing, match JD |
| Frontend styling | Tailwind CSS | 4.x | Utility-first, dev tốc độ cao |
| Frontend host | Vercel | Hobby free | CDN toàn cầu, auto deploy từ GitHub, free tier rộng |
| **Backend framework** | FastAPI | >=0.115 | Auto OpenAPI, validation Pydantic, async-ready |
| Backend language | Python | 3.12-slim | Stable, ML libs đầy đủ |
| **Agent framework** | LangGraph | 1.1.9 | Production-grade ReAct, state machine rõ ràng |
| LangChain | langchain | 1.2.15 | Tool calling ecosystem |
| LLM client | langchain-openai | >=1.0 | OpenAI-compatible API, trỏ Groq endpoint |
| **LLM** | Groq `openai/gpt-oss-120b` | LPU inference | Tốc độ ~1s/response, free tier rộng, không cần GPU |
| **Embedding model** | AITeamVN/Vietnamese_Embedding | 568M params, dim 1024 | SOTA Vietnamese embedding, MTEB top |
| Embedding lib | sentence-transformers | 5.4.1 | Standard API, cache tốt |
| **Vector DB** | ChromaDB | 1.5.9 | Persistent, simple API, đủ cho 6500 chunks |
| **Sparse retrieval** | rank-bm25 | 0.2.2 | BM25Okapi, lightweight, không cần ES |
| **OCR** | PaddleOCR-VL | Aistudio Baidu | Best-in-class cho mixed text + table layout |
| **Container** | Docker | 29.4.1 | Reproducible build, HF Spaces native support |
| **Container host** | HF Spaces | Docker SDK | 16GB RAM free, có HF cache pre-warm, IPv6 OK |
| Code repo | GitHub | thanhkien2005/Project2 | Public, sync với Vercel |

---

## 💾 Data Pipeline — Chi tiết từng bước

### 1. Nguồn dữ liệu (40 PDF, ~250MB)

| Nhóm | Số file | Nội dung | Mục đích trong agent |
|---|---|---|---|
| **BCTC VN30** | 32 | Báo cáo Tài chính Q1/2026 của 30 mã VN30 (HPG, VCB, VNM, FPT, ACB, MBB, TCB, ...) | Tra số liệu KPI: Vốn điều lệ, LNST, ROE, NIM, NPL |
| **ACBS Reports** | 5 | Cập nhật nhanh AGM của ACBS (HPG, MSN, DPM) | Văn phong + nhận định analyst |
| **BSC Brief/Morning** | 3 | Báo cáo sáng + nhận định ngành | Tin tức vĩ mô + thông tin ngành |
| **VCSC Daily** | 3 | Báo cáo phân tích DailyVN | So sánh phong cách analyst |
| **Internal Procedures** | 5 (markdown) | 5 thông tư nội bộ ACBS giả lập (TT-01 → TT-05) | Trả lời câu hỏi quy trình nội bộ |

Tổng cộng: **40 PDF + 5 markdown** = nguồn knowledge base.

### 2. OCR — PaddleOCR-VL trên Aistudio Baidu

> ⚠️ **OCR pipeline chạy trên web https://aistudio.baidu.com/paddleocr** — không tự host local. Lý do:
> - PaddleOCR-VL là SOTA cho **mixed text + table layout** (BCTC có nhiều bảng số)
> - Aistudio cung cấp **GPU free** + UI batch upload tiện
> - Output JSON có sẵn `block_label` (text / table / title / image) + `block_bbox` (vị trí trong trang) → đủ metadata cho chunking sau này

**Quy trình**:
1. Upload từng PDF lên Aistudio PaddleOCR
2. Chọn mode `Layout Analysis + Recognition` → giữ structure HTML cho bảng
3. Download output JSON về `data/parsed/{FILENAME}.json`
4. Mỗi file JSON là list các page, mỗi page có `prunedResult.parsing_res_list` chứa blocks

**Cấu trúc 1 block**:
```json
{
  "block_label": "table",          // text | table | title | image
  "block_content": "<table>...</table>",   // HTML cho bảng, plain text cho text
  "block_id": "p1_b3",
  "block_bbox": [x0, y0, x1, y1]   // toạ độ
}
```

→ Lý do dùng PaddleOCR thay vì `pymupdf` / `pdfplumber`: BCTC tiếng Việt có **bảng số liệu phức tạp** (merged cells, multi-header). PaddleOCR-VL output HTML giữ được structure bảng, pymupdf chỉ trả plain text → mất context bảng.

### 3. Chunking — Tách `text` và `table` riêng (`src/chunk_all.py`)

**Strategy 2-stream**:

| Block type | Strategy | Lý do |
|---|---|---|
| `text` | Gom các block text liên tiếp → RecursiveCharacterTextSplitter (chunk_size=2000, overlap=200) | Giữ context dài, splitter ưu tiên cắt theo `\n\n` → `\n` → `. ` → ` ` |
| `table` | Mỗi table = 1 chunk (hoặc split bảng dài giữ header) | Giữ nguyên cấu trúc HTML để LLM parse cells, không cắt giữa rows |

**Pseudo-code logic**:
```python
for page in pdf_pages:
    text_buf = []
    for block in page.blocks:
        if block.label == "table":
            flush(text_buf)              # flush text buffer trước
            for part in split_table(block):
                chunks.append({"text": part, "block_type": "table", ...})
        else:
            text_buf.append(clean(block.content))
    flush(text_buf)                      # flush phần text cuối page
```

**Cleaners cho text** (loại noise OCR):
- Remove `<img/>`, empty `<div></div>`, `<div>...</div>` wrapper
- Collapse whitespace `\s+` → ` `

**Cleaners cho table** (giữ HTML structure):
- Remove inline `style="..."`, `border="..."`
- Giữ `<table>`, `<tr>`, `<td>`, `<th>` để LLM parse

**Split bảng dài** (giữ header):
```python
def split_table(html, max_chars=1800):
    header_row = rows[0]
    for row in rows[1:]:
        if current_size + len(row) > max_chars:
            parts.append(header + current_chunk + </table>)
            current_chunk = [header_row, row]   # bảng kế tiếp giữ lại header
```

→ Đảm bảo mỗi chunk bảng đều có header → LLM hiểu được context cột.

### 4. 5 thông tư nội bộ ACBS (`data/internal_procedures/`)

Để **match yêu cầu JD** "Trả kết quả tìm kiếm bao gồm các bước và template thực hiện theo quy trình nội bộ", em tự viết 5 thông tư markdown mô phỏng văn bản nội bộ ACBS:

| File | Nội dung |
|---|---|
| `TT-01-Quy-trinh-phan-tich-co-phieu-ngan-hang.md` | 7 bước phân tích ngân hàng: KQKD → NIM → CAR → CIR → NPL/LLR → LDR → Định giá P/B |
| `TT-02-Quy-trinh-phan-tich-co-phieu-bat-dong-san.md` | Quy trình phân tích BĐS: hàng tồn kho, doanh thu chưa ghi nhận, gross margin |
| `TT-03-Quy-trinh-dinh-gia-DCF.md` | Discounted Cash Flow, WACC, terminal value |
| `TT-04-Tieu-chuan-khuyen-nghi-MUA-BAN-NAM-GIU.md` | Tiêu chuẩn BUY/HOLD/SELL theo upside potential |
| `TT-05-Template-bao-cao-cap-nhat-nhanh.md` | Template chuẩn cho báo cáo cập nhật nhanh |

Chunking riêng cho markdown (`src/acbs_chunk.py`):
- Split theo header `###` (mỗi section = 1 chunk)
- Prepend `[Thông tư TT-XX — <title>]` vào đầu chunk → giúp retrieval semantic match khi user hỏi "quy trình ACBS"

### 5. Embedding — `AITeamVN/Vietnamese_Embedding`

| Spec | Value |
|---|---|
| Model | AITeamVN/Vietnamese_Embedding |
| Params | 568M |
| Embedding dim | 1024 |
| Tokenizer | XLM-RoBERTa base |
| Max seq length | 8192 tokens |
| Pre-training | Trên ~30GB corpus tiếng Việt (báo, wiki, sách) |
| MTEB rank | Top Vietnamese embedding tại thời điểm release |

**Tại sao chọn model này** (so với multilingual options):
- `BAAI/bge-m3` — multilingual nhưng underperform trên domain finance VN
- `paraphrase-multilingual-mpnet-base-v2` — chỉ 384 dim, mất sắc thái
- `intfloat/multilingual-e5-large` — tốt nhưng không pre-train sâu trên VN
- `AITeamVN/Vietnamese_Embedding` ⭐ — pre-train sâu trên VN, 1024 dim đủ rộng, format prefix `"query: "` / `"passage: "` chuẩn E5-style

**Encoding pattern**:
```python
# At index time
embeddings = model.encode([f"passage: {chunk}" for chunk in chunks])

# At query time
query_emb = model.encode([f"query: {user_query}"], normalize_embeddings=True)
```

Prefix `query:` vs `passage:` là **convention của E5/Vietnamese_Embedding** — model được train với 2 mode khác nhau, dùng đúng prefix tăng đáng kể retrieval quality.

### 6. ChromaDB persistent

```python
client = chromadb.PersistentClient(path="./chromadb")
collection = client.get_or_create_collection(
    name="bctc_acbs",
    metadata={"hnsw:space": "cosine"}   # cosine similarity (không phải L2)
)

collection.add(
    ids=[f"chunk_{i}" for i in range(len(chunks))],
    embeddings=embeddings.tolist(),
    documents=[c["text"] for c in chunks],
    metadatas=[{"source": c["source"], "page": c["page"], ...} for c in chunks],
)
```

- **Cosine similarity** thay L2: cosine không sensitive với norm của vector → ổn định hơn cho embedding đã normalize.
- **Persistent**: lưu trên disk, không cần re-embed mỗi lần restart container.
- **Size**: 78MB cho 6514 chunks dim 1024 → fit thoải mái trong HF Space 16GB RAM.

---

## 🔍 Retrieval Engine — Hybrid Search

### Tổng quan: tại sao Hybrid?

Single-mode retrieval có điểm yếu rõ:

| Mode | Mạnh | Yếu |
|---|---|---|
| **BM25** (sparse) | Exact match keyword (ticker "HPG", "ROE"), không cần training | Không hiểu paraphrase ("vốn chủ" vs "equity"), miss semantic |
| **Dense** (embedding) | Hiểu semantic, paraphrase, đa ngôn ngữ | Có thể miss exact ticker, đôi khi "halucinate" similarity |
| **Hybrid (RRF)** | Tận dụng cả 2 | Complexity cao hơn, 2x compute |

→ Em chọn **Hybrid với Reciprocal Rank Fusion** vì BCTC vừa có keyword cứng (ticker, KPI) vừa có ngữ cảnh paraphrase.

### Pipeline retrieval

```
user query: "Vốn chủ sở hữu của HPG cuối Q1/2026 là bao nhiêu?"
   │
   ├─► Query expansion (thêm "hòa phát" nếu thấy "HPG", và ngược lại)
   │   → "Vốn chủ sở hữu của HPG cuối Q1/2026 là bao nhiêu? hòa phát"
   │
   ├─► Ticker extraction → ticker = "HPG"
   │
   ├─► BM25 search top 20 candidates
   │   tokenize tiếng Việt (regex giữ dấu) → bm25.get_scores()
   │
   ├─► Dense search top 20 candidates
   │   embed query với prefix "query: " → ChromaDB collection.query()
   │
   ├─► Reciprocal Rank Fusion
   │   score[doc] = Σ 1/(k + rank_in_each_list)   với k=60
   │
   ├─► Ticker source boost
   │   nếu chunk.source chứa "HPG" → score *= 2.0
   │
   └─► sort by RRF score → return top_k=3 chunks
```

### Code RRF + ticker boost

```python
def hybrid_search(query, top_k=3, k_rrf=60, candidates=20, source_boost=2.0):
    expanded = expand_query(query)
    ticker = extract_ticker(query)

    # Sparse
    bm25_scores = bm25.get_scores(tokenize(expanded))
    bm25_top = sorted(range(len(bm25_scores)), key=lambda i: -bm25_scores[i])[:candidates]

    # Dense
    q_emb = embed_model.encode([f"query: {expanded}"], normalize_embeddings=True)
    dense_res = collection.query(query_embeddings=q_emb.tolist(), n_results=candidates)
    dense_top = [int(id_.rsplit("_", 1)[-1]) for id_ in dense_res["ids"][0]]

    # RRF + ticker boost
    rrf = defaultdict(float)
    def add(rank, idx):
        s = 1.0 / (k_rrf + rank)
        if ticker and ticker.upper() in chunks[idx]["source"].upper():
            s *= source_boost
        rrf[idx] += s

    for rank, idx in enumerate(bm25_top): add(rank, idx)
    for rank, idx in enumerate(dense_top): add(rank, idx)

    return sorted(rrf.items(), key=lambda x: -x[1])[:top_k]
```

### Decision rationale các hyperparam

| Param | Value | Lý do |
|---|---|---|
| `k_rrf=60` | RRF chuẩn Cormack et al. 2009 | Đã prove trong nhiều benchmark, không cần tune |
| `candidates=20` | Lấy top 20 mỗi mode | Đủ wide để bù miss, không quá rộng làm RRF noise |
| `source_boost=2.0` | Nhân 2 khi ticker match source | Empirical: 1.5 quá nhẹ, 3.0 over-boost làm miss bảng so sánh đa cty |
| `top_k=3` | Trả 3 chunks cho LLM | Đủ context, không exceed token limit Groq |

### Query expansion — vì sao cần

Người dùng có thể hỏi 2 cách:
- "Vốn chủ HPG" → BM25 match ticker, embedding match "vốn chủ"
- "Vốn chủ Hòa Phát" → BM25 miss ticker, embedding may match

Em build `TICKER_NAMES` dict ánh xạ 32 mã VN30 → tên thường gọi:
```python
TICKER_NAMES = {
    "HPG": ["hòa phát", "hoa phat"],
    "VCB": ["vietcombank"],
    "TCB": ["techcombank"],
    ...
}
```

Hàm `expand_query`: nếu user gõ "Hòa Phát" → tự thêm "HPG" vào query → BM25 hit luôn. Ngược lại "HPG" → thêm "hòa phát" → dense embedding match nhiều passages hơn.

---

## 🎭 Agent Architecture — LangGraph ReAct với 3 Tool

### Tổng quan

Em dùng `langgraph.prebuilt.create_react_agent` thay vì manual ReAct loop vì:
- Production-grade: handle multi-turn tool calls, error retry, state persistence
- Built-in support cho `langchain.tools.tool` decorator
- Tích hợp tốt với ChatOpenAI (Groq endpoint)

### System prompt

```
Bạn là chuyên gia phân tích tài chính của ACBS, hỗ trợ trả lời câu hỏi về
30 cổ phiếu VN30 và các báo cáo phân tích ACBS/BSC/VCSC Q1/2026.

Quy tắc:
1. Phân loại câu hỏi để chọn tool đúng:
   - Câu hỏi tổng quát/định tính → retrieve_document
   - Hỏi 1 KPI cụ thể của 1 cty → extract_financial_metrics
   - So sánh 2 cty về 1 chỉ tiêu → compare_companies
2. Mỗi câu trả lời PHẢI có citation theo ĐÚNG format trong tool output, ví dụ:
   - [BCTC TCB - Trang 47]
   - [Báo cáo ACBS HPG - Trang 2]
   - [BSC Morning 05/05/2026 - Trang 1]
   - [VCSC Daily 04/05/2026 - Trang 8]
   COPY NGUYÊN VĂN citation từ context, KHÔNG đổi format.
3. Câu so sánh 2 cty: phải có 2 citation từ 2 BCTC khác nhau.
4. KHÔNG bịa số liệu. Nếu tool trả "Không tìm thấy", nói rõ với user.
5. Trả lời bằng tiếng Việt, ngắn gọn, chuyên nghiệp.
```

### Tool 1 — `retrieve_document(query, top_k=5)`

**Khi nào dùng**: câu hỏi tổng quát, định tính, không rõ ticker.

**Ví dụ query**:
- "Quy trình phân tích cổ phiếu ngân hàng theo ACBS"
- "Tình hình ngành thép Việt Nam Q1/2026"
- "Tiêu chuẩn khuyến nghị MUA của ACBS"

**Pseudo**:
```python
results = hybrid_search(query, top_k=5)
return "\n\n---\n\n".join(
    f"{format_citation(c.source, c.page)}\n{strip_html(c.text)[:1500]}"
    for c in results
)
```

### Tool 2 — `extract_financial_metrics(company_ticker, metric)`

**Khi nào dùng**: hỏi 1 KPI cụ thể của 1 công ty.

**Ví dụ query**:
- "Vốn chủ sở hữu của HPG Q1/2026"
- "ROE của VCB cuối quý"
- "NIM của TCB so với cùng kỳ năm trước"

**Pseudo**:
```python
query = f"{metric} của {ticker} Q1/2026"
results = hybrid_search(query, top_k=5)
relevant = [c for c in results if ticker in c.source]   # filter chunks đúng cty

prompt = f"""Trích CHÍNH XÁC giá trị "{metric}" của công ty {ticker} từ context.
CONTEXT: {context}
Format: {metric} của {ticker} = <giá trị> <đơn vị> <citation>
Citation COPY NGUYÊN VĂN từ context."""
return llm.invoke(prompt)
```

**Note**: tool này filter `ticker in chunk.source` → đảm bảo không lấy nhầm chunk của cty khác (dù retrieval rank cao).

### Tool 3 — `compare_companies(ticker_a, ticker_b, metric)`

**Khi nào dùng**: so sánh 2 cty về 1 chỉ tiêu.

**Ví dụ query**:
- "So sánh ROE của VCB và TCB"
- "Vốn điều lệ TCB hay ACB lớn hơn?"

**Pseudo** (tự gọi tool 2 cho cả 2 cty):
```python
val_a = extract_financial_metrics.invoke({"company_ticker": ticker_a, "metric": metric})
val_b = extract_financial_metrics.invoke({"company_ticker": ticker_b, "metric": metric})

prompt = f"""So sánh "{metric}" giữa {ticker_a} và {ticker_b}.
Dữ liệu {ticker_a}: {val_a}
Dữ liệu {ticker_b}: {val_b}

Trả lời 3-4 câu, nêu rõ cty nào lớn hơn, chênh lệch tuyệt đối + %, giữ 2 citation."""
return llm.invoke(prompt)
```

---

## 📑 Citation Format — Chuẩn ACBS

Mỗi answer Agent trả về phải kèm citation theo format chuẩn để recruiter ACBS thấy rõ "trả kết quả tìm kiếm bao gồm các viện dẫn" như JD yêu cầu:

| Loại source | Format citation | Ví dụ |
|---|---|---|
| BCTC niêm yết | `[BCTC <TICKER> - Trang <N>]` | `[BCTC HPG - Trang 5]` |
| Báo cáo phân tích ACBS | `[Báo cáo ACBS <TICKER> - Trang <N>]` | `[Báo cáo ACBS VCB - Trang 2]` |
| BSC Brief/Morning | `[BSC <Kind> <DD/MM/YYYY> - Trang <N>]` | `[BSC Morning 05/05/2026 - Trang 1]` |
| VCSC Daily | `[VCSC Daily <DD/MM/YYYY> - Trang <N>]` | `[VCSC Daily 04/05/2026 - Trang 8]` |
| VCSC ticker report | `[Báo cáo VCSC <TICKER> - Trang <N>]` | `[Báo cáo VCSC VHC - Trang 3]` |
| Thông tư nội bộ | `[Thông tư TT-<XX>]` | `[Thông tư TT-01]` |

**Implementation** (`format_citation()` trong `backend/app.py`):
```python
def format_citation(source: str, page: int) -> str:
    if len(source) <= 4 and source.isupper() and source.isalpha():
        return f"[BCTC {source} - Trang {page}]"
    if source.startswith("ACBS_"):
        return f"[Báo cáo ACBS {source.split('_')[1]} - Trang {page}]"
    if source.startswith("BSC_"):
        m = re.search(r"BSC_(\w+?)-(\d{2})(\d{2})-", source)
        if m:
            return f"[BSC {m.group(1)} {m.group(2)}/{m.group(3)}/2026 - Trang {page}]"
    # ...
```

**Citation extraction** (regex sau khi agent trả lời):
```python
CITATION_RE = re.compile(
    r"\[(?:BCTC [^\]]+|Báo cáo ACBS [^\]]+|BSC \w+ \d+/\d+/\d+ - Trang \d+|"
    r"VCSC Daily \d+/\d+/\d+ - Trang \d+|Báo cáo VCSC [^\]]+|"
    r"Thông tư TT-\d+[^\]]*)\]"
)

citations = sorted(set(m.group(0) for m in CITATION_RE.finditer(final_answer)))
```

→ Trả về `ChatResponse(answer=..., citations=[...], tools_used=[...])`. Frontend render `citations` thành badge màu vàng dưới message.

---

## 📊 Retrieval Benchmark

Em test trên 20 câu hỏi mẫu (mix 3 loại tool):

| Loại câu hỏi | Số câu | Top-1 hit | Top-3 hit |
|---|---|---|---|
| Định tính (retrieve_document) | 7 | 6/7 | 7/7 |
| KPI cụ thể (extract_financial_metrics) | 8 | 8/8 | 8/8 |
| So sánh 2 cty (compare_companies) | 5 | 5/5 | 5/5 |
| **Tổng** | **20** | **19/20 = 95%** | **20/20 = 100%** |

**Câu miss**: "Tiêu chuẩn khuyến nghị MUA của ACBS" → top-1 trả chunk Tổng quan TT-04 thay vì section 3.1 Tiêu chuẩn (rank 2). Acceptable vì top-3 vẫn có đúng chunk.

→ **Hybrid + ticker boost cải thiện đáng kể** so với baseline:
- BM25-only: top-1 14/20 (70%)
- Dense-only: top-1 16/20 (80%)
- Hybrid + RRF + ticker boost: top-1 19/20 (**95%**)

---

## 🎨 Frontend — Next.js 16

### Cấu trúc

```
frontend/
├── app/
│   ├── page.tsx       # Chat UI (Client Component)
│   ├── layout.tsx     # Root layout
│   └── globals.css    # Tailwind base + font fix
├── public/            # Static assets
├── package.json       # Next 16.2.6, React 19, Tailwind 4
└── .env.local         # NEXT_PUBLIC_API_URL → backend HF Spaces
```

### Features

| Feature | Implementation |
|---|---|
| Chat messages | `useState<Message[]>` với roles user/assistant |
| Citations | Badge màu vàng (`bg-amber-100`) dưới message |
| Tools used | Dòng nhỏ italic dưới citations |
| Auto-scroll | `useEffect` + `bottomRef.scrollIntoView` |
| Enter to send | `onKeyDown` check `e.key === "Enter" && !e.shiftKey` |
| Loading state | Disable textarea + Send button khi đang gọi API |
| Error handling | Try-catch fetch, show error message inline |

### Env var trick

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
```

- Prefix `NEXT_PUBLIC_` bắt buộc để client-side đọc được
- Default `""` để build không fail nếu env chưa set
- `.env.local` mặc định trong `.gitignore` → không leak khi push

### Deploy Vercel

1. Connect GitHub repo `thanhkien2005/Project2`
2. Root directory: `frontend/`
3. Environment variable: `NEXT_PUBLIC_API_URL=https://lovingtk5-acbs-rag-agent.hf.space`
4. Click Deploy → URL `project2-delta-lake.vercel.app` sau ~2 phút

---

## 🚀 Backend Deployment — HF Spaces Docker

### Dockerfile (xem `backend/Dockerfile`)

```dockerfile
FROM python:3.12-slim

RUN apt-get install -y build-essential git

# HF Spaces yêu cầu non-root user uid 1000
RUN useradd -m -u 1000 user
USER user

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model (~1.4GB) → tránh runtime download
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('AITeamVN/Vietnamese_Embedding', trust_remote_code=True)"

COPY app.py .
COPY data/ /app/data/         # chunks.jsonl + chromadb

EXPOSE 7860                    # HF Spaces required port
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

**Decision rationale**:
- `python:3.12-slim` thay full Python: tiết kiệm 800MB image
- `build-essential` cho `sentence-transformers` cần C++ compile (tokenizers)
- Pre-download model trong RUN: tránh download chậm + fail nếu HF rate-limit tại runtime
- `EXPOSE 7860`: HF Spaces force port 7860, không thay được
- `user uid 1000`: HF Spaces force non-root cho security

### Deploy quy trình

1. Tạo HF Space mới: SDK `Docker → Blank`, hardware `CPU basic (free)`
2. Setup HF Secret: `GROQ_API_KEY=gsk_...` (KHÔNG hardcode vào code)
3. Git LFS track `*.sqlite3`, `*.bin` (file chromadb ~70MB+)
4. Clone HF Space repo, copy code + data → push → HF tự build (~15-20 phút trên CPU yếu)

### Production patterns

| Pattern | Code | Lý do |
|---|---|---|
| Load model 1 lần lúc import | `embed_model = SentenceTransformer(...)` ở top-level | Tránh re-load mỗi request (1.4GB) |
| Single worker uvicorn | `uvicorn app:app --workers 1` mặc định | Multi-worker duplicate RAM, không scale được trên 16GB |
| CORS allow `*` | `CORSMiddleware(allow_origins=["*"])` | Cho phép Vercel frontend gọi được |
| HF Secrets cho API key | `os.environ["GROQ_API_KEY"]` | Không leak key trong code/logs |

---

## 🐛 Bugs Encountered & Lessons

### Bug 1 — PowerShell `curl` không phải real curl

**Triệu chứng**: Test API qua `curl -X POST ...` → response status 200 nhưng body là HTML ngrok warning page (`ERR_NGROK_6024`), không phải JSON FastAPI.

**Root cause**: PowerShell `curl` là alias của `Invoke-WebRequest`, KHÔNG hiểu flag `-H`, `-X`, `-d`.

**Fix**: Dùng `curl.exe` (real binary trong `C:\Windows\System32\curl.exe`):
```powershell
curl.exe -H "ngrok-skip-browser-warning: any" https://<URL>/health
```

**Lesson**: Trên Windows, gõ `curl --version` để verify đang dùng curl.exe vs alias.

### Bug 2 — Tailwind textarea chữ trắng khó nhìn

**Triệu chứng**: Textarea trong dark mode hệ thống → text màu trắng trên background trắng → không thấy.

**Root cause**: `app/globals.css` có block `@media (prefers-color-scheme: dark) { body { color: #fff; ... } }`. Textarea inherit color từ body.

**Fix**:
1. Xoá block `@media dark` trong globals.css
2. Thêm explicit class textarea: `text-gray-900 bg-white placeholder:text-gray-400`

**Lesson**: Khi build chat UI, luôn explicit text color cho input elements để không bị system dark mode override.

### Bug 3 — Docker daemon not running

**Triệu chứng**:
```
ERROR: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

**Root cause**: Docker Desktop GUI chưa start (Windows yêu cầu app GUI chạy mới có docker engine).

**Fix**: Mở Docker Desktop từ Start Menu → đợi tray icon chuyển "Engine running" (~30s). Verify bằng `docker info`.

### Bug 4 — pip ResolutionImpossible (LangChain ecosystem)

**Triệu chứng**:
```
ERROR: ResolutionImpossible
The conflict is caused by:
    The user requested langchain-core==1.0.1
    langchain-openai 0.3.0 depends on langchain-core<0.4.0
```

**Root cause**: Pin chính xác từng patch version → constraint chéo giữa các package langchain/langgraph.

**Fix**: Nới pin sang range major:
```
langchain==1.2.15
langchain-core>=1.0,<2.0
langchain-openai>=1.0,<2.0
langgraph==1.1.9
```

**Lesson**: LangChain ecosystem update tần suất cao, pin patch dễ break. Pin minor/major thì OK.

### Bug 5 — ChromaDB version mismatch (KeyError `_type`)

**Triệu chứng**:
```
KeyError: '_type'
File ".../chromadb/api/configuration.py", line 209, in from_json
```

**Root cause**: Colab dùng `chromadb==1.5.9`, container đang pin `chromadb==0.5.20` → schema persistent khác → không load được.

**Fix**: Check version Colab bằng `!pip show chromadb` → pin chính xác trong `requirements.txt`:
```
chromadb==1.5.9
sentence-transformers==5.4.1     # cùng cluster
langgraph==1.1.9
```

**Lesson**: ChromaDB persistent format **không backward-compatible** giữa minor versions. Embed ở version nào thì load ở version đó.

### Bug 6 — curl body parse error với tiếng Việt có dấu

**Triệu chứng**: POST body có dấu tiếng Việt → server nhận corrupted bytes → Pydantic validation fail.

**Root cause**: PowerShell shell nuốt UTF-8 encoding khi pipe.

**Fix**: Ghi body ra file rồi `--data-binary @file`:
```powershell
'{"query":"Vốn chủ sở hữu của HPG"}' | Out-File body.json -Encoding utf8
curl.exe -X POST "$URL/chat" -H "Content-Type: application/json" --data-binary "@body.json"
```

**Lesson**: Khi test API có tiếng Việt, luôn dùng file body thay vì inline string.

### Bug 7 — GROQ_API_KEY lộ trong chat (incident security)

**Triệu chứng**: Em paste full GROQ key thật vào prompt chat khi hỏi cách deploy → key leak vào conversation log.

**Fix protocol**:
1. **Revoke ngay** key cũ tại https://console.groq.com/keys
2. Tạo key mới
3. Setup HF Secret `GROQ_API_KEY` (không hardcode vào Dockerfile/code)
4. Local dev: file `.env` đã gitignore + paste qua env var: `GROQ_API_KEY=xxx docker run ...`

**Lesson interview-grade**: API key handling là **first principle security**. KHÔNG paste plaintext key vào chat/issue/commit/PR. Khi accident → revoke + rotate ngay, không chần chừ.

---

## 🔮 Future Improvements

### Retrieval
- [ ] **RAGAS evaluation**: faithfulness, answer relevance, context recall metrics
- [ ] **Reranker layer** (cross-encoder) sau RRF để boost top-1 lên >97%
- [ ] **Multi-query expansion**: LLM generate 3 query variants từ user input
- [ ] **HyDE** (Hypothetical Document Embeddings) cho câu hỏi mơ hồ

### Agent
- [ ] **Streaming SSE** response token-by-token (hiện block 8-12s)
- [ ] **Conversation memory** với LangGraph checkpoint
- [ ] **Tool: `summarize_report`** — tóm tắt full BCTC theo template TT-05
- [ ] **Tool: `recommendation`** — BUY/HOLD/SELL theo tiêu chuẩn TT-04

### Data
- [ ] **OCR re-run** với newer PaddleOCR-VL version cho bảng phức tạp
- [ ] **Multi-quarter coverage**: thêm Q2/Q3/Q4 BCTC để compare trend
- [ ] **Crawl thêm**: SSI Research, VND Securities, MBS reports
- [ ] **Update internal procedures**: thêm thông tư phân tích F&B, retail, IT

### Infra
- [ ] **Persistent volume** trên HF Spaces cho chat history
- [ ] **Rate limiting** (slowapi) tránh abuse free tier
- [ ] **Observability**: log query → tool → answer pipeline qua Langfuse
- [ ] **CI/CD**: GitHub Actions chạy retrieval test set trước khi deploy

---

## 📋 Project structure

```
.
├── backend/                              # Backend FastAPI + LangGraph (deploy HF Spaces)
│   ├── app.py                            # Main module — agent + 3 tools + FastAPI
│   ├── Dockerfile                        # Python 3.12-slim, non-root, port 7860
│   ├── requirements.txt                  # Pinned: chromadb 1.5.9, langgraph 1.1.9, ...
│   ├── .dockerignore
│   └── data/
│       ├── chunks.jsonl                  # 6514 chunks (BCTC + thông tư)
│       └── chromadb/                     # Persistent vector DB ~78MB
│
├── frontend/                             # Next.js 16 chat UI (deploy Vercel)
│   ├── app/
│   │   ├── page.tsx                      # Client component, chat + citations
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── public/
│   ├── package.json                      # Next 16.2.6, React 19, Tailwind 4
│   ├── tsconfig.json
│   └── .env.local                        # NEXT_PUBLIC_API_URL (gitignored)
│
├── src/                                  # Notebooks + chunking scripts (preprocessing)
│   ├── Embedding+ChromaDB.ipynb          # Phase 1: embed chunks → ChromaDB
│   ├── LangGraph_Agents.ipynb            # Phase 2: build agent + 3 tools + FastAPI
│   ├── chunk_all.py                      # Chunk 40 PDF → chunks.jsonl
│   ├── acbs_chunk.py                     # Chunk 5 thông tư markdown, append vào chunks.jsonl
│   ├── chunk_demo.py                     # Demo chunking 1 file để verify
│   └── body.json                         # Test payload cho curl
│
├── data/                                 # Source PDFs + OCR output
│   ├── *.pdf                             # 40 PDF gốc (BCTC + ACBS + BSC + VCSC)
│   ├── parsed/                           # OCR output JSON từ PaddleOCR
│   │   ├── HPG.json
│   │   ├── HPG.md                        # Markdown preview của OCR
│   │   └── ...
│   └── internal_procedures/              # 5 thông tư markdown giả lập
│       ├── TT-01-Quy-trinh-phan-tich-co-phieu-ngan-hang.md
│       ├── TT-02-Quy-trinh-phan-tich-co-phieu-bat-dong-san.md
│       ├── TT-03-Quy-trinh-dinh-gia-DCF.md
│       ├── TT-04-Tieu-chuan-khuyen-nghi-MUA-BAN-NAM-GIU.md
│       └── TT-05-Template-bao-cao-cap-nhat-nhanh.md
│
├── hf-space/                             # HF Spaces deploy mirror (gitignored)
├── chunks.jsonl                          # Backup root copy (gitignored — duplicate)
├── 75%Project2.md                        # Work log Day 5-7a (Colab phase)
├── phase2.md                             # Work log Day 7b (Vercel + HF deploy)
├── .gitignore
└── README.md                             # File này
```

---

## 🚀 Chạy local

### Yêu cầu môi trường

- Python 3.12+
- Node.js 18+
- Docker Desktop (cho backend)
- Groq API key (free tier tại https://console.groq.com/keys)

### 1. Clone repo

```bash
git clone https://github.com/thanhkien2005/Project2.git
cd Project2
```

### 2. Backend (FastAPI + LangGraph)

#### Option A — Docker (recommend)

```bash
cd backend
docker build -t acbs-rag-backend .
docker run -d --name acbs-rag -p 7860:7860 \
  -e GROQ_API_KEY="your_groq_key_here" \
  acbs-rag-backend

# Verify
curl http://localhost:7860/health
# {"status":"ok","chunks":6514,"collection_count":6514}
```

#### Option B — Python venv

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\Activate
pip install -r requirements.txt
export GROQ_API_KEY="your_groq_key_here"
uvicorn app:app --reload --port 7860
```

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
# Tạo .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:7860" > .env.local
npm run dev
# Mở http://localhost:3000
```

### 4. (Tùy chọn) Rebuild ChromaDB từ chunks.jsonl

Nếu `backend/data/chromadb/` bị xoá hoặc cần re-embed:

```bash
# Chạy notebook src/Embedding+ChromaDB.ipynb
# Hoặc script: TBD
```

PDFs gốc không commit lên GitHub (copyright + size). Re-run OCR pipeline cần:
1. Tải lại PDFs từ website công ty (Quan hệ cổ đông tab)
2. Upload lên https://aistudio.baidu.com/paddleocr
3. Download JSON về `data/parsed/`
4. Chạy `python src/chunk_all.py && python src/acbs_chunk.py`

---

## 📚 Interview Talking Points

### Architecture decisions

**Q: Tại sao tách Vercel + HF Spaces thay vì all-in-one?**
A: 3 lý do — (1) Bảo mật API key: Groq key chỉ tồn tại trên HF Secrets, không leak trong client bundle; (2) Mỗi platform tối ưu cho stack: Vercel cho Next.js edge CDN, HF Spaces cho Python ML với cache HF cache; (3) Scale độc lập: frontend traffic spike không ảnh hưởng backend inference.

**Q: Tại sao chọn LangGraph thay vì manual ReAct loop?**
A: Production-grade: handle multi-step tool calls, error retry, state machine rõ ràng. `create_react_agent` đã optimize prompt + tool calling pattern. Manual loop dễ break khi LLM trả format khác.

**Q: Hybrid retrieval có thực sự cần thiết không?**
A: Có. Em benchmark 20 câu: BM25-only 14/20 top-1 (70%), Dense-only 16/20 (80%), Hybrid+RRF+ticker boost 19/20 (95%). BCTC vừa có keyword cứng (ticker, KPI name) vừa cần semantic match (paraphrase). Hybrid bù lẫn nhau.

### Engineering decisions

**Q: Tại sao pre-download embedding model trong Dockerfile?**
A: 2 lý do — (1) Tránh runtime download chậm (1.4GB qua mạng container ~3-5 phút); (2) Tránh build fail nếu HF rate-limit lúc cold start.

**Q: Tại sao single uvicorn worker thay vì multi-worker?**
A: Data + model load 1 lần ở import time (chunks.jsonl ~7MB + embedding model 1.4GB + ChromaDB 78MB + BM25 index). Multi-worker duplicate RAM → exceed HF Spaces 16GB. Single worker đủ vì traffic demo không cao.

**Q: ChromaDB version pin chính xác `1.5.9` — sao không loose?**
A: ChromaDB persistent format **không backward-compatible** giữa minor versions. Em embed trên Colab `1.5.9`, nếu container pin `1.5.x` → có thể tự upgrade `1.6` → fail load. Bug 5 trong README có case này.

### Domain knowledge

**Q: Citation format `[BCTC HPG - Trang 5]` — sao quan trọng?**
A: JD ACBS yêu cầu "trả kết quả tìm kiếm bao gồm các viện dẫn". Citation chuẩn cho phép user verify số liệu (mở PDF, tìm trang) → giảm risk hallucination, tăng trust. Hơn nữa, analyst ACBS cần dẫn nguồn theo quy chuẩn báo cáo nội bộ.

**Q: 5 thông tư nội bộ giả lập — recruiter có nhận ra không?**
A: Em document rõ trong README đây là **mô phỏng** (giả lập) để demo flow "trả lời theo quy trình nội bộ" — không phải tài liệu thật ACBS. Phong cách content được viết để giống văn bản nội bộ thật (có mã hiệu TT-XX, ngày ban hành, người duyệt). Recruiter thường đánh giá cao việc tự build mock data hợp lý.

**Q: PaddleOCR vs pymupdf — khác gì?**
A: pymupdf chỉ trả plain text → mất structure bảng (BCTC có nhiều bảng merged cells). PaddleOCR-VL output HTML giữ `<table>`, `<tr>`, `<td>` → LLM parse được context cột. Trade-off: PaddleOCR chậm hơn (~30s/PDF) và phải host (em dùng Aistudio Baidu free), pymupdf nhanh < 1s nhưng dữ liệu kém chất lượng cho bảng.

---

## ⚠️ Disclaimer

- 5 thông tư nội bộ là **mô phỏng giả lập**, không phải tài liệu nội bộ thật của ACBS Securities.
- BCTC + báo cáo phân tích là **dữ liệu public** trên website Quan hệ cổ đông của các công ty niêm yết và website ACBS/BSC/VCSC.
- Project được build trong sprint 14 ngày như portfolio cho vị trí AI Engineer. **Không phải investment advice**.

---

## 📄 License

MIT License — feel free to fork, adapt, learn from this project.

---

## 👤 Author

**Thanh Kiên** — Applied Math @ HCMUS, AI Engineer aspirant
- 📧 kienthinhimacs2026@gmail.com
- 🌐 GitHub: [@thanhkien2005](https://github.com/thanhkien2005)
- 🤗 HF Hub: [@lovingTK5](https://huggingface.co/lovingTK5)

> Sprint Day 5-7 của challenge 14-day apply ACBS AI Engineer (28/04 → 20/05/2026).
> Project flagship — match 1-1 với JD requirements.
