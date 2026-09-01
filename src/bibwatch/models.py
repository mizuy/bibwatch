"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Journal:
    name: str | None = None
    iso_abbrev: str | None = None
    issn: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    published: str | None = None
    type: str = "journal"  # journal | preprint

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Journal:
        if not data:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Affiliation:
    institution: str
    country: str | None = None
    country_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Affiliation:
        return cls(
            institution=data.get("institution") or "Unknown",
            country=data.get("country"),
            country_code=data.get("country_code"),
        )


@dataclass
class Author:
    name: str
    last: str | None = None
    first: str | None = None
    initials: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str | None) -> Author | None:
        if not data:
            return None
        if isinstance(data, str):
            name = data.strip()
            return cls(name=name) if name else None
        name = str(data.get("name") or "").strip()
        if not name:
            last = str(data.get("last") or "").strip()
            first = str(data.get("first") or "").strip()
            name = " ".join(p for p in (last, first) if p)
        if not name:
            return None
        return cls(
            name=name,
            last=(str(data["last"]).strip() if data.get("last") else None),
            first=(str(data["first"]).strip() if data.get("first") else None),
            initials=(str(data["initials"]).strip() if data.get("initials") else None),
        )


@dataclass
class Abstract:
    original: str | None = None
    ja: str | None = None
    translated: bool = False

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.original is not None:
            out["original"] = self.original
        if self.ja is not None:
            out["ja"] = self.ja
        out["translated"] = self.translated
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Abstract:
        if not data:
            return cls()
        return cls(
            original=data.get("original"),
            ja=data.get("ja"),
            translated=bool(data.get("translated")),
        )


@dataclass
class Paper:
    id: str
    title: str
    watch_ids: list[str] = field(default_factory=list)
    authors: list[Author] = field(default_factory=list)
    journal: Journal = field(default_factory=Journal)
    affiliations: list[Affiliation] = field(default_factory=list)
    abstract: Abstract = field(default_factory=Abstract)
    urls: dict[str, str] = field(default_factory=dict)
    ids: dict[str, str] = field(default_factory=dict)
    fetched_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "watch_ids": self.watch_ids,
            "authors": [a.to_dict() for a in self.authors],
            "journal": self.journal.to_dict(),
            "affiliations": [a.to_dict() for a in self.affiliations],
            "abstract": self.abstract.to_dict(),
            "urls": self.urls,
            "ids": self.ids,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Paper:
        return cls(
            id=data["id"],
            title=data["title"],
            watch_ids=list(data.get("watch_ids") or []),
            authors=[a for a in (Author.from_dict(x) for x in (data.get("authors") or [])) if a],
            journal=Journal.from_dict(data.get("journal")),
            affiliations=[Affiliation.from_dict(a) for a in (data.get("affiliations") or [])],
            abstract=Abstract.from_dict(data.get("abstract")),
            urls=dict(data.get("urls") or {}),
            ids=dict(data.get("ids") or {}),
            fetched_at=data.get("fetched_at"),
        )


@dataclass
class Watch:
    id: str
    title: str
    enabled: bool = True
    feeds: list[dict[str, str]] = field(default_factory=list)
    translate: dict[str, Any] = field(default_factory=dict)
    rss: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Watch:
        return cls(
            id=data["id"],
            title=data.get("title") or data["id"],
            enabled=bool(data.get("enabled", True)),
            feeds=list(data.get("feeds") or []),
            translate=dict(data.get("translate") or {}),
            rss=dict(data.get("rss") or {}),
        )
