---
title: "FTP - Authentification"
date: 2026-01-23
image: "/img/banners/rootme-banner.png"
draft: false
rootme_id: 96
categories: ["Root-Me", "Réseau"]
tags: ["FTP", "Wireshark", "PCAP", "Facile"]
---

{{< rootme-challenge slug="ftp-authentification" >}}

Cette capture montre un cas classique : un service FTP sans chiffrement laisse passer `USER` et `PASS` en clair.

Le travail consiste surtout à aller rapidement vers les bons paquets, puis à confirmer proprement ce que le flux révèle.

## Environnement

- **Machine** : VM Debian (XFCE) sur VMware Fusion (MacBook Pro M1 Pro)
- **Utilisateur** : `alex`
- **Outil** : Wireshark

### Installation et hygiène minimale

```bash
sudo apt-get update
sudo apt-get -y install wireshark
```

Pendant l'installation, Debian demande :

> "Should non-superusers be able to capture packets?"
> ➡️ **Réponse : Non**

Je laisse la capture réservée à `root` pour rester sur une logique de moindre privilège.

## Démarche

### 1. Ouvrir la capture

J'ouvre `Téléchargements/ch1.pcap` dans Wireshark.

### 2. Cibler la phase d'authentification

Dans Wireshark :

- je filtre sur le trafic FTP ;
- je repère la séquence d'authentification ;
- je cherche les commandes `USER` puis `PASS`.

### 3. Confirmer dans le détail des paquets

Je vérifie ensuite dans le panneau du bas la commande FTP exacte envoyée par le client.

## Observations

- J'identifie l'utilisateur envoyé via `USER` :
  - **USER** = `[REDACTED]` *(valeur volontairement masquée)*
- Le mot de passe est présent dans la commande `PASS` :
  - **PASS** = `[REDACTED]` *(valeur volontairement masquée)*

## Résultat

✅ J'ai localisé les identifiants FTP dans le flux applicatif de la capture réseau.  
✅ **Challenge validé sur Root-Me.**

## Ce que je retiens

- FTP en clair reste très simple à auditer dans une capture réseau.
- Wireshark permet d'aller vite si on se concentre d'abord sur la séquence applicative utile.
- Même sur un exercice simple, je garde une logique de moindre privilège pendant la mise en place.

## Compétences mobilisées

- Analyse PCAP avec Wireshark
- Lecture du protocole FTP et de son authentification en clair
- Extraction d'informations au niveau applicatif
- Hygiène sécurité lors de l'installation et de la capture
