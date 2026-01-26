---
title: "\"Geneva\": Renew an SSL Certificate"
date: 2026-01-25
image: "/img/banners/sadservers.png"
draft: false
categories: ["SadServers", "Linux"]
tags: ["ssl"]
---

{{< sadservers-scenario slug="geneva" >}}

---

## Contexte

Il y a un serveur web Nginx qui tourne sur cette machine, configuré pour servir un site simple en HTTPS. Cependant, le certificat actuel a expiré ou n'est pas valide. L'objectif est de renouveler le certificat SSL.

---

## Analyse

Je commence par chercher où se trouve la configuration SSL de Nginx pour identifier les fichiers de certificat utilisés.

```bash
grep -r "ssl" /etc/nginx/
```

Cette commande me révèle les lignes intéressantes dans `/etc/nginx/sites-available/default` :

```nginx
listen 443 ssl;
ssl_certificate /etc/nginx/ssl/nginx.crt;
ssl_certificate_key /etc/nginx/ssl/nginx.key;
```

Les fichiers cibles sont donc `/etc/nginx/ssl/nginx.crt` (le certificat public) et `/etc/nginx/ssl/nginx.key` (la clé privée).

---

## Solution

Pour renouveler le certificat, je génère une nouvelle paire clé/certificat auto-signée avec `openssl`. Je remplace directement les fichiers existants.

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx.key \
  -out /etc/nginx/ssl/nginx.crt
```

Lors de la génération, `openssl` me demande des informations pour le "Distinguished Name" (DN). Je remplis avec les valeurs suivantes :

- **Country Name (2 letter code)** : `CH`
- **State or Province Name** : `Geneva`
- **Locality Name** : `Geneva`
- **Organization Name** : `Acme`
- **Organizational Unit Name** : `IT Department`
- **Common Name (e.g. server FQDN)** : `localhost`
- **Email Address** : (laisser vide)

Une fois les fichiers générés, je redémarre Nginx pour prendre en charge le nouveau certificat :

```bash
sudo systemctl restart nginx
```

---

## Vérification

Je vérifie que le certificat est bien chargé et valide en utilisant `openssl s_client` pour se connecter localement au serveur et inspecter le certificat servi.

**Vérification des dates :**
```bash
echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -dates
```
*Résultat attendu : `notBefore` doit être la date d'aujourd'hui et `notAfter` dans un an (2025).*

**Vérification du sujet :**
```bash
echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -subject
```
*Résultat :*
`subject=CN = localhost, O = Acme, OU = IT Department, L = Geneva, ST = Geneva, C = CH`

Tout correspond ! Le certificat est renouvelé et valide.

---

## Compétences démontrées

- **OpenSSL** : Génération de certificats auto-signés (req, x509).
- **Nginx** : Localisation de la configuration SSL et redémarrage du service.
- **Troubleshooting** : Vérification de la validité d'un certificat en ligne de commande.
