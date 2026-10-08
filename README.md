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
- **Lien d'une fiche** : `https://fiches.madcityzen.fr/<nom-de-la-fiche>` (liste et boutons
  « Copier le lien » sur la page d'accueil du site).

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
- Les pages sont exclues des moteurs de recherche (`noindex`).
- Secrets GitHub nécessaires : `NOTION_TOKEN`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
