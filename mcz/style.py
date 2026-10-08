CSS = """
:root{
  /* Charte MadCityZen 2025 : fond crème, encre aubergine, jaune primaire, bleu secondaire */
  --bg:#FFF9F0; --paper:#FBFDFF; --ink:#352C32; --muted:#5E545A; --line:#EADFCF;
  --primary:#F3AD22; --secondary:#64ACD9; --grad-a:#F8CF5C; --grad-b:#E8AE63; --alert:#B42318;
  --display:'Gabarito', 'Trebuchet MS', system-ui, sans-serif;
  --body:'Figtree', 'Segoe UI', system-ui, sans-serif;
  color-scheme: light;
}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--ink)}
a:focus-visible,button:focus-visible{outline:3px solid var(--secondary);outline-offset:3px}
.wrap{max-width:1200px;margin:0 auto;padding-inline:24px}
@media (max-width:480px){.wrap{padding-inline:16px}}
header.top{border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px 24px;padding-block:14px}
header.top img{height:46px;width:auto;display:block}
.kicker{font-family:var(--display);font-weight:600;font-size:13px;letter-spacing:.09em;text-transform:uppercase}
.meta{font-size:14px;color:var(--muted)}
.actions{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:10px;padding-top:20px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border:2px solid var(--ink);border-radius:999px;background:var(--ink);color:var(--bg);font-family:var(--display);font-weight:700;font-size:16px;line-height:1.1;text-decoration:none;cursor:pointer}
.btn:hover,.btn:focus-visible{background:var(--primary);border-color:var(--primary);color:var(--ink)}
.btn.ghost{background:transparent;color:var(--ink)}
.btn.ghost:hover,.btn.ghost:focus-visible{background:var(--primary);border-color:var(--primary)}
@media (max-width:560px){.actions{justify-content:stretch}.actions .btn{flex:1 1 0;justify-content:center;padding-inline:10px;font-size:15px}}
.headline{display:flex;flex-wrap:wrap;gap:28px;align-items:stretch;padding-block:20px 0}
.headline .txt{flex:1 1 520px;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:16px}
.headline .cover{flex:1 1 360px;min-width:0}
.headline .cover img{width:100%;height:100%;min-height:220px;max-height:340px;object-fit:cover;display:block;border-radius:24px}
h1{margin:0;font-family:var(--display);font-weight:900;font-size:clamp(36px,5.4vw,64px);line-height:1.04;text-wrap:balance}
h1 .sub{display:block;font-weight:700;font-size:.45em;line-height:1.2;margin-top:8px}
.callout{margin:0;padding:14px 18px;background:var(--paper);border:1px solid var(--line);border-radius:12px;font-size:18px;display:flex;gap:12px;align-items:flex-start}
.callout svg{flex:none;margin-top:3px}
.spec{margin:28px 0 0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--ink);border-radius:16px;background:var(--paper);overflow:hidden}
.spec div{display:flex;flex-direction:column;min-width:0;border-left:1px solid var(--ink)}
.spec div:first-child{border-left:0}
.spec dt{background:var(--primary);padding:11px 20px;font-family:var(--display);font-weight:700;font-size:15px;border-bottom:1px solid var(--ink)}
.spec dd{margin:0;padding:15px 20px;font-family:var(--display);font-weight:600;font-size:20px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
@media (max-width:640px){.spec{grid-template-columns:repeat(2,minmax(0,1fr))}.spec div:nth-child(3){border-left:0}.spec div:nth-child(n+3){border-top:1px solid var(--ink)}}
.body{display:flex;flex-wrap:wrap;gap:32px;align-items:flex-start;padding-block:44px 56px}
.main{flex:999 1 540px;min-width:0;display:flex;flex-direction:column;gap:28px}
.side{flex:1 1 340px;min-width:0;display:flex;flex-direction:column;gap:16px}
h2{margin:0;font-family:var(--display);font-weight:900;font-size:clamp(28px,3.2vw,38px);line-height:1.1}
ul.dash{margin:14px 0 0;padding:0;list-style:none;display:flex;flex-direction:column;gap:12px}
ul.dash>li{display:grid;grid-template-columns:8px 1fr;column-gap:14px}
ul.dash>li::before{content:"";width:8px;height:8px;margin-top:10px;border-radius:2px;background:var(--primary);outline:1px solid var(--ink)}
ul.sub{margin:8px 0 0;padding-left:20px;list-style:circle;display:flex;flex-direction:column;gap:4px}
.box{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:22px 26px}
.box h2{font-size:24px;font-weight:700}
.box ul{margin:10px 0 0;padding-left:20px}
.card{background:var(--paper);border:1px solid var(--ink);border-radius:16px;overflow:hidden}
.card h2{padding:13px 22px;background:var(--ink);color:var(--bg);font-weight:700;font-size:21px;line-height:1.25}
.card ul{margin:0;padding:16px 22px 18px 42px;display:flex;flex-direction:column;gap:8px}
.card ul ul{padding:6px 0 0 20px;gap:4px;list-style:circle}
.card.must{border:2px solid var(--alert)}
.card.must h2{background:var(--alert);color:#FFFFFF}
.link-site{display:inline-flex;align-self:flex-start;align-items:center;gap:10px;min-height:44px;padding:11px 22px;background:var(--bg);border:1px solid var(--ink);border-radius:999px;box-shadow:0 5px 0 var(--ink);text-decoration:none;font-weight:500}
.link-site:hover{background:#FFF3DD}
.media{background:var(--paper);border-top:1px solid var(--line)}
.media .wrap{padding-block:52px 72px}
.media h2{margin-bottom:22px}
.videos{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:20px;margin-bottom:24px}
.vthumb{position:relative;display:block;border-radius:20px;overflow:hidden;border:1px solid var(--ink);text-decoration:none;background:var(--ink)}
.vthumb img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.vthumb .play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:inline-flex;align-items:center;justify-content:center;width:80px;height:80px;border-radius:999px;background:var(--primary);border:1px solid var(--ink);box-shadow:0 5px 0 var(--ink);transition:transform .15s}
.vthumb:hover .play{transform:translate(-50%,-50%) scale(1.06)}
.vthumb .tag{position:absolute;left:14px;bottom:14px;padding:5px 12px;border-radius:999px;background:var(--ink);color:var(--bg);font-size:14px;font-weight:600}
video{width:100%;aspect-ratio:16/9;display:block;border-radius:20px;border:1px solid var(--ink);background:var(--ink)}
.gallery{columns:3 280px;column-gap:14px}
.gallery button{display:block;width:100%;padding:0;margin:0 0 14px;border:0;background:none;cursor:zoom-in;break-inside:avoid;border-radius:14px;overflow:hidden}
.gallery img{width:100%;height:auto;display:block}
.count{font-size:15px;color:var(--muted);margin:-12px 0 20px}
.empty{padding:28px;border:1px dashed var(--muted);border-radius:16px;color:var(--muted)}
footer.bot{background:var(--ink);color:var(--bg)}
footer.bot .wrap{display:flex;flex-wrap:wrap;gap:12px 24px;align-items:center;justify-content:space-between;padding-block:28px}
footer.bot a{color:var(--bg)}
.lb{position:fixed;inset:0;background:rgba(30,24,28,.92);display:flex;align-items:center;justify-content:center;padding:24px;z-index:10}
.lb img{max-width:100%;max-height:100%;border-radius:12px}
.lb button{position:absolute;top:calc(14px + env(safe-area-inset-top,0px));right:14px;min-width:44px;min-height:44px;border-radius:999px;border:1px solid var(--bg);background:var(--ink);color:var(--bg);font-size:22px;cursor:pointer}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
/* accueil */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:20px;padding-block:32px 64px}
.tile{display:flex;flex-direction:column;background:var(--paper);border:1px solid var(--line);border-radius:20px;overflow:hidden;text-decoration:none}
.tile:hover{border-color:var(--ink)}
.tile img{width:100%;aspect-ratio:3/2;object-fit:cover;display:block;background:var(--line)}
.tile .t{padding:16px 18px 20px;display:flex;flex-direction:column;gap:6px}
.tile .n{font-family:var(--display);font-weight:800;font-size:21px;line-height:1.2}
.tile .k{font-size:14px;color:var(--muted)}
.share{margin-top:auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:12px 18px 16px;border-top:1px solid var(--line)}
.share code{flex:1 1 180px;min-width:0;font-size:12px;overflow-wrap:anywhere;color:var(--muted);user-select:all}
.share button{min-height:40px;padding:8px 14px;border-radius:999px;border:1px solid var(--ink);background:var(--bg);color:var(--ink);font:500 14px var(--body);cursor:pointer}
"""
CSS += """
.spec-wrap{margin-top:28px;display:flex;flex-direction:column;gap:12px}
.spec-wrap .spec{margin:0}
.spec.cols-1{grid-template-columns:minmax(0,1fr)}.spec.cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.spec.cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}.spec.cols-5{grid-template-columns:repeat(5,minmax(0,1fr))}
@media (max-width:640px){.spec.cols-3,.spec.cols-5{grid-template-columns:repeat(2,minmax(0,1fr))}.spec div{border-left:0}.spec div:nth-child(even){border-left:1px solid var(--ink)}.spec div:nth-child(n+3){border-top:1px solid var(--ink)}}
.tbl{overflow-x:auto;border:1px solid var(--ink);border-radius:16px;background:var(--paper)}
.tbl table{width:100%;border-collapse:collapse;text-align:left}
.tbl th{background:var(--primary);padding:10px 16px;font-family:var(--display);font-weight:700;border-bottom:1px solid var(--ink)}
.tbl td{padding:10px 16px;border-top:1px solid var(--line);vertical-align:top}
.vlabel{font-family:var(--display);font-weight:700;font-size:18px;margin:0 0 8px}
.vitem{display:flex;flex-direction:column;min-width:0}
.vlink{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:10px 18px;border:1px solid var(--ink);border-radius:999px;text-decoration:none;font-weight:500;background:var(--bg)}
.extra p{margin:10px 0 0}
.cat{margin:40px 0 0;font-family:var(--display);font-weight:800;font-size:26px}
.grid.small{padding-block:16px 8px}
"""
