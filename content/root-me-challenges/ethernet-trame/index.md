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
00 05 73 a0 00 00 e0 69 95 d8 5a 13 86 dd 60 00
00 00 00 9b 06 40 26 07 53 00 00 60 2a bc 00 00
00 00 ba de c0 de 20 01 41 d0 00 02 42 33 00 00
00 00 00 00 00 04 96 74 00 50 bc ea 7d b8 00 c1
d7 03 80 18 00 e1 cf a0 00 00 01 01 08 0a 09 3e
69 b9 17 a1 7e d3 47 45 54 20 2f 20 48 54 54 50
2f 31 2e 31 0d 0a 41 75 74 68 6f 72 69 7a 61 74
69 6f 6e 3a 20 42 61 73 69 63 20 59 32 39 75 5a
6d 6b 36 5a 47 56 75 64 47 6c 68 62 41 3d 3d 0d
0a 55 73 65 72 2d 41 67 65 6e 74 3a 20 49 6e 73
61 6e 65 42 72 6f 77 73 65 72 0d 0a 48 6f 73 74
3a 20 77 77 77 2e 6d 79 69 70 76 36 2e 6f 72 67
0d 0a 41 63 63 65 70 74 3a 20 2a 2f 2a 0d 0a 0d
0a
```

---

## Analyse (méthode)

### 1. Conversion hexadécimal → ASCII

En convertissant la trame hexadécimale en ASCII, on peut identifier la requête HTTP :

```
GET / HTTP/1.1
Authorization: Basic Y29uZmk6ZGVudGlhbA==
User-Agent: InsaneBrowser
Host: www.myipv6.org
Accept: */*
```

### 2. Identification de l'authentification HTTP Basic

La ligne clé est :
```
Authorization: Basic Y29uZmk6ZGVudGlhbA==
```

L'authentification **HTTP Basic** encode les credentials au format `username:password` en **Base64**.

### 3. Décodage Base64

La chaîne `Y29uZmk6ZGVudGlhbA==` se termine par deux signes `==`, ce qui est caractéristique d'un encodage Base64.

Décodage :
```
Y29uZmk6ZGVudGlhbA== → confi:dential
```

**Résultat** :
- Username : `confi`
- Password : `dential`

Le mot de passe attendu par le challenge est : **`dential`**

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
