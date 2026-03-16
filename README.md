# Gerer le site simplement

Le projet est organise pour que tu puisses surtout travailler dans `content/`, `static/img/` et `modeles/`.

## Les dossiers a connaitre

- `content/` : les pages du site
- `static/img/` : les images
- `modeles/` : les modeles a copier
- `scripts/site.sh` : la commande simple pour previsualiser, verifier et publier

## Ou creer tes pages

- News : `content/news/<slug>/index.md`
- Root-Me : `content/root-me-challenges/<slug>/index.md`
- SadServers : `content/sadservers/<slug>/index.md`

Le principe recommande :

1. cree le dossier
2. copie le bon modele depuis `modeles/`
3. renomme-le en `index.md`
4. remplace le titre, la description, les tags et le texte
5. ajoute l'image si besoin dans `static/img/`
6. lance l'aperçu local

## Commandes utiles

Lancer le site en local :

```bash
./scripts/site.sh serve
```

Voir l'etat du contenu :

```bash
./scripts/site.sh status
```

Traduire une page en anglais si tu en as besoin :

```bash
./scripts/site.sh translate content/news/mon-article/index.md
```

Builder le site :

```bash
./scripts/site.sh build
```

Publier sur GitHub :

```bash
./scripts/site.sh publish "Mon message de commit"
```

## Anglais

Le francais est la source principale.

Tu peux publier une page seulement en francais.

La version anglaise est optionnelle. Si tu en veux une, utilise `translate` puis relis le resultat.

## Root-Me et SadServers

Tu as deux manieres de faire :

1. simple : tu copies `modeles/rootme.md` ou `modeles/sadservers.md` puis tu remplis les metadonnees toi-meme
2. assistee : tu utilises `./scripts/site.sh rootme <url>` ou `./scripts/site.sh sadservers <url>`

Si tu veux juste ajouter du contenu sans te prendre la tete, commence par les modeles.

## Images

- banniere commune : `/img/banners/...`
- image specifique d'article : `/img/news/<slug>/...`

Dans le frontmatter, il faut toujours utiliser un chemin qui commence par `/img/...`, jamais `static/img/...`.

## Regle simple d'edition

- texte normal : markdown classique
- vraie commande shell : bloc `bash`
- prompt, citation ou texte a lire tel quel : bloc `text {linenos=false}`

## A retenir

Pour l'edition quotidienne, tu peux presque tout faire sans toucher au code :

- copier un modele
- modifier `index.md`
- ajouter une image
- lancer `serve`
- publier
