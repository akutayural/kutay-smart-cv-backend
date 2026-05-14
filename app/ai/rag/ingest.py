import re
from pathlib import Path
from typing import Any

import yaml
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.core.config import get_settings

DATA_DIR = Path("app/data/corpus")
MIN_CHUNK_CHARS = 120

IMPORTANT_SHORT_SOURCES = {"visa.md", "skills.md", "education.md"}

HEADERS_TO_SPLIT_ON = [
    ("#", "title"),
    ("##", "section"),
    ("###", "subsection"),
]


def clean_text(text: str) -> str:
    text = re.sub(r"\[oai_citation:[^\]]*\]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw

    parts = raw.split("---", 2)

    if len(parts) < 3:
        return {}, raw

    metadata_raw = parts[1]
    body = parts[2]

    metadata = yaml.safe_load(metadata_raw) or {}

    return metadata, body


def normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            normalized[key] = value
            continue

        if isinstance(value, list):
            normalized[key] = [
                str(item)
                for item in value
                if item is not None
            ]
            continue

        normalized[key] = str(value)

    return normalized


def build_chunk_title(metadata: dict[str, Any]) -> str:
    parts = []

    for key in ("title", "section", "subsection"):
        value = metadata.get(key)

        if value:
            parts.append(str(value))

    return " > ".join(parts)


def extract_links_from_body(body: str) -> dict[str, dict[str, str]]:
    """
    Extract section-level links from markdown.

    Example:
    ## APIException
    ### URL
    https://github.com/...

    The returned mapping lets us enrich every chunk under "APIException"
    with the same URL metadata/content prefix.
    """
    section_links: dict[str, dict[str, str]] = {}

    current_section: str | None = None
    current_subsection: str | None = None

    for line in body.splitlines():
        stripped = line.strip()

        if stripped.startswith("## "):
            current_section = stripped.removeprefix("## ").strip()
            current_subsection = None
            section_links.setdefault(current_section, {})
            continue

        if stripped.startswith("### "):
            current_subsection = stripped.removeprefix("### ").strip().lower()
            continue

        if not current_section or not current_subsection:
            continue

        if current_subsection not in {
            "url",
            "urls",
            "link",
            "links",
            "documentation",
            "url/links/documentation",
        }:
            continue

        urls = re.findall(r"https?://\S+", stripped)

        for url in urls:
            cleaned_url = url.rstrip(").,]")

            if "github.com" in cleaned_url:
                section_links[current_section]["github_url"] = cleaned_url
                continue

            if "documentation" in current_subsection or "github.io" in cleaned_url:
                section_links[current_section]["documentation_url"] = cleaned_url
                continue

            section_links[current_section]["url"] = cleaned_url

    return {
        section: links
        for section, links in section_links.items()
        if links
    }


def build_link_prefix(metadata: dict[str, Any]) -> str:
    parts = []

    url = metadata.get("url")
    github_url = metadata.get("github_url")
    documentation_url = metadata.get("documentation_url")

    if url:
        parts.append(f"URL: {url}")

    if github_url:
        parts.append(f"GitHub: {github_url}")

    if documentation_url:
        parts.append(f"Documentation: {documentation_url}")

    return "\n".join(parts)


def load_documents() -> list[Document]:
    documents: list[Document] = []

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )

    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    for path in sorted(DATA_DIR.glob("*.md")):
        seen_contents: set[str] = set()

        raw = path.read_text(encoding="utf-8")
        file_metadata, body = parse_frontmatter(raw)
        body = clean_text(body)

        section_links = extract_links_from_body(body)

        base_metadata = normalize_metadata(file_metadata)
        base_metadata["source"] = path.name
        base_metadata["source_path"] = str(path)

        header_chunks = markdown_splitter.split_text(body)

        for header_chunk in header_chunks:
            chunk_metadata = {
                **base_metadata,
                **normalize_metadata(header_chunk.metadata),
            }

            section = chunk_metadata.get("section")
            if section in section_links:
                chunk_metadata.update(section_links[section])

            chunk_title = build_chunk_title(chunk_metadata)
            if chunk_title:
                chunk_metadata["chunk_title"] = chunk_title

            content = clean_text(header_chunk.page_content)

            link_prefix = build_link_prefix(chunk_metadata)
            if link_prefix:
                content = f"{link_prefix}\n\n{content}"

            smaller_chunks = fallback_splitter.split_text(content)

            for index, smaller_content in enumerate(smaller_chunks):
                smaller_content = clean_text(smaller_content)

                if (
                    len(smaller_content) < MIN_CHUNK_CHARS
                    and path.name not in IMPORTANT_SHORT_SOURCES
                ):
                    continue

                dedup_key = re.sub(r"\s+", " ", smaller_content).strip().lower()

                if dedup_key in seen_contents:
                    continue

                seen_contents.add(dedup_key)

                documents.append(
                    Document(
                        page_content=smaller_content,
                        metadata={
                            **chunk_metadata,
                            "chunk_index": index,
                        },
                    )
                )

    return documents


def main() -> None:
    settings = get_settings()

    documents = load_documents()

    embeddings = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )

    QdrantVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        force_recreate=True,
    )

    print(
        f"Ingested {len(documents)} chunks "
        f"from {DATA_DIR} into collection '{settings.qdrant_collection}'."
    )


if __name__ == "__main__":
    main()
