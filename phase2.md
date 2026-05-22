# Phase 2 — Day 7b: UI Next.js + Dockerize + Deploy production

**Ngày:** 2026-05-20 (sinh nhật em)
**Tiếp nối:** Sau quãng nghỉ 11 ngày, restart từ trạng thái 75% (file `75%Project2.md`)
**Kết quả:** Project 2 deploy production hoàn chỉnh — 8/8 milestone done

---

## 0. Bối cảnh khi bắt đầu

Trạng thái trước hôm nay (theo `75%Project2.md` ngày 09/05):
- ✅ Day 5: OCR 40 PDF + 6487 chunks BCTC + Hybrid retrieval (19/20 top-1)
- ✅ Day 6: LangGraph agent + 3 tools + citation format + 5 Thông tư nội bộ (6514 chunks)
- ✅ Day 7a: FastAPI + ngrok (chạy trong Colab notebook)
- ⏳ Day 7b: Next.js UI + Dockerize + Deploy HF + Vercel

Quãng nghỉ 11 ngày → Colab session disconnect → ngrok URL chết → cần restart.

---

## 1. URLs final (sau khi hoàn thành)

| Layer | URL | Host |
|---|---|---|
| **Frontend** | https://project2-delta-lake.vercel.app/ | Vercel |
| **Backend** | https://lovingtk5-acbs-rag-agent.hf.space/ | Hugging Face Spaces |
| **Backend Docs** | https://lovingtk5-acbs-rag-agent.hf.space/docs | (Swagger UI auto-gen) |
| **Source code** | https://github.com/thanhkien2005/Project2 | GitHub |
| **HF Space repo** | https://huggingface.co/spaces/lovingTK5/acbs-rag-agent | HF |

---

## 2. Architecture cuối

```
┌──────────────────────────────────────────────────────────────┐
│  Browser (Chrome/Firefox)                                    │
└──────────────────────────────────────────────────────────────┘
                          ↓ truy cập URL
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND — Next.js 16 + TypeScript + Tailwind               │
│  Host: Vercel (CDN toàn cầu, auto-deploy từ GitHub)          │
│  URL: project2-delta-lake.vercel.app                         │
│  Việc: chat UI, fetch backend, render citation               │
└──────────────────────────────────────────────────────────────┘
                          ↓ fetch HTTPS POST /chat
┌──────────────────────────────────────────────────────────────┐
│  BACKEND — Python FastAPI + LangGraph + ChromaDB             │
│  Host: HF Spaces (Docker, 16GB RAM, 2 vCPU free)             │
│  URL: lovingtk5-acbs-rag-agent.hf.space                      │
│  Việc: hybrid search → tool call → Groq LLM → JSON answer    │
└──────────────────────────────────────────────────────────────┘
                          ↓ HTTPS API call
┌──────────────────────────────────────────────────────────────┐
│  GROQ — openai/gpt-oss-120b (LPU inference)                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Timeline các bước (theo thứ tự đã làm)

### Step 1 — Restart backend ngrok (verify Day 7a còn sống)

**Mục tiêu:** Confirm endpoint Day 7a hoạt động trước khi xây frontend.

Quy trình:
1. Mở Colab → `LangGraph_Agents.ipynb` → bật GPU T4
2. Chạy lần lượt 9 cell (mount Drive → install → load chunks → embed model → ChromaDB → BM25 → tools → agent → FastAPI+ngrok)
3. Cell cuối in URL: `https://countable-skied-turban.ngrok-free.dev`

**Pitfall gặp:** PowerShell `curl` ≠ real curl
- `curl` trong PowerShell là alias của `Invoke-WebRequest`, KHÔNG hiểu flag `-H`, `-X`, `-d`
- Response status 200 nhưng body là ngrok warning page (`ERR_NGROK_6024`) chứ không phải JSON FastAPI
- **Fix:** Dùng `curl.exe` (real binary) hoặc `Invoke-RestMethod` native PowerShell

Lệnh test đúng:
```powershell
curl.exe -H "ngrok-skip-browser-warning: any" https://<URL>/health

'{"query":"..."}' | Out-File body.json -Encoding utf8
curl.exe -X POST "https://<URL>/chat" `
  -H "Content-Type: application/json" `
  -H "ngrok-skip-browser-warning: any" `
  --data-binary "@body.json"
```

Kết quả: `/health` OK, `/chat` trả full JSON với citation `[BCTC HPG - Trang 5]`.

---

### Step 2 — Next.js skeleton

**Mục tiêu:** Tạo project Next.js 16 + TypeScript + Tailwind trong folder `frontend/`.

**Pre-check:** Node.js ≥ 18 (`node -v` → v24.14.0 OK).

Lệnh chạy:
```powershell
cd "D:\14 days challenge\4\frontend"
npx create-next-app@latest . --typescript --tailwind --eslint --app `
  --no-src-dir --import-alias "@/*" --use-npm
```

Verify: `npm run dev` → trang Next.js mặc định hiện ở `http://localhost:3000`.

---

### Step 3 — Build chat UI + fetch ngrok backend

**Mục tiêu:** Chat UI 2 file (1 env + 1 page).

**File 1:** `frontend/.env.local`
```
NEXT_PUBLIC_API_URL=https://countable-skied-turban.ngrok-free.dev
```
- Prefix `NEXT_PUBLIC_` bắt buộc để client-side đọc được
- `.env.local` mặc định trong `.gitignore` → không leak khi push

**File 2:** `frontend/app/page.tsx`
- Client component với `useState` cho messages, input, loading
- `fetch(API_URL + "/chat")` với header `ngrok-skip-browser-warning`
- UI: header + scrollable message list + textarea + Send button
- Citation hiển thị badge màu vàng (`bg-amber-100`)
- Tools_used dòng nhỏ phía dưới
- Auto-scroll xuống khi có message mới
- Enter để gửi, Shift+Enter xuống dòng

Restart dev server (vì đổi `.env.local`):
```powershell
Ctrl+C
npm run dev
```

**Pitfall gặp:** Tailwind globals + dark-mode hệ thống → textarea text màu trắng khó nhìn.
- **Fix:**
  1. Xoá block `@media (prefers-color-scheme: dark) { ... }` trong `app/globals.css`
  2. Thêm `text-gray-900 bg-white placeholder:text-gray-400` vào className textarea

Test 3 query thành công:
- `Vốn chủ sở hữu của HPG cuối Q1/2026 là bao nhiêu?` → 139.781.792.206.472 VND [BCTC HPG - Trang 5]
- `So sánh ROE của VCB và TCB` → multi-tool compare_companies
- `Quy trình phân tích cổ phiếu ngân hàng theo ACBS` → retrieve_document

Quan sát: Llama tự dùng `[]` thay vì `【】` → **Bước 4 fix citation regex được SKIP**.

---

### Step 4 — Decision: SKIP streaming SSE

**Câu hỏi em:** "SSE streaming có tác dụng gì không?"

**Phân tích trade-off:**

| Khía cạnh | Có streaming | Không streaming |
|---|---|---|
| Answer correctness | Y hệt | Y hệt |
| Citation | Y hệt | Y hệt |
| UX | Chữ chảy ra 1-2s, "professional" | Đợi 8-12s rồi block văn bản |
| Effort | +200 LOC backend refactor + 80 LOC frontend, ~2h | 0 |
| Risk khi deploy | Cao (SSE qua HF Spaces có quirk) | Thấp |

**Quyết định: SKIP** — 3 lý do:
1. Đã trễ 13 ngày sau deadline ban đầu 2026-05-07
2. Recruiter ACBS đánh giá correctness + engineering, không phải animation
3. Case study Markdown signal mạnh hơn nhiều so với 2h streaming

→ Sang thẳng Bước 6 (Dockerize).

---

### Step 5 — Refactor notebook → `backend/app.py` module

**Mục tiêu:** Đóng gói toàn bộ logic notebook thành 1 file Python chạy độc lập.

Folder structure mới:
```
D:\14 days challenge\4\backend\
├── app.py              # Refactor từ notebook, 280 LOC
├── requirements.txt    # Pin versions chính xác
├── Dockerfile          # HF Spaces compatible
├── .dockerignore
└── data/
    ├── chunks.jsonl    # 6514 chunks
    └── chromadb/       # 78MB vector DB persistent
```

**`app.py` cấu trúc:**
- Config (env vars: DATA_DIR, GROQ_API_KEY, LLM_MODEL, EMBED_DEVICE)
- Load chunks + embedding model + ChromaDB + BM25 (executed at import time)
- TICKER_NAMES dict (32 mã VN30)
- `expand_query`, `extract_ticker`, `hybrid_search` (BM25+Dense+RRF+ticker boost)
- `strip_html_for_llm`, `format_citation`
- LLM: `ChatOpenAI` trỏ Groq endpoint `https://api.groq.com/openai/v1`
- 3 tools: `retrieve_document`, `extract_financial_metrics`, `compare_companies`
- LangGraph agent: `create_react_agent(llm, tools, prompt=SYSTEM)`
- FastAPI app: `GET /`, `GET /health`, `POST /chat`
- CORS middleware allow `*`
- Citation regex extract từ answer cuối

**Quan trọng:** Cập nhật vs file `75%Project2.md` cũ:
- LLM hiện tại: `openai/gpt-oss-120b` (KHÔNG phải Llama 3.3 70B như file cũ ghi)
- Agent: `langgraph.prebuilt.create_react_agent` (KHÔNG phải manual ReAct loop)

**Lệnh copy data:**
```powershell
cd "D:\14 days challenge\4\backend"
mkdir data
Copy-Item "..\data\chunks.jsonl" ".\data\"
Copy-Item "..\chromadb" ".\data\chromadb" -Recurse
```

---

### Step 6 — Dockerfile + build local

**`Dockerfile` structure:**
```dockerfile
FROM python:3.12-slim
RUN apt-get install build-essential git
RUN useradd -m -u 1000 user      # HF Spaces yêu cầu non-root
USER user
ENV HF_HOME=/home/user/.cache/huggingface PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt . && pip install -r requirements.txt
RUN python -c "SentenceTransformer('AITeamVN/Vietnamese_Embedding', ...)"  # Pre-download 1.4GB
COPY app.py . && COPY data/ /app/data/
EXPOSE 7860                       # HF Spaces required port
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

**Pitfall 1: Docker daemon chưa chạy**
```
ERROR: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```
- **Fix:** Mở Docker Desktop GUI từ Start Menu, đợi tray icon chuyển "Engine running"
- Verify bằng `docker info`

**Pitfall 2: pip resolver conflict**
```
ERROR: ResolutionImpossible
The conflict is caused by:
    The user requested langchain-core==1.0.1
    langchain-openai 0.3.0 depends on langchain-core<0.4.0  ← XUNG ĐỘT
```
- Root cause: pin chính xác từng patch version → mỗi package có constraint chéo
- **Fix:** Nới pin sang range major: `langchain-openai>=1.0,<2.0`

**Pitfall 3: ChromaDB version mismatch**
```
KeyError: '_type'
File ".../chromadb/api/configuration.py", line 209, in from_json
```
- Root cause: Colab dùng `chromadb==1.5.9`, container đang pin `chromadb==0.5.20` → schema persistent khác → không đọc được
- **Fix:** Check version Colab bằng `!pip show chromadb` → pin chính xác `chromadb==1.5.9` trong `requirements.txt`
- Phải pin các package khác trong cùng cluster:
  - `sentence-transformers==5.4.1`
  - `langgraph==1.1.9`
  - `langchain==1.2.15`

**Lệnh build + test:**
```powershell
cd "D:\14 days challenge\4\backend"
docker build -t acbs-rag-backend .                # ~10-15 phút lần đầu
docker run -d --name acbs-rag -p 7860:7860 `
  -e GROQ_API_KEY="<KEY_MỚI>" acbs-rag-backend
docker logs acbs-rag                              # check "Application startup complete"
```

Browser test: `http://localhost:7860/docs` → Swagger UI → Try `/chat` → JSON response OK.

**⚠️ Bài học bảo mật:** Em từng paste GROQ key thật vào chat → phải revoke ngay tại https://console.groq.com/keys, tạo key mới. Lúc deploy lên HF Spaces dùng **HF Secrets** chứ không hardcode.

---

### Step 7 — Deploy HF Spaces (backend)

**Phase 7.1 — Chuẩn bị:**
1. Tạo HF account → username `lovingTK5`
2. Settings → Access Tokens → New token, type **Write**, copy `hf_...`
3. https://huggingface.co/new-space:
   - Name: `acbs-rag-agent`
   - SDK: **Docker → Blank**
   - Hardware: `CPU basic (free)`
   - Visibility: **Public**
4. Tab Settings của Space → Variables and secrets → New secret `GROQ_API_KEY` = key mới

**Phase 7.2 — Push code qua Git LFS:**

ChromaDB folder có `chroma.sqlite3` ~50-70MB + index `.bin` ~20MB → cần Git LFS.

```powershell
# Cài Git LFS 1 lần
winget install -e --id GitHub.GitLFS
git lfs install

# Clone Space repo
cd "D:\14 days challenge\4"
git clone https://huggingface.co/spaces/lovingTK5/acbs-rag-agent hf-space
cd hf-space

# Setup LFS tracking
git lfs track "*.sqlite3"
git lfs track "*.bin"

# Copy files từ backend/
Copy-Item ..\backend\app.py .
Copy-Item ..\backend\Dockerfile .
Copy-Item ..\backend\requirements.txt .
Copy-Item ..\backend\.dockerignore .
Copy-Item ..\backend\data -Recurse -Destination .\data

# Push
git add .
git commit -m "Deploy ACBS RAG Agent backend"
git push                                          # Upload 81MB LFS files
```

Sau push, HF Space tự build (~15-20 phút trên CPU yếu). Theo dõi tab Logs.

**Verify:**
- `https://lovingtk5-acbs-rag-agent.hf.space/health` → JSON `{"status":"ok","chunks":6514,"collection_count":6514}` ✅
- `https://lovingtk5-acbs-rag-agent.hf.space/docs` → Swagger UI ✅
- `POST /chat` qua Swagger → answer + citation OK ✅

---

### Step 8 — Update frontend trỏ HF backend

Đổi `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=https://lovingtk5-acbs-rag-agent.hf.space
```

Restart dev server. Test query → fetch HF Space → answer OK với citation đầy đủ. CORS không lỗi (CORSMiddleware allow `*` đã có sẵn trong `app.py`).

---

### Step 9 — Push frontend lên GitHub

```powershell
cd "D:\14 days challenge\4\frontend"
git init && git branch -M main
git add .                                         # .env.local đã trong .gitignore
git commit -m "Initial: ACBS RAG agent frontend (Next.js 16 + TS + Tailwind)"
git remote add origin https://github.com/thanhkien2005/Project2.git
git push -u origin main
```

GitHub Personal Access Token cần scope `repo`.

Verify trên GitHub repo: có đủ `app/`, `package.json`, `tsconfig.json`, `tailwind.config.ts`. KHÔNG có `.env.local` (đã bị `.gitignore` exclude).

---

### Step 10 — Deploy Vercel (frontend)

1. https://vercel.com/new → Import Git Repository → chọn `thanhkien2005/Project2`
2. Configure:
   - Project Name: `acbs-rag-frontend` (đổi từ "project2")
   - Framework Preset: Next.js (auto-detect)
   - Build/Output/Install: để trống (mặc định)
3. **Environment Variables (QUAN TRỌNG):**
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://lovingtk5-acbs-rag-agent.hf.space`
   - Environment: **Production and Preview** (chọn cái đầu tiên trong 4 option)
4. Click Deploy → đợi ~2-3 phút

URL final: `https://project2-delta-lake.vercel.app/`

**Test 2 query thực tế:**

| Query | Tool | Kết quả |
|---|---|---|
| Vốn điều lệ VCB cuối Q1/2026 | extract_financial_metrics | 83.556.750.940.000 đồng [BCTC VCB - Trang 12] |
| So sánh vốn điều lệ TCB và ACB | compare_companies | TCB 70,862 tỷ vs ACB 51,367 tỷ (+38%) |

→ Đáp án đúng cả về business — VCB Big4 vốn lớn nhất, TCB > ACB sau giai đoạn tăng vốn 2024-2026.

---

## 4. Tổng hợp các pitfall + fix

| # | Vấn đề | Root cause | Fix |
|---|---|---|---|
| 1 | PowerShell `curl` lỗi với header/POST | Alias của `Invoke-WebRequest`, không phải real curl | Dùng `curl.exe` (real binary) |
| 2 | Tailwind textarea chữ trắng khó nhìn | Globals.css có `@media dark` → body inherit color sáng | Xoá block dark, thêm explicit `text-gray-900 bg-white` |
| 3 | Docker daemon not running | Docker Desktop GUI chưa start | Mở app Docker Desktop, đợi "Engine running" |
| 4 | pip ResolutionImpossible | Pin patch chính xác → constraint chéo | Nới pin sang range major (`>=1.0,<2.0`) |
| 5 | ChromaDB KeyError `_type` | Persistent format mismatch (0.5.x vs 1.x) | Pin chính xác chromadb==1.5.9 giống Colab |
| 6 | curl body parse error với tiếng Việt có dấu | Encoding shell PowerShell nuốt UTF-8 | Ghi body ra file → `--data-binary @file` |
| 7 | GROQ key lộ trong chat conversation | Paste key thật khi `docker run -e GROQ_API_KEY=...` | Revoke key cũ, tạo key mới, dùng HF Secrets cho production |

---

## 5. Stack công nghệ cuối

| Layer | Công nghệ | Version pin |
|---|---|---|
| Frontend framework | Next.js | 16.2.6 (Turbopack) |
| Frontend language | TypeScript | latest |
| Frontend styling | Tailwind CSS | 4.x |
| Frontend host | Vercel | free hobby tier |
| Backend framework | FastAPI | >=0.115 |
| Backend language | Python | 3.12-slim |
| Agent framework | LangGraph | 1.1.9 |
| LangChain | langchain | 1.2.15 |
| LLM client | langchain-openai | >=1.0 (trỏ Groq) |
| LLM model | Groq `openai/gpt-oss-120b` | inference LPU |
| Embedding | AITeamVN/Vietnamese_Embedding | 568M params, dim 1024 |
| Embedding lib | sentence-transformers | 5.4.1 |
| Vector DB | ChromaDB | 1.5.9 (persistent) |
| Sparse retrieval | rank-bm25 | 0.2.2 |
| Container | Docker | 29.4.1 (Desktop) |
| Container host | HF Spaces | Docker SDK, 16GB RAM, 2 vCPU free |
| Code repo | GitHub | thanhkien2005/Project2 |

---

## 6. Decision rationale (cho phỏng vấn ACBS)

| Quyết định | Lý do |
|---|---|
| Tách 2-tier (Vercel + HF Spaces) | Bảo mật API key, scale độc lập, mỗi platform tối ưu cho 1 stack |
| Chọn Next.js thay Streamlit | JD ACBS yêu cầu TypeScript skill, Next.js show được FE engineering |
| Chọn HF Spaces thay Railway/Render | Free tier 16GB RAM phù hợp embedding model 1.4GB, có sẵn HF cache |
| Skip streaming SSE | Cosmetic, không thay đổi correctness, dành effort cho deploy ổn định |
| Skip RAGAS evaluation | Đã có metric 19/20 top-1 đủ chứng minh quality, RAGAS over-engineering cho portfolio |
| Hybrid retrieval BM25+Dense+RRF | BM25 đơn lẻ kém với câu định tính, Dense đơn lẻ không phân biệt ticker → kết hợp + ticker boost |
| Pre-download model trong Dockerfile | Tránh runtime download chậm + fail nếu HF rate-limit |
| Single uvicorn worker | Data + model load 1 lần ở import time, multi-worker sẽ duplicate RAM |

---

## 7. Còn lại

Em đã quyết định để Project 3 ưu tiên hơn:

1. ⏳ **Project 3** — Stock Forecasting VN30 (vnstock + LightGBM/LSTM)
2. ⏳ **README case study** cho GitHub repo `thanhkien2005/Project2` — viết Markdown ~200 dòng, có:
   - Live demo URL + screenshots
   - Problem statement match JD ACBS
   - Architecture diagram
   - Tech stack rationale
   - Engineering decisions
   - Retrieval benchmark
   - Lessons learned
   - How to run locally
3. ⏳ **Video demo** quay UI thật + giải thích bằng giọng
4. ⏳ Đính URL + repo vào CV ACBS

---

## 8. Thời gian thực tế

- Plan ban đầu (file 75%): 1.5 ngày cho Day 7b
- Thực tế: **1 ngày** (2026-05-20, từ sáng đến tối)
- Lý do nhanh hơn plan: skip Bước 4 (citation đã đúng) + skip Bước 5 (streaming)

---

## 9. Tóm 1 câu

**Đã đẩy được toàn bộ Project 2 từ "notebook Colab + ngrok tạm" sang "production 2-tier: Vercel + HF Spaces, có URL vĩnh viễn gắn CV". Test 2 query nghiệp vụ ACBS (vốn điều lệ + so sánh) đúng cả về kết quả và format citation theo JD.**
