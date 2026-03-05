---
title: "Saint John: What is Writing to this Log File?"
date: 2026-01-24
image: "/img/banners/sadservers.png"
draft: false
reading_time: 10
categories: ["SadServers", "Linux"]
tags: ["lsof", "process", "troubleshooting", "Easy"]
---

{{< sadservers-scenario slug="saint-john" >}}

---

## Contexte

Un fichier log `/var/log/bad.log` grossit continuellement sur le système. Il faut identifier quel processus écrit dedans et l'arrêter **sans supprimer** le fichier ou le script source.

---

## Environnement / Setup

- **Machine** : VM SadServers (Ubuntu/Debian)
- **Utilisateur** : `admin` (avec accès sudo)
- **Fichier cible** : `/var/log/bad.log`

---

## Analyse (méthode)

### 1. Identifier le processus qui écrit dans le fichier

La commande `lsof` (LiSt Open Files) permet de lister tous les fichiers ouverts sur le système, y compris ceux en cours d'écriture.

```bash
sudo lsof /var/log/bad.log
```

**Résultat** :
```
COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF   NODE NAME
[processus_identifie] [PID] admin 3w REG ... /var/log/bad.log
```

**Analyse** :
- **COMMAND** : `[processus_identifie]` → processus responsable de l'écriture
- **PID** : `[PID]` → identifiant du processus
- **USER** : `admin` → l'utilisateur propriétaire
- **FD** : `3w` → File Descriptor 3 en mode **write** (écriture)
- **TYPE** : `REG` → fichier régulier

On en déduit que le processus identifié (PID trouvé avec `lsof`) écrit dans `/var/log/bad.log`.

### 2. Arrêter le processus

Pour arrêter le processus sans supprimer le fichier Python, on utilise la commande `kill` avec le PID :

```bash
sudo kill <PID_IDENTIFIE>
```

Cette commande envoie un signal `SIGTERM` (terminaison gracieuse) au processus 587.

### 3. Vérification

Pour confirmer que le processus est bien arrêté et que le fichier ne grossit plus :

```bash
tail -f /var/log/bad.log
```

Si aucune nouvelle ligne n'apparaît, le processus est arrêté avec succès.

---

## Remarques

- **`lsof`** : Commande très puissante pour le troubleshooting système. Elle permet de voir quels processus ont quels fichiers ouverts.
- **`kill` vs `kill -9`** : 
  - `kill <PID>` envoie SIGTERM (arrêt propre)
  - `kill -9 <PID>` envoie SIGKILL (arrêt forcé, à utiliser en dernier recours)
- **Alternatives** :
  - `fuser /var/log/bad.log` : Une autre méthode pour identifier les processus utilisant un fichier
  - `ps aux | grep badlog` : Pour vérifier si le processus est toujours actif

---

## Résultat

✅ Processus identifié via `lsof`  
✅ Processus arrêté avec `sudo kill <PID_IDENTIFIE>`  
✅ Fichier `/var/log/bad.log` ne grossit plus  
✅ **Challenge validé sur SadServers.**

---

## Compétences démontrées

- Utilisation de `lsof` pour identifier les fichiers ouverts
- Compréhension des processus Linux et des PID
- Gestion des processus avec `kill`
- Troubleshooting système Linux
