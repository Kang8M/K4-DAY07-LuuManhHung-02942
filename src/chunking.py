from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        stripped = text.strip()
        if not stripped:
            return []

        # Split *after* the punctuation (lookbehind) so it stays attached
        # to the sentence instead of being swallowed by the split.
        sentences = re.split(r"(?<=[.!?])\s+", stripped)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group).strip())
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []

        # Base case 1: already small enough, nothing left to do.
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 2: out of separators — fall back to a hard cut so we
        # never return a chunk longer than chunk_size.
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator, rest = remaining_separators[0], remaining_separators[1:]
        parts = list(current_text) if separator == "" else current_text.split(separator)

        # Recurse down: any part still too long gets split with the next,
        # narrower separator.
        pieces: list[str] = []
        for part in parts:
            if not part:
                continue
            if len(part) > self.chunk_size:
                pieces.extend(self._split(part, rest))
            else:
                pieces.append(part)

        # Merge up: glue adjacent small pieces back together (re-inserting
        # the separator) until they are close to chunk_size, otherwise a
        # text made of short lines/words explodes into tiny chunks.
        merged: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = buffer + separator + piece if buffer else piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    merged.append(buffer)
                buffer = piece
        if buffer:
            merged.append(buffer)
        return merged


class HeadingChunker:
    """
    Split markdown text into one chunk per heading section.

    Each markdown heading line ("#" ... "######") starts a new section that
    runs until the next heading. Regulation-style documents (`## Điều 4 —
    ...`) are already segmented into complete semantic units by whoever
    wrote them, so this mostly just respects that structure instead of
    re-discovering it.
    """

    HEADING_RE = re.compile(r"^(#{1,6})[ \t]+.+$", re.M)

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        stripped = text.strip()
        if not stripped:
            return []

        matches = list(self.HEADING_RE.finditer(stripped))
        if not matches:
            return self._fallback.chunk(stripped)

        sections: list[str] = []
        if matches[0].start() > 0:
            preamble = stripped[: matches[0].start()].strip()
            if preamble:
                sections.append(preamble)

        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(stripped)
            section = stripped[match.start() : end].strip()
            if section:
                sections.append(section)

        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            # Section too long: fall back to recursive splitting on the
            # body, then re-attach the heading to every sub-chunk so it
            # doesn't lose the "what is this section about" context.
            heading_line, _, body = section.partition("\n")
            for sub in self._fallback.chunk(body.strip()):
                chunks.append(f"{heading_line}\n{sub}".strip())

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count else 0
            result[name] = {"count": count, "avg_length": avg_length, "chunks": chunks}
        return result
