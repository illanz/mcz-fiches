"""Génération HTML des fiches et de la page d'accueil."""
import html
import json
import re
import unicodedata
from datetime import datetime

from .style import CSS

ROBOTS = "noindex, nofollow, noarchive, nosnippet, noimageindex"

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


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


TITLE_SEP = re.compile(r"\s+[-–—]\s*")


def split_title_parts(t):
    """« NOM - Sous-titre » → (nom, sous-titre)."""
    parts = TITLE_SEP.split(t.strip(), 1)
    return (parts[0], parts[1]) if len(parts) == 2 and parts[1] else (t, "")


def split_title(t):
    a, b = split_title_parts(t)
    return f'{esc(a)}<span class="sub">{esc(b)}</span>' if b else esc(t)


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


DL_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg>'
PRINT_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/></svg>'

PRINT_JS = """<script>
(function(){
  var b=document.getElementById('print-pdf'); if(!b) return;
  b.addEventListener('click', function(){
    var url=b.getAttribute('data-pdf');
    var ua=navigator.userAgent, mobile=/Android|iPhone|iPad|iPod/i.test(ua) || (navigator.maxTouchPoints>1 && /Macintosh/.test(ua));
    var safari=/^((?!chrome|chromium|android|crios|fxios|edg).)*safari/i.test(ua);
    if(mobile || safari){ window.open(url, '_blank', 'noopener'); return; }
    var old=document.getElementById('print-frame'); if(old) old.remove();
    var f=document.createElement('iframe'); f.id='print-frame'; f.src=url;
    f.style.cssText='position:fixed;right:0;bottom:0;width:1px;height:1px;border:0;opacity:0';
    f.onload=function(){ setTimeout(function(){ try{ f.contentWindow.focus(); f.contentWindow.print(); }catch(e){ window.open(url,'_blank','noopener'); } }, 300); };
    document.body.appendChild(f);
  });
})();
</script>"""


def page(f, logo, pdf=None):
    """f : modèle complet d'une fiche (contenu + médias préparés) ; pdf : adresse du résumé A4."""
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

    actions = ""
    if pdf:
        fname = f"Fiche-technique-MadCityZen-{f['slug']}.pdf"
        actions = (f'<div class="actions"><a class="btn" href="{pdf}" download="{fname}">{DL_ICON}<span>Télécharger la fiche PDF</span></a>'
                   f'<button type="button" class="btn ghost" id="print-pdf" data-pdf="{pdf}">{PRINT_ICON}<span>Imprimer</span></button></div>')
    short = split_title_parts(title)[0]
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="{ROBOTS}">
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
{actions}
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
{PRINT_JS if pdf else ""}
</body>
</html>
"""


CAT_CSS = """
.cnav{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
.cnav .wrap{display:flex;flex-wrap:wrap;gap:7px;align-items:center;padding-block:10px}
.cnav a{flex:none;display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border:1.5px solid var(--ink);border-radius:999px;text-decoration:none;color:var(--ink);font-family:var(--display);font-weight:700;font-size:14.5px;line-height:1;background:#fff}
.cnav a:hover,.cnav a:focus-visible{background:var(--primary)}
.cnav a small{font-weight:600;font-size:12px;opacity:.7}
.cnav input{flex:none;width:190px;margin-left:auto;padding:5px 12px;border:1.5px solid var(--line);border-radius:999px;font:inherit;font-size:15px;background:#fff;color:var(--ink)}
.cnav input:focus{outline:none;border-color:var(--ink)}
.intro{padding-block:26px 6px}
.intro h1{font-size:clamp(30px,4vw,46px)}
.intro p{margin:8px 0 0;max-width:64ch}
.csec{scroll-margin-top:110px;padding-top:26px}
.chead{display:flex;align-items:baseline;gap:14px;padding:12px 18px;background:var(--ink);color:var(--bg);border-radius:14px;border-left:10px solid var(--primary)}
.chead h2{font-size:clamp(24px,2.8vw,32px);font-weight:900;letter-spacing:.01em;text-transform:uppercase;color:var(--bg)}
.chead span{font-family:var(--display);font-weight:600;font-size:15px;color:var(--primary)}
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,165px),1fr));gap:10px;padding-top:12px}
.ct{display:flex;flex-direction:column;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;text-decoration:none;color:var(--ink);transition:border-color .15s,transform .15s}
.ct:hover,.ct:focus-visible{border-color:var(--ink);transform:translateY(-2px)}
.ct img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--line)}
.ct span{padding:7px 10px 9px;font-family:var(--display);font-weight:700;font-size:14.5px;line-height:1.2}
.ct span small{display:block;font-family:var(--body);font-weight:400;font-size:12.5px;color:var(--muted);margin-top:2px}
.noimg{display:flex;align-items:center;justify-content:center;aspect-ratio:16/9;background:var(--bg);border-bottom:1px solid var(--line)}
.ct .noimg img{width:42%;aspect-ratio:auto;object-fit:contain;background:none;opacity:.55}
.empty{display:none;padding:30px 0;color:var(--muted)}
.foot{padding-block:40px 56px;color:var(--muted);font-size:14px}
@media (max-width:760px){.cnav .wrap{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}.cnav input{width:130px;order:-1;margin-left:0}}
@media (max-width:560px){.cgrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.ct span{font-size:14px}}
"""


def index(fiches, logo, base_url):
    """Liste publique (non indexée) de toutes les fiches, par catégorie."""
    cats = []
    for f in fiches:
        if f["category"] not in cats:
            cats.append(f["category"])
    nav, blocks = [], []
    for i, c in enumerate(cats):
        items = [x for x in fiches if x["category"] == c]
        anchor = "c-" + (re.sub(r"[^a-z0-9]+", "-", strip_accents(c).lower()).strip("-") or str(i))
        nav.append(f'<a href="#{anchor}">{esc(c)} <small>{len(items)}</small></a>')
        tiles = []
        for f in items:
            img = f.get("thumb")
            im = f'<img src="{img}" alt="" loading="lazy" decoding="async">' if img else f'<i class="noimg"><img src="/{logo}" alt=""></i>'
            name, sub = split_title_parts(f["title"])
            sub_html = f"<small>{esc(sub)}</small>" if sub else ""
            tiles.append(f'<a class="ct" href="/{f["slug"]}" data-q="{esc(strip_accents(f["title"]).lower())}">{im}<span>{esc(name)}{sub_html}</span></a>')
        blocks.append(f'<section class="csec" id="{anchor}"><div class="chead"><h2>{esc(c)}</h2><span>{len(items)} fiche{"s" if len(items) > 1 else ""}</span></div><div class="cgrid">{"".join(tiles)}</div></section>')
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="{ROBOTS}">
<title>Fiches techniques MadCityZen</title>
<link rel="icon" href="/{logo}">
{FONTS}
<style>{CSS}{CAT_CSS}</style>
</head>
<body>
<header class="top"><div class="wrap"><img src="/{logo}" alt="MadCityZen"><span class="kicker">Fiches techniques</span></div></header>
<div class="wrap intro"><h1>Fiches techniques des animations</h1>
<p>{len(fiches)} animations classées par univers. Cliquez sur une fiche pour consulter le détail technique, le staff, les besoins sur place, les photos et les vidéos.</p></div>
<nav class="cnav" aria-label="Catégories"><div class="wrap">{"".join(nav)}<input type="search" placeholder="Rechercher…" aria-label="Rechercher une animation" id="q"></div></nav>
<main class="wrap">
{"".join(blocks)}
<p class="empty" id="none">Aucune animation ne correspond à cette recherche.</p>
</main>
<div class="wrap foot">MadCityZen · Animations et team building · <a href="https://www.madcityzen.fr">www.madcityzen.fr</a></div>
<script>
(function(){{
  var q=document.getElementById('q'), none=document.getElementById('none');
  function norm(s){{ return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim(); }}
  q.addEventListener('input', function(){{
    var v=norm(q.value), any=false;
    document.querySelectorAll('.csec').forEach(function(sec){{
      var n=0; sec.querySelectorAll('.ct').forEach(function(t){{ var ok=!v||t.getAttribute('data-q').indexOf(v)>=0; t.hidden=!ok; if(ok) n++; }});
      sec.hidden=n===0; if(n) any=true;
    }});
    none.style.display=any?'none':'block';
  }});
}})();
</script>
</body>
</html>
"""


def blank(logo):
    """Page neutre (accueil et erreur) : aucun lien vers les fiches."""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="{ROBOTS}">
<title>MadCityZen</title>
<link rel="icon" href="/{logo}">
{FONTS}
<style>{CSS}</style>
</head>
<body>
<main class="wrap" style="min-height:70vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;text-align:center">
<img src="/{logo}" alt="MadCityZen" style="height:72px;width:auto">
<p style="max-width:44ch;margin:0">Cette page n’est pas disponible. Pour toute information, rendez-vous sur <a href="https://www.madcityzen.fr">www.madcityzen.fr</a>.</p>
</main>
</body>
</html>
"""
