"""ACBS RAG Agent — FastAPI module for production deployment.

Refactor từ LangGraph_Agents.ipynb sang Python module standalone, dùng cho
Docker / HF Spaces. Single-worker uvicorn vì data + model load 1 lần lúc start.
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

import chromadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


# ============================================================================
# Config
# ============================================================================
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
CHUNKS_FILE = DATA_DIR / "chunks.jsonl"
CHROMADB_DIR = DATA_DIR / "chromadb"
COLLECTION_NAME = "bctc_acbs"
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEVICE = os.getenv("EMBED_DEVICE", "cpu")


# ============================================================================
# Data + model load (executed at import time)
# ============================================================================
print(f"[1/4] Loading chunks from {CHUNKS_FILE}...", flush=True)
with CHUNKS_FILE.open(encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]
print(f"      Loaded {len(chunks)} chunks", flush=True)

print(f"[2/4] Loading embedding model: {EMBEDDING_MODEL} (device={DEVICE})...", flush=True)
embed_model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True, device=DEVICE)
print(f"      Embedding dim: {embed_model.get_sentence_embedding_dimension()}", flush=True)

print(f"[3/4] Loading ChromaDB from {CHROMADB_DIR}...", flush=True)
chroma_client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
)
print(f"      Collection count: {collection.count()}", flush=True)

print("[4/4] Indexing BM25...", flush=True)
VN_CHARS = "a-z0-9àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
TOKEN_RE = re.compile(f"[{VN_CHARS}]+")
HTML_RE = re.compile(r"<[^>]+>")


def tokenize(text: str) -> list:
    text = HTML_RE.sub(" ", text).lower()
    return TOKEN_RE.findall(text)


corpus_tokens = [tokenize(c["text"] + " " + c["source"]) for c in chunks]
bm25 = BM25Okapi(corpus_tokens)
print(f"      BM25 indexed {len(corpus_tokens)} chunks", flush=True)


# ============================================================================
# Ticker map + hybrid retrieval
# ============================================================================
TICKER_NAMES = {
    "HPG": ["hòa phát", "hoa phat"], "VCB": ["vietcombank"],
    "VNM": ["vinamilk"], "VHC": ["vĩnh hoàn", "vinh hoan"],
    "VHM": ["vinhomes"], "VIC": ["vingroup"], "VRE": ["vincom retail"],
    "FPT": ["fpt"], "BID": ["bidv"], "CTG": ["vietinbank"],
    "TCB": ["techcombank"], "MBB": ["mb bank", "mbbank"],
    "STB": ["sacombank"], "VPB": ["vpbank"], "HDB": ["hdbank"],
    "VIB": ["vib"], "TPB": ["tpbank"], "LPB": ["lpbank"],
    "SSB": ["seabank"], "ACB": ["acb"], "BVH": ["bảo việt", "bao viet"],
    "GAS": ["pv gas"], "PLX": ["petrolimex"], "POW": ["pv power"],
    "GVR": ["cao su"], "DGC": ["đức giang"], "MSN": ["masan"],
    "NVL": ["novaland"], "PDR": ["phát đạt"], "KDH": ["khang điền"],
    "SAB": ["sabeco"], "BCM": ["becamex"],
}


def expand_query(q: str) -> str:
    q_low = q.lower()
    extra = [t for t, names in TICKER_NAMES.items()
             if any(n in q_low for n in names) and t.lower() not in q_low]
    return q + (" " + " ".join(extra) if extra else "")


def extract_ticker(query: str):
    q_low = query.lower()
    for ticker in TICKER_NAMES:
        if re.search(rf"\b{ticker.lower()}\b", q_low):
            return ticker
    for ticker, names in TICKER_NAMES.items():
        if any(n in q_low for n in names):
            return ticker
    return None


def hybrid_search(query: str, top_k: int = 3, k_rrf: int = 60,
                  candidates: int = 20, source_boost: float = 2.0):
    expanded = expand_query(query)
    ticker = extract_ticker(query)

    bm25_scores = bm25.get_scores(tokenize(expanded))
    bm25_top = sorted(range(len(bm25_scores)), key=lambda i: -bm25_scores[i])[:candidates]

    q_emb = embed_model.encode(
        [f"query: {expanded}"], normalize_embeddings=True, convert_to_numpy=True
    )
    dense_res = collection.query(query_embeddings=q_emb.tolist(), n_results=candidates)
    dense_top = [int(id_.rsplit("_", 1)[-1]) for id_ in dense_res["ids"][0]]

    rrf = defaultdict(float)

    def add(rank: int, idx: int):
        s = 1.0 / (k_rrf + rank)
        if ticker and ticker.upper() in chunks[idx]["source"].upper():
            s *= source_boost
        rrf[idx] += s

    for rank, idx in enumerate(bm25_top):
        add(rank, idx)
    for rank, idx in enumerate(dense_top):
        add(rank, idx)

    return sorted(rrf.items(), key=lambda x: -x[1])[:top_k]


# ============================================================================
# LLM + helpers
# ============================================================================
def strip_html_for_llm(text: str) -> str:
    text = re.sub(r"</tr>\s*<tr[^>]*>", "\n", text)
    text = re.sub(r"</td>\s*<td[^>]*>", " | ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def format_citation(source: str, page: int) -> str:
    if len(source) <= 4 and source.isupper() and source.isalpha():
        return f"[BCTC {source} - Trang {page}]"
    if source.startswith("ACBS_"):
        parts = source.split("_")
        if len(parts) >= 2:
            return f"[Báo cáo ACBS {parts[1]} - Trang {page}]"
    if source.startswith("BSC_"):
        m = re.search(r"BSC_(\w+?)-(\d{2})(\d{2})-", source)
        if m:
            kind, dd, mm = m.group(1), m.group(2), m.group(3)
            return f"[BSC {kind} {dd}/{mm}/2026 - Trang {page}]"
        return f"[Báo cáo BSC - Trang {page}]"
    if source.startswith("VCSC_"):
        m = re.match(r"VCSC_(\d{4})(\d{2})(\d{2})_DailyVN", source)
        if m:
            yyyy, mm, dd = m.group(1), m.group(2), m.group(3)
            return f"[VCSC Daily {dd}/{mm}/{yyyy} - Trang {page}]"
        m2 = re.match(r"VCSC_(\w+)-", source)
        if m2:
            return f"[Báo cáo VCSC {m2.group(1).upper()} - Trang {page}]"
        return f"[Báo cáo VCSC - Trang {page}]"
    return f"[{source} - Trang {page}]"


llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
    temperature=0,
)


def call_llm(prompt: str) -> str:
    resp = llm.invoke(prompt)
    return resp.content


# ============================================================================
# Tools (3 tools y hệt notebook)
# ============================================================================
@tool
def retrieve_document(query: str, top_k: int = 5) -> str:
    """Tìm thông tin tổng quát trong vector DB"""
    results = hybrid_search(query, top_k=top_k)
    parts = []
    for idx, _ in results:
        c = chunks[idx]
        readable = strip_html_for_llm(c["text"])[:1500]
        citation = format_citation(c["source"], c["page"])
        parts.append(f"{citation}\n{readable}")
    return "\n\n---\n\n".join(parts)


@tool
def extract_financial_metrics(company_ticker: str, metric: str) -> str:
    """Trích 1 KPI của 1 công ty từ BCTC"""
    query = f"{metric} của {company_ticker} Q1/2026"
    results = hybrid_search(query, top_k=5)
    relevant = [
        chunks[idx] for idx, _ in results
        if company_ticker.upper() in chunks[idx]["source"].upper()
    ]
    if not relevant:
        return f"Không tìm thấy chunks của {company_ticker} cho '{metric}'"

    context = "\n\n".join(
        f"{format_citation(c['source'], c['page'])}\n{strip_html_for_llm(c['text'])[:1200]}"
        for c in relevant[:3]
    )
    prompt = f"""Trích CHÍNH XÁC giá trị "{metric}" của công ty {company_ticker} từ context.

CONTEXT:
{context}

Format trả lời (1 dòng):
{metric} của {company_ticker} = <giá trị> <đơn vị> <citation>

Trong đó <citation> COPY NGUYÊN VĂN từ context, vd "[BCTC TCB - Trang 47]" hoặc "[Báo cáo ACBS HPG - Trang 2]".

Nếu không tìm thấy: "Không tìm thấy {metric} của {company_ticker}"."""
    return call_llm(prompt)


@tool
def compare_companies(ticker_a: str, ticker_b: str, metric: str) -> str:
    """So sánh MỘT chỉ tiêu tài chính giữa HAI công ty.
    Dùng khi user hỏi 'So sánh X và Y về Z' hoặc 'X hay Y có Z lớn hơn'.
    Tự gọi extract_financial_metrics cho cả 2 cty rồi tổng hợp."""
    val_a = extract_financial_metrics.invoke({"company_ticker": ticker_a, "metric": metric})
    val_b = extract_financial_metrics.invoke({"company_ticker": ticker_b, "metric": metric})
    prompt = f"""Dựa vào 2 dữ liệu sau, so sánh "{metric}" giữa {ticker_a} và {ticker_b}.

Dữ liệu {ticker_a}: {val_a}
Dữ liệu {ticker_b}: {val_b}

Trả lời ngắn gọn (3-4 câu), nêu rõ:
- Cty nào có {metric} lớn hơn
- Chênh lệch tuyệt đối + % chênh lệch
- Giữ nguyên citation [Chunk N] từ dữ liệu gốc"""
    return call_llm(prompt)


# ============================================================================
# Agent
# ============================================================================
SYSTEM = """Bạn là chuyên gia phân tích tài chính của ACBS, hỗ trợ trả lời câu hỏi về 30 cổ phiếu VN30 và các báo cáo phân tích ACBS/BSC/VCSC Q1/2026.

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
5. Trả lời bằng tiếng Việt, ngắn gọn, chuyên nghiệp."""

tools_list = [retrieve_document, extract_financial_metrics, compare_companies]
agent = create_react_agent(llm, tools_list, prompt=SYSTEM)
print("Agent ready.", flush=True)


# ============================================================================
# FastAPI app
# ============================================================================
app = FastAPI(title="ACBS RAG Agent", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    citations: list
    tools_used: list


CITATION_RE = re.compile(
    r"\[(?:BCTC [^\]]+|Báo cáo ACBS [^\]]+|BSC \w+ \d+/\d+/\d+ - Trang \d+|"
    r"VCSC Daily \d+/\d+/\d+ - Trang \d+|Báo cáo VCSC [^\]]+|"
    r"Thông tư TT-\d+[^\]]*)\]"
)


@app.get("/")
def root():
    return {"service": "ACBS RAG Agent", "endpoints": ["/health", "/chat"]}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "chunks": len(chunks),
        "collection_count": collection.count(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = agent.invoke({"messages": [("user", req.query)]})
    tools_used = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls") and msg.tool_calls
        for tc in msg.tool_calls
    ]
    final_answer = result["messages"][-1].content
    citations = sorted(set(m.group(0) for m in CITATION_RE.finditer(final_answer)))
    return ChatResponse(
        answer=final_answer,
        citations=citations,
        tools_used=tools_used,
    )
