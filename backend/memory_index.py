"""Build and query the Chroma memory index for LifeTrace."""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_configured_chroma_path = os.getenv("LIFETRACE_CHROMA_PATH")
DEFAULT_CHROMA_PATH = (
    Path(_configured_chroma_path)
    if _configured_chroma_path and Path(_configured_chroma_path).is_absolute()
    else PROJECT_ROOT / (_configured_chroma_path or "outputs/chroma_lifetrace")
)


@dataclass(frozen=True)
class MemoryItem:
    id: str
    source_type: str
    source_key: str
    time_range: str
    title: str
    text: str
    evidence: tuple[str, ...]
    page_type: str
    anchor_id: str
    locations: tuple[str, ...] = ()
    apps: tuple[str, ...] = ()
    photo_scenes: tuple[str, ...] = ()
    activities: tuple[str, ...] = ()

    def metadata(self) -> dict[str, str]:
        return {
            "sourceType": self.source_type,
            "sourceKey": self.source_key,
            "timeRange": self.time_range,
            "title": self.title,
            "evidence": "\n".join(self.evidence),
            "pageType": self.page_type,
            "anchorId": self.anchor_id,
            "snippet": _clip(_humanize_text(self.text), 130),
            "locations": "|".join(self.locations),
            "apps": "|".join(self.apps),
            "photoScenes": "|".join(self.photo_scenes),
            "activities": "|".join(self.activities),
        }


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text."""


class LLMEmbeddingProvider:
    """Embedding provider backed by an OpenAI-compatible embeddings endpoint."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.client.create_embeddings(texts)


class LocalHashEmbeddingProvider:
    """Small deterministic embedding provider for offline demo and tests."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class ChromaMemoryIndex:
    """Thin wrapper around a persistent Chroma collection."""

    def __init__(self, path: Path = DEFAULT_CHROMA_PATH, collection_name: str = "lifetrace_memory") -> None:
        try:
            import chromadb
        except ModuleNotFoundError as exc:
            raise RuntimeError("chromadb is not installed. Run: python -m pip install chromadb") from exc

        self.path = path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return int(self.collection.count())

    def upsert_items(self, items: list[MemoryItem], embedding_provider: EmbeddingProvider, batch_size: int = 32) -> None:
        if not items:
            return
        for start in range(0, len(items), batch_size):
            batch = items[start : start + batch_size]
            documents = [item.text for item in batch]
            embeddings = embedding_provider.embed_texts(documents)
            self.collection.upsert(
                ids=[item.id for item in batch],
                documents=documents,
                metadatas=[item.metadata() for item in batch],
                embeddings=embeddings,
            )

    def query(
        self,
        text: str,
        embedding_provider: EmbeddingProvider,
        n_results: int = 12,
    ) -> list[dict[str, Any]]:
        query_embedding = embedding_provider.embed_texts([text])[0]
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        candidates: list[dict[str, Any]] = []
        for item_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            evidence = [line for line in str(metadata.get("evidence", "")).split("\n") if line.strip()]
            candidates.append(
                {
                    "id": item_id,
                    "score": _distance_to_score(float(distance)),
                    "sourceType": metadata.get("sourceType", ""),
                    "sourceKey": metadata.get("sourceKey", ""),
                    "timeRange": metadata.get("timeRange", ""),
                    "title": metadata.get("title", ""),
                    "snippet": metadata.get("snippet") or _clip(_humanize_text(document), 120),
                    "evidence": evidence[:5] or [metadata.get("title", "候选记忆")],
                    "openTarget": {
                        "pageType": metadata.get("pageType", "daily"),
                        "sourceKey": metadata.get("sourceKey", ""),
                        "anchorId": metadata.get("anchorId", ""),
                    },
                    "metadataText": _metadata_text(metadata),
                }
            )
        return candidates


def build_memory_items(daily_data: dict[str, Any], month_data: dict[str, Any]) -> list[MemoryItem]:
    """Flatten daily and monthly LifeTrace data into searchable memory items."""

    items: list[MemoryItem] = []
    if isinstance(daily_data.get("days"), list):
        for day in daily_data["days"]:
            if isinstance(day, dict) and day.get("dateKey"):
                items.extend(_daily_items(day))
    else:
        items.extend(_daily_items(daily_data))
    items.extend(_month_items(month_data))
    return items


def enrich_query_text(query_plan: dict[str, Any]) -> str:
    parts = [query_plan["searchText"]]
    for key in ("timeHints", "locationHints", "appHints", "activityHints", "visualHints", "keywords"):
        parts.extend(query_plan.get(key, []))
    return " ".join(part for part in parts if str(part).strip())


def boost_candidates(candidates: list[dict[str, Any]], query_plan: dict[str, Any]) -> list[dict[str, Any]]:
    terms = []
    for key in ("timeHints", "locationHints", "appHints", "activityHints", "visualHints", "keywords"):
        terms.extend(str(item).lower() for item in query_plan.get(key, []) if str(item).strip())

    boosted = []
    for candidate in candidates:
        haystack = " ".join(
            [
                candidate.get("title", ""),
                candidate.get("snippet", ""),
                candidate.get("timeRange", ""),
                candidate.get("metadataText", ""),
                " ".join(candidate.get("evidence", [])),
            ]
        ).lower()
        bonus = sum(0.04 for term in terms if term and term in haystack)
        item = dict(candidate)
        item["score"] = round(min(1.0, float(item["score"]) + bonus), 4)
        boosted.append(item)
    return sorted(boosted, key=lambda item: item["score"], reverse=True)


def _daily_items(data: dict[str, Any]) -> list[MemoryItem]:
    date_key = data["dateKey"]
    items: list[MemoryItem] = []

    context = data.get("dailyContextText", "")
    if context:
        items.append(
            MemoryItem(
                id=f"daily_{_safe_key(date_key)}_context",
                source_type="daily_context",
                source_key=date_key,
                time_range="全天",
                title=f"{date_key} 日总结",
                text=f"{date_key} {data.get('basicInfo', {}).get('dayType', '')} {context}",
                evidence=(_clip(_humanize_text(context), 160),),
                page_type="daily",
                anchor_id="summary",
                activities=_split_day_type(data.get("basicInfo", {}).get("dayType", "")),
            )
        )

    for index, segment in enumerate(data.get("memorySegments", []), 1):
        segment_id = f"seg_{index}"
        related_apps = tuple(segment.get("relatedApps", []))
        related_locations = tuple(segment.get("relatedLocations", []))
        related_photos = tuple(segment.get("relatedPhotos", []))
        segment_type = str(segment.get("segmentType", "memory"))
        items.append(
            MemoryItem(
                id=f"daily_{_safe_key(date_key)}_{segment_id}",
                source_type="daily_segment",
                source_key=date_key,
                time_range=segment.get("timeRange", "未知时间"),
                title=segment.get("title", "生活片段"),
                text=" ".join(
                    [
                        date_key,
                        segment.get("timeRange", ""),
                        segment.get("title", ""),
                        segment.get("description", ""),
                        " ".join(related_apps),
                        " ".join(related_locations),
                        " ".join(related_photos),
                        " ".join(segment.get("evidence", [])),
                    ]
                ),
                evidence=tuple(segment.get("evidence", [])) or (segment.get("description", "生活片段"),),
                page_type="daily",
                anchor_id=segment_id,
                locations=related_locations,
                apps=related_apps,
                photo_scenes=related_photos,
                activities=(segment_type,),
            )
        )

    for index, item in enumerate(data.get("appUsage", []), 1):
        app_name = item.get("appName", "未知 App")
        items.append(
            MemoryItem(
                id=f"daily_{_safe_key(date_key)}_app_{index}",
                source_type="app_usage",
                source_key=date_key,
                time_range=item.get("timeRange", "未知时间"),
                title=f"{app_name} 使用记录",
                text=f"{date_key} {item.get('timeRange', '')} {app_name} {item.get('appCategory', '')} {item.get('durationMinutes', 0)} 分钟 {item.get('note', '')}",
                evidence=(f"{item.get('timeRange', '')} 使用 {app_name} 约 {item.get('durationMinutes', 0)} 分钟",),
                page_type="daily",
                anchor_id="app_usage",
                apps=(app_name,),
                activities=(item.get("appCategory", ""),),
            )
        )

    for index, item in enumerate(data.get("locationStays", []), 1):
        location = item.get("locationLabel", "未知地点")
        items.append(
            MemoryItem(
                id=f"daily_{_safe_key(date_key)}_location_{index}",
                source_type="location_stay",
                source_key=date_key,
                time_range=item.get("timeRange", "未知时间"),
                title=f"{location} 停留",
                text=f"{date_key} {item.get('timeRange', '')} {location} {item.get('stayMinutes', 0)} 分钟 {item.get('stayType', '')}",
                evidence=(f"{item.get('timeRange', '')} 在{location}停留约 {item.get('stayMinutes', 0)} 分钟",),
                page_type="daily",
                anchor_id="location_stays",
                locations=(location,),
                activities=(item.get("stayType", ""),),
            )
        )

    for index, item in enumerate(data.get("photoMoments", []), 1):
        scene = item.get("sceneLabel", "照片")
        items.append(
            MemoryItem(
                id=f"daily_{_safe_key(date_key)}_photo_{index}",
                source_type="photo_moment",
                source_key=date_key,
                time_range=item.get("time", "未知时间"),
                title=f"{scene} 照片",
                text=f"{date_key} {item.get('time', '')} {scene} {item.get('photoCount', 0)} 张 {item.get('ocrText', '')} {item.get('note', '')}",
                evidence=(f"{item.get('time', '')} {scene} {item.get('photoCount', 0)} 张",),
                page_type="daily",
                anchor_id="photo_moments",
                photo_scenes=(scene,),
            )
        )

    return items


def _month_items(data: dict[str, Any]) -> list[MemoryItem]:
    month_key = data["monthKey"]
    items: list[MemoryItem] = []
    monthly_context = data.get("monthlyContextText", "")
    if monthly_context:
        items.append(
            MemoryItem(
                id=f"month_{_safe_key(month_key)}_summary",
                source_type="month_summary",
                source_key=month_key,
                time_range=data.get("basicInfo", {}).get("monthRange", month_key),
                title=f"{month_key} 阶段总结",
                text=f"{month_key} {monthly_context}",
                evidence=(_clip(_humanize_text(monthly_context), 160),),
                page_type="month",
                anchor_id="summary",
            )
        )

    for index, item in enumerate(data.get("monthHighlights", []), 1):
        title = item.get("title", "本月重点")
        items.append(
            MemoryItem(
                id=f"month_{_safe_key(month_key)}_highlight_{index}",
                source_type="month_highlight",
                source_key=month_key,
                time_range=data.get("basicInfo", {}).get("monthRange", month_key),
                title=title,
                text=f"{month_key} {title} {item.get('description', '')} {' '.join(item.get('evidence', []))}",
                evidence=tuple(item.get("evidence", [])) or (item.get("description", "本月重点"),),
                page_type="month",
                anchor_id=f"highlight_{index}",
            )
        )

    for index, item in enumerate(data.get("possiblePatterns", []), 1):
        title = item.get("patternName", "可能规律")
        items.append(
            MemoryItem(
                id=f"month_{_safe_key(month_key)}_pattern_{index}",
                source_type="month_pattern",
                source_key=month_key,
                time_range=data.get("basicInfo", {}).get("monthRange", month_key),
                title=title,
                text=f"{month_key} {title} {item.get('description', '')} {' '.join(item.get('evidence', []))}",
                evidence=tuple(item.get("evidence", [])) or (item.get("description", "可能规律"),),
                page_type="month",
                anchor_id=f"pattern_{index}",
            )
        )

    stats = data.get("monthlyStats", {})
    stat_specs = [
        ("mainLocationRanking", "locationLabel", "totalStayMinutes", "分钟", "主要地点"),
        ("mainActivityRanking", "activityType", "estimatedMinutes", "分钟", "主要活动"),
        ("appCategoryRanking", "appCategory", "totalMinutes", "分钟", "App 类型"),
        ("photoSceneRanking", "sceneLabel", "count", "次", "照片场景"),
    ]
    for stat_key, label_key, value_key, suffix, stat_title in stat_specs:
        for index, item in enumerate(stats.get(stat_key, []), 1):
            label = item.get(label_key, "统计项")
            items.append(
                MemoryItem(
                    id=f"month_{_safe_key(month_key)}_{_safe_key(stat_key)}_{index}",
                    source_type="month_stat",
                    source_key=month_key,
                    time_range=data.get("basicInfo", {}).get("monthRange", month_key),
                    title=f"{stat_title}：{label}",
                    text=f"{month_key} {stat_title} {label} {item.get(value_key, 0)}{suffix} {item.get('description', '')} {item.get('mainStayType', '')}",
                    evidence=(f"{label}：{item.get(value_key, 0)}{suffix}", item.get("description", "月度统计")),
                    page_type="month",
                    anchor_id="ranking_sections",
                    locations=(label,) if label_key == "locationLabel" else (),
                    apps=(label,) if label_key == "appCategory" else (),
                    photo_scenes=(label,) if label_key == "sceneLabel" else (),
                    activities=(label,) if label_key == "activityType" else (),
                )
            )

    return items


def _split_day_type(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value).replace("＋", "+").split("+") if part.strip())


def _metadata_text(metadata: dict[str, Any]) -> str:
    parts = [
        metadata.get("locations", ""),
        metadata.get("apps", ""),
        metadata.get("photoScenes", ""),
        metadata.get("activities", ""),
    ]
    return " ".join(part.replace("|", " ") for part in parts if part)


def _distance_to_score(distance: float) -> float:
    return round(max(0.0, min(1.0, 1.0 - distance)), 4)


def _clip(text: str, max_length: int) -> str:
    text = _humanize_text(" ".join(str(text).split()))
    if len(text) <= max_length:
        return text or "暂无摘要"
    clipped = text[: max_length - 1]
    for mark in ("。", "；", ";"):
        last_mark_index = clipped.rfind(mark)
        if last_mark_index >= max_length * 0.55:
            return clipped[: last_mark_index + 1]
    return clipped.rstrip("，。；;:：, ") + "。"


def _humanize_text(text: str) -> str:
    replacements = {
        "数据完整度为 high": "数据完整度较高",
        "数据完整度为 medium": "数据完整度中等",
        "数据完整度为 low": "数据完整度较低",
        "整体数据完整度为 high": "整体数据完整度较高",
        "整体数据完整度为 medium": "整体数据完整度中等",
        "整体数据完整度为 low": "整体数据完整度较低",
    }
    result = str(text)
    for source, target in replacements.items():
        result = result.replace(source, target)
    return result


def _safe_key(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value)).strip("_").lower()


def _tokens(text: str) -> list[str]:
    raw = str(text).lower()
    ascii_tokens = re.findall(r"[a-z0-9_]+", raw)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", raw)
    cjk_bigrams = [raw[index : index + 2] for index in range(len(raw) - 1) if _is_cjk_pair(raw[index : index + 2])]
    return ascii_tokens + cjk_chars + cjk_bigrams


def _is_cjk_pair(value: str) -> bool:
    return len(value) == 2 and all("\u4e00" <= char <= "\u9fff" for char in value)
