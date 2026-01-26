# Workflows d'automatisation

Ce fichier documente les scripts d'automatisation pour la gestion du site.

## 1. Ajouter un nouveau challenge

Ce script permet d'ajouter automatiquement un challenge (Root-Me ou SadServers). Il détecte le type de lien, récupère les infos (titre, description, points, etc.) et crée les fichiers markdown.

**Commande :**
```bash
python3 scripts/add-challenge.py <URL_DU_CHALLENGE>
```

**Exemples :**
*   **Root-Me :**
    ```bash
    python3 scripts/add-challenge.py "https://www.root-me.org/fr/Challenges/Cryptanalyse/Hash-DCC2"
    ```
*   **SadServers :**
    ```bash
    python3 scripts/add-challenge.py "https://sadservers.com/scenario/saskatoon"
    ```

## 2. Mettre à jour le profil Root-Me

Ce script met à jour les statistiques globales (rang, points) et les détails des challenges (validations, difficulté) dans les fichiers markdown existants.

**Commande :**
```bash
python3 scripts/fetch-rootme.py
```

> **Note :** La mise à jour des données est également lancée automatiquement après l'ajout d'un challenge via `add-challenge.py`.
