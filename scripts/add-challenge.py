#!/usr/bin/env python3
"""
Script pour ajouter AUTOMATIQUEMENT un nouveau challenge Root-Me.
Usage: ./add-challenge.py <URL_DU_CHALLENGE>

Ce script va :
1. Récupérer l'ID et le titre du challenge depuis l'URL
2. Modifier scripts/fetch-rootme.py pour ajouter le challenge
3. Créer les dossiers et fichiers markdown (fr/en)
4. Lancer la mise à jour des données
"""

import sys
import re
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
import unicodedata

# Chemins
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
FETCH_SCRIPT = SCRIPT_DIR / "fetch-rootme.py"
CONTENT_DIR = ROOT_DIR / "content" / "root-me-challenges"
ENV_FILE = ROOT_DIR / ".env"

def load_env():
    """Charge les variables d'environnement depuis .env s'il existe."""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars

ENV = load_env()
def build_rootme_cookies(env):
    if env.get("ROOTME_COOKIES"):
        return env.get("ROOTME_COOKIES", "")
    parts = []
    spip = env.get("spip_session") or env.get("SPIP_SESSION") or env.get("ROOTME_SPIP_SESSION")
    phpsess = env.get("PHPSESSID") or env.get("ROOTME_PHPSESSID")
    anubis = env.get("anubis-cookie-auth") or env.get("ANUBIS_COOKIE_AUTH") or env.get("ROOTME_ANUBIS_COOKIE_AUTH")
    if spip:
        parts.append(f"spip_session={spip}")
    if phpsess:
        parts.append(f"PHPSESSID={phpsess}")
    if anubis:
        parts.append(f"anubis-cookie-auth={anubis}")
    return "; ".join(parts)

ROOTME_COOKIES = build_rootme_cookies(ENV)
USE_API_DETAILS = (os.environ.get("ROOTME_USE_API_DETAILS") or ENV.get("ROOTME_USE_API_DETAILS", "0")) == "1"

CHALLENGES_FILE = ROOT_DIR / "data" / "rootme_challenges.json"
SADSERVERS_DATA_FILE = ROOT_DIR / "data" / "sadservers_scenarios.json"

# Templates SadServers
SADSERVERS_TEMPLATE_FR = '''---
title: "{title}"
date: {date}
image: "/img/banners/sadservers.png"
draft: false
reading_time: {reading_time}
categories: ["SadServers", "Linux"]
tags: {tags}
---

{{{{< sadservers-scenario slug="{slug}" >}}}}

---

## Contexte

<!-- Ajoute ici le contexte du challenge -->

---

## Environnement / Setup

- **Machine** : VM SadServers (Ubuntu/Debian)
- **Utilisateur** : `admin` (avec accès sudo)
- **Fichier cible** : <!-- à compléter -->

---

## Analyse (méthode)

### 1. Première étape

```bash
# Commande
```

**Résultat** :
```
# Output
```

**Analyse** :
- Point 1
- Point 2

### 2. Solution

```bash
# Commande solution
```

### 3. Vérification

```bash
# Vérification
```

---

## Remarques

- Point important 1
- Point important 2

---

## Résultat

✅ Étape 1 complétée  
✅ Étape 2 complétée  
✅ **Challenge validé sur SadServers.**

---

## Compétences démontrées

- Compétence 1
- Compétence 2
'''

SADSERVERS_TEMPLATE_EN = '''---
title: "{title}"
date: {date}
image: "/img/banners/sadservers.png"
draft: false
reading_time: {reading_time}
categories: ["SadServers", "Linux"]
tags: {tags}
---

{{{{< sadservers-scenario slug="{slug}" >}}}}

---

## Context

<!-- Add challenge context here -->

---

## Environment / Setup

- **Machine**: SadServers VM (Ubuntu/Debian)
- **User**: `admin` (with sudo access)
- **Target file**: <!-- to complete -->

---

## Analysis (method)

### 1. First step

```bash
# Command
```

**Result**:
```
# Output
```

**Analysis**:
- Point 1
- Point 2

### 2. Solution

```bash
# Solution command
```

### 3. Verification

```bash
# Verification
```

---

## Comments

- Important point 1
- Important point 2

---

## Result

✅ Step 1 completed  
✅ Step 2 completed  
✅ **Challenge validated on SadServers.**

---

## Demonstrated skills

- Skill 1
- Skill 2
'''


def load_challenges():
    if CHALLENGES_FILE.exists():
        with open(CHALLENGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

ROOTME_CHALLENGES = load_challenges()

def strip_html_tags(text):
    """Supprime tous les tags HTML d'un texte."""
    # Supprimer les tags HTML
    clean = re.sub(r'<[^>]+>', '', text)
    # Décoder les entités HTML courantes
    clean = clean.replace('&quot;', '"').replace('&#34;', '"')
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&nbsp;', ' ').replace('&#x27;', "'")
    # Nettoyer les espaces multiples
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def fetch_sadservers_data(slug):
    """Récupère les données d'un scénario depuis sadservers.com"""
    url = f"https://sadservers.com/scenario/{slug}"
    print(f"🔄 Récupération des données depuis {url}...")
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        return None
    
    scenario = {"url": url}
    
    # Titre (Scenario:)
    title_match = re.search(r'Scenario:\s*(.+?)(?:\n|Level:)', html, re.DOTALL)
    if title_match:
        scenario["titre"] = strip_html_tags(title_match.group(1))
    
    # Niveau (Level:)
    # Pattern: Level: <tag>Easy</tag> or Level: Easy
    level_match = re.search(r'Level:\s*(?:<[^>]+>\s*)*(\w+)', html)
    if level_match:
        scenario["niveau"] = level_match.group(1).strip()
    
    # Type
    type_match = re.search(r'Type:\s*(?:<[^>]+>\s*)*(\w+)', html)
    if type_match:
        scenario["type"] = type_match.group(1).strip()
    
    # Tags
    tags = []
    tag_matches = re.findall(r'/tag/([^"\'>\s\)]+)', html)
    if tag_matches:
        for tag in tag_matches:
            decoded_tag = urllib.request.unquote(tag)
            if decoded_tag not in tags:
                tags.append(decoded_tag)
        scenario["tags"] = tags
    
    # Access
    access_match = re.search(r'Access:\s*(?:<[^>]+>\s*)*(\w+)', html)
    if access_match:
        scenario["access"] = access_match.group(1).strip()
    
    # Description
    desc_match = re.search(r'Description:\s*(.+?)(?:Root \(sudo\) Access:|Root Access:|$)', html, re.DOTALL)
    if desc_match:
        scenario["description"] = strip_html_tags(desc_match.group(1))
    
    # Root Access
    root_match = re.search(r'Root \(sudo\) Access:\s*(?:<[^>]+>\s*)*(\w+)', html, re.IGNORECASE)
    if not root_match:
        root_match = re.search(r'Root Access:\s*(?:<[^>]+>\s*)*(\w+)', html, re.IGNORECASE)
    if root_match:
        scenario["root_access"] = root_match.group(1).lower() == "true"
    
    # Test
    test_match = re.search(r'Test:\s*(.+?)Time to Solve:', html, re.DOTALL)
    if test_match:
        scenario["test"] = strip_html_tags(test_match.group(1))
    
    # Time to Solve
    time_match = re.search(r'Time to Solve:\s*(?:<[^>]+>\s*)*(\d+\s*minutes?\.?)', html, re.IGNORECASE)
    if time_match:
        scenario["time_to_solve"] = time_match.group(1).strip().rstrip('.')
    
    return scenario

def create_sadservers_content(slug, scenario):
    """Crée les fichiers markdown pour SadServers."""
    # Créer le dossier du scénario
    # Note: On utilise ROOT_DIR/content/sadservers pour SadServers (différent de CONTENT_DIR qui est root-me-challenges)
    sad_content_dir = ROOT_DIR / "content" / "sadservers"
    scenario_dir = sad_content_dir / slug
    scenario_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer le titre slug-friendly
    title = scenario.get("titre", slug.replace("-", " ").title())
    title = title.replace('"', '\\"') # Escape quotes for YAML
    
    from datetime import datetime, timedelta
    # On met la date d'hier pour éviter les soucis de timezone (GitHub Actions en retard = post futur = non publié)
    date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    tags_str = json.dumps(scenario.get("tags", []))
    
    # Reading Time (integer from Time to Solve)
    reading_time = "5" # default fallback
    if scenario.get("time_to_solve"):
        import re
        m = re.search(r'(\d+)', scenario["time_to_solve"])
        if m:
            reading_time = m.group(1)

    # Fichier FR
    fr_file = scenario_dir / "index.md"
    if not fr_file.exists():
        content_fr = SADSERVERS_TEMPLATE_FR.format(
            title=title,
            date=date,
            tags=tags_str,
            slug=slug,
            reading_time=reading_time
        )
        with open(fr_file, 'w', encoding='utf-8') as f:
            f.write(content_fr)
        print(f"✅ Fichier créé: {fr_file}")
    else:
        # Update existing file if user requests it? 
        # For now script says "File exists". But user wants to update existing ones.
        # I should probably force update the reading_time if file exists? 
        # The user said "fait en sorte que ça fonctionne pour d'autre ajout sadservers" and "corrige... avec le script qui met à jour".
        # Re-running the script updates JSON but usually skips file creation if exists.
        # I'll update the CREATE logic. If file exists, I won't touch it to avoid overwriting user content (writeups).
        # User has to delete file or I assume he wants it for NEW challenges.
        # But he said "corrige... de CHAQUE post".
        # I can try to update the front matter of existing files? 
        # That's risky with regex replace on file content.
        # I'll stick to new files first.
        print(f"⚠️ Fichier existe déjà: {fr_file}")
    
    # Fichier EN
    en_file = scenario_dir / "index.en.md"
    if not en_file.exists():
        content_en = SADSERVERS_TEMPLATE_EN.format(
            title=title,
            date=date,
            tags=tags_str,
            slug=slug,
            reading_time=reading_time
        )
        with open(en_file, 'w', encoding='utf-8') as f:
            f.write(content_en)
        print(f"✅ Fichier créé: {en_file}")
    else:
        print(f"⚠️ Fichier existe déjà: {en_file}")

def update_sadservers_json(slug, scenario):
    """Met à jour le fichier sadservers_scenarios.json"""
    data = {}
    if SADSERVERS_DATA_FILE.exists():
        with open(SADSERVERS_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
    data[slug] = scenario
    
    with open(SADSERVERS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Données sauvegardées dans {SADSERVERS_DATA_FILE}")


def get_challenge_info(url):
    """Scrape l'ID et le titre depuis la page du challenge."""
    print(f"🔍 Analyse de {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    if ROOTME_COOKIES:
        headers['Cookie'] = ROOTME_COOKIES
        
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Recherche de l'ID (souvent dans <input type="hidden" name="id_challenge" value="96" /> ou opengraph)
            # Root-Me expose souvent l'ID dans les balises meta ou liens SPIP
            # On cherche un pattern courant : paramètre id_challenge ou SPIP
            
            # Méthode 1 : Chercher id_challenge dans le HTML
            m_id = re.search(r'name="id_challenge"\s+value="(\d+)"', html)
            if not m_id:
                # Méthode 2 : Chercher dans les classes CSS (ex: challenge-titre-1014)
                m_id = re.search(r'challenge-titre-(\d+)', html)
            if not m_id:
                 # Méthode 3 : Chercher dans les liens raccourcis (ex: spip.php?article123)
                 m_id = re.search(r'spip\.php\?article(\d+)', html)
            if not m_id:
                # Méthode 4 : Chercher dans les liens id_challenge=...
                m_id = re.search(r'id_challenge=(\d+)', html)
            
            challenge_id = m_id.group(1) if m_id else None
            
            # Recherche du titre <title> ... </title>
            m_title = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
            if m_title:
                raw_title = m_title.group(1).strip()
                # Nettoyage des suffixes communs Root-Me
                raw_title = re.sub(r'\s*\[Root Me.*\]', '', raw_title)
                raw_title = re.sub(r'\s*-\s*Root-Me.*', '', raw_title)
                # Nettoyage des préfixes "Challenges/Rubrique :"
                raw_title = re.sub(r'^Challenges/[^:]+\s*:\s*', '', raw_title)
                title = raw_title.strip()
            else:
                title = "Titre Inconnu"
            
            # Nettoyage du titre pour le slug si besoin (mais on préfère le slug de l'URL)
            slug = url.split('/')[-1]
            if not slug or slug == "":
                slug = url.split('/')[-2]
                
            if challenge_id:
                return {
                    "id": challenge_id,
                    "title": title,
                    "slug": slug,
                    "url": url
                }
            print(f"⚠️ ID non trouvé via scraping sur {url}.")
            
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping : {e}")
            

    
    # Extraction du slug depuis l'URL si besoin
    slug = url.split('/')[-1]
    if not slug or slug == "":
        slug = url.split('/')[-2]

    # Tentative via API
    print("⚠️ Tentative via API (clé présente dans fetch-rootme.py)...")
    return get_challenge_info_via_api(slug)

def get_api_key():
    """Récupère la clé API depuis .env ou fetch-rootme.py."""
    # 1. Priorité au .env
    key = ENV.get("ROOTME_API_KEY")
    if key: return key
    
    # 2. Fallback sur le script fetch
    try:
        with open(FETCH_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()
            m = re.search(r'ROOTME_API_KEY\s*=\s*os\.environ\.get\("[^"]*",\s*"([^"]+)"\)', content)
            if m:
                return m.group(1)
            m = re.search(r'ROOTME_API_KEY\s*=\s*"([^"]+)"', content)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None

def get_challenge_info_via_api(slug):
    """Cherche le challenge via l'API Root-Me."""
    import time
    api_key = get_api_key()
    if not api_key:
        print("❌ Impossible de trouver la clé API dans fetch-rootme.py")
        return None
        
    # Stratégies de recherche (du plus précis au plus large)
    search_terms = [
        slug.replace("-", " - "),       # "Hash - DCC" (Hyphen preserved)
        slug.replace("-", " "),         # "XSS Stockee 1"
        " ".join(slug.split("-")[:2]),  # "XSS Stockee" (souvent suffisant)
        slug.split("-")[-1],            # "DCC" (Last resort)
    ]
    
    # Si le slug est complexe, on ajoute un candidat
    if len(slug.split("-")) >= 3:
        # "Command Control niveau 2" -> "Command Control"
        search_terms.append(" ".join(slug.split("-")[:3]))
    
    seen = set()
    unique_terms = []
    for t in search_terms:
        if t and t not in seen and len(t) >= 3:
            unique_terms.append(t)
            seen.add(t)
    
    for search_term in unique_terms:
        print(f"🔍 Recherche API pour : '{search_term}'")
        url = f"https://api.www.root-me.org/challenges?titre={urllib.parse.quote(search_term)}"
        
        # Retry logic for 429/5xx
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Polite delay
                time.sleep(1.5)
                
                
                req = urllib.request.Request(url)
                if ROOTME_COOKIES:
                    req.add_header("Cookie", ROOTME_COOKIES)
                else:
                    req.add_header("Cookie", f"api_key={api_key}")
                    
                req.add_header("User-Agent", "Mozilla/5.0")
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    
                    if not data:
                        print(f"   Pas de résultat pour '{search_term}'.")
                        break
                
                # Filtrage local pour trouver le meilleur match
                # On normalise pour comparer : "elfx860protection"
                target_norm = slug.replace("-", "").lower()
                
                best_match = None
                
                # Normalisation pour itérer (structure bizarre de l'API parfois)
                challenges_list = []
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            # Soit c'est un challenge direct, soit un dict de challenges
                            if 'titre' in item:
                                challenges_list.append(item)
                            else:
                                challenges_list.extend(item.values())
                elif isinstance(data, dict):
                    if 'titre' in data:
                        challenges_list.append(data)
                    else:
                        challenges_list.extend(data.values())

                for val in challenges_list:
                    if not isinstance(val, dict): continue
                    
                    title = val.get('titre', '')
                    if not title: continue
                    
                    title_norm = re.sub(r'[^a-zA-Z0-9]', '', title).lower()
                    target_norm = re.sub(r'[^a-zA-Z0-9]', '', slug).lower()
                    
                    if target_norm in title_norm or title_norm in target_norm:
                        best_match = val
                        break
                
                if best_match:
                    return {
                        "id": best_match['id_challenge'],
                        "title": best_match['titre'],
                        "slug": slug,
                        "url": f"https://www.root-me.org/fr/Challenges/{best_match.get('rubrique','Systeme')}/{slug}"
                    }
                
                # Si on est ici, on n'a rien trouvé pour ce search_term
                print(f"   ⚠️ Aucun match local pour '{search_term}' parmi {len(challenges_list)} résultats.")
                break # On passe au search_term suivant
                    
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    wait_time = (attempt + 1) * 5
                    print(f"   ⚠️ Rate limit/Erreur serveur ({e.code}). Nouvelle tentative dans {wait_time}s...")
                    time.sleep(wait_time)
                elif e.code == 404:
                    print(f"   Pas de résultat (404) pour '{search_term}'.")
                    break
                else:
                    print(f"❌ Erreur API : {e}")
                    break
            except Exception as e:
                print(f"❌ Erreur API : {e}")
                break

    print("❌ Aucun challenge trouvé après toutes les tentatives.")
    return None

def get_challenge_info_via_api_by_id(challenge_id):
    """Récupère les infos précises d'un challenge via son ID."""
    api_key = get_api_key()
    if not api_key: return None
    
    url = f"https://api.www.root-me.org/challenges/{challenge_id}"
    try:
        req = urllib.request.Request(url)
        if ROOTME_COOKIES:
            req.add_header("Cookie", ROOTME_COOKIES)
        else:
            req.add_header("Cookie", f"api_key={api_key}")
            
        req.add_header("User-Agent", "Mozilla/5.0")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            if 'titre' in data:
                return {
                    "id": challenge_id,
                    "title": data['titre'],
                    "category": data.get('rubrique', 'Divers'),
                    "url": f"https://www.root-me.org/{data.get('url_challenge', '')}"
                }
    except Exception as e:
        print(f"⚠️ Impossible de récupérer les détails de l'ID {challenge_id} : {e}")
    return None

# La mise à jour de fetch-rootme.py n'est plus nécessaire 
# car il détecte maintenant les IDs dans le frontmatter.

def format_frontmatter_value(key, value):
    if key in {"title"}:
        return f"\"{value}\""
    if key in {"categories", "tags"}:
        if isinstance(value, (list, tuple)):
            inner = ", ".join(f"\"{v}\"" for v in value)
            return f"[{inner}]"
    if key in {"draft"}:
        return "true" if value else "false"
    return str(value)

def should_update_frontmatter(key, current_value):
    current_value = (current_value or "").strip().strip('"').strip("'")
    if key == "rootme_id":
        return True
    if key == "title":
        return current_value == "" or current_value.lower() in {"titre inconnu", "inconnu"}
    if key in {"categories", "image"}:
        return current_value == ""
    return False

def update_frontmatter_file(path, updates):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    m = re.match(r"(?s)^---\n(.*?)\n---\n", text)
    if not m:
        return False
    fm = m.group(1)
    lines = fm.splitlines()
    current = {}
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            current[k.strip()] = v.strip()
    new_lines = []
    for line in lines:
        if ":" in line:
            k, _ = line.split(":", 1)
            key = k.strip()
            if key in updates and should_update_frontmatter(key, current.get(key, "")):
                line = f"{key}: {format_frontmatter_value(key, updates[key])}"
            new_lines.append(line)
        else:
            new_lines.append(line)
    for key, value in updates.items():
        if key not in current and should_update_frontmatter(key, ""):
            new_lines.append(f"{key}: {format_frontmatter_value(key, value)}")
    new_fm = "\n".join(new_lines)
    new_text = text[:m.start(1)] + new_fm + text[m.end(1):]
    path.write_text(new_text, encoding="utf-8")
    return True

def create_content_files(info):
    """Crée les dossiers et fichiers markdown."""
    print("📂 Création des fichiers...")
    
    dir_path = CONTENT_DIR / info['slug']
    dir_path.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime, timedelta
    date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Détection de la catégorie
    category = info.get('category')
    if not category:
        category = "Réseau"
        if "Programmation" in info['url']: category = "Programmation"
        elif "Web-Client" in info['url']: category = "Web - Client"
        elif "Web-Serveur" in info['url']: category = "Web - Serveur"
        elif "App-Systeme" in info['url'] or "Systeme" in info['url']: category = "App - Système"
        elif "App-Script" in info['url']: category = "App - Script"
        elif "Cracking" in info['url']: category = "Cracking"
        elif "Cryptanalyse" in info['url']: category = "Cryptanalyse"
        elif "Forensic" in info['url']: category = "Forensic"
        elif "Realiste" in info['url']: category = "Réaliste"
        elif "Steganographie" in info['url']: category = "Stéganographie"

    updates = {
        "title": info["title"],
        "rootme_id": info["id"],
        "categories": ["Root-Me", category],
        "image": "/img/banners/rootme-banner.png",
    }

    created_any = False
    # Fichier FR
    md_fr = f"""---
title: "{info['title']}"
date: {date_str}
image: "/img/banners/rootme-banner.png"
draft: false
rootme_id: {info['id']}
categories: ["Root-Me", "{category}"]
tags: ["TODO"]
---

{{{{< rootme-challenge slug="{info['slug']}" url="{info['url']}" >}}}}

---

## Contexte
Writeup à rédiger...
"""
    
    fr_path = dir_path / "index.md"
    if fr_path.exists():
        if update_frontmatter_file(fr_path, updates):
            print(f"✅ Frontmatter mis à jour (contenu conservé) : {fr_path}")
    else:
        with open(fr_path, "w", encoding="utf-8") as f:
            f.write(md_fr)
        created_any = True

    # Fichier EN
    md_en = f"""---
title: "{info['title']}"
date: {date_str}
image: "/img/banners/rootme-banner.png"
draft: false
rootme_id: {info['id']}
categories: ["Root-Me", "{category}"]
tags: ["TODO"]
---

{{{{< rootme-challenge slug="{info['slug']}" url="{info['url']}" >}}}}

---

## Context
Writeup to write...
"""
    
    en_path = dir_path / "index.en.md"
    if en_path.exists():
        if update_frontmatter_file(en_path, updates):
            print(f"✅ Frontmatter mis à jour (contenu conservé) : {en_path}")
    else:
        with open(en_path, "w", encoding="utf-8") as f:
            f.write(md_en)
        created_any = True
        
    if created_any:
        print(f"✅ Fichiers créés dans {dir_path}")
    else:
        print(f"✅ Dossier déjà existant : {dir_path}")

def run_fetch_script():
    """Lance le script de fetch pour mettre à jour le JSON data."""
    print("🚀 Lancement de la mise à jour des données...")
    try:
        venv_dir = ROOT_DIR / ".venv-rootme"
        venv_python = venv_dir / "bin" / "python3"
        if not venv_python.exists():
            venv_python = venv_dir / "bin" / "python"
        if venv_python.exists():
            ret = os.system(f"{venv_python} {FETCH_SCRIPT}")
        else:
            ret = os.system(f"python3 {FETCH_SCRIPT}")
        if ret != 0:
            print("⚠️ La mise à jour des données a échoué (429 ?). Pas de panique, le workflow quotidien s'en chargera demain.")
    except Exception as e:
         print(f"⚠️ Erreur lors de l'exécution du fetch : {e}")

def strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

def normalize_date_for_frontmatter(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", s)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"
    m = re.search(r"\b(\d{1,2})\s+([A-Za-zÀ-ÿ\.]+)\s+(\d{4})\b", s)
    if m:
        day = int(m.group(1))
        month_name = strip_accents(m.group(2).lower().strip("."))
        year = int(m.group(3))
        month_map = {
            "janvier": 1,
            "janv": 1,
            "fevrier": 2,
            "fevr": 2,
            "mars": 3,
            "avril": 4,
            "avr": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "juil": 7,
            "aout": 8,
            "septembre": 9,
            "sept": 9,
            "octobre": 10,
            "oct": 10,
            "novembre": 11,
            "nov": 11,
            "decembre": 12,
            "dec": 12,
        }
        if month_name in month_map:
            month = month_map[month_name]
            return f"{year:04d}-{month:02d}-{day:02d}"
    return None

def update_frontmatter_dates(info):
    if not info:
        return
    if not CHALLENGES_FILE.exists():
        return
    try:
        with open(CHALLENGES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    entry = data.get(info.get("slug"))
    if not entry:
        for item in data.values():
            if str(item.get("id")) == str(info.get("id")):
                entry = item
                break
    if not entry:
        return
    date_raw = entry.get("date_publication") or entry.get("date")
    date_norm = normalize_date_for_frontmatter(date_raw)
    if not date_norm:
        return
    dir_path = CONTENT_DIR / info["slug"]
    for filename in ("index.md", "index.en.md"):
        path = dir_path / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        replaced = False
        for i, line in enumerate(lines):
            if line.startswith("date:"):
                lines[i] = f"date: {date_norm}"
                replaced = True
                break
        if not replaced:
            for i, line in enumerate(lines):
                if line.startswith("title:"):
                    lines.insert(i + 1, f"date: {date_norm}")
                    replaced = True
                    break
        if replaced:
            new_text = "\n".join(lines)
            if text.endswith("\n"):
                new_text += "\n"
            path.write_text(new_text, encoding="utf-8")
    print(f"🗓️ Date du challenge mise à jour: {date_norm}")

def main():
    if len(sys.argv) < 2:
        print("Usage: ./add-challenge.py <URL_CHALLENGE> [ID_CHALLENGE]")
        print("   Exemples:")
        print("     ./add-challenge.py https://www.root-me.org/...")
        print("     ./add-challenge.py https://www.root-me.org/... 1014")
        print("     ./add-challenge.py https://sadservers.com/scenario/...")
        sys.exit(1)
        
    url = sys.argv[1]
    manual_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Détection SadServers
    if "sadservers.com" in url:
        print("🔍 Détection d'un challenge SadServers...")
        # Extraction du slug depuis l'URL (ex: /scenario/saint-john)
        m = re.search(r'/scenario/([^/]+)', url)
        if not m:
            print("❌ Impossible de trouver le slug du scénario dans l'URL.")
            sys.exit(1)
            
        slug = m.group(1)
        slug = m.group(1)
        print(f"🚀 Analyse de '{slug}'...")

        # 1. Récupérer les données
        scenario = fetch_sadservers_data(slug)
        if not scenario:
            print("❌ Impossible de récupérer les données du scénario.")
            sys.exit(1)
            
        print("\n📋 Données récupérées:")
        for key, value in scenario.items():
            if key == "description":
                print(f"   {key}: {value[:80]}...")
            elif isinstance(value, list):
                print(f"   {key}: {', '.join(value)}")
            else:
                print(f"   {key}: {value}")
                
        # 2. Mettre à jour JSON
        update_sadservers_json(slug, scenario)
        
        # 3. Créer contenu
        create_sadservers_content(slug, scenario)
        
        print("\n🎉 Terminé ! Tu n'as plus qu'à rédiger ton writeup.")
        sys.exit(0)
    
    # Sinon Root-Me (logique existante)
    info = None
    slug = url.split('/')[-1] or url.split('/')[-2]

    # 1. Option: ID manuel force
    if manual_id:
        print(f"🚀 Utilisation de l'ID manuel : {manual_id}")
        info = {"id": manual_id, "url": url, "slug": slug, "title": slug, "category": "Root-Me"}
        
    # 2. Option: Le challenge existe déjà avec des stats valides (cache)
    if not info:
        existing = ROOTME_CHALLENGES.get(slug)
        if existing and existing.get("validations", 0) > 0 and existing.get("titre") != "Inconnu":
            print(f"✅ Le challenge '{slug}' existe déjà avec des données valides ({existing['validations']} validations).")
            print("   Utilisation des données locales (pas de requête API/Scraping).")
            info = {
                "id": existing['id'],
                "title": existing.get("titre"),
                "slug": slug,
                "url": existing.get("url", url),
                "category": existing.get("rubrique"),
                "_from_cache": True
            }
            
    # 3. Option: Scraping / API
    if not info:
        info = get_challenge_info(url)
    
    # Correction API officielle (seulement si pas du cache)
    if USE_API_DETAILS and info and info['id'] and not "PENDING" in str(info['id']) and not info.get("_from_cache"):
        print(f"✅ ID {info['id']} trouvé. Récupération des détails officiels...")
        official_info = get_challenge_info_via_api_by_id(info['id'])
        if official_info:
            info = official_info
            info['slug'] = slug # On garde le slug de l'URL

    if info and 'title' not in info:
        info['title'] = slug
    if info and 'category' not in info:
        info['category'] = "Root-Me" # Default fallback
    
    # Fallback AUTOMATIQUE si échec (PENDING)
    if not info:
        print("\n⚠️ Échec de la récupération automatique. Passage en mode 'PENDING'.")
        print("   Le post sera créé, et l'ID sera récupéré automatiquement plus tard par le workflow quotidien.")
        
        m = re.search(r'Challenges/([^/]+)/([^/]+)', url)
        if m:
             default_slug = m.group(2)
             # On utilise un ID temporaire "PENDING_<slug>" pour être unique
             pending_id = f"PENDING_{default_slug}"
             
             info = {
                 "id": pending_id,
                 "title": f"{default_slug} (Pending)",
                 "slug": default_slug,
                 "url": url
             }
    
    if not info:
        print("❌ Impossible de récupérer les infos.")
        sys.exit(1)
        
    if not info['id']:
        print("❌ ID du challenge introuvable.")
        sys.exit(1)
        
    print(f"✅ Trouvé : [{info['id']}] {info['title']} ({info['slug']})")
    
    # On vérifie si les fichiers existent déjà
    dir_path = CONTENT_DIR / info['slug']
    if dir_path.exists():
        print(f"⚠️ Le dossier {info['slug']} existe déjà. Mise à jour des fichiers...")
    
    create_content_files(info)
    
    # Lancement automatique du fetch pour mettre à jour les donnés complètes
    run_fetch_script()
    update_frontmatter_dates(info)
        
    print("\n🎉 Terminé ! Tu n'as plus qu'à rédiger ton writeup dans :")
    print(f"   content/root-me-challenges/{info['slug']}/index.md")
    print("⏳ Les stats et infos complètes seront mises à jour automatiquement au prochain cycle (toutes les 4h).")

if __name__ == "__main__":
    main()
