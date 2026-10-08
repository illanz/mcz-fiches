"""Génération HTML des fiches et de la page d'accueil."""
import html
import json
import re
from datetime import datetime

from .style import CSS

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gabarito:wght@600;700;800;900&family=Figtree:wght@400;500;600&display=swap">')

BULB = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18h6"></path><path d="M10 21h4"></path><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.4 1 1.1 1 1.8V16h5v-.3c0-.7.4-1.4 1-1.8A6 6 0 0 0 12 3z"></path></svg>'
PLAY = '<svg width="30" height="30" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="#352C32"></path></svg>'

LIGHTBOX_JS = """<script>
(function(){
  var lb=null;
  function close(){ if(lb){ lb.remove(); lb=null; } }
  document.addEventListener('click', function(e){
    var b=e.target.closest('[data-full]'); if(!b) return;
    close(); lb=document.createElement('div'); lb.className='lb'; lb.setAttribute('role','dialog'); lb.setAttribute('aria-label','Photo agrandie');
    var img=document.createElement('img'); img.src=b.getAttribute('data-full'); img.alt=b.querySelector('img').alt;
    var x=document.createElement('button'); x.type='button'; x.setAttribute('aria-label','Fermer'); x.textContent='×';
    x.addEventListener('click', close); lb.addEventListener('click', function(ev){ if(ev.target===lb) close(); });
    lb.appendChild(img); lb.appendChild(x); document.body.appendChild(lb); x.focus();
  });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') close(); });
})();
</script>"""


def esc(s):
    return html.escape(s or "")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def nodes_html(nodes, cls="dash"):
    out = []
    for n in nodes:
        if n["type"] == "group":
            out.append(nodes_html(n["children"], cls))
            continue
        sub = f'<ul class="sub">{nodes_html(n["children"], "sub")}</ul>' if n["children"] else ""
        if cls == "dash":
            out.append(f"<li><span>{n['html']}{sub}</span></li>")
        else:
            out.append(f"<li>{n['html']}{sub}</li>")
    return "".join(out)


def card_nodes(nodes):
    out = []
    for n in nodes:
        if n["type"] == "group":
            out.append(card_nodes(n["children"]))
            continue
        sub = f"<ul>{card_nodes(n['children'])}</ul>" if n["children"] else ""
        out.append(f"<li>{n['html']}{sub}</li>")
    return "".join(out)


def split_title(t):
    if " - " in t:
        a, b = t.split(" - ", 1)
        return f'{esc(a)}<span class="sub">{esc(b)}</span>'
    return esc(t)


def table_html(t, primary=False):
    n = len(t["headers"])
    if primary and n and len(t["rows"]) <= 3:
        blocks = []
        for row in t["rows"]:
            cells = "".join(f"<div><dt>{strip_tags(h) or '&nbsp;'}</dt><dd>{v or '&nbsp;'}</dd></div>" for h, v in zip(t["headers"], row))
            cls = "" if n == 4 else f" cols-{n}"
            blocks.append(f'<dl class="spec{cls}">{cells}</dl>')
        return f'<div class="spec-wrap">{"".join(blocks)}</div>'
    head = "".join(f"<th scope=\"col\">{strip_tags(h)}</th>" for h in t["headers"])
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in t["rows"])
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def fr_date(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except Exception:
        return ""


def dur(sec):
    return f"{int(sec) // 60}:{int(sec) % 60:02d}" if sec else None


def page(f, logo):
    """f : modèle complet d'une fiche (contenu + médias préparés)."""
    title = f["title"]
    secs = f["sections"]
    by_key = {}
    for s in secs:
        by_key.setdefault(s["key"], []).append(s)

    cover = f.get("cover")
    cover_html = f'<div class="cover"><img src="{cover}" alt="{esc(title)}"></div>' if cover else ""
    callout = f'<p class="callout">{BULB}<span>{f["callout"]}</span></p>' if f.get("callout") else ""

    tables = f["tables"]
    spec = table_html(tables[0], primary=True) if tables else ""
    other_tables = tables[1:]

    main = []
    for s in by_key.get("intro", []):
        main.append(f'<div class="extra"><ul class="dash">{nodes_html(s["nodes"])}</ul></div>')
    for s in by_key.get("deroule", []):
        main.append(f'<div><h2>{esc(s["title"])}</h2><ul class="dash">{nodes_html(s["nodes"])}</ul></div>')
    for s in by_key.get("options", []):
        main.append(f'<div class="box"><h2>{esc(s["title"])}</h2><ul>{card_nodes(s["nodes"])}</ul></div>')
    for s in by_key.get("other", []):
        main.append(f'<div class="extra"><h2>{esc(s["title"])}</h2><ul class="dash">{nodes_html(s["nodes"])}</ul></div>')
    for t in other_tables:
        main.append(table_html(t))
    for l in f["site_links"]:
        main.append(f'<a class="link-site" href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["text"])}</a>')

    side = []
    for key, cls in (("technique", "card"), ("staff", "card"), ("client", "card must")):
        for s in by_key.get(key, []):
            side.append(f'<div class="{cls}"><h2>{esc(s["title"])}</h2><ul>{card_nodes(s["nodes"])}</ul></div>')

    body_layout = f"""<section class="wrap body">
<div class="main">{''.join(main)}</div>
{'<aside class="side">' + ''.join(side) + '</aside>' if side else ''}
</section>"""

    # médias
    vids = []
    for v in f["videos"]:
        label = f'<p class="vlabel">{esc(v["label"])}</p>' if v.get("label") else ""
        if v["kind"] == "vimeo":
            d = dur(v.get("duration"))
            tag = "Vidéo" + (f" · {d}" if d else "")
            if v.get("thumb"):
                vids.append(f'<div class="vitem">{label}<a class="vthumb" href="{esc(v["link"])}" target="_blank" rel="noopener" aria-label="Lire la vidéo (nouvel onglet)"><img src="{v["thumb"]}" alt="Miniature de la vidéo" loading="lazy"><span class="play">{PLAY}</span><span class="tag">{tag}</span></a></div>')
            else:
                vids.append(f'<div class="vitem">{label}<a class="vlink" href="{esc(v["link"])}" target="_blank" rel="noopener">▶ Voir la vidéo</a></div>')
        elif v["kind"] == "file":
            poster = f' poster="{v["poster"]}"' if v.get("poster") else ""
            vids.append(f'<div class="vitem">{label}<video controls preload="none" playsinline{poster}><source src="{v["mp4"]}" type="video/mp4"></video></div>')
        elif v["kind"] == "link":
            vids.append(f'<div class="vitem">{label}<a class="vlink" href="{esc(v["link"])}" target="_blank" rel="noopener">▶ Voir la vidéo</a></div>')
    vids_html = f'<div class="videos">{"".join(vids)}</div>' if vids else ""

    photos = f["photos"]
    gal = ""
    if photos:
        items = "".join(
            f'<button type="button" data-full="{p["1600"]}" aria-label="Agrandir la photo {i + 1}"><img src="{p["800"]}" width="{min(800, p["w"])}" height="{round(min(800, p["w"]) * p["h"] / max(p["w"], 1))}" alt="{esc(title)}, photo {i + 1}" loading="lazy"></button>'
            for i, p in enumerate(photos))
        gal = f'<p class="count">{len(photos)} photo{"s" if len(photos) > 1 else ""}</p><div class="gallery">{items}</div>'
    media_extra = f'<ul class="dash">{nodes_html(f["media_nodes"])}</ul>' if f.get("media_nodes") else ""
    media_title = f.get("media_title") or ("Photos & Vidéos" if vids else "Photos")
    media_html = ""
    if vids or photos or media_extra:
        media_html = f'<section class="media"><div class="wrap"><h2>{esc(media_title)}</h2>{media_extra}{vids_html}{gal}</div></section>'

    short = title.split(" - ")[0]
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>{esc(short.title())} · Fiche technique MadCityZen</title>
<link rel="icon" href="/{logo}">
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
<img src="/{logo}" alt="MadCityZen">
<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px"><span class="kicker">Fiche technique</span><span class="meta">Mise à jour le {fr_date(f["updated"])}</span></div>
</div></header>
<main>
<section class="wrap">
<div class="headline">
<div class="txt"><h1>{split_title(title)}</h1>{callout}</div>
{cover_html}
</div>
{spec}
</section>
{body_layout}
{media_html}
</main>
<footer class="bot"><div class="wrap"><span class="kicker">MadCityZen · {esc(title)}</span><a href="https://www.madcityzen.fr" target="_blank" rel="noopener">www.madcityzen.fr</a></div></footer>
{LIGHTBOX_JS if photos else ""}
</body>
</html>
"""


def index(fiches, logo, base_url):
    cats = []
    for f in fiches:
        if f["category"] not in cats:
            cats.append(f["category"])
    blocks = []
    for c in cats:
        tiles = []
        for f in (x for x in fiches if x["category"] == c):
            img = f.get("thumb")
            im = f'<img src="{img}" alt="" loading="lazy">' if img else '<img alt="">'
            n_ph, n_v = len(f["photos"]), len(f["videos"])
            link = f"{base_url}/{f['slug']}"
            tiles.append(f'<div class="tile"><a href="/{f["slug"]}" style="display:flex;flex-direction:column;text-decoration:none">{im}<span class="t"><span class="n">{esc(f["title"])}</span><span class="k">{n_ph} photo{"s" if n_ph > 1 else ""} · {n_v} vidéo{"s" if n_v > 1 else ""}</span></span></a><div class="share"><code>{esc(link)}</code><button type="button" data-copy="{esc(link)}">Copier le lien</button></div></div>')
        blocks.append(f'<h2 class="cat">{esc(c)}</h2><div class="grid small">{"".join(tiles)}</div>')
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>Fiches techniques MadCityZen</title>
<link rel="icon" href="/{logo}">
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap"><img src="/{logo}" alt="MadCityZen"><span class="kicker">Fiches techniques</span></div></header>
<main class="wrap" style="padding-bottom:64px">
<h1 style="margin-top:36px;font-size:clamp(32px,4.4vw,52px)">Fiches techniques</h1>
<p style="max-width:62ch;margin:12px 0 0">{len(fiches)} fiches, mises à jour automatiquement depuis Notion. Copiez le lien d’une fiche pour le joindre à un devis.</p>
{"".join(blocks)}
</main>
<script>
document.addEventListener('click', function(e){{
  var b=e.target.closest('[data-copy]'); if(!b) return;
  var t=b.getAttribute('data-copy');
  function done(){{ b.textContent='Lien copié'; setTimeout(function(){{ b.textContent='Copier le lien'; }},1800); }}
  function fallback(){{ var r=document.createRange(); r.selectNodeContents(b.previousElementSibling); var s=getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent='Lien sélectionné'; }}
  try{{ navigator.clipboard.writeText(t).then(done, fallback); }}catch(err){{ fallback(); }}
}});
</script>
</body>
</html>
"""
