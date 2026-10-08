"""Client minimal de l'API Notion (lecture seule), avec reprise automatique sur limite de débit."""
import os
import time
import requests

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"


class Notion:
    def __init__(self, token=None):
        self.token = token or os.environ["NOTION_TOKEN"]
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": VERSION,
            "Content-Type": "application/json",
        })
        self.calls = 0

    def _req(self, method, path, **kw):
        for attempt in range(8):
            self.calls += 1
            r = self.s.request(method, API + path, timeout=60, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                wait = float(r.headers.get("Retry-After", 2 ** attempt))
                time.sleep(min(wait, 30))
                continue
            if r.status_code >= 400:
                raise RuntimeError(f"Notion {method} {path} -> {r.status_code}: {r.text[:300]}")
            time.sleep(0.34)  # ~3 requêtes / seconde
            return r.json()
        raise RuntimeError(f"Notion {method} {path}: trop de tentatives")

    def page(self, page_id):
        return self._req("GET", f"/pages/{page_id}")

    def children(self, block_id):
        out, cursor = [], None
        while True:
            q = "?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
            r = self._req("GET", f"/blocks/{block_id}/children{q}")
            out += r["results"]
            if not r.get("has_more"):
                return out
            cursor = r["next_cursor"]

    def tree(self, block_id, skip_types=("child_database", "child_page")):
        """Tous les blocs, avec leurs enfants dans b['_children']."""
        blocks = self.children(block_id)
        for b in blocks:
            if b.get("has_children") and b["type"] not in skip_types:
                b["_children"] = self.tree(b["id"], skip_types)
        return blocks

    def query_data_source(self, ds_id, flt=None, sorts=None):
        out, cursor = [], None
        while True:
            body = {"page_size": 100}
            if flt:
                body["filter"] = flt
            if sorts:
                body["sorts"] = sorts
            if cursor:
                body["start_cursor"] = cursor
            r = self._req("POST", f"/data_sources/{ds_id}/query", json=body)
            out += r["results"]
            if not r.get("has_more"):
                return out
            cursor = r["next_cursor"]


def plain(rich):
    return "".join(t.get("plain_text", "") for t in rich or [])


def file_url(obj):
    """URL d'un objet fichier Notion (file / external / file_upload)."""
    if not obj:
        return None
    t = obj.get("type")
    if t == "external":
        return obj["external"]["url"]
    if t == "file":
        return obj["file"]["url"]
    return None
