---
title: "ETHERNET - Trame"
date: 2026-01-24
image: "/img/banners/rootme-banner.png"
draft: false
rootme_id: 336
categories: ["Root-Me", "Réseau"]
tags: ["Ethernet", "Wireshark", "Base64", "HTTP", "Facile"]
---

{{< rootme-challenge slug="ethernet-trame" >}}

Ce challenge demande de repartir d'une trame Ethernet brute en hexadécimal pour retrouver l'information sensible qu'elle transporte.

Ici, le point important est une authentification HTTP Basic visible directement dans la charge utile.

## Environnement

- **Machine** : VM Debian (XFCE) sur VMware Fusion (MacBook Pro M1 Pro)
- **Utilisateur** : `alex`
- **Outils** : CyberChef, décodeur Base64 en ligne

## Donnée fournie

```
[Trame brute fournie par l'énoncé - valeur complète non reproduite ici]
```

## Démarche

### 1. Repasser la trame en ASCII

En convertissant la trame hexadécimale en ASCII, on fait ressortir la requête HTTP contenue dans le flux :

```
GET / HTTP/1.1
Authorization: Basic [REDACTED_BASE64]
User-Agent: InsaneBrowser
Host: www.myipv6.org
Accept: */*
```

### 2. Isoler l'élément utile

La ligne à retenir est :

```
Authorization: Basic [REDACTED_BASE64]
```

Une authentification **HTTP Basic** encode simplement le couple `username:password` en **Base64**.

### 3. Vérifier le Base64

La chaîne `Y29uZmk6ZGVudGlhbA==` se termine par `==`, ce qui correspond bien à un encodage Base64.

Une fois décodée, on retrouve le format attendu :

```
[REDACTED_BASE64] → [username]:[password]
```

**Ce que j'obtiens** :
- Username : `[REDACTED]`
- Password : `[REDACTED]`

Les identifiants exacts sont volontairement masqués pour respecter la confidentialité des challenges.

## Ce que je retiens

- **HTTP Basic** transmet les credentials en clair. Base64 est un encodage, pas un chiffrement.
- **Base64** se repère souvent par :
  - Caractères alphanumériques + `+` et `/`
  - Terminaison par `=` ou `==`
- **Outils pratiques** :
  - CyberChef (https://gchq.github.io/CyberChef/)
  - Décodeurs Base64 en ligne
  - `echo "Y29uZmk6ZGVudGlhbA==" | base64 -d` (ligne de commande)

## Résultat

✅ J'ai identifié la requête HTTP dans la trame Ethernet.  
✅ J'ai décodé l'authentification Basic en Base64.  
✅ **Challenge validé sur Root-Me.**

## Compétences mobilisées

- Lecture et analyse de trames réseau brutes (hexadécimal)
- Compréhension du protocole HTTP et de l'authentification Basic
- Décodage Base64
- Détection d'informations sensibles dans le trafic réseau
