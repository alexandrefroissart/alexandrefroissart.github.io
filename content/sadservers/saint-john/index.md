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

Ici, le problème est simple mais très réaliste : un fichier `/var/log/bad.log` grossit en continu, et il faut identifier le processus responsable sans toucher ni au fichier ni au script source.

## Environnement

- **Machine** : VM SadServers (Ubuntu/Debian)
- **Utilisateur** : `admin` (avec accès sudo)
- **Fichier cible** : `/var/log/bad.log`

## Démarche

### 1. Identifier le processus qui écrit dans le fichier

La commande `lsof` liste les fichiers ouverts sur le système, y compris ceux qui sont en cours d'écriture.

```bash
sudo lsof /var/log/bad.log
```

**Résultat** :
```
COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF   NODE NAME
[processus_identifie] [PID] admin 3w REG ... /var/log/bad.log
```

- **COMMAND** : `[processus_identifie]` -> processus responsable de l'écriture
- **PID** : `[PID]` -> identifiant du processus
- **USER** : `admin` -> utilisateur propriétaire
- **FD** : `3w` -> file descriptor 3 en mode **write**
- **TYPE** : `REG` → fichier régulier

Le processus trouvé avec `lsof` est donc bien celui qui écrit dans `/var/log/bad.log`.

### 2. Arrêter proprement le processus

Pour l'arrêter sans supprimer le fichier Python, j'utilise `kill` avec le PID repéré juste avant :

```bash
sudo kill <PID_IDENTIFIE>
```

Cette commande envoie un signal `SIGTERM`, donc une terminaison propre, au processus identifié.

### 3. Vérifier que l'écriture s'arrête

Pour confirmer que le processus est bien stoppé et que le fichier ne grossit plus :

```bash
tail -f /var/log/bad.log
```

Si plus aucune nouvelle ligne n'apparaît, la correction est bonne.

## Ce que je retiens

- `lsof` est un très bon réflexe pour le troubleshooting système quand un fichier grossit ou reste verrouillé.
- Je commence par `SIGTERM` avant d'envisager un `kill -9`, parce qu'un arrêt propre est toujours préférable.
- `fuser /var/log/bad.log` aurait aussi permis d'identifier rapidement le processus.

## Résultat

✅ Processus identifié via `lsof`  
✅ Processus arrêté avec `sudo kill <PID_IDENTIFIE>`  
✅ Fichier `/var/log/bad.log` ne grossit plus  
✅ **Challenge validé sur SadServers.**

## Compétences mobilisées

- Utilisation de `lsof` pour identifier les fichiers ouverts
- Compréhension des processus Linux et des PID
- Gestion des processus avec `kill`
- Troubleshooting système Linux
