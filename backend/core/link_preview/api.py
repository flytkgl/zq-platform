"""
Link Preview API - 获取 URL 元数据用于 Embed/书签预览卡片
"""
import re
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/link-preview", tags=["链接预览"])

_cache: dict[str, dict] = {}
_CACHE_MAX = 200


class LinkPreviewResponse(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    favicon: Optional[str] = None
    site_name: Optional[str] = None


class _MetaParser(HTMLParser):
    """轻量 HTML 解析器，提取 title 和 meta 中的 OG 元数据"""

    def __init__(self):
        super().__init__()
        self.title: Optional[str] = None
        self.og_title: Optional[str] = None
        self.og_description: Optional[str] = None
        self.og_image: Optional[str] = None
        self.og_site_name: Optional[str] = None
        self.description: Optional[str] = None
        self.favicon: Optional[str] = None
        self._in_title = False
        self._title_parts: list[str] = []
        self._done = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]):
        if self._done:
            return
        attrs_dict = {k.lower(): v for k, v in attrs if k}

        if tag == "title":
            self._in_title = True
            self._title_parts = []
            return

        if tag == "meta":
            prop = (attrs_dict.get("property") or "").lower()
            name = (attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content") or ""

            if prop == "og:title":
                self.og_title = content
            elif prop == "og:description":
                self.og_description = content
            elif prop == "og:image":
                self.og_image = content
            elif prop == "og:site_name":
                self.og_site_name = content
            elif name == "description":
                self.description = content

        if tag == "link":
            rel = (attrs_dict.get("rel") or "").lower()
            href = attrs_dict.get("href") or ""
            if "icon" in rel and href:
                self.favicon = href

    def handle_data(self, data: str):
        if self._in_title:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str):
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_parts).strip()
        if tag == "head":
            self._done = True


def _resolve_url(base: str, path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if path.startswith(("http://", "https://", "//")):
        return path
    return urljoin(base, path)


def _domain_favicon(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


async def _fetch_metadata(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ZQBot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    async with httpx.AsyncClient(
        follow_redirects=True, timeout=5.0, verify=False
    ) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return {"url": url}

        text = resp.text[:50_000]

    parser = _MetaParser()
    try:
        parser.feed(text)
    except Exception:
        pass

    return {
        "url": url,
        "title": parser.og_title or parser.title,
        "description": parser.og_description or parser.description,
        "image": _resolve_url(url, parser.og_image),
        "favicon": _resolve_url(url, parser.favicon) or _domain_favicon(url),
        "site_name": parser.og_site_name,
    }


@router.get("", response_model=LinkPreviewResponse)
async def get_link_preview(url: str = Query(..., description="要预览的 URL")):
    """获取指定 URL 的元数据"""
    if not re.match(r"^https?://", url):
        url = f"https://{url}"

    if url in _cache:
        return LinkPreviewResponse(**_cache[url])

    try:
        metadata = await _fetch_metadata(url)
    except Exception:
        metadata = {"url": url}

    if len(_cache) >= _CACHE_MAX:
        oldest = next(iter(_cache))
        del _cache[oldest]
    _cache[url] = metadata

    return LinkPreviewResponse(**metadata)
