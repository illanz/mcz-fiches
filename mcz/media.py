"""Téléchargement et préparation des médias (photos, couvertures, vidéos, miniatures Vimeo).

Chaque fichier préparé est mis en cache sous une clé stable : il n'est retraité que si la source
change dans Notion. Les fichiers finaux portent des noms neutres (aucun nom de fichier d'origine,
donc aucun nom de client ou de prestataire n'apparaît dans les adresses)."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:  # HEIC facultatif
    pass

MAX_VIDEO = 24 * 1024 * 1024  # limite Cloudflare Pages : 25 Mio par fichier


def key(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


class Media:
    def __init__(self, cache_dir: Path, out_dir: Path, log=print):
        self.cache = cache_dir / "files"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.out = out_dir / "media"
        self.out.mkdir(parents=True, exist_ok=True)
        self.log = log
        self.http = requests.Session()
        self.http.headers["User-Agent"] = "mcz-fiches-builder"
        meta = cache_dir / "vimeo.json"
        self.vimeo_meta_path = meta
        self.vimeo_meta = json.loads(meta.read_text()) if meta.exists() else {}

    def save_meta(self):
        self.vimeo_meta_path.write_text(json.dumps(self.vimeo_meta, ensure_ascii=False))

    # ---- utilitaires
    def _publish(self, name, sub):
        src = self.cache / name
        dst = self.out / sub / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
        return f"media/{sub}/{name}"

    def _download(self, url):
        r = self.http.get(url, timeout=120)
        r.raise_for_status()
        return r.content

    def _save_jpeg(self, im, path, maxside, quality=82):
        im = im.copy()
        im.thumbnail((maxside, maxside))
        if im.mode not in ("RGB", "L"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.convert("RGBA").split()[-1])
            im = bg
        im.convert("RGB").save(path, "JPEG", quality=quality, optimize=True, progressive=True)

    # ---- images
    def image(self, url, k, sub="p", sizes=(800, 1600)):
        """Retourne {'w','h', '<taille>': chemin publié} ou None."""
        names = {s: f"{k}-{s}.jpg" for s in sizes}
        info_path = self.cache / f"{k}.json"
        if not all((self.cache / n).exists() for n in names.values()) or not info_path.exists():
            if not url:
                return None
            try:
                im = Image.open(BytesIO(self._download(url)))
                im = ImageOps.exif_transpose(im)
            except Exception as e:
                self.log(f"  ! image illisible ({e.__class__.__name__}) {urlparse(url).path[-60:]}")
                return None
            for s, n in names.items():
                self._save_jpeg(im, self.cache / n, s)
            w, h = im.size
            info_path.write_text(json.dumps({"w": w, "h": h}))
        info = json.loads(info_path.read_text())
        res = {"w": info["w"], "h": info["h"]}
        for s, n in names.items():
            res[s] = self._publish(n, sub)
        return res

    def cached_image(self, k, sub="p", sizes=(800, 1600)):
        names = [f"{k}-{s}.jpg" for s in sizes]
        if all((self.cache / n).exists() for n in names) and (self.cache / f"{k}.json").exists():
            return self.image(None, k, sub, sizes)
        return None

    # ---- vidéos hébergées dans Notion
    def video_file(self, url, k):
        mp4, jpg = f"{k}.mp4", f"{k}.jpg"
        if not (self.cache / mp4).exists():
            if not url:
                return None
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "src"
                with self.http.get(url, timeout=600, stream=True) as r:
                    r.raise_for_status()
                    with open(src, "wb") as f:
                        for chunk in r.iter_content(1 << 20):
                            f.write(chunk)
                ok = False
                for height, crf in ((720, 26), (720, 30), (540, 32), (480, 34)):
                    dst = Path(td) / "out.mp4"
                    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                           "-vf", f"scale=-2:'min({height},ih)'", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                           "-movflags", "+faststart", str(dst)]
                    if subprocess.run(cmd).returncode != 0:
                        break
                    if dst.stat().st_size <= MAX_VIDEO:
                        shutil.copy2(dst, self.cache / mp4)
                        ok = True
                        break
                if not ok:
                    self.log("  ! vidéo trop lourde ou illisible, ignorée")
                    return None
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(self.cache / mp4),
                                "-frames:v", "1", "-vf", "scale=1280:-2", str(self.cache / jpg)])
        res = {"mp4": self._publish(mp4, "v")}
        if (self.cache / jpg).exists():
            res["poster"] = self._publish(jpg, "v")
        return res

    # ---- Vimeo
    @staticmethod
    def vimeo_link(url):
        """Lien public propre vers la vidéo (sans paramètres de partage)."""
        u = urlparse(url)
        if "player.vimeo.com" in u.netloc:
            vid = u.path.rstrip("/").split("/")[-1]
            h = parse_qs(u.query).get("h", [None])[0]
            return f"https://vimeo.com/{vid}" + (f"/{h}" if h else "")
        return f"https://vimeo.com{u.path}".rstrip("/")

    def vimeo(self, url):
        link = self.vimeo_link(url)
        meta = self.vimeo_meta.get(link)
        if meta is None:
            try:
                r = self.http.get("https://vimeo.com/api/oembed.json", params={"url": link, "width": 1280}, timeout=30)
                meta = r.json() if r.ok else {}
            except Exception:
                meta = {}
            meta = {k: meta.get(k) for k in ("thumbnail_url", "duration", "title")}
            self.vimeo_meta[link] = meta
        res = {"link": link, "duration": meta.get("duration")}
        if meta.get("thumbnail_url"):
            th = self.image(meta["thumbnail_url"], key("vimeo", link), sub="t", sizes=(1280,))
            if th:
                res["thumb"] = th[1280]
        return res
