---
title: "\"Geneva\": Renew an SSL Certificate"
date: 2026-01-25
image: "/img/banners/sadservers.png"
draft: false
reading_time: 10
categories: ["SadServers", "Linux"]
tags: ["ssl"]
---

{{< sadservers-scenario slug="geneva" >}}

Le but ici n'est pas de refaire toute la configuration Nginx, mais d'aller directement au bon endroit : retrouver le certificat utilisé, en générer un nouveau, puis vérifier que le service présente bien le bon fichier.

## Environnement

- **Service** : Nginx en HTTPS
- **Objectif** : remplacer un certificat expiré ou invalide
- **Outils** : `grep`, `openssl`, `systemctl`

## Démarche

### 1. Retrouver la configuration SSL active

Je commence par chercher où la configuration SSL de Nginx référence les fichiers de certificat.

```bash
grep -r "ssl" /etc/nginx/
```

Cette commande fait ressortir les lignes utiles dans `/etc/nginx/sites-available/default` :

```nginx
listen 443 ssl;
ssl_certificate /etc/nginx/ssl/nginx.crt;
ssl_certificate_key /etc/nginx/ssl/nginx.key;
```

Les fichiers cibles sont donc `/etc/nginx/ssl/nginx.crt` pour le certificat public et `/etc/nginx/ssl/nginx.key` pour la clé privée.

### 2. Régénérer un certificat propre

Je régénère ensuite une nouvelle paire clé/certificat auto-signée avec `openssl`.

Je remplace ensuite les fichiers SSL utilisés par Nginx.

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout <chemin_cle_ssl> \
  -out <chemin_certificat_ssl>
```

Pendant la génération, `openssl` demande le **Distinguished Name**.

Je renseigne des valeurs cohérentes avec le serveur, sans publier ici le jeu exact.

Une fois les fichiers générés, je redémarre Nginx pour qu'il prenne en charge le nouveau certificat :

```bash
sudo systemctl restart nginx
```

### 3. Vérifier le certificat servi

Je contrôle ensuite que Nginx présente bien le nouveau certificat avec `openssl s_client`.

**Vérification des dates :**
```bash
echo | openssl s_client -connect <hote>:443 2>/dev/null | openssl x509 -noout -dates
```
*Résultat attendu : `notBefore` récent, `notAfter` plus loin dans le temps.*

**Vérification du sujet :**
```bash
echo | openssl s_client -connect <hote>:443 2>/dev/null | openssl x509 -noout -subject
```

Si les dates sont bonnes et que Nginx redémarre sans erreur, la correction est validée.

## Ce que je retiens

- Sur ce type d'exercice, le plus important est de retrouver vite les bons fichiers au lieu de repartir de zéro.
- `openssl s_client` reste un réflexe très utile pour vérifier ce que le service expose vraiment.
- Une vérification après redémarrage est indispensable : générer un certificat ne suffit pas, il faut aussi confirmer qu'il est bien servi.

## Compétences mobilisées

- OpenSSL pour générer un certificat auto-signé
- Lecture de configuration Nginx
- Vérification d'un certificat en ligne de commande
- Troubleshooting d'un service HTTPS
