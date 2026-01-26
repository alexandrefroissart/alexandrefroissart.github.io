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

---

## Contexte

FTP transmet l'authentification en clair (USER/PASS) si aucune couche chiffrée n'est utilisée.  
Le but est d'identifier ces échanges dans un fichier `.pcap`.

---

## Environnement / Setup

- **Machine** : VM Debian (XFCE) sur VMware Fusion (MacBook Pro M1 Pro)
- **Utilisateur** : `alex`
- **Outil** : Wireshark

### Installation (sécurité)

```bash
sudo apt-get update
sudo apt-get -y install wireshark
```

Pendant l'installation, Debian demande :

> "Should non-superusers be able to capture packets?"
> ➡️ **Réponse : Non**

**Pourquoi ?** J'évite d'autoriser la capture réseau aux utilisateurs non-root (réduction de surface d'attaque / moindre privilège).

---

## Analyse (méthode)

1. J'ouvre la capture : `Téléchargements/ch1.pcap`

2. Dans Wireshark :
   - Je filtre sur FTP (ou je repère les trames où le protocole est FTP)
   - Je cherche la séquence d'authentification FTP :
     - `USER ...`
     - `PASS ...`

3. Je vérifie dans le détail du paquet (panneau du bas) la commande FTP envoyée.

---

## Observations

- J'identifie l'utilisateur envoyé via `USER` :
  - **USER** = `cdts3500`
- Le mot de passe est présent dans la commande `PASS` :
  - **PASS** = `[REDACTED]` *(valeur volontairement masquée)*

---

## Résultat

✅ J'ai localisé les identifiants FTP dans le flux applicatif de la capture réseau.  
✅ **Challenge validé sur Root-Me.**

---

## Compétences démontrées

- Analyse PCAP avec Wireshark
- Lecture de protocole FTP (authentification en clair)
- Extraction d'informations côté couche application
- Hygiène sécurité : moindre privilège lors de l'installation/capture
