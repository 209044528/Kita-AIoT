import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import settings


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    title: str
    section: str
    content: str


def _tokens(text: str) -> list[str]:
    text = text.lower()
    ascii_tokens = re.findall(r"[a-z0-9_+-]+", text)
    chinese_tokens: list[str] = []
    for segment in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(segment) <= 6:
            chinese_tokens.append(segment)
        chinese_tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))
        chinese_tokens.extend(segment[index : index + 3] for index in range(len(segment) - 2))
    return ascii_tokens + chinese_tokens


def _split_document(path: Path) -> list[KnowledgeChunk]:
    text = path.read_text(encoding="utf-8")
    document_title = path.stem
    section = "正文"
    buffer: list[str] = []
    chunks: list[KnowledgeChunk] = []

    def flush() -> None:
        content = "\n".join(buffer).strip()
        if content:
            chunks.append(
                KnowledgeChunk(
                    source=path.name,
                    title=document_title,
                    section=section,
                    content=content,
                )
            )
        buffer.clear()

    for line in text.splitlines():
        if line.startswith("# "):
            flush()
            document_title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            section = line[3:].strip()
        else:
            buffer.append(line)
    flush()
    return chunks


@lru_cache(maxsize=1)
def load_chunks() -> tuple[KnowledgeChunk, ...]:
    root = Path(settings.KNOWLEDGE_BASE_DIR)
    if not root.is_absolute():
        root = Path.cwd() / root
    chunks: list[KnowledgeChunk] = []
    for path in sorted(root.glob("*.md")):
        chunks.extend(_split_document(path))
    return tuple(chunks)


def retrieve(question: str, top_k: int | None = None) -> list[dict]:
    query_tokens = _tokens(question)
    if not query_tokens:
        return []

    scored: list[tuple[float, KnowledgeChunk]] = []
    for chunk in load_chunks():
        title_text = f"{chunk.title} {chunk.section}".lower()
        content_tokens = _tokens(chunk.content)
        token_set = set(content_tokens)
        score = sum(2.0 for token in query_tokens if token in token_set)
        score += sum(3.0 for token in query_tokens if token in title_text)
        if score:
            score += min(len(set(query_tokens) & token_set), 8) * 0.25
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, chunk in scored[: top_k or settings.RAG_TOP_K]:
        results.append(
            {
                "source": chunk.source,
                "title": chunk.title,
                "section": chunk.section,
                "score": round(score, 2),
                "content": chunk.content[:1200],
            }
        )
    return results


def build_context(references: list[dict]) -> str:
    return "\n\n".join(
        f"[{index}] {item['title']} / {item['section']}\n{item['content']}"
        for index, item in enumerate(references, start=1)
    )


def local_answer(question: str, references: list[dict]) -> str:
    if not references:
        return "当前知识库中没有检索到足够相关的内容，请补充设备型号、告警类型或现场现象。"
    evidence = "\n".join(
        f"- {item['title']}（{item['section']}）：{item['content'][:240].strip()}"
        for item in references
    )
    return f"根据当前知识库，针对“{question}”可参考：\n{evidence}"
