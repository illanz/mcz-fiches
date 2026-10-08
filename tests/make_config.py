"""Génère config/fiches.json (une fois) : id Notion -> slug figé, étiquette(s) de galerie, catégorie.
Les slugs sont figés pour que les liens envoyés dans les devis ne changent jamais."""
import json, re, unicodedata
from pathlib import Path

ROWS = [
# (catégorie, id, titre, [étiquettes galerie])
("Artistique","d7eaab89d55743f5b890f7b45d2502a4","ATELIER FRESQUE",["Fresque Keith Haring"]),
("Artistique","6ea042e9a18f4ff58e223e295ecee572","FRESQUE SUR MESURE",["Fresque Complexe"]),
("Artistique","b74ebfce844d44cb9cb83736b6d4ac6d","ATELIER GRAFFITI",["Graffiti"]),
("Artistique","bce7cb1d1968424ead326e00ffa160d9","ATELIER MOSAÏQUE",["Atelier mosaïque"]),
("Artistique","b634e917b9d640a9a8f587b861d6c39d","GRAFFWALL - Street Art Corporate",["GraffWall"]),
("Artistique","87ea4dda56924cee820369b99662f254","LIGHT PAINTING",["Light Painting"]),
("Artistique","a4e00e9bdd634d928b3bec80ca0398fa","ON THE GROUND - Stand Photo Original",["On the Ground"]),
("Artistique","f845b482c26c4fbb86b1e59c935b8b5f","PHOTO MOSAIC WALL - Atelier Photo Mosaïque",["Photo Mosaique Wall"]),
("Artistique","cba05b3acfa14234af43e2ba4241abd4","POSTER BOX - Posters Géants",["Poster Box"]),
("Artistique","7201e30c256a4794895943e496441fc3","SLEEVE FACE",["Sleeve Face"]),
("Cinéma","5899746bc7e7455b9c76176269faacda","ATELIER COURTS MÉTRAGES - Cameras",["Courts Métrages"]),
("Cinéma","19869304d14880c48b20c17423f15be7","ATELIER COURTS METRAGES - Tablettes",["Courts Métrages"]),
("Cinéma","0a0c571f55664f2eac9ec93d55ffc6eb","ATELIER DOUBLAGE -Doublage Cinéma",["Doublage"]),
("Cinéma","108ed48a2dd74fc4a72635b9c7252604","CLIP DUB",["Clip Dub"]),
("Cinéma","ef0b86b6ac0d4ee5bff874a5af2f822e","HOME STORY - Interview d’Equipe a distance",["Home Story"]),
("Cinéma","8e69dc033094453fa0ea927353eef1a2","TRUCK TRUCK STUDIO - Studio Audiovisuel Mobile",["Truck Truck Studio"]),
("Cinéma","7709b15bd6d8455387fb0015cae8ff54","ZAPPING",["Zapping"]),
("Créatif","f669588c0cd244fda6abfc353233cf22","CREATION DE PARFUMS",["Création de parfums"]),
("Créatif","da8673b8bef843b790cd10aef9fcad8b","CUSTOM PARTY - Personnalisation d’objets",["Custom Party"]),
("Créatif","da6ef3e9125149f7ba374622e81a8502","ORIGAMI",["Origami"]),
("Cuisine","e2ac41234b4f42afb032d07ef680291c","COCKTAIL GAGNANT - Atelier Cocktail",["Création Cocktails"]),
("Cuisine","40fe827edfb541c1b69c2f00019d9974","HOME COOKING - Atelier Cuisine en Ligne",["Home Cooking"]),
("Musical","1bbe2c57f8484111a1e98a6786b051dd","AFRICAN BEATS",["African beats"]),
("Musical","89e1a3b091544f0cad58aa7c36faedfd","BODY PERC - Atelier Body Percussions",["Body Perc"]),
("Musical","f7c6092deb124d6b865d9ca22ee1ba36","FLASH MOB",["Flash Mob"]),
("Musical","0fc1d5c7817d437a9cebb3f6297feee7","LA BOITE A CHANSONS - Cabine Karaoke",["Boîte à Chansons"]),
("Musical","83106246cd21423ca0a1c04991814525","LIP DUB STUDIO",["Lip Dub Studio"]),
("Musical","d7502335314b4177beffab41175152d1","SAMBA BATUCADA",["Batucada"]),
("Musical","b456e6856b3a4a239e468a2d671a2b03","TAP TAP SYMPHONY",["Tap Tap Symphony"]),
("Musical","74a8aece21ab480b8095cdac58593cef","TEAM HAKA - Haka d'Entreprise",["Haka"]),
("Bien-Être","7fbab55038e44f219c9404b657506041","ATELIER D-TOX",["Atelier D-tox"]),
("Bien-Être","82ee0cee9aad4c7f97df53187318e5eb","INITIATION AU QI GONG",[]),
("Bien-Être","29c545a08ef74d009092a58f79a723e0","INITIATION AU YOGA",[]),
("Bien-Être","d19cb12ba78a4515b3d4592641e45fa6","MASSAGE AMMA",["Massage Amma"]),
("Bien-Être","13de1dbb5c1c4f0281f5cf78a43c144a","RELAX@HOME",[]),
("Digital","f4211e5cb05643e1ae94f9c5a2110129","4D SIMULATEUR",["4D Simulateur"]),
("Digital","1277b7e874e8444aa373ba4fb0ed34ea","BREAK WALL",["Break Wall"]),
("Digital","b4c2131535b647659ac88d0557bbed02","BUBBLE BOARD - Mur digital collectif",["BubbleBoard"]),
("Digital","9ff22046cdc24742923d4fdc65e0e111","COURSE DIGITALE",["Team Race"]),
("Digital","d1b09a1c8f3d42f2badffc3efd61fe65","DIGI BEER PONG - Beer Pong Digital",["Digibeer Pong"]),
("Digital","801a102e120d4effbb59fde78e8b37ea","DIGITAL MOSAIC",["Mosaïc Digitale"]),
("Digital","272dab463243482185e5908780ca0a13","DRONES VOLANTS",["Drones volants"]),
("Digital","2828c1a7edcb4fedbccb18d12f06a609","FAB BAR - Atelier Fab Lab",["Fab Bar"]),
("Digital","1cbfcc2462594a73ae649ea9e34b2704","GRAFFITI DIGITAL",["Graff IT"]),
("Digital","19169304d1488000bb49e802f28cd1e7","MINI U CRISTAL",["Mini U Cristal"]),
("Digital","0cffedb8f1c34beba370c2f972d4d776","MINI U - Figurines 3D",["Mini U"]),
("Digital","d1ed5fc533094e2c82afe03721a51c27","MINI U FOR YOU",["Mini U"]),
("Digital","1e0fcb70f7c74cd0b43a1862f6d3ee15","PAC MAN VR",["Pac Man VR"]),
("Digital","039cb0443c5141848479e53e7f658928","PHOTO BOOTH VIRTUEL",[]),
("Digital","f8c2cd16fb214ae29e8d7b4a4cee5346","RÉALITÉ VIRTUELLE",["HTC Vive Total Immersion"]),
("Digital","3d8faf6809cc45a1be383eed4101194f","RETRO GAMING",["Retro Games"]),
("Digital","85d888968dd24d44976e2d11c5bebec6","ROBOTS BOXE",["Robot Boxe"]),
("Digital","c17ebdf6d6544f2aa937614b3becbbd0","ROBOTS FOOT",["Robot Foot"]),
("Digital","9400022c41d64cabb9b43740279e24c0","TARGETS",["Targets"]),
("Digital","de4d6078f203473991a7d6029f92ff64","TEAM RACE - Course Digitale",["Team Race"]),
("Digital","5374b76b10f94497a0f3f92abf5f53c8","VR 360°",["VR 360°"]),
("Insolite","49c7458b9ba446fe9d765b5065fd6702","BATAILLE DE POLOCHONS",["Bataille de Polochons"]),
("Insolite","1f437b557c964ec5ae6164d7018be5fb","BLINDSTORMING",[]),
("Insolite","29f2f85a10844d8dab166fcf5a35f35b","DESTRUCTION CONSTRUCTIVE - Rage Room",["Destruction Constructive"]),
("Insolite","b52ef386ddc544cfa6842f4389352564","OFFICE BATTLEFIELD",["Office Battlefield"]),
("Insolite","15f10fadec0a4acd9a68875a2dd18849","SECRET DEFI",[]),
("Construction","1c24789c41194cddb23eea628e319711","LEGO MANIA - Défi Lego",["Lego Mania"]),
("Construction","023c8105107c4c99bb2d727ad11d560d","ROBOT MAKERS - Challenge Robotique",["Robot Makers"]),
("Enquête","64ae8df663134a13a6e54dc918d9ebbc","ESCAPE GAME VISIO - Escape Game Virtuel",["Escape Game Visio"]),
("Enquête","8ca61f9fee294113a57d62ae7cdefabe","SPACE K - Escape Game Entreprise",["Escape Game Space K"]),
("Jeu de piste","56ba83aad0e044d597699198aafd8c3b","RALLYE 3.0",[]),
("Jeu de piste","14f3832ece644c96b3bab6a576eb72c0","RALLYE INTERACTIF",["Rallye Interactif"]),
("Olympiades","f6b528c28e7f462a858d4222e09d4ee3","DEGUSTATION D’INSECTES",["Dégustation insectes"]),
("Olympiades","9ae14d3ce8b143bd9f9533b391ba895c","EXTRÊME DÉFI",["Extrêmes Défis"]),
("Olympiades","e2fa8e6c8448424f80628f672dc3580d","MAD GAMES - Olympiades Enteprise",["Mad Games"]),
("Olympiades","1ba69304d148803dabf5c13baa3a668b","OBJECTIF TOTEM - Olympiades Koh Lanta",["Objectif Totem"]),
("Quiz","9dfb4c07b8b6430988e06b5f5d724723","SUPER QUIZ - Quiz Entreprise",[]),
("Quiz","cc434382209f49c49a1c2fd51de17e0f","CLICK & MEET - Qui est Qui ?",["Click & Meet"]),
("Quiz","e24bffe0c7784bc98d817bf2bb9f0d4b","HOME BLIND TEST",[]),
("Quiz","c49f79ab2817479d800e3da1072b6a5c","HOME CHALLENGE - Challenge a Domicile",["Quiz Ciné Séries"]),
("Quiz","b5bec559e34c40809feb9241ce6f3895","HOME SCHOOL",[]),
("Quiz","61421bf1dc494f36814d1f1bf5a84de5","LA BOITE À QUESTIONS",["Boîte à Questions"]),
("Quiz","30d269cfd56d4b79862d3951cffaad77","MAD BURGER - Burger Quiz",["Mad Burger"]),
("Quiz","4f409ecbce144beea40ef582f5917e0e","QUIZ CINE SERIES",["Quiz Ciné Séries"]),
("Quiz","8a19d6efade44ef7af973ad63d89f210","QUIZ RACE - Quiz Interactif",["Quiz Race"]),
("RSE","369f92eb93df419fadb0b2ce200bd3f9","CREACYCYCLE - Atelier Recyclage",["Créacycle"]),
("RSE","d70392ed6a154ad181ae50730b52bd52","GREEN TAG - Fresque Végétale",["Green Tag"]),
("RSE","19769304d1488001b373cd577513239b","MINI JARDIN",["Mini Jardin"]),
("Sportif","0fe763f6e923458784fb5eb77c15c576","FIT & FUN",["Fit & Fun"]),
("Théâtre","cc7f5693a953429eac1b99595a9fe957","TEAM THÉÂTRE",["Team Théâtre"]),
]


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def main():
    bases = [slugify(t.split(" - ")[0]) for _, _, t, _ in ROWS]
    out = []
    for (cat, pid, title, tags), base in zip(ROWS, bases):
        slug = base if bases.count(base) == 1 else slugify(title)
        out.append({"id": pid, "slug": slug, "title": title, "category": cat, "photo_tags": tags})
    slugs = [o["slug"] for o in out]
    assert len(set(slugs)) == len(slugs), [s for s in slugs if slugs.count(s) > 1]
    p = Path(__file__).resolve().parent.parent / "config" / "fiches.json"
    p.write_text(json.dumps({"_doc": "id Notion -> slug figé (ne pas modifier un slug déjà envoyé à un client), étiquette(s) de la galerie 'Photos Animations', catégorie de repli.",
                             "fiches": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(out), "fiches")


if __name__ == "__main__":
    main()
