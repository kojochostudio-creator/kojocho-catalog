#!/usr/bin/env python3
"""Build only four search entries from existing catalog authority; no ledger sync.

Run after any legacy catalog refresh, which writes the older 11-URL sitemap.
--check validates generated output without writing. Products/taxonomy stay read-only.
"""
from __future__ import annotations

import argparse
import json
import re
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://kojochostudio-creator.github.io/kojocho-catalog/"
GA = "G-BZ0J1CM929"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
PAGES = {
    "pixel-art": {
        "collection": "pixel-art", "label": "Pixel Art",
        "title": "Japanese Pixel Art Game Assets | KojochoStudio",
        "description": "Browse existing pixel art sets, including Japanese folk horror props, shops, schools and urban stations, with links to BOOTH and itch.io.",
        "heading": "Pixel Art Props for Game Scenes",
        "intro": "Browse the Catalog’s pixel art sets for Japanese settings and everyday game scenes. Choose from folk horror props, arcade objects, convenience stores, school classrooms and urban stations. Open each marketplace listing to check its included files and usage terms.",
        "related": ["japanese-horror-assets", "japanese-props", "free-game-assets"],
    },
    "3d-assets": {
        "collection": "3d", "label": "3D Assets",
        "title": "Japanese 3D Game Assets & Props | KojochoStudio",
        "description": "Find Japanese 3D props from the existing Catalog, including signs, torii gates, sliding doors and tea cups. View available marketplace listings.",
        "heading": "Japanese 3D Props for Game Environments",
        "intro": "Explore the Catalog’s existing 3D props for Japanese environments and interiors. The selection includes a market signboard, a shrine torii gate, sliding doors, tea cups and ryokan interior props. Check each marketplace listing for its file formats, included models and usage terms.",
        "related": ["japanese-props", "workshops-shops", "pixel-art"],
    },
    "japanese-horror-assets": {
        "collection": None, "label": "Japanese Horror Assets",
        "title": "Japanese Horror Game Assets | Folk Horror Pixel Props | KojochoStudio",
        "description": "Discover the Japanese Folk Horror Pixel Props 12 PNG Set in the existing Catalog, with direct BOOTH and itch.io links and related collections.",
        "heading": "Japanese Folk Horror Assets for Game Scenes",
        "intro": "Explore the Japanese Folk Horror Pixel Props set for your game scenes. The set is offered as 12 PNG files. Visit its marketplace listing for the included props and usage terms, or browse the related pixel art collection for other scene assets.",
        "related": ["pixel-art", "japanese-props", "free-game-assets"],
    },
    "free-game-assets": {
        "collection": "free-sampler", "label": "Free Game Assets",
        "title": "Free Game Assets & Icon Samplers | KojochoStudio",
        "description": "Try the free potion bottle icon mini pack and existing icon samplers. Find free download links alongside clearly identified full-pack listings.",
        "heading": "Free Game Assets and Icon Samplers",
        "intro": "Start with the free potion bottle icon mini pack or try the available weather crafting and Japanese apothecary icon samplers. Sampler links are separate from the paid full-pack listings shown on the same cards. Check the linked listing for the sampler’s contents and usage terms before downloading.",
        "related": ["rpg-ui-icons", "pixel-art", "bundles"],
    },
}
LABELS = {**{slug: page["label"] for slug, page in PAGES.items()},
          "japanese-props": "Japanese Props", "workshops-shops": "Workshops & Shops",
          "rpg-ui-icons": "RPG & UI Icons", "bundles": "Bundles"}


def selections(root=ROOT):
    products = json.loads((root / "products.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((root / "site_taxonomy.json").read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in products}
    assert len(by_id) == len(products), "Duplicate product IDs"
    collections = {c["id"]: c for c in taxonomy["collections"]}
    selected = {}
    for slug, page in PAGES.items():
        if page["collection"]:
            ids = collections[page["collection"]]["product_ids"]
        else:
            # Existing explicit product title, not a new taxonomy assignment.
            ids = [p["id"] for p in products if re.search(r"\bhorror\b|ホラー", p["title_en"] + " " + p["title_jp"], re.I)]
        assert ids and len(ids) == len(set(ids)), f"Empty/duplicate selection: {slug}"
        selected[slug] = [by_id[i] for i in ids]
        for p in selected[slug]:
            assert p["status"] in {"PUBLISHED", "SELLABLE", "PUBLIC_READY"}
            assert p.get("booth_url") or p.get("itch_url")
            assert (root / p["cover_image"]).is_file()
    return selected


def link(label, url, css="store-link"):
    assert url.startswith("https://"), f"Unexpected marketplace URL: {url}"
    return f'<a class="{css}" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'


def card(p, free_page=False):
    prices, links = [], []
    sampler = bool(p.get("free_demo_url") or p.get("booth_sampler_url"))
    for market, prefix in (("BOOTH", "booth"), ("itch.io", "itch")):
        if p.get(prefix + "_url"):
            prices.append(f'{market}: {p.get(prefix + "_price") or "See store"}')
            label = market + (" (full pack)" if free_page and sampler else "")
            links.append(link(label, p[prefix + "_url"]))
    for field, label in (("free_demo_url", "Free sampler (itch.io)"), ("booth_sampler_url", "Free sampler (BOOTH)")):
        if p.get(field):
            links.append(link(label, p[field]))
    note = '<p class="collection-label">Free sampler available · full pack sold separately</p>' if free_page and sampler else ""
    jp = f'<p class="title-jp" lang="ja">{escape(p["title_jp"])}</p>' if p["title_jp"] else ""
    return f'''<article class="product-card" data-product-id="{p['id']}">
<img src="../{escape(p['cover_image'], quote=True)}" alt="{escape(p['title_en'], quote=True)}" loading="lazy">
<div class="product-content">{note}<h3 class="title-en">{escape(p['title_en'])}</h3>{jp}
<p class="prices">{escape(' | '.join(prices))}</p><div class="store-links">{''.join(links)}</div></div>
</article>'''


def render(slug, selected):
    p = PAGES[slug]
    cards = "\n".join(card(product, slug == "free-game-assets") for product in selected)
    related = "\n".join(f'<a class="category-filter" href="../{s}/">{escape(LABELS[s])}</a>' for s in p["related"])
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(p['title'])}</title>
  <meta name="description" content="{escape(p['description'], quote=True)}">
  <link rel="canonical" href="{BASE}{slug}/">
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
  <script>window.dataLayer = window.dataLayer || []; function gtag(){{dataLayer.push(arguments);}} gtag('js', new Date()); gtag('config', '{GA}');</script>
  <link rel="stylesheet" href="../assets/css/site.css">
</head>
<body>
  <header class="site-header"><div class="hero"><p class="eyebrow">KojochoStudio</p>
    <h1>{escape(p['heading'])}</h1><p class="intro">{escape(p['intro'])}</p>
    <a class="browse-button" href="../">Back to Catalog</a></div></header>
  <main class="catalog-wrap">
    <section class="catalog-section" aria-labelledby="collection-heading">
      <div class="section-heading section-heading-row"><h2 id="collection-heading">{escape(p['label'])}</h2><p class="status">{len(selected)} existing Catalog {'product' if len(selected) == 1 else 'products'}</p></div>
      <div class="product-grid" aria-label="{escape(p['label'])} products">
{cards}
      </div>
    </section>
    <section class="catalog-section" aria-labelledby="related-heading">
      <div class="section-heading"><h2 id="related-heading">Related Collections</h2></div>
      <nav class="category-filters" aria-label="Related collections">{related}</nav>
    </section>
  </main>
  <footer class="site-footer"><a href="../">Catalog Home</a> · <a href="../faq/">FAQ &amp; Usage Guide</a></footer>
</body>
</html>
'''


def sitemap(root=ROOT):
    path = root / "sitemap.xml"
    old = path.read_text(encoding="utf-8")
    tree = ET.fromstring(old)
    assert tree.tag == f"{{{NS}}}urlset"
    urls = [loc.text for loc in tree.findall(f"{{{NS}}}url/{{{NS}}}loc")]
    assert len(urls) == len(set(urls)), "Duplicate sitemap URLs"
    assert all(url.startswith(BASE) for url in urls)
    additions = [BASE + slug + "/" for slug in PAGES if BASE + slug + "/" not in urls]
    assert len(urls) + len(additions) == 15, "Unexpected sitemap authority; inspect before generating"
    return old.replace("</urlset>", "".join(f"  <url>\n    <loc>{url}</loc>\n  </url>\n" for url in additions) + "</urlset>")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    selected = selections()
    outputs = {ROOT / slug / "index.html": render(slug, products) for slug, products in selected.items()}
    outputs[ROOT / "sitemap.xml"] = sitemap()
    for path, content in outputs.items():
        if args.check:
            assert path.read_text(encoding="utf-8") == content, f"Stale generated page: {path}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"BUILD": "PASS", "mode": "check" if args.check else "generate", "products": {s: [p['id'] for p in ps] for s, ps in selected.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
