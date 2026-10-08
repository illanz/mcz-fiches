"""Transforme les blocs Notion d'une fiche en modèle de données, sans rien reformuler.

Les sections sont reconnues par leur titre Notion (Déroulé, Options disponibles, Fiche technique,
Staff, Le client doit fournir, Photos & Vidéos). Toute autre section est conservée telle quelle,
avec son titre : aucun contenu de la fiche n'est perdu."""
import html
import re
import unicodedata

from .notion import plain

KNOWN = [
    ("deroule", "Déroulé"),
    ("options", "Options disponibles"),
    ("technique", "Fiche technique"),
    ("staff", "Staff"),
    ("client", "Le client doit fournir"),
    ("media", "Photos & Vidéos"),
]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9& ]", " ", s)).strip()


def section_key(title):
    n = norm(title)
    if n.startswith("deroule"):
        return "deroule"
    if n.startswith("options") or n == "option":
        return "options"
    if n.startswith("fiche technique"):
        return "technique"
    if n.startswith("staff"):
        return "staff"
    if "doit fournir" in n:
        return "client"
    if n.startswith("photo") or n.startswith("video"):
        return "media"
    return None


def is_internal(url):
    return (not url) or url.startswith("/") or "notion.so" in url or "notion.site" in url or "notion.com" in url


def rich_html(rich):
    out = []
    for t in rich or []:
        txt = html.escape(t.get("plain_text", ""), quote=False)
        if not txt:
            continue
        a = t.get("annotations") or {}
        if a.get("code"):
            txt = f"<code>{txt}</code>"
        if a.get("bold"):
            txt = f"<strong>{txt}</strong>"
        if a.get("italic"):
            txt = f"<em>{txt}</em>"
        if a.get("strikethrough"):
            txt = f"<s>{txt}</s>"
        href = t.get("href")
        if href and not is_internal(href):
            txt = f'<a href="{html.escape(href)}" target="_blank" rel="noopener">{txt}</a>'
        out.append(txt)
    s = "".join(out).replace("\n", "<br>")
    s = re.sub(r"</strong><strong>", "", s)
    return s


def first_link(rich):
    for t in rich or []:
        if t.get("href") and not is_internal(t["href"]):
            return t["href"]
    return None


LIST_TYPES = ("bulleted_list_item", "numbered_list_item", "to_do", "toggle")
TEXT_TYPES = ("paragraph", "quote", "callout")


class FicheParser:
    def __init__(self, notion=None):
        self.notion = notion
        self.reset()

    def reset(self):
        self.callout = None
        self.sections = []          # [{key, title, nodes}]
        self.cur = None
        self.tables = []            # [{headers, rows}]
        self.site_links = []        # [{text, url}]
        self.videos = []            # [{kind, url, label, block_id, name}]
        self.images = []            # [{url, block_id}]
        self.pending_label = None
        self.media_title = None

    # ---- sections
    def open_section(self, title):
        key = section_key(title)
        if key == "media":
            self.media_title = title.strip()
        self.cur = {"key": key or "other", "title": title.strip(), "nodes": []}
        self.sections.append(self.cur)

    def add_node(self, node):
        if self.pending_label:  # titre de vidéo non suivi d'une vidéo : conservé comme texte
            label, self.pending_label = self.pending_label, None
            self.add_node({"type": "item", "html": f"<strong>{html.escape(label)}</strong>", "children": []})
        if self.cur is None:
            self.cur = {"key": "intro", "title": "", "nodes": []}
            self.sections.append(self.cur)
        self.cur["nodes"].append(node)

    # ---- nodes
    def list_node(self, b):
        t = b["type"]
        data = b[t]
        text = rich_html(data.get("rich_text"))
        if t == "to_do":
            text = ("☑ " if data.get("checked") else "☐ ") + text
        children = []
        for c in b.get("_children", []):
            n = self.child_node(c)
            if n:
                children.append(n)
        if not text.strip() and not children:
            return None
        return {"type": "item", "html": text, "children": children}

    def child_node(self, b):
        t = b["type"]
        if t in LIST_TYPES:
            return self.list_node(b)
        if t in TEXT_TYPES:
            text = rich_html(b[t].get("rich_text"))
            kids = [n for n in (self.child_node(c) for c in b.get("_children", [])) if n]
            if not text.strip() and not kids:
                return None
            return {"type": "item", "html": text, "children": kids}
        if t in ("link_to_page", "child_page"):
            title = self.page_title(b)
            return {"type": "item", "html": html.escape(title), "children": []} if title else None
        if t in ("column_list", "column", "synced_block"):
            kids = [n for n in (self.child_node(c) for c in b.get("_children", [])) if n]
            return {"type": "group", "children": kids} if kids else None
        return None

    def page_title(self, b):
        if b["type"] == "child_page":
            return b["child_page"].get("title", "")
        if not self.notion:
            return ""
        ltp = b["link_to_page"]
        pid = ltp.get("page_id")
        if not pid:
            return ""
        try:
            p = self.notion.page(pid)
            for prop in p.get("properties", {}).values():
                if prop.get("type") == "title":
                    return plain(prop["title"])
        except Exception:
            return ""
        return ""

    # ---- walk
    def walk(self, blocks):
        for b in blocks:
            t = b["type"]
            if t in ("column_list", "column", "synced_block"):
                self.walk(b.get("_children", []))
            elif t in ("heading_1", "heading_2", "heading_3"):
                rich = b[t].get("rich_text")
                text = plain(rich).strip()
                link = first_link(rich)
                if link and ("lien vers" in norm(text) or "madcityzen.fr" in link):
                    self.site_links.append({"text": text, "url": link})
                    continue
                if not text:
                    continue
                if self.cur and self.cur["key"] == "media" and section_key(text) is None:
                    self.pending_label = text  # ex. « Option : Clip Animé Mosaic Balade »
                    continue
                self.open_section(text)
                if b.get("_children"):  # titre dépliable
                    self.walk(b["_children"])
            elif t == "callout" and self.callout is None and not self.sections:
                self.callout = rich_html(b[t].get("rich_text"))
                kids = [n for n in (self.child_node(c) for c in b.get("_children", [])) if n]
                if kids:
                    self.add_node({"type": "group", "children": kids})
            elif t == "table":
                rows = [[rich_html(c) for c in r["table_row"]["cells"]] for r in b.get("_children", []) if r["type"] == "table_row"]
                if rows:
                    has_head = b["table"].get("has_column_header", True)
                    headers = rows[0] if has_head else [""] * len(rows[0])
                    body = rows[1:] if has_head else rows
                    # retire les colonnes entièrement vides
                    keep = [i for i in range(len(headers)) if re.sub(r"<[^>]+>", "", headers[i]).strip() or any(re.sub(r"<[^>]+>", "", r[i]).strip() for r in body if i < len(r))]
                    self.tables.append({
                        "headers": [re.sub(r"</?strong>", "", headers[i]) for i in keep],
                        "rows": [[r[i] if i < len(r) else "" for i in keep] for r in body],
                        "section": self.cur["key"] if self.cur else "intro",
                    })
            elif t == "video":
                v = b["video"]
                if v.get("type") == "external":
                    self.videos.append({"kind": "external", "url": v["external"]["url"], "label": self.pending_label, "block_id": b["id"]})
                elif v.get("type") == "file":
                    self.videos.append({"kind": "file", "url": v["file"]["url"], "label": self.pending_label, "block_id": b["id"],
                                        "name": v.get("name") or "", "edited": b.get("last_edited_time")})
                self.pending_label = None
            elif t in ("embed", "bookmark"):
                url = b[t].get("url", "")
                if "vimeo.com" in url or "youtube.com" in url or "youtu.be" in url:
                    self.videos.append({"kind": "external", "url": url, "label": self.pending_label, "block_id": b["id"]})
                    self.pending_label = None
                elif url:
                    self.add_node({"type": "item", "html": f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(url)}</a>', "children": []})
            elif t == "image":
                im = b["image"]
                url = im.get(im.get("type"), {}).get("url")
                if url:
                    self.images.append({"url": url, "block_id": b["id"], "edited": b.get("last_edited_time")})
            elif t == "child_database":
                continue  # galerie « Photos Animations » : lue directement dans la base
            elif t in ("paragraph", "quote") or t in LIST_TYPES or t in ("link_to_page", "child_page", "callout"):
                # un paragraphe qui n'est qu'un lien vers madcityzen.fr = lien vers la page du site
                if t == "paragraph":
                    rich = b[t].get("rich_text")
                    link = first_link(rich)
                    if link and "madcityzen.fr" in link and "lien vers" in norm(plain(rich)):
                        self.site_links.append({"text": plain(rich).strip(), "url": link})
                        continue
                n = self.child_node(b)
                if n:
                    self.add_node(n)

    def parse(self, blocks):
        self.reset()
        self.walk(blocks)
        # sections vides retirées
        self.sections = [s for s in self.sections if s["nodes"] or s["key"] == "media"]
        return {
            "callout": self.callout,
            "sections": [s for s in self.sections if s["key"] != "media"],
            "media_nodes": [n for s in self.sections if s["key"] == "media" for n in s["nodes"]],
            "media_title": self.media_title,
            "tables": self.tables,
            "site_links": self.site_links,
            "videos": self.videos,
            "images": self.images,
        }
