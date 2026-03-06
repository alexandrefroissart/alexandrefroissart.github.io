# Gestion rapide du site

Le site se gère maintenant avec une seule commande :

```bash
./scripts/site.sh
```

Sans argument, tu as un petit menu.

## Commandes utiles

Créer une news :

```bash
./scripts/site.sh news
```

Ajouter un challenge Root-Me depuis son URL :

```bash
./scripts/site.sh rootme "https://www.root-me.org/fr/Challenges/Reseau/ftp-authentification"
```

Ajouter un scenario SadServers depuis son URL :

```bash
./scripts/site.sh sadservers "https://sadservers.com/scenario/saint-john"
```

Traduire une seule page :

```bash
./scripts/site.sh translate content/news/mon-article/index.md
```

Traduire tout ce qui n'a pas encore de version anglaise :

```bash
./scripts/site.sh translate
```

Builder le site :

```bash
./scripts/site.sh build
```

Lancer le site en local :

```bash
./scripts/site.sh serve
```

Voir les brouillons et les pages sans traduction anglaise :

```bash
./scripts/site.sh status
```

Publier sur GitHub :

```bash
./scripts/site.sh publish "Mon message de commit"
```

## Organisation simple

- `content/news/` : tes articles d'actualite
- `content/root-me-challenges/` : tes challenges Root-Me
- `content/sadservers/` : tes scenarios SadServers
- `static/img/` : tes images
- `data/rootme_challenges.json` et `data/sadservers_scenarios.json` : les donnees recuperees automatiquement

## Workflow conseille

Pour une news :

1. `./scripts/site.sh news`
2. Tu rediges la page creee
3. `./scripts/site.sh translate content/news/ton-slug/index.md`
4. `./scripts/site.sh build`
5. `./scripts/site.sh publish "Ajout news ..."`

Pour Root-Me ou SadServers :

1. `./scripts/site.sh rootme "<url>"` ou `./scripts/site.sh sadservers "<url>"`
2. Tu completes le contenu genere
3. `./scripts/site.sh build`
4. `./scripts/site.sh publish "Ajout challenge ..."`

## Notes pratiques

- Les mots-cles se mettent dans `tags: [...]`
- Les categories se mettent dans `categories: [...]`
- Pour une image d'article, mets-la de preference dans `static/img/news/<slug>/`
- Ensuite utilise un chemin du type `/img/news/<slug>/mon-image.jpg`

Le but est que tu puisses tout gerer seul avec des commandes courtes et toujours les memes.
