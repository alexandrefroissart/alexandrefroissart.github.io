#!/usr/bin/env python3
"""
Script pour récupérer les données Root-Me via l'API.
- Données du profil utilisateur
- Données des challenges

Usage: python3 fetch-rootme.py
"""

import urllib.request
import urllib.error
import json
import os
import sys
import re
import time
import subprocess
import socket
from http.client import IncompleteRead
from pathlib import Path
from datetime import datetime
from html import unescape
import unicodedata
import random
try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None

# Configuration Root-Me
ENV_FILE = Path(__file__).parent.parent / ".env"

def load_env():
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
ROOTME_UID = ENV.get("ROOTME_UID", "1071705")
ROOTME_API_KEY = ENV.get("ROOTME_API_KEY", "1071705_b1a923c6f19edcb89aa15bee046a6fe745144f36dbb24c316752ee391fc1a958")
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

ROOTME_COOKIES = build_rootme_cookies(ENV)  # Cookies complets (e.g. "spip_session=...; api_key=...")
ROOTME_PROFILE_URL = ENV.get("ROOTME_PROFILE_URL") or f"https://www.root-me.org/{ENV.get('ROOTME_USER', 'Alexandre-Froissart')}"

# Chemins
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
PROFILE_FILE = DATA_DIR / "rootme.json"
CHALLENGES_FILE = DATA_DIR / "rootme_challenges.json"
CONTENT_DIR = SCRIPT_DIR.parent / "content" / "root-me-challenges"
ROOT_DIR = SCRIPT_DIR.parent
DEFAULT_VENV_DIR = ROOT_DIR / ".venv-rootme"

API_DISABLED = False

SCRAPE_DELAY_RANGE = (2.0, 4.0)
DEBUG_HTML = os.environ.get("ROOTME_DEBUG_HTML", "0") == "1"
DEBUG_DIR = Path(os.environ.get("ROOTME_DEBUG_DIR", str(ROOT_DIR / ".debug" / "rootme")))
FORCE_HTML_VALIDATIONS = os.environ.get("ROOTME_FORCE_HTML_VALIDATIONS", "1") == "1"

# NOTE: On ne définit plus les challenges ici, on les détecte dans /content/root-me-challenges/*/index.md
# via la clé 'rootme_id' dans le frontmatter.
CHALLENGES = {}

# Normalisation/Parsing HTML
DIFFICULTY_LABELS = {
    1: "Très facile",
    2: "Facile",
    3: "Moyen",
    4: "Difficile",
    5: "Très difficile",
}

GENERIC_TITLES = {
    "root-me",
    "root me",
    "rootme",
    "challenges",
    "challenge",
    "user",
    "profil de user",
    "bienvenue",
}

INVALID_DATES = {"", "-1", "0", "inconnu", "unknown", None}

CATEGORY_TO_SEGMENT = {
    "reseau": "Reseau",
    "programmation": "Programmation",
    "web-serveur": "Web-Serveur",
    "web-client": "Web-Client",
    "app-systeme": "App-Systeme",
    "app-script": "App-Script",
    "cryptanalyse": "Cryptanalyse",
    "forensic": "Forensic",
    "cracking": "Cracking",
    "realiste": "Realiste",
    "steganographie": "Steganographie",
}

_BS4_WARNED = False


def _in_venv(target_path):
    try:
        return Path(sys.prefix).resolve() == Path(target_path).resolve()
    except Exception:
        return False


def _venv_has_bs4(venv_dir):
    try:
        for site in venv_dir.glob("lib/python*/site-packages/bs4/__init__.py"):
            if site.exists():
                return True
    except Exception:
        return False
    return False


def ensure_beautifulsoup():
    """Tente d'importer BeautifulSoup, sinon installe beautifulsoup4 via pip."""
    global BeautifulSoup
    if BeautifulSoup is not None:
        return True
    venv_dir = Path(os.environ.get("ROOTME_VENV", DEFAULT_VENV_DIR))
    venv_python = venv_dir / "bin" / "python3"
    if not venv_python.exists():
        venv_python = venv_dir / "bin" / "python"

    # Déjà dans le venv : tente l'install ici
    if _in_venv(venv_dir):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
            from bs4 import BeautifulSoup as _BeautifulSoup  # type: ignore
            BeautifulSoup = _BeautifulSoup
            print("✅ BeautifulSoup installé dans le venv.")
            return True
        except Exception as e:
            print(f"⚠️ Installation de BeautifulSoup impossible dans le venv: {e}")
            BeautifulSoup = None
            return False

    # Évite la boucle infinie si on a déjà tenté un bootstrap
    if os.environ.get("ROOTME_VENV_BOOTSTRAP") == "1":
        print("⚠️ Venv bootstrap déjà tenté. Fallback regex actif.")
        return False

    # Crée un venv dédié et relance le script dedans
    try:
        print("⚠️ BeautifulSoup manquant. Création d'un venv local et relance automatique...")
        if not venv_dir.exists():
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        if not _venv_has_bs4(venv_dir):
            # Installe bs4 dans le venv si manquant
            subprocess.check_call([str(venv_python), "-m", "pip", "install", "beautifulsoup4"])
        env = os.environ.copy()
        env["ROOTME_VENV_BOOTSTRAP"] = "1"
        os.execvpe(str(venv_python), [str(venv_python)] + sys.argv, env)
    except Exception as e:
        print(f"⚠️ Impossible de créer/activer le venv automatiquement: {e}")
        BeautifulSoup = None
        return False


# Best-effort install on startup so scraping is robust.
ensure_beautifulsoup()


def normalize_space(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()

def is_basic_profile_url(url):
    if not url:
        return True
    return ("page=info_auteur" in url) or ("spip.php?auteur" in url)

def build_profile_slug(name):
    if not name:
        return None
    if "@" in name:
        return None
    slug = normalize_space(name)
    if not slug:
        return None
    slug = re.sub(r"[\s_]+", "-", slug.strip())
    slug = re.sub(r"-{2,}", "-", slug)
    return slug

def build_pretty_profile_url(name):
    slug = build_profile_slug(name)
    if not slug:
        return None
    return f"https://www.root-me.org/{slug}?lang=fr"


def safe_get_text(node):
    if node is None:
        return ""
    if hasattr(node, "get_text"):
        try:
            return node.get_text(" ", strip=True)
        except Exception:
            return str(node)
    return str(node)


def normalize_category_key(text):
    if not text:
        return ""
    raw = normalize_space(str(text))
    raw = unicodedata.normalize("NFKD", raw)
    raw = raw.encode("ascii", "ignore").decode("ascii")
    raw = raw.lower()
    raw = re.sub(r"\s*-\s*", "-", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def _safe_filename(text):
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", str(text)).strip("_")


def debug_dump(kind, ident, url, html=None, status=None, error=None):
    if not DEBUG_HTML:
        return
    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = _safe_filename(f"{kind}_{ident}_{ts}")
        if html is not None:
            path = DEBUG_DIR / f"{base}.html"
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"<!-- url: {url} status: {status} -->\n")
                f.write(html)
        if error:
            path = DEBUG_DIR / f"{base}.log"
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"url: {url}\nstatus: {status}\nerror: {error}\n")
    except Exception:
        pass


def is_profile_html(html):
    if not html:
        return False
    # Reject generic "profil de user" pages (not authenticated)
    if re.search(r"profil\\s+de\\s+user", html, re.IGNORECASE):
        return False
    if re.search(r'<meta name="author" content="user"', html, re.IGNORECASE):
        return False
    # Strong markers for user profile pages
    if "inc=score" in html or "inc=valid" in html or "inc=ctf" in html:
        return True
    if re.search(r"\\bClassement\\b", html, re.IGNORECASE) and re.search(r"\\bValidations\\b", html, re.IGNORECASE):
        return True
    if re.search(r"\\bProfil\\b", html, re.IGNORECASE) and re.search(r"\\bScore\\b", html, re.IGNORECASE):
        return True
    return False


def is_logged_out(html):
    if not html:
        return False
    if ("page=login" in html or "Se connecter" in html) and "Déconnexion" not in html:
        return True
    if "page=identifiants" in html or "Créer un compte" in html:
        return True
    return False


def find_inc_score_url(html, base_url):
    if not html:
        return None
    href = None
    if BeautifulSoup is not None:
        try:
            soup = BeautifulSoup(html, "html.parser")
            link = soup.find("a", href=re.compile(r"user\\?inc=score", re.IGNORECASE))
            if link:
                href = link.get("href")
        except Exception:
            href = None
    if not href:
        m = re.search(r'href="(user\\?inc=score[^"]*)"', html, re.IGNORECASE)
        if m:
            href = m.group(1)
    if not href:
        return None
    return urllib.parse.urljoin(base_url, href)


def parse_profile_score_html(html, result):
    if not html:
        return result
    try:
        if BeautifulSoup is None:
            return result
        soup = BeautifulSoup(html, "html.parser")
        # Ignore generic/anonymous score blocks
        user_span = soup.select_one("h1 span.txt_6forum")
        if user_span:
            user_label = normalize_space(user_span.get_text(" ", strip=True)).lower()
            if user_label == "user":
                return result
        # Icon-based extraction (more reliable than labels)
        icon_map = {
            "classement.svg": "position",
            "valid.svg": "score",
            "rubon5.svg": "challenges_resolus",
        }
        for img in soup.find_all("img"):
            src = img.get("src") or ""
            key = None
            for icon, mapped in icon_map.items():
                if icon in src:
                    key = mapped
                    break
            if not key:
                continue
            h3 = img.find_parent("h3")
            if not h3:
                parent = img.find_parent()
                h3 = parent.find("h3") if parent else None
            if not h3:
                continue
            val = coerce_int(safe_get_text(h3))
            if val is not None:
                result[key] = val
        # Tiles with Points / Place / Challenges
        label_map = {
            "points": "score",
            "score": "score",
            "place": "position",
            "rang": "position",
            "challenges": "challenges_resolus",
            "validations": "challenges_resolus",
        }
        for span in soup.find_all("span", class_=re.compile(r"\\bgras\\b", re.IGNORECASE)):
            label = normalize_space(span.get_text(" ", strip=True)).lower()
            key = label_map.get(label)
            if not key:
                continue
            container = span.parent
            h3 = container.find("h3") if container else None
            if h3:
                val = coerce_int(safe_get_text(h3))
                if val is not None:
                    result[key] = val
        # Table fallback (rank)
        if not result.get("position"):
            td = soup.find("td", class_=re.compile(r"\\bgras\\b", re.IGNORECASE))
            if td:
                m = re.search(r"#\\s*(\\d+)", safe_get_text(td))
                if m:
                    result["position"] = coerce_int(m.group(1))
    except Exception:
        pass
    return result


def fetch_profile_score_direct(headers):
    """Récupère le bloc score utilisateur via l'endpoint AJAX."""
    urls = [
        "https://www.root-me.org/user?inc=score&lang=fr",
        "https://www.root-me.org/User?inc=score&lang=fr",
        "https://www.root-me.org/?page=user&inc=score&lang=fr",
    ]
    for url in urls:
        html = fetch_url_text(url, headers=headers, timeout=10, max_retries=2, debug_label="profile_score")
        if not html:
            continue
        if is_logged_out(html):
            continue
        parsed = parse_profile_score_html(html, {})
        score_val = parsed.get("score") or 0
        pos_val = parsed.get("position") or 0
        chall_val = parsed.get("challenges_resolus") or 0
        if score_val > 0 or pos_val > 0 or chall_val > 0:
            return parsed
    return None


def fetch_rank_from_leaderboard(username):
    """Récupère le rang réel depuis la page de profil public Root-Me via curl."""
    if not username:
        return None
    
    import subprocess
    
    # Nettoyer le username pour l'URL
    search_name = username.replace(" ", "-").replace("_", "-")
    
    # Construire la commande curl avec les cookies si disponibles
    profile_url = f"https://www.root-me.org/{search_name}?lang=fr"
    
    # Lire les cookies depuis le fichier .env si disponibles
    cookie_str = ""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            cookies = {}
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        parts = line.strip().split("=", 1)
                        if len(parts) == 2:
                            cookies[parts[0]] = parts[1]
            spip = cookies.get("spip_session", "")
            php = cookies.get("PHPSESSID", "")
            if spip or php:
                cookie_str = f"spip_session={spip}; PHPSESSID={php}"
        except Exception:
            pass
    
    # Exécuter curl (bypasse la protection anti-bot Anubis)
    cmd = ["curl", "-s", "-L", "--max-time", "15"]
    if cookie_str:
        cmd.extend(["-H", f"Cookie: {cookie_str}"])
    cmd.append(profile_url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        html = result.stdout
        
        if not html or "classement.svg" not in html:
            print(f"⚠️ Curl n'a pas retourné le profil attendu")
            return None
        
        # Extraire le rang avec pattern regex
        # Format: classement.svg...'/>&nbsp;274734
        patterns = [
            r"classement\.svg[^/]*/>\s*&nbsp;\s*(\d+)",
            r"classement\.svg[^/]*/>&nbsp;(\d+)",
            r"classement\.svg[^>]*>\s*&nbsp;\s*(\d+)",
            r"classement\.svg.*?(\d{4,})",
        ]
        
        for pattern in patterns:
            m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if m:
                rank = coerce_int(m.group(1))
                if rank and rank > 0 and rank < 500000:
                    print(f"✅ Rang trouvé via curl: #{rank}")
                    return rank
        
        print(f"⚠️ Pattern rang non trouvé dans le HTML curl")
    except subprocess.TimeoutExpired:
        print(f"⚠️ Curl timeout pour {profile_url}")
    except FileNotFoundError:
        print(f"⚠️ Curl non disponible, fallback urllib")
        # Fallback vers la méthode urllib originale
        return _fetch_rank_urllib(username)
    except Exception as e:
        print(f"⚠️ Erreur curl: {e}")
    
    return None


def _fetch_rank_urllib(username):
    """Fallback: récupère le rang via urllib (bloqué par anti-bot)."""
    search_name = username.replace(" ", "-").replace("_", "-")
    profile_url = f"https://www.root-me.org/{search_name}?lang=fr"
    
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    if ROOTME_COOKIES:
        headers["Cookie"] = ROOTME_COOKIES
    
    html = fetch_url_text(profile_url, headers=headers, timeout=15, max_retries=2, debug_label="profile_rank")
    if not html or "classement.svg" not in html:
        return None
    
    m = re.search(r"classement\.svg.*?(\d{4,})", html, re.DOTALL)
    if m:
        return coerce_int(m.group(1))
    return None


def category_to_segment(category):
    key = normalize_category_key(category)
    return CATEGORY_TO_SEGMENT.get(key)


def parse_frontmatter_categories(content):
    if not content.startswith("---"):
        return []
    parts = content.split("---", 2)
    if len(parts) < 3:
        return []
    fm = parts[1]
    categories = []
    # Inline list: categories: ["Root-Me", "Réseau"]
    m_inline = re.search(r"^categories:\s*\[(.*?)\]\s*$", fm, re.MULTILINE)
    if m_inline:
        raw = m_inline.group(1)
        for item in raw.split(","):
            item = item.strip().strip('"').strip("'")
            if item:
                categories.append(item)
        return categories
    # Multi-line list:
    lines = fm.splitlines()
    in_list = False
    for line in lines:
        if not in_list:
            if re.match(r"^categories:\s*$", line.strip()):
                in_list = True
            continue
        # Stop if next key
        if re.match(r"^\w+:\s*", line.strip()):
            break
        m_item = re.match(r"^\s*-\s*(.+)$", line)
        if m_item:
            item = m_item.group(1).strip().strip('"').strip("'")
            if item:
                categories.append(item)
    return categories


def clean_title(raw_title):
    if not raw_title:
        return ""
    title = normalize_space(unescape(str(raw_title)))
    title = re.sub(r"\s*\[Root\s*Me.*\]", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*Root[-\s]?Me.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Challenges?/[^:]+\s*:\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Challenges?\s*:\s*", "", title, flags=re.IGNORECASE)
    return title.strip()


def is_generic_title(title):
    t = normalize_space(title).lower()
    return not t or t in GENERIC_TITLES


def coerce_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = normalize_space(str(value))
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    if digits.isdigit():
        return int(digits)
    return None


def extract_percent(text):
    if not text:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
    if not m:
        return None
    return m.group(1).replace(",", ".") + "%"


def extract_date_from_text(text):
    if not text:
        return None
    # ISO date
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if m:
        return m.group(1)
    # FR long date: 24 décembre 2012
    m = re.search(r"\b(\d{1,2}\s+[A-Za-zÀ-ÿ]+(?:\s+\d{4})?)\b", text)
    if m and re.search(r"\d{4}", m.group(1)):
        return normalize_space(m.group(1))
    # Slash date
    m = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", text)
    if m:
        return m.group(1)
    return None


def normalize_difficulty(value, level=None):
    if value is not None:
        if isinstance(value, (int, float)) and int(value) in DIFFICULTY_LABELS:
            return DIFFICULTY_LABELS[int(value)]
        s = normalize_space(str(value))
        if s.isdigit() and int(s) in DIFFICULTY_LABELS:
            return DIFFICULTY_LABELS[int(s)]
        if s:
            return s
    if level in DIFFICULTY_LABELS:
        return DIFFICULTY_LABELS[level]
    return None


def merge_challenge_data(new_data, old_data):
    if not old_data:
        return new_data
    merged = dict(old_data)
    for key, val in new_data.items():
        if key in ("validations", "score"):
            try:
                if isinstance(val, str) and val.isdigit():
                    val_int = int(val)
                elif isinstance(val, int):
                    val_int = val
                else:
                    val_int = None
                if val_int and val_int > 0:
                    merged[key] = val_int
            except Exception:
                pass
            continue
        if key == "note":
            if val and val != "0%":
                merged[key] = val
            continue
        if key == "date":
            if val and str(val).strip().lower() not in INVALID_DATES:
                merged[key] = val
            continue
        if key == "difficulte":
            if val and val != "Inconnu":
                merged[key] = val
            continue
        if isinstance(val, str):
            if val and val not in ("Inconnu", "Titre Inconnu", "?", "0%"):
                merged[key] = val
            continue
        if val is not None:
            merged[key] = val
    # S'assurer que l'URL est la plus complète
    if new_data.get("url"):
        merged["url"] = new_data["url"]
    return merged


def parse_challenge_html_regex(html):
    """Fallback regex-only parsing if BeautifulSoup is unavailable."""
    result = {}

    # Score (Points)
    m_score = re.search(r'h2[^>]*>\s*(\d+)(?:&nbsp;|\s)*Points', html, re.IGNORECASE)
    if not m_score:
        m_score = re.search(r'(\d+)(?:&nbsp;|\s)*Points', html, re.IGNORECASE)
    if m_score:
        result["score"] = coerce_int(m_score.group(1))

    # Auteur & Date
    m_author_block = re.search(r'h4>Auteur</h4>(.*?)(?:<div|h4)', html, re.DOTALL | re.IGNORECASE)
    if m_author_block:
        block = m_author_block.group(1)
        m_user = re.search(r'<a[^>]*>([^<]+)</a>', block)
        m_date = re.search(r'<time[^>]*>([^<]+)</time>', block)
        if m_user:
            result["auteur"] = normalize_space(m_user.group(1))
        if m_date:
            result["date"] = normalize_space(m_date.group(1).replace("&nbsp;", " "))

    if not result.get("date"):
        date_guess = extract_date_from_text(unescape(html))
        if date_guess:
            result["date"] = date_guess

    # Difficulté
    m_diff = re.search(r'class="[^"]*difficulte(\d+)a[^"]*"[^>]*title="([^":]+)', html, re.IGNORECASE)
    if m_diff:
        level = coerce_int(m_diff.group(1))
        label = normalize_space(m_diff.group(2))
        result["difficulte"] = normalize_difficulty(label, level=level)
    else:
        m_diff = re.search(r'class="[^"]*difficulte(\d+)a[^"]*"', html, re.IGNORECASE)
        if m_diff:
            level = coerce_int(m_diff.group(1))
            result["difficulte"] = normalize_difficulty(None, level=level)

    # Validations / Challengeurs
    m_val = re.search(r'validations?_challenge[^>]*>\s*([\d\s\.\xa0]+)', html, re.IGNORECASE)
    if not m_val:
        m_val = re.search(r'>(\d+(?:[\s\.]\d+)*)(?:&nbsp;|\s)+(?:Challengeurs|Validations)<', html, re.IGNORECASE)
    if m_val:
        result["validations"] = coerce_int(m_val.group(1))

    # Titre <title>
    m_title = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    if m_title:
        raw_title = m_title.group(1).strip()
        title = clean_title(raw_title)
        if not is_generic_title(title):
            result["titre"] = title

    # Taux de réussite (pourcentage)
    m_tx = re.search(r'>([\d\.,]+)\s*%<', html)
    if m_tx:
        result["note"] = m_tx.group(1) + "%"

    return result


def parse_challenge_html(html):
    """Parse la page HTML d'un challenge Root-Me avec BS4 (fallback regex)."""
    global _BS4_WARNED

    if BeautifulSoup is None:
        if not _BS4_WARNED:
            print("⚠️ BeautifulSoup non disponible. Fallback regex actif.")
            _BS4_WARNED = True
        return parse_challenge_html_regex(html)
    try:
        soup = BeautifulSoup(html, "html.parser")
        result = {}
        # JSON-LD (si présent)
        ld_items = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                raw = script.string or script.get_text()
                if not raw:
                    continue
                data = json.loads(raw)
                if isinstance(data, list):
                    ld_items.extend(data)
                elif isinstance(data, dict):
                    ld_items.append(data)
            except Exception:
                continue

        # Titre (priorité à og:title puis h1 puis <title>)
        candidates = []
        meta = soup.find("meta", attrs={"property": "og:title"})
        if meta and meta.get("content"):
            candidates.append(meta["content"])
        meta = soup.find("meta", attrs={"name": "twitter:title"})
        if meta and meta.get("content"):
            candidates.append(meta["content"])
        h1 = soup.find("h1")
        if h1:
            candidates.append(safe_get_text(h1))
        title_el = soup.select_one(".titre, .challenge-title, .titre-challenge")
        if title_el:
            candidates.append(safe_get_text(title_el))
        if soup.title and soup.title.string:
            candidates.append(soup.title.string)

        for cand in candidates:
            title = clean_title(cand)
            if title and not is_generic_title(title):
                result["titre"] = title
                break

        if not result.get("titre"):
            for entry in ld_items:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name") or entry.get("headline")
                if name:
                    title = clean_title(name)
                    if title and not is_generic_title(title):
                        result["titre"] = title
                        break

        # Score
        for node in soup.find_all(string=re.compile(r"\bPoints\b", re.IGNORECASE)):
            text = normalize_space(getattr(node, "strip", lambda: str(node))())
            container = node.parent if hasattr(node, "parent") else None
            if container is not None and hasattr(container, "get_text"):
                text = normalize_space(safe_get_text(container))
            m = re.search(r"(\d+)\s*Points", text, re.IGNORECASE)
            if m:
                result["score"] = coerce_int(m.group(1))
                break
        if "score" not in result:
            score_el = soup.select_one(".points, .score, .challenge-score, .points_challenge, span.color2")
            if score_el:
                result["score"] = coerce_int(safe_get_text(score_el))

        # Auteur & Date
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            result["auteur"] = normalize_space(meta_author["content"])

        meta_time = soup.find("meta", attrs={"property": "article:published_time"})
        if meta_time and meta_time.get("content"):
            result["date"] = normalize_space(meta_time["content"])

        author_label = soup.find(string=re.compile(r"\bAuteur\b", re.IGNORECASE))
        if author_label and (not result.get("auteur") or not result.get("date")):
            label_tag = author_label.parent if hasattr(author_label, "parent") else None
            if label_tag:
                for sib in label_tag.next_siblings:
                    if getattr(sib, "name", None) in {"h4", "h3", "dt"}:
                        break
                    if hasattr(sib, "find"):
                        if not result.get("auteur"):
                            link = sib.find("a")
                            if link:
                                result["auteur"] = normalize_space(safe_get_text(link))
                        if not result.get("date"):
                            time_tag = sib.find("time")
                            if time_tag:
                                result["date"] = normalize_space(safe_get_text(time_tag))
                    if result.get("auteur") and result.get("date"):
                        break

        if not result.get("date"):
            time_tag = soup.find("time")
            if time_tag:
                result["date"] = normalize_space(safe_get_text(time_tag))

        if not result.get("date"):
            date_guess = extract_date_from_text(soup.get_text(" ", strip=True))
            if date_guess:
                result["date"] = date_guess

        if not result.get("auteur"):
            for entry in ld_items:
                if not isinstance(entry, dict):
                    continue
                author = entry.get("author")
                if isinstance(author, dict):
                    name = author.get("name")
                    if name:
                        result["auteur"] = normalize_space(name)
                        break
                if isinstance(author, list):
                    for a in author:
                        if isinstance(a, dict) and a.get("name"):
                            result["auteur"] = normalize_space(a.get("name"))
                            break
                    if result.get("auteur"):
                        break

        if not result.get("date"):
            for entry in ld_items:
                if isinstance(entry, dict):
                    date_pub = entry.get("datePublished") or entry.get("dateCreated")
                    if date_pub:
                        result["date"] = normalize_space(date_pub)
                        break

        # Difficulté
        diff_el = soup.find(class_=re.compile(r"\bdifficulte\d+a\b", re.IGNORECASE))
        if diff_el:
            label = None
            level = None
            title_attr = diff_el.get("title") or diff_el.get("aria-label")
            if title_attr:
                label = normalize_space(title_attr.split(":")[0])
            class_str = " ".join(diff_el.get("class", []))
            m = re.search(r"difficulte(\d+)a", class_str, re.IGNORECASE)
            if m:
                level = coerce_int(m.group(1))
            result["difficulte"] = normalize_difficulty(label, level=level)
        else:
            diff_label = soup.find(string=re.compile(r"Difficul", re.IGNORECASE))
            if diff_label:
                parent = diff_label.parent if hasattr(diff_label, "parent") else None
                if parent is not None and hasattr(parent, "get_text"):
                    text = normalize_space(parent.get_text(" ", strip=True))
                else:
                    text = normalize_space(str(diff_label))
                m = re.search(r"Difficul\w*\s*[:\-]\s*([A-Za-zÀ-ÿ ]+)", text)
                if m:
                    result["difficulte"] = normalize_difficulty(m.group(1))
        if not result.get("difficulte"):
            diff_span = soup.select_one("span.rendu-v2, .rendu-v2")
            if diff_span:
                result["difficulte"] = normalize_difficulty(safe_get_text(diff_span))

        # Validations / Challengeurs
        for sel in [".validations_challenge", ".nb_validation", ".challengeurs", ".validations"]:
            el = soup.select_one(sel)
            if el:
                val = coerce_int(safe_get_text(el))
                if val is not None:
                    result["validations"] = val
                    break
        if "validations" not in result:
            for node in soup.find_all(string=re.compile(r"Challengeurs|Validations", re.IGNORECASE)):
                parent = node.parent if hasattr(node, "parent") else None
                if parent is not None and hasattr(parent, "get_text"):
                    text = normalize_space(parent.get_text(" ", strip=True))
                else:
                    text = normalize_space(str(node))
                val = coerce_int(text)
                if val is not None:
                    result["validations"] = val
                    break

        # Taux de réussite (note)
        for node in soup.find_all(string=re.compile(r"R[ée]ussite|Success|Taux", re.IGNORECASE)):
            parent = node.parent if hasattr(node, "parent") else None
            if parent is not None and hasattr(parent, "get_text"):
                text = normalize_space(parent.get_text(" ", strip=True))
            else:
                text = normalize_space(str(node))
            pct = extract_percent(text)
            if pct:
                result["note"] = pct
                break
        if "note" not in result:
            pct = extract_percent(soup.get_text(" ", strip=True))
            if pct:
                result["note"] = pct

        # Rubrique / Thème (via liens catégories)
        if not result.get("rubrique"):
            for link in soup.find_all("a", href=re.compile(r"/fr/Challenges/[^/]+/?$")):
                href = link.get("href") or ""
                if href.rstrip("/") == "/fr/Challenges":
                    continue
                text = normalize_space(safe_get_text(link))
                if text and text.lower() != "challenges":
                    result["rubrique"] = text
                    break

        return result
    except Exception as e:
        print(f"⚠️ Parsing BS4 échoué: {e}. Fallback regex actif.")
        return parse_challenge_html_regex(html)


def extract_number_from_patterns(text, patterns):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = coerce_int(m.group(1))
            if val is not None:
                return val
    return None


def parse_profile_html(html):
    """Parse le profil Root-Me en HTML (fallback si API KO)."""
    result = {}
    raw_text = normalize_space(unescape(html))
    if re.search(r"profil\\s+de\\s+user", raw_text, re.IGNORECASE):
        return result

    # Titre / Nom
    if BeautifulSoup is not None:
        try:
            soup = BeautifulSoup(html, "html.parser")
            meta = soup.find("meta", attrs={"property": "og:title"})
            if meta and meta.get("content"):
                result["nom"] = clean_title(meta["content"])
            if not result.get("nom"):
                h1 = soup.find("h1")
                if h1:
                    result["nom"] = normalize_space(safe_get_text(h1))
            if not result.get("nom") and soup.title and soup.title.string:
                result["nom"] = clean_title(soup.title.string)
            if result.get("nom") and ("plateforme" in result["nom"].lower()):
                result["nom"] = None
            # Try structured stats from profile page
            result = parse_profile_score_html(html, result)
            # Fallback texte global
            text_blob = normalize_space(soup.get_text(" ", strip=True))
        except Exception:
            text_blob = raw_text
    else:
        text_blob = raw_text

    # Score / Position / Validations depuis patterns HTML + texte global
    score_patterns = [
        r"Score[^\d]*(\d[\d\s\.]*)",
        r"(\d[\d\s\.]*)\s*Points",
    ]
    position_patterns = [
        r"(?:Position|Rang|Classement|Place)[^\d#]*(?:#\s*)?(\d[\d\s\.]*)",
    ]
    validations_patterns = [
        r"(?:Validations|Challengeurs|Challenges)[^\d]*(\d[\d\s\.]*)",
        r"Challenges?\s*(?:résolus|resolus|validés|valides)[^\d]*(\d[\d\s\.]*)",
    ]

    if not is_logged_out(text_blob):
        if result.get("score") is None:
            result["score"] = extract_number_from_patterns(text_blob, score_patterns)
        if result.get("position") is None:
            result["position"] = extract_number_from_patterns(text_blob, position_patterns)
        if result.get("challenges_resolus") is None:
            result["challenges_resolus"] = extract_number_from_patterns(text_blob, validations_patterns)

    # Nettoyage nom si vide/générique
    if result.get("nom") and is_generic_title(result["nom"]):
        result["nom"] = None

    return result


def read_response_text(response):
    """Lit la réponse HTTP en gérant IncompleteRead et l'encodage."""
    charset = response.headers.get_content_charset() or "utf-8"
    try:
        raw = response.read()
    except IncompleteRead as e:
        raw = e.partial
    return raw.decode(charset, errors="replace")


def fetch_url_text(url, headers=None, timeout=10, max_retries=3, backoff_base=2.0, debug_label=None):
    """Récupère une URL avec retry (gère 429/5xx + Retry-After)."""
    headers = headers or {}
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                html = read_response_text(response)
                if debug_label:
                    debug_dump("page", debug_label, url, html=html, status=getattr(response, "status", None))
                return html
        except urllib.error.HTTPError as e:
            last_error = e
            body = None
            try:
                body = e.read()
            except Exception:
                body = None
            if body is not None and debug_label:
                try:
                    charset = e.headers.get_content_charset() or "utf-8"
                except Exception:
                    charset = "utf-8"
                html = body.decode(charset, errors="replace")
                debug_dump("error", debug_label, url, html=html, status=e.code, error=str(e))
            elif debug_label:
                debug_dump("error", debug_label, url, html=None, status=e.code, error=str(e))
            if e.code in (429, 500, 502, 503, 504):
                retry_after = e.headers.get("Retry-After")
                if retry_after and str(retry_after).isdigit():
                    wait_time = int(retry_after)
                else:
                    wait_time = backoff_base * (2 ** attempt) + random.uniform(0.2, 0.8)
                time.sleep(wait_time)
                continue
            return None
        except (TimeoutError, socket.timeout) as e:
            last_error = e
            if debug_label:
                debug_dump("error", debug_label, url, html=None, status=None, error=str(e))
            wait_time = backoff_base * (2 ** attempt) + random.uniform(0.2, 0.8)
            time.sleep(wait_time)
            continue
        except urllib.error.URLError as e:
            last_error = e
            if debug_label:
                debug_dump("error", debug_label, url, html=None, status=None, error=str(e))
            wait_time = backoff_base * (2 ** attempt) + random.uniform(0.2, 0.8)
            time.sleep(wait_time)
            continue
    if last_error:
        print(f"⚠️ Erreur scraping: {last_error}")
    return None


def api_request(endpoint):
    """Effectue une requête vers l'API Root-Me avec retry."""
    import time

    global API_DISABLED
    if API_DISABLED:
        return None
    
    url = f"https://api.www.root-me.org{endpoint}"
    
    max_retries = 0 # TEMP: Fail fast to trigger scraping
    for attempt in range(max_retries + 1):
        try:
            # Polite delay
            time.sleep(2)  # Increased to 2s because pagination is aggressive
            
            req = urllib.request.Request(url)
            
            # Gestion des cookies: Priorité à ROOTME_COOKIES (navigateur) sinon api_key
            if ROOTME_COOKIES:
                req.add_header("Cookie", ROOTME_COOKIES)
            else:
                req.add_header("Cookie", f"api_key={ROOTME_API_KEY}")

            req.add_header("User-Agent", "Mozilla/5.0")
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print(f"⚠️ API 401 détecté. Désactivation des appels API pour ce run.")
                API_DISABLED = True
                return None
            if e.code == 429:
                print(f"⚠️ API 429 détecté. Désactivation des appels API pour ce run.")
                API_DISABLED = True
                return None
            if e.code == 429 or e.code >= 500:
                wait_time = (attempt + 1) * 5
                print(f"⚠️ Erreur API ({endpoint}): {e.code}. Retry dans {wait_time}s...")
                time.sleep(wait_time)
            elif e.code == 404:
                print(f"❌ Ressource non trouvée ({endpoint})")
                return None
            else:
                print(f"❌ Erreur API ({endpoint}): {e}")
                return None
        except (TimeoutError, socket.timeout) as e:
            print(f"❌ Erreur connexion ({endpoint}): {e}")
            time.sleep(2) # Petit retry reseau
        except urllib.error.URLError as e:
            print(f"❌ Erreur connexion ({endpoint}): {e}")
            time.sleep(2) # Petit retry reseau
            
    print(f"❌ Abandon après {max_retries} tentatives pour {endpoint}")
    sys.stdout.flush()
    return None


def scrape_profile_html():
    """Scrape le profil HTML en utilisant les cookies si disponibles."""
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    if ROOTME_COOKIES:
        headers["Cookie"] = ROOTME_COOKIES

    user = ENV.get("ROOTME_USER", "Alexandre-Froissart")
    candidates = []
    pretty_url = build_pretty_profile_url(user)
    if pretty_url:
        candidates.append(pretty_url)
        candidates.append(pretty_url.replace("?lang=fr", ""))
    if ROOTME_PROFILE_URL and ROOTME_PROFILE_URL not in candidates:
        candidates.append(ROOTME_PROFILE_URL)
    if ROOTME_UID:
        candidates.extend([
            f"https://www.root-me.org/spip.php?auteur{ROOTME_UID}",
            f"https://www.root-me.org/?page=info_auteur&id_auteur={ROOTME_UID}",
        ])
    if user and "@" not in user:
        candidates.extend([
            f"https://www.root-me.org/{user}",
            f"https://www.root-me.org/fr/{user}",
            f"https://www.root-me.org/Users/{user}",
            f"https://www.root-me.org/User/{user}",
            f"https://www.root-me.org/Membres/{user}",
        ])

    scraped = None
    profile_url = None
    score_data = fetch_profile_score_direct(headers)
    for url in candidates:
        try:
            html = fetch_url_text(url, headers=headers, timeout=10, max_retries=2, debug_label="profile")
            if not html:
                continue
            if not is_profile_html(html):
                continue
            scraped = parse_profile_html(html)
            # Si disponible, récupérer le bloc score en AJAX
            inc_score_url = find_inc_score_url(html, url)
            if inc_score_url:
                score_html = fetch_url_text(inc_score_url, headers=headers, timeout=10, max_retries=2, debug_label="profile_score")
                if score_html and not is_logged_out(score_html):
                    scraped = parse_profile_score_html(score_html, scraped or {})
            profile_url = url
            score_val = scraped.get("score") or 0
            pos_val = scraped.get("position") or 0
            chall_val = scraped.get("challenges_resolus") or 0
            if scraped.get("nom") or score_val > 0 or pos_val > 0 or chall_val > 0:
                break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            print(f"⚠️ Fallback profil HTML échoué sur {url}: {e}")
        except Exception as e:
            print(f"⚠️ Fallback profil HTML échoué sur {url}: {e}")

    if score_data:
        scraped = scraped or {}
        # Priorité aux stats AJAX si disponibles
        scraped.update({k: v for k, v in score_data.items() if v})
    elif DEBUG_HTML:
        print("⚠️ Profil score AJAX indisponible (cookies invalides ?).")

    score_val = (scraped.get("score") or 0) if scraped else 0
    pos_val = (scraped.get("position") or 0) if scraped else 0
    chall_val = (scraped.get("challenges_resolus") or 0) if scraped else 0
    if scraped and (scraped.get("nom") or score_val > 0 or pos_val > 0 or chall_val > 0):
        preferred_url = None
        if ROOTME_PROFILE_URL and not is_basic_profile_url(ROOTME_PROFILE_URL):
            preferred_url = ROOTME_PROFILE_URL
        else:
            preferred_url = build_pretty_profile_url(scraped.get("nom") or user)
        if not preferred_url:
            preferred_url = profile_url or ROOTME_PROFILE_URL
        profile = {
            "nom": scraped.get("nom") or user,
            "score": score_val,
            "position": pos_val,
            "challenges_resolus": chall_val,
            "profil_url": preferred_url,
            "derniere_mise_a_jour": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Si le rang est 0 ou semble invalide, essayer le classement public
        if not profile["position"] or profile["position"] == 0 or profile["position"] > 500000:
            username = profile.get("nom") or user
            print(f"🔍 Récupération du rang depuis le classement public pour {username}...")
            real_rank = fetch_rank_from_leaderboard(username)
            if real_rank:
                profile["position"] = real_rank
        
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        print(f"✅ Profil (HTML): {profile['score']} pts, #{profile['position']}, {profile['challenges_resolus']} challenges")
        return profile
    return None


def fetch_profile():
    """Récupère le profil utilisateur."""
    print("🔄 Récupération du profil...")
    if ROOTME_COOKIES:
        profile = scrape_profile_html()
        if profile:
            return profile

    data = api_request(f"/auteurs/{ROOTME_UID}")
    
    if not data:
        profile = scrape_profile_html()
        if profile:
            return profile
        # API et scraping ont échoué - créer un profil de base avec le rang du classement
        user = ENV.get("ROOTME_USER", "Alexandre-Froissart")
        print(f"🔍 API/scraping échoué, tentative de récupération du rang depuis le classement public pour {user}...")
        real_rank = fetch_rank_from_leaderboard(user)
        if real_rank:
            # Créer un profil minimal avec le rang récupéré
            profile = {
                "nom": user.replace("-", " "),
                "score": 0,  # Sera mis à jour lors d'une prochaine exécution réussie
                "position": real_rank,
                "challenges_resolus": 0,
                "profil_url": f"https://www.root-me.org/{user}",
                "derniere_mise_a_jour": datetime.now().strftime("%Y-%m-%d")
            }
            # Essayer de récupérer les anciennes données pour conserver score/challenges
            if PROFILE_FILE.exists():
                try:
                    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                        old_data = json.load(f)
                    if old_data.get("score"):
                        profile["score"] = old_data["score"]
                    if old_data.get("challenges_resolus"):
                        profile["challenges_resolus"] = old_data["challenges_resolus"]
                    if old_data.get("nom"):
                        profile["nom"] = old_data["nom"]
                except Exception:
                    pass
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            print(f"✅ Profil (classement public): #{profile['position']}")
            return profile
        
        # Fallback final: conserver les données existantes si aucune récupération n'a réussi
        if PROFILE_FILE.exists():
            try:
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    old_profile = json.load(f)
                print(f"⚠️ Utilisation des données existantes: #{old_profile.get('position', 'N/A')}")
                return old_profile
            except Exception:
                pass
        
        return None
    
    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    user = ENV.get("ROOTME_USER", "Alexandre-Froissart")
    preferred_url = None
    if ROOTME_PROFILE_URL and not is_basic_profile_url(ROOTME_PROFILE_URL):
        preferred_url = ROOTME_PROFILE_URL
    else:
        preferred_url = build_pretty_profile_url(data.get("nom") or user)
    if not preferred_url:
        preferred_url = ROOTME_PROFILE_URL

    validations_raw = data.get("validations", [])
    if isinstance(validations_raw, list):
        challenges_resolus = len(validations_raw)
    else:
        challenges_resolus = coerce_int(validations_raw) or 0

    profile = {
        "nom": data.get("nom", "Alexandre-Froissart"),
        "score": coerce_int(data.get("score")) or 0,
        "position": coerce_int(data.get("position")) or 0,
        "challenges_resolus": challenges_resolus,
        "profil_url": preferred_url,
        "derniere_mise_a_jour": datetime.now().strftime("%Y-%m-%d")
    }

    if ROOTME_COOKIES:
        headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity", "Cookie": ROOTME_COOKIES}
        score_data = fetch_profile_score_direct(headers)
        if score_data:
            for key in ("score", "position", "challenges_resolus"):
                if score_data.get(key):
                    profile[key] = score_data[key]
    
    # Si le rang est 0 ou semble invalide, essayer de le récupérer depuis le classement public
    if not profile.get("position") or profile["position"] == 0 or profile["position"] > 500000:
        username = profile.get("nom") or ENV.get("ROOTME_USER", "Alexandre-Froissart")
        print(f"🔍 Récupération du rang depuis le classement public pour {username}...")
        real_rank = fetch_rank_from_leaderboard(username)
        if real_rank:
            profile["position"] = real_rank
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Profil: {profile['score']} pts, #{profile['position']}, {profile['challenges_resolus']} challenges")
    return profile


def fetch_challenge(challenge_id, override_url=None, debug_label=None):
    """Récupère les données d'un challenge."""
    data = api_request(f"/challenges/{challenge_id}")
    
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
        
    api_failed = False
    if not data:
        # Si API fail, on continue si on a une URL pour scraper
        if override_url:
            print(f"⚠️ Pas de données API pour {challenge_id}, fallback scraping sur {override_url}")
            api_failed = True
            data = {
               "titre": "Inconnu",
               "rubrique": "Autre", 
               "url_challenge": override_url,
               "validations": [],
               "score": "?",
               "difficulte": "Inconnu",
               "auteurs": {},
               "date_publication": ""
            }
        else:
            print(f"⚠️ Pas de données pour le challenge {challenge_id}")
            return None
        
    # print(f"DEBUG CHALLENGE {challenge_id} KEYS:", data.keys()) # Debug clés
    
    # Extraire le premier auteur
    auteurs = data.get("auteurs", {})
    auteur_nom = "Inconnu"
    if auteurs and isinstance(auteurs, dict) and '0' in auteurs:
        auteur_nom = auteurs['0'].get('nom', 'Inconnu')
    
    # Date
    date_pub = data.get("date_publication", "")
    if isinstance(date_pub, int):
        date_pub = str(date_pub)
    if isinstance(date_pub, str) and date_pub.strip().lower() in INVALID_DATES:
        date_pub = ""

    # Normaliser la difficulté si l'API renvoie un niveau numérique
    data["difficulte"] = normalize_difficulty(data.get("difficulte"))
    
    # Validations (Nombre)
    # Par défaut, on force le scraping HTML (plus stable, évite les 429)
    validations_count = 0
    if not FORCE_HTML_VALIDATIONS:
        # Pagination API (si activée)
        offset = 0
        validations_initial = data.get("validations", [])
        if isinstance(validations_initial, dict):
            current_count = len(validations_initial)
            validations_count += current_count
        elif isinstance(validations_initial, list):
            current_count = len(validations_initial)
            validations_count += current_count
        else:
            current_count = 0
        
        # Si on a eu 100 résultats, il faut aller chercher la suite
        if current_count >= 100:
            print(f"     📚 Pagination des validations (100+)...")
            while True:
                offset += 100
                try:
                    page_data = api_request(f"/challenges/{challenge_id}?debut_validations={offset}")
                    if not page_data: break
                    # Normaliser la réponse API (parfois liste)
                    if isinstance(page_data, list):
                        if page_data and isinstance(page_data[0], dict) and "validations" in page_data[0]:
                            page_data = page_data[0]
                        else:
                            c_page = len(page_data)
                            validations_count += c_page
                            if c_page < 100:
                                break
                            continue
                    if not isinstance(page_data, dict):
                        break

                    v_page = page_data.get("validations", [])
                    c_page = 0
                    if isinstance(v_page, dict):
                        c_page = len(v_page)
                    elif isinstance(v_page, list):
                        c_page = len(v_page)
                    
                    validations_count += c_page
                    
                    if c_page < 100:
                        break
                    if offset > 5000: 
                        print("     ⚠️ Limite de pagination atteinte (5000+)")
                        break
                except Exception as e:
                    print(f"     ⚠️ Erreur pagination: {e}")
                    break

    nb_validations = validations_count if (not api_failed and not FORCE_HTML_VALIDATIONS) else 0

    # Rubrique (Si dict, prendre le titre, sinon string)
    rubrique_raw = data.get("rubrique", "Réseau")
    rubrique = rubrique_raw
    if isinstance(rubrique_raw, dict):
        rubrique = rubrique_raw.get("titre", "Réseau")

    # Scraping complémentaire
    url_challenge = data.get("url_challenge", "")
    if url_challenge and not url_challenge.startswith("http"):
        url_challenge = f"https://www.root-me.org/{url_challenge}"
    elif "api.www." in url_challenge:
        url_challenge = url_challenge.replace("api.www.", "www.")
    
    real_validations = nb_validations
    real_votes = "0%"

    if url_challenge:
        try:
            # Polite delay for scrapping
            time.sleep(random.uniform(*SCRAPE_DELAY_RANGE))
            
            headers = {
                'User-Agent': 'Mozilla/5.0', 
                'Accept-Encoding': 'identity',
            }
            if ROOTME_COOKIES:
                headers['Cookie'] = ROOTME_COOKIES
            else:
                headers['Cookie'] = f"api_key={ROOTME_API_KEY}"
                
            html = fetch_url_text(url_challenge, headers=headers, timeout=10, max_retries=3, debug_label=debug_label)
            if not html:
                raise urllib.error.HTTPError(url_challenge, 429, "Too Many Requests", hdrs=None, fp=None)

            scraped = parse_challenge_html(html) or {}

            # Titre
            if scraped.get("titre"):
                if is_generic_title(data.get("titre", "")) or data.get("titre", "").lower() in {"inconnu", "titre inconnu"}:
                    data["titre"] = scraped["titre"]
                else:
                    data["titre"] = scraped["titre"]

            # Score
            if scraped.get("score") is not None:
                data["score"] = scraped["score"]

            # Auteur & Date
            if scraped.get("auteur"):
                auteur_nom = scraped["auteur"]
                if scraped.get("date"):
                    if str(scraped["date"]).strip().lower() not in INVALID_DATES:
                        date_pub = scraped["date"]

            # Difficulté
            if scraped.get("difficulte"):
                data["difficulte"] = scraped["difficulte"]

            # Rubrique
            if scraped.get("rubrique"):
                rubrique = scraped["rubrique"]

                # Validations (HTML prioritaire pour la stabilité)
                if scraped.get("validations") is not None:
                    real_validations = scraped["validations"]

                # Taux de réussite
                if scraped.get("note"):
                    real_votes = scraped["note"]
                
        except urllib.error.HTTPError as e:
            print(f"⚠️ Erreur scraping (HTTP {e.code}) pour {challenge_id}")
        except Exception as e:
            print(f"⚠️ Erreur scraping: {e}")

    return {
        "id": challenge_id,
        "titre": data.get("titre", "Titre Inconnu"),
        "rubrique": rubrique,
        "auteur": auteur_nom,
        "date": date_pub if str(date_pub).strip().lower() not in INVALID_DATES else "",
        "score": data.get("score", 0), 
        "difficulte": data.get("difficulte", 1), 
        "validations": real_validations,
        "note": real_votes, # Contient le pourcentage ex "30%"
    }


def fetch_all_challenges_with_stats():
    """Récupère les données les challenges présents sur le disque et retourne les stats."""
    print("🔄 Détection dynamique des challenges via frontmatter...")
    
    discovered_challenges = {}
    existing_data = {}
    if CHALLENGES_FILE.exists():
        try:
            with open(CHALLENGES_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = {}
    
    if CONTENT_DIR.exists():
        for item in CONTENT_DIR.iterdir():
            if item.is_dir():
                md_file = item / "index.md"
                if md_file.exists():
                    try:
                        with open(md_file, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Recherche de rootme_id dans le frontmatter
                            m = re.search(r'^rootme_id:\s*"?(\w+)"?', content, re.MULTILINE)
                            if m:
                                cid = m.group(1)
                                categories = parse_frontmatter_categories(content)
                                category_segment = None
                                for cat in categories:
                                    if cat.strip().lower() == "root-me":
                                        continue
                                    category_segment = category_to_segment(cat)
                                    if category_segment:
                                        break
                                discovered_challenges[cid] = {
                                    "slug": item.name,
                                    "id": cid,
                                    "url": f"https://www.root-me.org/fr/Challenges/TODO/{item.name}" # Sera mis à jour par l'API
                                }
                                # Essayer de choper l'URL si présente ou reconstruire
                                url_match = re.search(r'{{< rootme-challenge .* url="([^"]+)"', content)
                                if url_match:
                                    discovered_challenges[cid]["url"] = url_match.group(1)
                                elif category_segment:
                                    discovered_challenges[cid]["url"] = f"https://www.root-me.org/fr/Challenges/{category_segment}/{item.name}"
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la lecture de {md_file}: {e}")

    active_count = len(discovered_challenges)
    print(f"📂 Challenges trouvés dans le contenu : {list(discovered_challenges.keys())} ({active_count})")
    
    challenges_data = {}
    stats = [] # {id, name, status, info}
    
    for challenge_id, info in discovered_challenges.items():
        slug = info.get("slug")
            
        # Gestion des IDs "PENDING"
        if "PENDING" in str(challenge_id):
            print(f"   - Tentative de résolution pour {challenge_id} ({info['slug']})...")
            # On utilise la logique de recherche via API (copiée/adaptée de add-challenge.py)
            # Mais ici on va simplifier : recherche par titre exact ou slug
            found = False
            slug = info['slug']
            
            # Stratégie multi-candidats
            candidates = [
                slug.replace("-", " - "),       # "Hash - DCC"
                slug.replace("-", " "),         # "HTTP Open redirect"
                slug.replace("-", " - ", 1).replace("-", " "), # "HTTP - Open redirect"
                " ".join(slug.split("-")[-2:]), # "Open redirect"
                slug.split("-")[-1]             # "redirect"
            ]
            search_terms = []
            for c in candidates:
                if c and c not in search_terms and len(c) >= 3:
                     search_terms.append(c) # Dedoublonnage
            
            for search_term in search_terms:
                if found: break
                
                # Recherche API
                try:
                    # Petite pause
                    time.sleep(2)
                    url = f"https://api.www.root-me.org/challenges?titre={urllib.parse.quote(search_term)}"
                    headers = {'User-Agent': 'Mozilla/5.0', "Cookie": f"api_key={ROOTME_API_KEY}"}
                    req = urllib.request.Request(url, headers=headers)
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode("utf-8"))
                        
                        if data:
                             # On cherche le bon
                             target_norm = slug.replace("-", "").lower()
                             challenges_list = []
                             if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        if 'titre' in item: challenges_list.append(item)
                                        else: challenges_list.extend(item.values())
                             elif isinstance(data, dict):
                                if 'titre' in data: challenges_list.append(data)
                                else: challenges_list.extend(data.values())

                             for val in challenges_list:
                                if not isinstance(val, dict): continue
                                title = val.get('titre', '')
                                title_norm = re.sub(r'[^a-zA-Z0-9]', '', title).lower()
                                target_norm = re.sub(r'[^a-zA-Z0-9]', '', slug).lower()
                                
                                if target_norm in title_norm or title_norm in target_norm:
                                    # TROUVÉ !
                                    found = True
                                    real_id = str(val['id_challenge'])
                                    print(f"     🎉 ID trouvé : {real_id} ! Mise à jour du fichier...")
                                    md_path = CONTENT_DIR / slug / "index.md"
                                    if md_path.exists():
                                        print(f"     📝 Mise à jour de {md_path.name} avec ID {real_id}...")
                                        with open(md_path, 'r', encoding='utf-8') as f:
                                            md_content = f.read()
                                        
                                        # Remplacer rootme_id: PENDING_... par rootme_id: real_id
                                        md_content = re.sub(r'^rootme_id:\s*"?PENDING_[^"\n]+"?', f'rootme_id: {real_id}', md_content, flags=re.MULTILINE)
                                        
                                        with open(md_path, 'w', encoding='utf-8') as f:
                                            f.write(md_content)
                                    
                                    # On met à jour l'info locale pour que la suite du script fonctionne
                                    challenge_id = real_id
                                    info['id'] = int(real_id)
                                    stats.append({"id": challenge_id, "name": slug, "status": "RESOLVED", "info": f"ID {real_id} found"})
                                    break
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                         print(f"     ⚠️ Pas de résultat pour '{search_term}' (404)")
                    else:
                         print(f"     ⚠️ Erreur résolution PENDING: {e}")
                except Exception as e:
                    print(f"     ⚠️ Erreur résolution PENDING: {e}")
            
            if not found:
                print(f"     ⚠️ Impossible de résoudre {challenge_id} pour l'instant.")
                stats.append({"id": challenge_id, "name": slug, "status": "WARNING", "info": "Resolution failed (404/API)"})
                continue

        if "url" in info:
             url_override = info["url"]
        
        print(f"   - Challenge {challenge_id} ({info['slug']})...")
        debug_label = info.get("slug") or str(challenge_id)
        data = fetch_challenge(challenge_id, override_url=info.get("url"), debug_label=debug_label)
        
        if data:
            # Fusion avec cache existant si nécessaire
            existing = existing_data.get(info["slug"])
            if existing:
                data = merge_challenge_data(data, existing)
            # Préserver l'URL définie dans CHALLENGES si elle est valide (pas de TODO)
            if "url" in info and "TODO" not in info["url"]:
                data["url"] = info["url"]
            
            # S'assurer que le challenge a une URL, sinon fallback sur celle de l'API (qui est partielle "fr/...")
            if not data.get("url") or not data["url"].startswith("http"):
                  partial = data.get("url_challenge", "") or data.get("url", "")
                  if partial:
                       data["url"] = f"https://www.root-me.org/{partial}"
            
            challenges_data[info["slug"]] = data
            print(f"     ✅ {data['titre']}: {data['score']} pts, {data.get('validations', '?')} validations")
            stats.append({"id": challenge_id, "name": data['titre'], "status": "OK", "info": f"{data['score']} pts"})
            
            # SAUVEGARDE INCREMENTALE (Pour ne pas tout perdre si crash/429)
            try:
                 DATA_DIR.mkdir(parents=True, exist_ok=True)
                 with open(CHALLENGES_FILE, "w", encoding="utf-8") as f:
                     json.dump(challenges_data, f, indent=2, ensure_ascii=False)
                 print(f"     💾 Sauvegardé ({len(challenges_data)} total)")
            except Exception as e:
                 print(f"     ⚠️ Echec sauvegarde incrémentale : {e}")

        else:
             existing = existing_data.get(info["slug"])
             if existing:
                 challenges_data[info["slug"]] = existing
                 stats.append({"id": challenge_id, "name": existing.get("titre", info['slug']), "status": "CACHED", "info": "Cache used"})
             else:
                 stats.append({"id": challenge_id, "name": info['slug'], "status": "ERROR", "info": "Fetch failed"})
    
    # Sauvegarde finale deja faite incrémentalement, mais on repasse
    print(f"✅ {len(challenges_data)} challenge(s) sauvegardé(s) au total")
    return challenges_data, stats

def fetch_all_challenges():
    d, _ = fetch_all_challenges_with_stats()
    return d


def generate_summary(profile, challenges_data, stats_challenges):
    """Génère un résumé complet pour GitHub Actions et stdout."""
    # Stats gloabales
    total = len(stats_challenges)
    success = len([c for c in stats_challenges if c['status'] == 'OK'])
    failed = len([c for c in stats_challenges if c['status'] == 'ERROR'])
    
    # 1. Output pour stdout (Console lisible)
    print("\n" + "="*50)
    print("📊 RAPPORT DE MISSION ROOT-ME")
    print("="*50)
    
    if profile:
        print(f"👤 PROFIL : {profile['nom']}")
        print(f"   Score : {profile['score']} | Rang : #{profile['position']}")
    else:
        print("👤 PROFIL : ❌ Récupération échouée")
        
    print(f"\n🏆 CHALLENGES : {success}/{total} mis à jour")
    
    for c in stats_challenges:
        icon = "✅" if c['status'] == 'OK' else "❌"
        # Alignement pour lisibilité
        print(f"   {icon} [{c['id']}] {c['name']:<30} : {c['info']}")

    print("="*50 + "\n")
    
    # 2. Output pour GitHub Actions (Markdown)
    github_step_summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if github_step_summary:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md_lines = []
        md_lines.append(f"# 📊 Rapport de Mise à Jour Root-Me")
        md_lines.append(f"**📅 Date** : {date_str} (UTC)")
        
        # Section Profil
        md_lines.append("## 👤 Profil")
        if profile:
             md_lines.append(f"| Indicateur | Valeur |")
             md_lines.append(f"|---|---|")
             md_lines.append(f"| **Score** | `{profile['score']}` |")
             md_lines.append(f"| **Rang** | `#{profile['position']}` |")
             md_lines.append(f"| **Validations** | `{profile['challenges_resolus']}` |")
        else:
             md_lines.append("⚠️ *Impossible de récupérer le profil*")

        # Section Challenges
        md_lines.append(f"## 🏆 Challenges ({success}/{total})")
        if failed == 0:
            md_lines.append("✅ **Tous les challenges sont à jour !**")
        else:
            md_lines.append(f"⚠️ **{failed} erreurs détectées**")
            
        md_lines.append("| ID | Challenge | Statut | Info |")
        md_lines.append("|---|---|---|---|")
        
        for c in stats_challenges:
            icon = "✅" if c['status'] == 'OK' else "❌"
            status_clean = "OK" if c['status'] == 'OK' else f"**{c['status']}**"
            name_clean = c['name'].replace("|", "-") # Eviter de casser le markdown table
            info_clean = str(c['info']).replace("|", "-")
            md_lines.append(f"| {c['id']} | {name_clean} | {icon} {status_clean} | {info_clean} |")
            
        try:
            with open(github_step_summary, 'a', encoding='utf-8') as f:
                f.write("\n".join(md_lines) + "\n")
            print("✅ Résumé GitHub généré.")
        except Exception as e:
            print(f"⚠️ Impossible d'écrire le résumé GitHub : {e}")

def main():
    print("=" * 50)
    print("🎯 Root-Me Data Fetcher (v2.0 Enhanced)")
    print("=" * 50)
    
    # Mode Persistant (CI/GitHub Actions)
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    max_duration_hours = 3
    loop_interval_minutes = 30
    
    start_time = time.time()
    
    print(f"\n🕒 Démarrage cycle unique (CI={is_ci})...")
    sys.stdout.flush()
    
    profile = fetch_profile()
    challenges_data, run_stats = fetch_all_challenges_with_stats() 
    generate_summary(profile, challenges_data, run_stats)

    print("=" * 50)
    print("✅ Mise à jour terminée!")


if __name__ == "__main__":
    main()
