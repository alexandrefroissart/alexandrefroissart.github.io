# Gestion rapide du site

Le workflow recommande maintenant est simple :

1. tu dupliques un modele Markdown dans `modeles/`
2. tu edits ton fichier tranquillement
3. tu regardes le rendu en local
4. tu publies quand c'est pret

Le terminal ne sert plus surtout qu'a :

- previsualiser
- verifier
- traduire
- publier

## Modeles a copier

- `modeles/news.md`
- `modeles/rootme.md`
- `modeles/sadservers.md`

Tu peux ouvrir ces fichiers, copier leur contenu, puis le coller dans ton nouveau `index.md`.

## Ou mettre tes pages

- `content/news/<slug>/index.md`
- `content/root-me-challenges/<slug>/index.md`
- `content/sadservers/<slug>/index.md`

## Workflow recommande

### Pour une news

1. cree le dossier `content/news/<slug>/`
2. copie `modeles/news.md` dans `content/news/<slug>/index.md`
3. remplace le titre, la description, les categories, les tags et le texte
4. mets ton image dans `static/img/news/<slug>/`
5. utilise un chemin du type `/img/news/<slug>/mon-image.jpg`

### Pour un challenge Root-Me

1. cree le dossier `content/root-me-challenges/<slug>/`
2. copie `modeles/rootme.md` dans `content/root-me-challenges/<slug>/index.md`
3. remplis le bloc `rootme_meta:` a la main
4. redige ton writeup

### Pour un scenario SadServers

1. cree le dossier `content/sadservers/<slug>/`
2. copie `modeles/sadservers.md` dans `content/sadservers/<slug>/index.md`
3. remplis le bloc `sadservers_meta:` a la main
4. redige ton writeup

## Commandes utiles

Lancer le site en local :

```bash
./scripts/site.sh serve
```

Voir l'etat du contenu :

```bash
./scripts/site.sh status
```

Traduire une seule page :

```bash
./scripts/site.sh translate content/news/mon-article/index.md
```

Traduire tout ce qui n'a pas encore de version anglaise :

```bash
./scripts/site.sh translate
```

Publier sur GitHub :

```bash
./scripts/site.sh publish "Mon message de commit"
```

Les commandes `news`, `rootme` et `sadservers` existent encore, mais elles sont maintenant optionnelles.

## Quand tu rediges

Pour une vraie commande shell, utilise un bloc `bash` :

```bash
grep -R SSL /etc/nginx
```

Pour un prompt, une consigne ou un texte de test, utilise un bloc `text` sans numeros de ligne :

```text {linenos=false}
Fais-moi un mini-cours clair pour comprendre...
```

Regle simple :

- `bash` = commande technique, avec numeros de ligne
- `text {linenos=false}` = prompt, citation, consigne, sans numeros

## Notes pratiques

- les mots-cles se mettent dans `tags: [...]`
- les categories se mettent dans `categories: [...]`
- pour voir le rendu en direct pendant que tu ecris : `./scripts/site.sh serve`
- ensuite ouvre [http://127.0.0.1:1313](http://127.0.0.1:1313)
