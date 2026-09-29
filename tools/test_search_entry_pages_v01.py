#!/usr/bin/env python3
"""Offline, stdlib-only contract checks for the four search entry pages."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://kojochostudio-creator.github.io/kojocho-catalog/"
NEW = ("pixel-art", "3d-assets", "japanese-horror-assets", "free-game-assets")
EXPECTED = {
    "pixel-art": ("pixel-art", 6),
    "3d-assets": ("3d", 5),
    "japanese-horror-assets": (None, 1),
    "free-game-assets": ("free-sampler", 3),
}
OLD_SITEMAP = {
    "", "bundles/", "rpg-ui-icons/", "japanese-props/", "workshops-shops/", "faq/",
    "products/rpg-icons-bundle/", "products/grimoires-arcane-research/",
    "products/workshop-props-bundle/", "products/sake-brewery-props/",
    "products/showa-retro-sento-props/",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.h1: list[str] = []
        self.intros: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.sources: list[str] = []
        self.cards: list[dict] = []
        self._stack: list[tuple[str, dict | None]] = []
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        cls = set((a.get("class") or "").split())
        if tag == "title": self._stack.append((tag, None)); self._text = []
        elif tag == "meta" and a.get("name") == "description": self.description = a.get("content") or ""
        elif tag == "h1": self._stack.append((tag, None)); self._text = []
        elif tag == "p" and "intro" in cls: self._stack.append((tag, None)); self._text = []
        elif tag == "a":
            self.links.append((a.get("href") or "", ""))
            for _tag, obj in reversed(self._stack):
                if obj and "id" in obj:
                    obj["links"].append((a.get("href") or "", "")); break
            self._stack.append((tag, {"link": len(self.links) - 1})); self._text = []
        elif tag == "img": self.sources.append(a.get("src") or "")
        if tag == "article" and a.get("data-product-id") is not None:
            card = {"id": int(a["data-product-id"]), "title": "", "cover": "", "prices": "", "links": []}
            self.cards.append(card); self._stack.append((tag, card))
        elif tag in ("h3", "p") and self._stack and self._stack[-1][1] and "id" in self._stack[-1][1]:
            if tag == "h3" or "prices" in cls:
                self._stack.append((tag, {"field": "title" if tag == "h3" else "prices", "card": self._stack[-1][1]})); self._text = []
        elif tag == "img" and self._stack and self._stack[-1][1] and "id" in self._stack[-1][1]:
            self._stack[-1][1]["cover"] = a.get("src") or ""

    def handle_data(self, data: str) -> None:
        if self._stack:
            self._text.append(data)
            for tag, obj in reversed(self._stack):
                if obj and "field" in obj:
                    obj["card"][obj["field"]] += data
                    break
            for tag, obj in reversed(self._stack):
                if obj and "link" in obj:
                    href, text = self.links[obj["link"]]
                    self.links[obj["link"]] = (href, text + data)
                    for _tag, card in reversed(self._stack):
                        if card and "id" in card and card["links"]:
                            card["links"][-1] = (href, text + data)
                            break
                    break

    def handle_endtag(self, tag: str) -> None:
        if not self._stack: return
        if tag in ("title", "h1"):
            value = "".join(self._text).strip()
            if tag == "title": self.title = value
            else: self.h1.append(value)
        elif tag == "p":
            for open_tag, obj in reversed(self._stack):
                if open_tag == "p" and obj is None:
                    # Only paragraphs carrying the intro class are pushed with no field.
                    value = "".join(self._text).strip()
                    if value: self.intros.append(value)
                    break
        # Close the nearest matching element; card records remain available.
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                self._stack = self._stack[:i]
                break


def read_json(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def parse(path: Path) -> PageParser:
    parser = PageParser(); parser.feed(path.read_text(encoding="utf-8")); return parser


def selections(products, taxonomy):
    by_id = {p["id"]: p for p in products}
    collections = {c["id"]: c for c in taxonomy["collections"]}
    result = {}
    for slug, (collection_id, count) in EXPECTED.items():
        if collection_id:
            ids = collections[collection_id]["product_ids"]
        else:
            ids = [p["id"] for p in products if re.search(r"\bhorror\b|ホラー", p["title_en"] + " " + p["title_jp"], re.I)]
        assert len(ids) == count and len(ids) == len(set(ids)), f"{slug}: authority membership"
        if slug == "japanese-horror-assets": assert ids == [4973531], "horror selector drift"
        result[slug] = [by_id[i] for i in ids]
    return result


def check_cards(slug: str, products: list[dict], parser: PageParser) -> None:
    assert [c["id"] for c in parser.cards] == [p["id"] for p in products], f"{slug}: card IDs"
    for card, product in zip(parser.cards, products):
        assert card["title"].strip() == product["title_en"], f"{slug}/{product['id']}: title"
        assert card["cover"] == "../" + product["cover_image"], f"{slug}/{product['id']}: cover"
        prices = []
        if product.get("booth_url"): prices.append("BOOTH: " + (product.get("booth_price") or "See store"))
        if product.get("itch_url"): prices.append("itch.io: " + (product.get("itch_price") or "See store"))
        assert card["prices"].strip() == " | ".join(prices), f"{slug}/{product['id']}: prices"
        expected = []
        sampler = bool(product.get("free_demo_url") or product.get("booth_sampler_url"))
        for market, field in (("BOOTH", "booth_url"), ("itch.io", "itch_url")):
            if product.get(field): expected.append((product[field], market + (" (full pack)" if slug == "free-game-assets" and sampler else "")))
        for field, label in (("free_demo_url", "Free sampler (itch.io)"), ("booth_sampler_url", "Free sampler (BOOTH)")):
            if product.get(field): expected.append((product[field], label))
        assert card["links"] == expected, f"{slug}/{product['id']}: marketplace links"


def test_local_links(paths: list[tuple[str, Path]]) -> None:
    for url_path, path in paths:
        doc = parse(path)
        for value in doc.sources + [href for href, _ in doc.links]:
            if not value or urlsplit(value).scheme or value.startswith("//"): continue
            target_url = urljoin(BASE + url_path, value)
            parsed = urlsplit(target_url)
            target = ROOT / parsed.path.removeprefix("/kojocho-catalog/")
            if str(parsed.path).endswith("/"): target /= "index.html"
            assert target.is_file(), f"broken local link: {url_path} -> {value}"
            if parsed.fragment:
                target_doc = parse(target)
                raw = target.read_text(encoding="utf-8")
                assert f'id="{parsed.fragment}"' in raw or f'name="{parsed.fragment}"' in raw, f"bad fragment: {value}"


def main() -> int:
    products = read_json("products.json"); taxonomy = read_json("site_taxonomy.json")
    assert len(products) == 120 and len({p["id"] for p in products}) == 120
    selected = selections(products, taxonomy)
    parsers = {slug: parse(ROOT / slug / "index.html") for slug in NEW}
    titles = []; descriptions = []; headings = []
    for slug in NEW:
        doc = parsers[slug]; assert len(doc.h1) == 1 and 2 <= len(re.findall(r"[.!?](?:\s|$)", " ".join(doc.intros))) <= 4, f"{slug}: intro"
        assert doc.title and doc.description and len(doc.links) > 0
        assert doc.title not in titles and doc.description not in descriptions and doc.h1[0] not in headings
        titles.append(doc.title); descriptions.append(doc.description); headings.append(doc.h1[0])
        raw = (ROOT / slug / "index.html").read_text(encoding="utf-8")
        assert f'<link rel="canonical" href="{BASE}{slug}/">' in raw and "G-BZ0J1CM929" in raw
        check_cards(slug, selected[slug], doc)
    home = parse(ROOT / "index.html"); home_raw = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "Japanese Game Assets | PNG, Pixel Art, 3D &amp; RPG Icons | KojochoStudio" in home_raw
    for slug in NEW: assert f'href="{slug}/"' in home_raw
    for slug in ("bundles", "rpg-ui-icons", "japanese-props", "workshops-shops"): assert f'href="{slug}/"' in home_raw
    tree = ET.parse(ROOT / "sitemap.xml"); urls = [e.text for e in tree.findall(".//{*}loc")]
    assert len(urls) == len(set(urls)) == 15 and all(u.startswith(BASE) for u in urls)
    paths = [(urlsplit(u).path.removeprefix("/kojocho-catalog/"), ROOT / urlsplit(u).path.removeprefix("/kojocho-catalog/") / "index.html") for u in urls]
    assert {p for p, _ in paths} == OLD_SITEMAP | {s + "/" for s in NEW}
    assert all(path.is_file() for _, path in paths)
    test_local_links([("", ROOT / "index.html")] + paths)
    import generate_search_entry_pages_v01 as generator
    for slug in NEW:
        assert (ROOT / slug / "index.html").read_text(encoding="utf-8") == generator.render(slug, selected[slug])
    assert (ROOT / "sitemap.xml").read_text(encoding="utf-8") == generator.sitemap()
    changed = set(subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines())
    allowed = {"index.html", "sitemap.xml", "tools/generate_search_entry_pages_v01.py", "tools/test_search_entry_pages_v01.py"}
    allowed.update(slug + "/index.html" for slug in NEW)
    assert changed <= allowed, f"unexpected tracked changes: {sorted(changed)}"
    protected = ["products.json", "site_taxonomy.json", "assets/css/site.css", "assets/js/collection-page.js", "assets/js/catalog.js",
                 "products/rpg-icons-bundle/index.html", "products/grimoires-arcane-research/index.html",
                 "products/workshop-props-bundle/index.html", "products/sake-brewery-props/index.html",
                 "products/showa-retro-sento-props/index.html"]
    for name in protected:
        assert subprocess.check_output(["git", "diff", "--quiet", "HEAD", "--", name], cwd=ROOT).strip() == b""
    print(json.dumps({"NEW_ENTRY_PAGE_COUNT": 4, "ALL_HTTP_200": "NOT_TESTED", "CANONICAL_PASS": True, "INTERNAL_LINK_PASS": True, "SITEMAP_VALID": True, "SITEMAP_URL_COUNT": 15, "PRODUCT_DATA_MUTATION_COUNT": 0, "MARKETPLACE_MUTATION_COUNT": 0, "BUILD": "PASS", "STATIC_VALID": "PASS", "LOCAL_RENDER": "NOT_TESTED"}, ensure_ascii=False))
    return 0


if __name__ == "__main__": raise SystemExit(main())
