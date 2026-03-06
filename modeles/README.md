# Modeles de depart

Ces fichiers sont faits pour etre copies puis modifies a la main.

Workflow simple :

1. cree ton dossier cible dans `content/`
2. copie le modele adapte
3. renomme-le en `index.md`
4. remplis le frontmatter et le texte
5. lance `./scripts/site.sh serve`
6. ouvre [http://127.0.0.1:1313](http://127.0.0.1:1313)

Les trois modeles disponibles :

- `news.md`
- `rootme.md`
- `sadservers.md`

Pour Root-Me et SadServers, les blocs `rootme_meta` et `sadservers_meta` permettent maintenant de remplir les informations directement dans le fichier, sans passer par le script.
