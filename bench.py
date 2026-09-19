"""
Công cụ benchmark cá nhân — Lab 07 Giai đoạn 3.

Không phải bài tập chấm bằng pytest. Nó làm 4 việc:
    1. Đọc từng file .md trong data/library/, tách frontmatter (metadata) và content.
    2. Chunk phần content bằng CHUNKER bên dưới, mỗi chunk -> một Document.
    3. Nạp vào EmbeddingStore, chạy 5 câu hỏi trong gold-answer.json qua search_with_filter().
    4. In top-3 kèm score và doc_id để đối chiếu với gold answer.

Mỗi lần thử chiến lược khác chỉ đổi DÒNG gán CHUNKER bên dưới, mọi thứ khác giữ nguyên.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from src.chunking import FixedSizeChunker, HeadingChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

DATA_DIR = Path("data/library")
GOLD_ANSWERS_PATH = Path("gold-answer.json")

# --- Đổi đúng MỘT dòng này để thử chiến lược khác --------------------------
CHUNKER = HeadingChunker(chunk_size=400)
# CHUNKER = FixedSizeChunker(chunk_size=400, overlap=80)
# CHUNKER = RecursiveChunker(chunk_size=400)
# CHUNKER = SentenceChunker(max_sentences_per_chunk=3)
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
FRONTMATTER_FIELD_RE = re.compile(r'^(\w+):\s*"?([^"\n]+?)"?\s*$', re.M)


def parse_frontmatter(raw_text: str) -> tuple[dict, str]:
    """Split a .md file into (frontmatter metadata, body content)."""
    match = FRONTMATTER_RE.match(raw_text)
    if not match:
        return {}, raw_text.strip()
    frontmatter_text, body = match.groups()
    metadata = dict(FRONTMATTER_FIELD_RE.findall(frontmatter_text))
    return metadata, body.strip()


def load_documents(chunker) -> list[Document]:
    """Chunk every .md file in DATA_DIR into Documents (1 chunk = 1 Document)."""
    documents: list[Document] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw_text)
        for i, chunk_text in enumerate(chunker.chunk(body)):
            documents.append(
                Document(
                    id=f"{path.stem}#{i}",
                    content=chunk_text,
                    # doc_id trỏ về file gốc, không phải id của chunk.
                    metadata={**metadata, "doc_id": path.stem},
                )
            )
    return documents


def load_gold_queries() -> list[dict]:
    """gold-answer.json dùng cú pháp Python (True/None, chuỗi nối bằng ngoặc),
    không phải JSON thuần, nên parse bằng ast.literal_eval thay vì json.load."""
    return ast.literal_eval(GOLD_ANSWERS_PATH.read_text(encoding="utf-8"))


def make_cached_embedder(embedder: Callable[[str], list[float]]) -> Callable[[str], list[float]]:
    """Cache theo hash nội dung — chạy lại bench.py nhiều lần không tốn thêm tiền/API call."""
    cache: dict[str, list[float]] = {}

    def cached(text: str) -> list[float]:
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key not in cache:
            cache[key] = embedder(text)
        return cache[key]

    return cached


def resolve_embedder() -> tuple[Callable[[str], list[float]], str]:
    """Cùng logic fallback với main.py: chọn provider qua .env, lỗi/thiếu key thì
    quay về _mock_embed chứ không crash. Trả về (hàm embed đã cache, tên backend)."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()

    try:
        if provider == "local":
            embedder = LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        elif provider == "openai":
            embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        elif provider == "gemini":
            embedder = GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
        else:
            return _mock_embed, "mock embeddings fallback"
    except Exception:
        return _mock_embed, "mock embeddings fallback (lỗi khởi tạo provider, đã fallback)"

    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    return make_cached_embedder(embedder), backend_name


def main() -> None:
    md_files = sorted(DATA_DIR.glob("*.md"))
    documents = load_documents(CHUNKER)

    embedder, backend_name = resolve_embedder()
    store = EmbeddingStore(collection_name="bench", embedding_fn=embedder)
    store.add_documents(documents)

    print(f"Embedding backend   : {backend_name}")
    print(f"Chiến lược chunking : {type(CHUNKER).__name__}")
    print(f"Số tài liệu nguồn   : {len(md_files)}")
    print(f"Số chunk đã nạp     : {store.get_collection_size()}")
    print("=" * 78)

    queries = load_gold_queries()
    for query in queries:
        metadata_filter = query["filter"]
        results = store.search_with_filter(
            query["question"], top_k=3, metadata_filter=metadata_filter
        )

        print(f"\n[{query['id']}] {query['question']}")
        print(f"  filter={metadata_filter}  needs_filter={query['needs_filter']}")
        print(f"  gold_answer: {query['gold_answer']}")
        if not results:
            print("  (không có kết quả nào khớp filter)")
        for rank, result in enumerate(results, start=1):
            preview = " ".join(result["content"].split())[:150]
            print(
                f"  [{rank}] score={result['score']:.3f} "
                f"doc_id={result['metadata'].get('doc_id')} :: {preview}"
            )


if __name__ == "__main__":
    main()
