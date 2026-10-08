# Fiches techniques MadCityZen

Site des fiches techniques des animations, généré automatiquement depuis Notion
(page « Fiches Descriptives Animations » et base « Photos Animations ») et publié sur
Cloudflare Pages : **https://fiches.madcityzen.fr**

## Au quotidien

- **Modifier une fiche** : modifier la page dans Notion. Le site se met à jour seul
  3 fois par jour (≈ 5h, 12h, 17h).
- **Ajouter des photos** : ajouter une ligne dans « Photos Animations » avec la bonne étiquette.
- **Publier tout de suite** : GitHub → onglet **Actions** → « Publier les fiches techniques »
  → **Run workflow**.
- **Lien d'une fiche** : `https://fiches.madcityzen.fr/<nom-de-la-fiche>`. La liste complète, avec
  les boutons « Copier le lien », est à une adresse interne non devinable :
  `https://fiches.madcityzen.fr/<catalogue_path>/` (voir `config/site.json`). Ne jamais la publier.

## Ajouter une nouvelle fiche

1. Créer la page dans Notion et l'ajouter dans la page « Fiches Descriptives Animations ».
2. À la publication suivante, elle apparaît automatiquement (adresse déduite de son titre).
3. Pour afficher sa galerie photo, ajouter son étiquette « Photos Animations » dans
   `config/fiches.json` (champ `photo_tags`). Le résumé de chaque publication (onglet Actions)
   signale les fiches concernées.

⚠ Ne jamais modifier le `slug` d'une fiche existante : c'est l'adresse déjà envoyée aux clients.

## Fonctionnement

- `build.py` lit Notion (jeton `NOTION_TOKEN`, lecture seule), prépare photos (800 et 1600 px),
  couvertures, miniatures Vimeo et vidéos Notion (converties en MP4 ≤ 24 Mo), puis génère `out/`.
- Le texte est repris **tel quel** de Notion ; toute section non standard est conservée.
- Un cache évite de retraiter ce qui n'a pas changé.
- Non-référencement : balise `robots` et en-tête `X-Robots-Tag` (noindex, nofollow, noarchive,
  nosnippet, noimageindex) sur toutes les réponses, y compris photos et vidéos ; `robots.txt` laisse
  passer les robots pour qu'ils lisent cette consigne ; accueil et page d'erreur neutres, sans lien
  vers les fiches ; l'adresse technique `*.pages.dev` redirige vers le domaine (`redirect_pages_dev`).
- Secrets GitHub nécessaires : `NOTION_TOKEN`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
