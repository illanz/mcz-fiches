"""Test hors ligne : simule l'API Notion (blocs au format officiel) pour vérifier lecture et rendu."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image  # noqa: E402

import build  # noqa: E402
from mcz.media import Media  # noqa: E402
from mcz import render  # noqa: E402


def rt(text, bold=False, href=None):
    return {"type": "text", "plain_text": text, "href": href, "annotations": {"bold": bold, "italic": False, "strikethrough": False, "underline": False, "code": False}}


def blk(t, rich=None, children=None, **extra):
    b = {"id": f"{t}-{id(rich)}", "type": t, "has_children": bool(children), t: {"rich_text": rich or [], **extra}}
    if children:
        b["_children"] = children
    return b


def li(text, children=None, bold=None):
    rich = [rt(text)] if not bold else [rt(bold, True), rt(text)]
    return blk("bulleted_list_item", rich, children)


FRESQUE = [
    blk("callout", [rt("Découvrez le “Pop Art” et mettez vos valeurs en images")]),
    {"id": "cl", "type": "column_list", "has_children": True, "column_list": {}, "_children": [
        {"id": "c1", "type": "column", "has_children": True, "column": {}, "_children": [
            blk("heading_1", [rt("Déroulé")]),
            li("Plusieurs sous-groupes… ", bold=None),
            blk("bulleted_list_item", [rt("Voir "), rt("Pop Art (Keith Haring)", True), rt(", Street Art.\nDeuxième ligne")]),
            blk("heading_2", [rt("Options disponibles ")]),
            li("Fresque sur-mesure avec un visuel travaillé en amont"),
            blk("bulleted_list_item", []),
            {"id": "t", "type": "table", "has_children": True, "table": {"has_column_header": True}, "_children": [
                {"type": "table_row", "table_row": {"cells": [[rt("Format", True)], [rt("Durée", True)], [rt("Pax")], [rt("Surface")], []]}},
                {"type": "table_row", "table_row": {"cells": [[rt("Team Building")], [rt("2h30")], [rt("Jusqu’a 800 pax")], [rt("2m²/personne")], []]}},
            ]},
            blk("heading_3", [rt("Lien vers la page de l’animation sur le site www.madcityzen.fr", href="https://www.madcityzen.fr/x")]),
        ]},
        {"id": "c2", "type": "column", "has_children": True, "column": {}, "_children": [
            blk("heading_2", [rt("Fiche technique")]),
            li("Peut se dérouler en intérieur ou extérieur"),
            li("Notre matériel : ", [li("Toiles coton sur chassis 40x50cm"), li("Peintures acryliques")]),
            blk("heading_2", [rt("Staff")]),
            li("1 artiste peintre pour 5 groupes"),
            blk("heading_2", [rt("Le client "), rt("doit fournir")]),
            li("Un espace de travail pour les participants"),
            blk("heading_2", [rt("Tarifs spécifiques")]),
            blk("paragraph", [rt("Section inconnue conservée telle quelle")]),
        ]},
    ]},
    blk("heading_1", [rt("Photos & Vidéos")]),
    {"id": "db", "type": "child_database", "has_children": False, "child_database": {"title": ""}},
    blk("heading_3", [rt("Option : Clip Animé Mosaic Balade")]),
    {"id": "v1", "type": "video", "has_children": False, "video": {"type": "external", "external": {"url": "https://vimeo.com/89089396?share=copy"}}},
    {"id": "v2", "type": "video", "has_children": False, "video": {"type": "external", "external": {"url": "https://player.vimeo.com/video/52937485?h=92864f55d2"}}},
]


class FakeNotion:
    calls = 0

    def page(self, pid):
        return {"id": pid, "last_edited_time": "2026-07-24T13:29:04.848Z", "cover": None,
                "properties": {"title": {"type": "title", "title": [rt("ATELIER FRESQUE")]}}}

    def tree(self, pid):
        return FRESQUE

    def children(self, pid):
        return [{"type": "image", "image": {"type": "file", "file": {"url": "https://example/x.jpg"}}}]

    def query_data_source(self, ds, flt=None, sorts=None):
        return [{"id": f"row{i}", "last_edited_time": "2026", "properties": {}} for i in range(3)]


def main():
    tmp = ROOT / "tests" / "_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    out = tmp / "out"
    media = Media(tmp / "cache", out, print)
    sample = tmp / "sample.jpg"
    Image.new("RGB", (1200, 800), (243, 173, 34)).save(sample)
    media._download = lambda url: sample.read_bytes()
    media.vimeo_meta = {"https://vimeo.com/89089396": {"thumbnail_url": "x", "duration": 75},
                        "https://vimeo.com/52937485/92864f55d2": {"thumbnail_url": None, "duration": None}}
    n = FakeNotion()
    state = {"fiches": {}}
    photos = build.PhotoLibrary(n, media, state)
    cfg = {"id": "p1", "slug": "atelier-fresque", "photo_tags": ["Fresque Keith Haring"], "category": "Artistique"}
    f = build.build_fiche(n, media, photos, state, cfg, "p1", "Artistique")
    (out / "atelier-fresque.html").write_text(render.page(f, build.LOGO), encoding="utf-8")
    (out / "index.html").write_text(render.index([f], build.LOGO, build.BASE_URL), encoding="utf-8")
    print(json.dumps({k: f[k] for k in ("site_links", "videos", "tables")}, ensure_ascii=False, indent=1)[:1500])
    print("sections:", [(s["key"], s["title"], len(s["nodes"])) for s in f["sections"]])
    print("photos:", len(f["photos"]), "cover:", f["cover"])
    # 2e passage : tout doit venir du cache
    f2 = build.build_fiche(n, media, photos.__class__(n, media, state), state, cfg, "p1", "Artistique")
    assert len(f2["photos"]) == 3 and f2["videos"][0]["thumb"], "cache"
    print("OK")


if __name__ == "__main__":
    main()
