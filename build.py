"""Génère le site des fiches techniques MadCityZen à partir de Notion.

Usage : NOTION_TOKEN=... python build.py [--only slug1,slug2]
Sortie : dossier out/ prêt à publier sur Cloudflare Pages. Cache : dossier .cache/.
"""
import argparse
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

from mcz.notion import Notion, plain, file_url
from mcz.parse import FicheParser
from mcz.media import Media, key
from mcz import render

ROOT = Path(__file__).parent
OUT = ROOT / "out"
CACHE = ROOT / ".cache"
INDEX_PAGE = "8a50a915e7434ef39a6ac8d31fed6d21"          # « Fiches Descriptives Animations »
PHOTOS_DS = "15a9f3e2-8e61-483f-82bf-69ae5dcb4b1f"        # base « Photos Animations »
BASE_URL = "https://fiches.madcityzen.fr"
LOGO = "media/logo-madcityzen.svg"
PARSER_VERSION = 2  # à incrémenter quand la lecture des fiches change : force leur relecture

warnings = []


def log(*a):
    print(*a, flush=True)


def warn(msg):
    warnings.append(msg)
    log("  ⚠ " + msg)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def nid(x):
    return x.replace("-", "")


def page_title(p):
    for prop in p.get("properties", {}).values():
        if prop.get("type") == "title":
            return plain(prop["title"]).strip()
    return ""


def read_index(notion):
    """Ordre et catégories des fiches, tels qu'ils apparaissent dans la page Notion d'index."""
    order, cat = [], None

    def walk(blocks):
        nonlocal cat
        for b in blocks:
            t = b["type"]
            if t in ("heading_1", "heading_2", "heading_3"):
                txt = plain(b[t]["rich_text"]).strip()
                if txt:
                    cat = txt
            elif t == "link_to_page" and b["link_to_page"].get("page_id"):
                order.append((nid(b["link_to_page"]["page_id"]), cat))
            elif t == "child_page":
                order.append((nid(b["id"]), cat))
            elif t == "paragraph":
                for r in b["paragraph"]["rich_text"]:
                    if r.get("type") == "mention" and r["mention"].get("type") == "page":
                        order.append((nid(r["mention"]["page"]["id"]), cat))
            if b.get("_children"):
                walk(b["_children"])

    walk(notion.tree(INDEX_PAGE))
    seen, res = set(), []
    for pid, c in order:
        if pid not in seen:
            seen.add(pid)
            res.append((pid, c))
    return res


class PhotoLibrary:
    """Photos de la base « Photos Animations », par étiquette, avec cache par ligne."""

    def __init__(self, notion, media, state):
        self.notion, self.media = notion, media
        self.rows_state = state.setdefault("photo_rows", {})
        self.by_tag = {}

    def for_tag(self, tag):
        if tag in self.by_tag:
            return self.by_tag[tag]
        rows = self.notion.query_data_source(
            PHOTOS_DS,
            flt={"property": "Étiquettes", "select": {"equals": tag}},
            sorts=[{"timestamp": "created_time", "direction": "ascending"}])
        photos = []
        for row in rows:
            rid, edited = nid(row["id"]), row["last_edited_time"]
            st = self.rows_state.get(rid)
            keys = None
            if st and st["edited"] == edited:
                cached = [self.media.cached_image(k) for k in st["keys"]]
                if all(cached):
                    photos += cached
                    continue
            # sources : propriété fichiers + images du contenu de la page
            sources = []
            for prop in row.get("properties", {}).values():
                if prop.get("type") == "files":
                    for fobj in prop["files"]:
                        u = file_url(fobj)
                        if u:
                            sources.append(u)
            for b in self.notion.children(row["id"]):
                if b["type"] == "image":
                    u = file_url(b["image"])
                    if u:
                        sources.append(u)
            keys = []
            for i, u in enumerate(sources):
                k = key("photo", rid, i, edited)
                res = self.media.image(u, k)
                if res:
                    keys.append(k)
                    photos.append(res)
            self.rows_state[rid] = {"edited": edited, "keys": keys}
        self.by_tag[tag] = photos
        return photos


def build_fiche(notion, media, photos, state, cfg, pid, category):
    p = notion.page(pid)
    title = page_title(p) or cfg.get("title", "")
    edited = p["last_edited_time"]
    fstate = state.setdefault("fiches", {}).get(pid)

    if fstate and fstate["edited"] == edited and fstate.get("model") and fstate.get("v") == PARSER_VERSION:
        model = fstate["model"]
        # médias déjà préparés : on republie depuis le cache
        if model.get("cover_key"):
            c = media.cached_image(model["cover_key"], "c", (1600,))
            model["cover"] = "/" + c[1600] if c else None
        for v in model["videos"]:
            if v["kind"] == "file" and v.get("key"):
                r = media.video_file(None, v["key"])
                if r:
                    v["mp4"] = "/" + r["mp4"]
                    v["poster"] = "/" + r["poster"] if r.get("poster") else None
            if v["kind"] == "vimeo":
                vm = media.vimeo(v["link"])
                v["thumb"] = "/" + vm["thumb"] if vm.get("thumb") else None
    else:
        log(f"  · lecture Notion : {title}")
        parsed = FicheParser(notion).parse(notion.tree(pid))
        model = {k: parsed[k] for k in ("callout", "sections", "media_nodes", "media_title", "tables", "site_links")}
        # couverture (les fonds Notion génériques sont ignorés)
        model["cover"], model["cover_key"] = None, None
        cu = file_url(p.get("cover"))
        if cu and "/images/page-cover/" not in cu:
            ck = key("cover", pid, edited)
            c = media.image(cu, ck, "c", (1600,))
            if c:
                model["cover"], model["cover_key"] = "/" + c[1600], ck
        # vidéos
        vids = []
        for v in parsed["videos"]:
            if v["kind"] == "external" and "vimeo.com" in v["url"]:
                vm = media.vimeo(v["url"])
                vids.append({"kind": "vimeo", "link": vm["link"], "duration": vm.get("duration"),
                             "thumb": "/" + vm["thumb"] if vm.get("thumb") else None, "label": v.get("label")})
                if not vm.get("thumb"):
                    warn(f"{title} : miniature Vimeo introuvable ({vm['link']})")
            elif v["kind"] == "external":
                vids.append({"kind": "link", "link": v["url"], "label": v.get("label")})
            elif v["kind"] == "file":
                vk = key("video", v["block_id"], v.get("edited"))
                log(f"    vidéo Notion → conversion")
                r = media.video_file(v["url"], vk)
                if r:
                    vids.append({"kind": "file", "key": vk, "mp4": "/" + r["mp4"],
                                 "poster": "/" + r["poster"] if r.get("poster") else None, "label": v.get("label")})
                else:
                    warn(f"{title} : une vidéo Notion n'a pas pu être publiée (trop lourde ou illisible)")
        model["videos"] = vids
        # images placées directement dans le corps de la fiche → ajoutées à la galerie
        model["body_photo_keys"] = []
        for im in parsed["images"]:
            k = key("bodyimg", im["block_id"], im.get("edited"))
            if media.image(im["url"], k):
                model["body_photo_keys"].append(k)
        state["fiches"][pid] = {"edited": edited, "model": model, "v": PARSER_VERSION}

    # photos de la galerie
    gallery = []
    tags = cfg.get("photo_tags")
    if tags is None:
        tags = []
    for t in tags:
        gallery += photos.for_tag(t)
    gallery += [x for x in (media.cached_image(k) for k in model.get("body_photo_keys", [])) if x]
    gal =[{"w": g["w"], "h": g["h"], "800": "/" + g[800], "1600": "/" + g[1600]} for g in gallery]

    if not model["sections"]:
        warn(f"{title} : aucune section reconnue")
    return {**model, "id": pid, "title": title, "slug": cfg["slug"], "category": category or cfg.get("category", ""),
            "updated": edited, "photos": gal,
            "thumb": model.get("cover") or (gal[0]["800"] if gal else None)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="slugs séparés par des virgules (test)")
    args = ap.parse_args()

    cfg_list = json.loads((ROOT / "config" / "fiches.json").read_text(encoding="utf-8"))["fiches"]
    cfg_by_id = {c["id"]: c for c in cfg_list}
    CACHE.mkdir(exist_ok=True)
    state_path = CACHE / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    state.setdefault("fiches", {})

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    notion = Notion()
    media = Media(CACHE, OUT, log)
    photos = PhotoLibrary(notion, media, state)

    log("Lecture de l'index Notion…")
    try:
        order = read_index(notion)
    except Exception as e:
        warn(f"index Notion illisible ({e}) : ordre de la configuration utilisé")
        order = [(c["id"], c["category"]) for c in cfg_list]
    known = {pid for pid, _ in order}
    for c in cfg_list:  # fiches configurées absentes de l'index : conservées à la fin
        if c["id"] not in known:
            order.append((c["id"], c["category"]))

    only = set(args.only.split(",")) if args.only else None
    used_slugs = {c["slug"] for c in cfg_list}
    fiches = []
    for pid, cat in order:
        cfg = cfg_by_id.get(pid)
        if not cfg:
            try:
                t = page_title(notion.page(pid))
            except Exception:
                continue
            slug = slugify(t.split(" - ")[0]) or pid
            if slug in used_slugs:
                slug = slugify(t) or pid
            used_slugs.add(slug)
            cfg = {"id": pid, "slug": slug, "title": t, "category": cat, "photo_tags": []}
            warn(f"nouvelle fiche « {t} » publiée à /{slug} : ajoutez son étiquette photo dans config/fiches.json")
        if only and cfg["slug"] not in only:
            continue
        log(f"• {cfg['slug']}")
        try:
            f = build_fiche(notion, media, photos, state, cfg, pid, cat)
        except Exception as e:
            warn(f"{cfg['slug']} : erreur, fiche ignorée ({e})")
            continue
        (OUT / f"{f['slug']}.html").write_text(render.page(f, LOGO), encoding="utf-8")
        fiches.append(f)

    (OUT / "media").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "assets" / "logo-madcityzen.svg", OUT / LOGO)
    (OUT / "index.html").write_text(render.index(fiches, LOGO, BASE_URL), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (OUT / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n\n/media/*\n  Cache-Control: public, max-age=604800\n")
    (OUT / "404.html").write_text(render.index(fiches, LOGO, BASE_URL), encoding="utf-8")

    (OUT / "rapport-publication.json").write_text(json.dumps({
        "fiches": len(fiches), "appels_notion": notion.calls,
        "avertissements": warnings,
        "detail": [{"slug": f["slug"], "titre": f["title"], "photos": len(f["photos"]), "videos": len(f["videos"]),
                    "sections": [s["title"] for s in f["sections"]]} for f in fiches],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    media.save_meta()
    state_path.write_text(json.dumps(state, ensure_ascii=False))
    n_files = sum(1 for _ in OUT.rglob("*") if _.is_file())
    log(f"\n{len(fiches)} fiches générées, {n_files} fichiers, {notion.calls} appels Notion.")
    if warnings:
        log(f"\n{len(warnings)} avertissement(s) :")
        for w in warnings:
            log("  - " + w)
    summary = Path(__import__("os").environ.get("GITHUB_STEP_SUMMARY", "/dev/null"))
    with open(summary, "a") as fh:
        fh.write(f"### {len(fiches)} fiches publiées\n\n")
        for w in warnings:
            fh.write(f"- ⚠ {w}\n")
    if len(fiches) == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
