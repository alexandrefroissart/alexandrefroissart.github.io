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

---

## Contexte

Ce challenge consiste à analyser une trame Ethernet brute fournie en hexadécimal.  
L'objectif est d'identifier les informations sensibles transmises, notamment une authentification HTTP Basic.

---

## Environnement / Setup

- **Machine** : VM Debian (XFCE) sur VMware Fusion (MacBook Pro M1 Pro)
- **Utilisateur** : `alex`
- **Outils** : CyberChef, décodeur Base64 en ligne

### Données fournies

```
[Trame brute fournie par l'énoncé - valeur complète non reproduite ici]
```

---

## Analyse (méthode)

### 1. Conversion hexadécimal → ASCII

En convertissant la trame hexadécimale en ASCII, on peut identifier la requête HTTP :

```
GET / HTTP/1.1
Authorization: Basic [REDACTED_BASE64]
User-Agent: InsaneBrowser
Host: www.myipv6.org
Accept: */*
```

### 2. Identification de l'authentification HTTP Basic

La ligne clé est :
```
Authorization: Basic [REDACTED_BASE64]
```

L'authentification **HTTP Basic** encode les credentials au format `username:password` en **Base64**.

### 3. Décodage Base64

La chaîne `Y29uZmk6ZGVudGlhbA==` se termine par deux signes `==`, ce qui est caractéristique d'un encodage Base64.

Décodage :
```
[REDACTED_BASE64] → [username]:[password]
```

**Résultat** :
- Username : `[REDACTED]`
- Password : `[REDACTED]`

Les identifiants exacts sont volontairement masqués pour respecter la confidentialité des challenges.

---

## Remarques

- **HTTP Basic Auth** : Ce mécanisme d'authentification transmet les credentials en clair (encodé Base64, mais **pas chiffré**). C'est pourquoi il est dangereux sans HTTPS.
- **Base64** : L'encodage Base64 se reconnaît souvent par :
  - Caractères alphanumériques + `+` et `/`
  - Terminaison par `=` ou `==` (padding)
- **Outils utiles** :
  - CyberChef (https://gchq.github.io/CyberChef/)
  - Décodeurs Base64 en ligne
  - `echo "Y29uZmk6ZGVudGlhbA==" | base64 -d` (ligne de commande)

---

## Résultat

✅ J'ai identifié la requête HTTP dans la trame Ethernet.  
✅ J'ai décodé l'authentification Basic en Base64.  
✅ **Challenge validé sur Root-Me.**

---

## Compétences démontrées

- Lecture et analyse de trames réseau brutes (hexadécimal)
- Compréhension du protocole HTTP et de l'authentification Basic
- Décodage Base64
- Détection d'informations sensibles dans le trafic réseau
