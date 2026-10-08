"""Fiche technique imprimable : une page A4 par animation.

Priorité aux informations pratiques (spécifications, fiche technique, staff, éléments à fournir,
options). Le déroulé n'apparaît qu'en résumé (premiers points, repris tels quels) selon la place
restante, avec quelques photos et un QR code vers la fiche complète en ligne.
Le contenu est ajusté automatiquement pour tenir sur une seule page."""
import html
import io
import re

import qrcode
import qrcode.image.svg

from .render import split_title, card_nodes, strip_tags, fr_date

ROBOTS = "noindex, nofollow, noarchive, nosnippet, noimageindex"


def qr_svg(url):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=1)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode()
    return svg[svg.index("<svg"):]


def deroule_summary(sections, budget=520):
    """Premiers points du déroulé, mot pour mot, jusqu'à la place prévue (coupe en fin de phrase)."""
    nodes = [n for s in sections if s["key"] == "deroule" for n in s["nodes"]]
    flat = []
    for n in nodes:
        if n["type"] == "group":
            flat += n["children"]
        else:
            flat.append(n)
    out, used, cut = [], 0, False
    for n in flat:
        text = n["html"]
        plain = strip_tags(text)
        if not plain:
            continue
        if used + len(plain) <= budget:
            out.append(text)
            used += len(plain)
            continue
        # coupe à la dernière fin de phrase qui tient
        room = budget - used
        if room > 120:
            sentences = re.split(r"(?<=[.!?])\s+", plain)
            acc = ""
            for s_ in sentences:
                if len(acc) + len(s_) + 1 > room:
                    break
                acc = (acc + " " + s_).strip()
            if acc:
                out.append(html.escape(acc) + " …")
        cut = True
        break
    return out, cut or len(out) < len(flat)


def page(f, logo, base_url):
    url = f"{base_url}/{f['slug']}"
    by_key = {}
    for s in f["sections"]:
        by_key.setdefault(s["key"], []).append(s)

    def block(key, cls=""):
        return "".join(
            f'<section class="box {cls}"><h3>{html.escape(s["title"])}</h3><ul>{card_nodes(s["nodes"])}</ul></section>'
            for s in by_key.get(key, []))

    spec = ""
    if f["tables"]:
        t = f["tables"][0]
        rows = "".join(
            "<div class=\"spec\">" + "".join(f"<div><span>{strip_tags(h)}</span><b>{v or '—'}</b></div>" for h, v in zip(t["headers"], r)) + "</div>"
            for r in t["rows"])
        spec = rows

    others = "".join(
        f'<section class="box"><h3>{html.escape(s["title"])}</h3><ul>{card_nodes(s["nodes"])}</ul></section>'
        for s in by_key.get("other", []))

    # déroulé : tous les points principaux, mot pour mot ; les derniers sont retirés si la page déborde
    flat = []
    for s in by_key.get("deroule", []):
        for n in s["nodes"]:
            flat += n["children"] if n["type"] == "group" else [n]
    flat = [n for n in flat if strip_tags(n["html"])]
    deroule = ""
    if flat:
        items = "".join(f'<li class="d">{n["html"]}</li>' for n in flat)
        deroule = (f'<section class="box soft" id="der"><h3>Déroulé (résumé)</h3><ul>{items}</ul>'
                   f'<p class="more" hidden>Déroulé complet sur la fiche en ligne.</p></section>')

    photos = []
    if f.get("cover"):
        photos.append(f["cover"].lstrip("/"))
    for p in f.get("photos", []):
        src = p["800"].lstrip("/")
        if src not in photos:
            photos.append(src)
    photos = photos[:3]
    ph_html = ""
    if photos:
        main = f'<img class="ph main" src="{photos[0]}" alt="">'
        small = "".join(f'<img class="ph" src="{p}" alt="">' for p in photos[1:3])
        ph_html = f'<div class="photos">{main}<div class="row">{small}</div></div>'

    n_ph, n_v = len(f.get("photos", [])), len(f.get("videos", []))
    media_note = []
    if n_ph:
        media_note.append(f"{n_ph} photo{'s' if n_ph > 1 else ''}")
    if n_v:
        media_note.append(f"{n_v} vidéo{'s' if n_v > 1 else ''}")
    media_txt = (" · ".join(media_note) + " à voir en ligne") if media_note else "Fiche complète en ligne"

    callout = f'<p class="callout">{f["callout"]}</p>' if f.get("callout") else ""

    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="robots" content="{ROBOTS}">
<title>{html.escape(f['title'])} · Fiche technique MadCityZen</title>
<style>
@font-face{{font-family:Gabarito;src:url(assets/gabarito-latin-wght-normal.woff2) format("woff2");font-weight:400 900}}
@font-face{{font-family:Figtree;src:url(assets/figtree-latin-wght-normal.woff2) format("woff2");font-weight:300 900}}
@page{{size:A4;margin:0}}
:root{{--ink:#352C32;--muted:#5E545A;--line:#E6DACB;--primary:#F3AD22;--bg:#FFF9F0;--alert:#B42318;--fs:9.4pt}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:#fff;color:var(--ink);font-family:Figtree,Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.sheet{{width:210mm;height:297mm;padding:11mm 12mm 9mm;display:flex;flex-direction:column;overflow:hidden;font-size:var(--fs);line-height:1.38}}
header{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid var(--primary);padding-bottom:3.5mm}}
header img{{height:12mm}}
header .k{{text-align:right;font-family:Gabarito,Arial,sans-serif;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:8.5pt}}
header .k small{{display:block;font-family:Figtree,Arial,sans-serif;font-weight:400;letter-spacing:0;text-transform:none;color:var(--muted);font-size:8pt;margin-top:1mm}}
.title{{margin:4.5mm 0 3mm}}
h1{{margin:0;font-family:Gabarito,Arial,sans-serif;font-weight:900;font-size:2.55em;line-height:1.02}}
h1 .sub{{display:block;font-weight:700;font-size:.46em;line-height:1.25;margin-top:1.2mm}}
.callout{{margin:2.2mm 0 0;padding:2mm 3mm;background:var(--bg);border-left:3px solid var(--primary);font-size:1.05em}}
.spec{{display:grid;grid-template-columns:repeat(auto-fit,minmax(0,1fr));border:1px solid var(--ink);border-radius:3mm;overflow:hidden;margin-bottom:2mm}}
.spec>div{{display:flex;flex-direction:column;border-left:1px solid var(--ink)}}
.spec>div:first-child{{border-left:0}}
.spec span{{background:var(--primary);padding:1.3mm 2.6mm;font-family:Gabarito,Arial,sans-serif;font-weight:700;font-size:.9em;border-bottom:1px solid var(--ink)}}
.spec b{{padding:1.8mm 2.6mm;font-family:Gabarito,Arial,sans-serif;font-weight:600;font-size:1.12em}}
.cols{{flex:1;min-height:0;display:grid;grid-template-columns:57fr 43fr;grid-template-rows:minmax(0,1fr);gap:4mm;margin-top:2mm}}
.col{{display:flex;flex-direction:column;gap:2.6mm;min-width:0;min-height:0}}
.col>*{{flex:none}}
.box{{border:1px solid var(--ink);border-radius:2.5mm;overflow:hidden;break-inside:avoid}}
.box h3{{margin:0;padding:1.4mm 3mm;background:var(--ink);color:#fff;font-family:Gabarito,Arial,sans-serif;font-weight:700;font-size:1.08em}}
.box ul{{margin:0;padding:2mm 3mm 2.2mm 6.5mm}}
.box li{{margin:.5mm 0}}
.box ul ul{{padding:.6mm 0 0 4mm;list-style:circle}}
.box.alert{{border:1.6px solid var(--alert)}}
.box.alert h3{{background:var(--alert)}}
.box.opt h3{{background:var(--primary);color:var(--ink)}}
.box.soft{{border-color:var(--line)}}
.box.soft h3{{background:var(--bg);color:var(--ink);border-bottom:1px solid var(--line)}}
.more[hidden]{{display:none}}
.more{{margin:0;padding:0 3mm 2mm;color:var(--muted);font-size:.9em;font-style:italic}}
.photos{{display:flex;flex-direction:column;gap:1.6mm}}
.photos .row{{display:grid;grid-template-columns:1fr 1fr;gap:1.6mm}}
.ph{{width:100%;object-fit:cover;border-radius:2mm;display:block}}
.ph.main{{height:42mm}}
.row .ph{{height:24mm}}
.online{{display:flex;gap:3mm;align-items:center;border:1px dashed var(--muted);border-radius:2.5mm;padding:2mm 2.6mm}}
.online svg{{width:19mm;height:19mm;flex:none}}
.online b{{font-family:Gabarito,Arial,sans-serif;font-size:1.02em;display:block}}
.online span{{color:var(--muted);font-size:.92em;word-break:break-all}}
footer{{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:2mm;margin-top:3mm;font-size:7.6pt;color:var(--muted)}}
</style></head>
<body><div class="sheet" id="sheet">
<header><img src="{logo}" alt="MadCityZen"><div class="k">Fiche technique<small>Mise à jour le {fr_date(f['updated'])}</small></div></header>
<div class="title"><h1>{split_title(f['title'])}</h1>{callout}</div>
{spec}
<div class="cols" id="cols">
<div class="col" id="left">{block('technique')}{block('staff')}{block('client', 'alert')}{block('options', 'opt')}{others}</div>
<div class="col" id="right">{ph_html}{deroule}<div class="online">{qr_svg(url)}<div><b>Fiche complète en ligne</b><span>{media_txt}<br>{html.escape(url.replace('https://', ''))}</span></div></div></div>
</div>
<footer><span>MadCityZen · Animations et team building</span><span>www.madcityzen.fr</span></footer>
</div>
<script>
// ajuste la taille du texte pour que tout tienne sur une page A4
(async function(){{
  await document.fonts.ready;
  await Promise.all([...document.images].map(i=>i.complete?0:new Promise(r=>{{i.onload=i.onerror=r}})));
  const sheet=document.getElementById('sheet'), cols=document.getElementById('cols'), root=document.documentElement;
  const over=()=>[...cols.children].some(c=>c.scrollHeight>cols.clientHeight+1);
  const dropOne=()=>{{ if(!der) return false; const li=der.querySelectorAll('li.d'); if(li.length<=1) return false;
    li[li.length-1].remove(); der.querySelector('.more').hidden=false; return true; }};
  let fs=10.2; root.style.setProperty('--fs', fs+'pt');
  // le résumé du déroulé va dans la colonne où il peut afficher le plus de points
  const L=document.getElementById('left'), R=document.getElementById('right');
  let der=document.getElementById('der');
  const derHTML=der?der.outerHTML:null;
  const place=(col)=>{{ const old=document.getElementById('der'); if(old) old.remove();
    const t=document.createElement('div'); t.innerHTML=derHTML; const d=t.firstChild;
    if(col===R) R.insertBefore(d, R.querySelector('.online')); else L.appendChild(d); return d; }};
  const fitCount=(d)=>{{ while(over()){{ const li=d.querySelectorAll('li.d'); if(li.length<=1) break; li[li.length-1].remove(); d.querySelector('.more').hidden=false; }} return over()?-1:d.querySelectorAll('li.d').length; }};
  let nL=0,nR=0; if(derHTML){{ nL=fitCount(place(L)); nR=fitCount(place(R)); if(nL>nR) place(L), fitCount(document.getElementById('der')); der=document.getElementById('der'); }}
  // 1) taille de lecture confortable : on raccourcit d'abord le résumé du déroulé
  while(over() && dropOne()){{}}
  // 2) puis on réduit le texte si les informations pratiques ne tiennent toujours pas
  while(over() && fs>6.6){{ fs-=0.2; root.style.setProperty('--fs', fs+'pt'); }}
  if(over()){{ const p=document.querySelector('.photos .row'); if(p) p.remove(); }}
  if(over() && der){{ der.remove(); }}
  window.__fit={{nL, nR, fs:+fs.toFixed(1), over:over(), deroule:der?der.querySelectorAll('li.d').length:0}};
}})();
</script>
</body></html>
"""
