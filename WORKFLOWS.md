# Workflows avances

Ce fichier est seulement la pour la partie automatisation.

Pour l'edition normale du site, lis plutot `README.md`.

## Ce qui reste automatise

- mise a jour des donnees Root-Me affichees sur le site
- creation assistee d'un challenge Root-Me ou SadServers a partir d'une URL
- traduction facultative vers l'anglais

## Commandes avancees

Ajouter un challenge Root-Me depuis son URL :

```bash
./scripts/site.sh rootme "https://www.root-me.org/fr/Challenges/Reseau/ftp-authentification"
```

Ajouter un scenario SadServers depuis son URL :

```bash
./scripts/site.sh sadservers "https://sadservers.com/scenario/geneva"
```

Mettre a jour les donnees Root-Me :

```bash
python3 scripts/fetch-rootme.py
```

## GitHub Actions

Le workflow planifie :

- rafraichit les donnees Root-Me
- rebuild le site
- deploye sur GitHub Pages

Secrets attendus cote GitHub :

- `ROOTME_API_KEY`

Le scraping HTML Root-Me n'est pas la voie recommandee en CI.
