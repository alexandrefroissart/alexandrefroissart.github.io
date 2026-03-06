#!/usr/bin/env python3
"""
Boite a outils simple pour gerer le site sans passer par l'IA.

Commandes principales:
  ./scripts/site.sh news
  ./scripts/site.sh rootme <url>
  ./scripts/site.sh sadservers <url>
  ./scripts/site.sh translate [fichier]
  ./scripts/site.sh build
  ./scripts/site.sh serve
  ./scripts/site.sh status
  ./scripts/site.sh publish "Mon message"
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT_DIR / "content"
SCRIPTS_DIR = ROOT_DIR / "scripts"
PARIS_TZ = ZoneInfo("Europe/Paris")


ROOTME_PLACEHOLDER_FR = "Writeup à rédiger..."
ROOTME_PLACEHOLDER_EN = "Writeup to write..."
SADSERVERS_PLACEHOLDER_FR = "<!-- Ajoute ici le contexte du challenge -->"
SADSERVERS_PLACEHOLDER_EN = "<!-- Add challenge context here -->"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        text=True,
        check=check,
    )


def prompt(label: str, default: str | None = None, required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    if not sys.stdin.isatty():
        if default is not None:
            return default
        if required:
            raise SystemExit(f"Champ requis manquant: {label}")
        return ""
    while True:
        value = input(f"{label}{suffix} : ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""


def prompt_bool(label: str, default: bool = True) -> bool:
    hint = "O/n" if default else "o/N"
    value = input(f"{label} [{hint}] : ").strip().lower()
    if not value:
        return default
    return value in {"o", "oui", "y", "yes"}


def parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def yaml_array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def now_frontmatter() -> str:
    return datetime.now(PARIS_TZ).replace(second=0, microsecond=0).isoformat()


def split_frontmatter(content: str) -> tuple[str, str]:
    if not content.startswith("---"):
        return "", content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return "", content
    return parts[1], parts[2].lstrip("\n")


def replace_body(path: Path, body: str) -> None:
    current = path.read_text(encoding="utf-8")
    frontmatter, _ = split_frontmatter(current)
    if frontmatter:
        new_content = f"---\n{frontmatter}---\n\n{body.rstrip()}\n"
    else:
        new_content = body.rstrip() + "\n"
    path.write_text(new_content, encoding="utf-8")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def news_body_template() -> str:
    return dedent(
        """\
        ## En bref

        - ...
        - ...
        - ...

        ## Ce qui change

        <!-- Explique ici l'information principale, sans faire trop long. -->

        ## Mon avis

        <!-- Mets ici ton retour personnel, ton ressenti, et ce que tu retiens sur le terrain. -->

        ## Sources

        - ...
        - ...
        """
    )


def rootme_body_template_fr(slug: str) -> str:
    return dedent(
        f"""\
        {{{{< rootme-challenge slug="{slug}" >}}}}

        <!-- Résume ici en 2 ou 3 phrases le but du challenge et ce qu'il t'a appris. -->

        ## Environnement

        - **Machine** : VM Debian (XFCE) sur VMware Fusion
        - **Utilisateur** : `alex`
        - **Outils** : ...

        ## Démarche

        ### 1. Première étape

        ```bash
        # commande
        ```

        <!-- Explique ici ce que tu observes et pourquoi cette étape est utile. -->

        ### 2. Vérification ou exploitation

        ```bash
        # commande
        ```

        <!-- Explique ici le résultat utile, sans divulguer une réponse confidentielle du challenge. -->

        ## Ce que je retiens

        - ...
        - ...
        - ...

        ## Résultat

        ✅ ...
        ✅ **Challenge validé sur Root-Me.**

        ## Compétences mobilisées

        - ...
        - ...
        """
    )


def rootme_body_template_en(slug: str) -> str:
    return dedent(
        f"""\
        {{{{< rootme-challenge slug="{slug}" >}}}}

        <!-- Summarize here in 2 or 3 sentences what the challenge was about and what it taught you. -->

        ## Environment

        - **Machine**: Debian VM (XFCE) on VMware Fusion
        - **User**: `alex`
        - **Tools**: ...

        ## Approach

        ### 1. First step

        ```bash
        # command
        ```

        <!-- Explain here what you observe and why this step matters. -->

        ### 2. Verification or exploitation

        ```bash
        # command
        ```

        <!-- Explain here the useful result, without disclosing a confidential challenge answer. -->

        ## What I remember

        - ...
        - ...
        - ...

        ## Result

        ✅ ...
        ✅ **Challenge validated on Root-Me.**

        ## Skills mobilized

        - ...
        - ...
        """
    )


def sadservers_body_template_fr(slug: str) -> str:
    return dedent(
        f"""\
        {{{{< sadservers-scenario slug="{slug}" >}}}}

        <!-- Résume ici le problème du scénario et ce que tu as dû corriger. -->

        ## Environnement

        - **Machine** : VM SadServers
        - **Utilisateur** : `admin` (avec sudo)
        - **Service / fichier cible** : ...

        ## Démarche

        ### 1. Diagnostic

        ```bash
        # commande
        ```

        <!-- Explique ici ce que la commande montre. -->

        ### 2. Correction

        ```bash
        # commande
        ```

        <!-- Explique ici ce que tu corriges et pourquoi. -->

        ### 3. Vérification

        ```bash
        # commande
        ```

        ## Ce que je retiens

        - ...
        - ...
        - ...

        ## Résultat

        ✅ ...
        ✅ **Challenge validé sur SadServers.**

        ## Compétences mobilisées

        - ...
        - ...
        """
    )


def sadservers_body_template_en(slug: str) -> str:
    return dedent(
        f"""\
        {{{{< sadservers-scenario slug="{slug}" >}}}}

        <!-- Summarize here the scenario issue and what you had to fix. -->

        ## Environment

        - **Machine**: SadServers VM
        - **User**: `admin` (with sudo)
        - **Target service / file**: ...

        ## Approach

        ### 1. Diagnosis

        ```bash
        # command
        ```

        <!-- Explain here what the command shows. -->

        ### 2. Fix

        ```bash
        # command
        ```

        <!-- Explain here what you fix and why. -->

        ### 3. Verification

        ```bash
        # command
        ```

        ## What I remember

        - ...
        - ...
        - ...

        ## Result

        ✅ ...
        ✅ **Challenge validated on SadServers.**

        ## Skills mobilized

        - ...
        - ...
        """
    )


def create_news(args: argparse.Namespace) -> None:
    title = args.title or prompt("Titre de l'article", required=True)
    slug = args.slug or prompt("Slug", default=slugify(title))
    description = args.description or prompt("Description courte", required=True)
    image = args.image or prompt("Chemin de l'image", default="/img/banners/waveform-traffic.png")
    categories_raw = args.categories or prompt("Catégories (séparées par des virgules)", default="News IA")
    tags_raw = args.tags or prompt("Mots-clés (séparés par des virgules)", default="")

    categories = parse_csv(categories_raw)
    tags = parse_csv(tags_raw)
    path = CONTENT_DIR / "news" / slug / "index.md"

    if path.exists() and not args.force:
        raise SystemExit(f"Le fichier existe déjà: {path}")

    frontmatter = dedent(
        f"""\
        ---
        title: {json.dumps(title, ensure_ascii=False)}
        slug: {json.dumps(slug, ensure_ascii=False)}
        date: {now_frontmatter()}
        image: {json.dumps(image, ensure_ascii=False)}
        draft: false
        categories: {yaml_array(categories)}
        tags: {yaml_array(tags)}
        description: {json.dumps(description, ensure_ascii=False)}
        ---
        """
    )
    content = frontmatter + "\n" + news_body_template()

    if args.dry_run:
        print("\n--- APERCU ---\n")
        print(content)
        print(f"\nChemin cible: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"✅ Article créé: {path}")

    if args.translate_now or prompt_bool("Créer aussi la version anglaise maintenant ?", default=False):
        translate_file(path, force=False)


def extract_rootme_slug(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def extract_sadservers_slug(url: str) -> str:
    match = re.search(r"/scenario/([^/]+)/?$", url)
    if not match:
        raise SystemExit("Impossible de trouver le slug SadServers dans l'URL.")
    return match.group(1)


def upgrade_generated_rootme(slug: str) -> None:
    fr_path = CONTENT_DIR / "root-me-challenges" / slug / "index.md"
    en_path = CONTENT_DIR / "root-me-challenges" / slug / "index.en.md"

    if fr_path.exists():
        fr_text = fr_path.read_text(encoding="utf-8")
        if ROOTME_PLACEHOLDER_FR in fr_text:
            replace_body(fr_path, rootme_body_template_fr(slug))
            print(f"✅ Modèle FR Root-Me modernisé: {fr_path}")

    if en_path.exists():
        en_text = en_path.read_text(encoding="utf-8")
        if ROOTME_PLACEHOLDER_EN in en_text:
            replace_body(en_path, rootme_body_template_en(slug))
            print(f"✅ Modèle EN Root-Me modernisé: {en_path}")


def upgrade_generated_sadservers(slug: str) -> None:
    fr_path = CONTENT_DIR / "sadservers" / slug / "index.md"
    en_path = CONTENT_DIR / "sadservers" / slug / "index.en.md"

    if fr_path.exists():
        fr_text = fr_path.read_text(encoding="utf-8")
        if SADSERVERS_PLACEHOLDER_FR in fr_text:
            replace_body(fr_path, sadservers_body_template_fr(slug))
            print(f"✅ Modèle FR SadServers modernisé: {fr_path}")

    if en_path.exists():
        en_text = en_path.read_text(encoding="utf-8")
        if SADSERVERS_PLACEHOLDER_EN in en_text:
            replace_body(en_path, sadservers_body_template_en(slug))
            print(f"✅ Modèle EN SadServers modernisé: {en_path}")


def add_rootme(args: argparse.Namespace) -> None:
    url = args.url or prompt("URL du challenge Root-Me", required=True)
    slug = extract_rootme_slug(url)
    cmd = ["python3", str(SCRIPTS_DIR / "add-challenge.py"), url]
    if args.manual_id:
        cmd.append(args.manual_id)
    run(cmd)
    upgrade_generated_rootme(slug)
    print(f"📝 Fichier principal: {CONTENT_DIR / 'root-me-challenges' / slug / 'index.md'}")


def add_sadservers(args: argparse.Namespace) -> None:
    url = args.url or prompt("URL du scenario SadServers", required=True)
    slug = extract_sadservers_slug(url)
    run(["python3", str(SCRIPTS_DIR / "add-challenge.py"), url])
    upgrade_generated_sadservers(slug)
    print(f"📝 Fichier principal: {CONTENT_DIR / 'sadservers' / slug / 'index.md'}")


def translate_file(path: Path, force: bool = False) -> None:
    cmd = [str(SCRIPTS_DIR / "translate.sh"), "--file", str(path)]
    if force:
        cmd.append("--force")
    run(cmd)


def translate_command(args: argparse.Namespace) -> None:
    if args.path:
        translate_file(Path(args.path), force=args.force)
        return

    cmd = [str(SCRIPTS_DIR / "translate.sh")]
    if args.force:
        cmd.append("--force")
    run(cmd)


def build_command(_: argparse.Namespace) -> None:
    run(["hugo", "--minify", "--config", "hugo.yaml"])


def serve_command(args: argparse.Namespace) -> None:
    port = str(args.port)
    run(
        [
            "hugo",
            "server",
            "--bind",
            "127.0.0.1",
            "--port",
            port,
            "--disableFastRender",
        ]
    )


def git_output(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=ROOT_DIR, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def status_command(_: argparse.Namespace) -> None:
    fr_files = []
    missing_en = []
    drafts = []

    for md_file in CONTENT_DIR.rglob("*.md"):
        if ".en." in md_file.name or md_file.name == "_index.md":
            continue
        fr_files.append(md_file)
        content = md_file.read_text(encoding="utf-8")
        if "draft: true" in content:
            drafts.append(md_file)
        en_file = md_file.parent / "index.en.md" if md_file.name == "index.md" else md_file.with_name(md_file.stem + ".en.md")
        if not en_file.exists():
            missing_en.append(md_file)

    print(f"Pages FR: {len(fr_files)}")
    print(f"Traductions EN manquantes: {len(missing_en)}")
    print(f"Brouillons: {len(drafts)}")

    if missing_en:
        print("\nSans version EN :")
        for path in missing_en[:10]:
            print(f"  - {path.relative_to(ROOT_DIR)}")

    if drafts:
        print("\nBrouillons :")
        for path in drafts[:10]:
            print(f"  - {path.relative_to(ROOT_DIR)}")


def publish_command(args: argparse.Namespace) -> None:
    message = args.message or prompt("Message de commit", default="Update site")
    if not git_output(["git", "status", "--porcelain"]):
        print("Aucun changement à publier.")
        return

    build_command(args)
    run(["git", "add", "."])
    run(["git", "commit", "-m", message])
    run(["git", "pull", "--rebase", "origin", "main"])
    run(["git", "push", "origin", "main"])


def menu() -> None:
    print(
        dedent(
            """\
            Gestion du site
            1. Nouvelle news
            2. Ajouter un challenge Root-Me
            3. Ajouter un scenario SadServers
            4. Traduire une page
            5. Traduire tout
            6. Build
            7. Preview local
            8. Etat du contenu
            9. Publier sur GitHub
            """
        )
    )
    choice = input("Choix : ").strip()
    if choice == "1":
        create_news(argparse.Namespace(title=None, slug=None, description=None, image=None, categories=None, tags=None, translate_now=False, dry_run=False, force=False))
    elif choice == "2":
        add_rootme(argparse.Namespace(url=None, manual_id=None))
    elif choice == "3":
        add_sadservers(argparse.Namespace(url=None))
    elif choice == "4":
        path = prompt("Chemin du fichier FR à traduire", required=True)
        translate_command(argparse.Namespace(path=path, force=False))
    elif choice == "5":
        translate_command(argparse.Namespace(path=None, force=False))
    elif choice == "6":
        build_command(argparse.Namespace())
    elif choice == "7":
        serve_command(argparse.Namespace(port=1313))
    elif choice == "8":
        status_command(argparse.Namespace())
    elif choice == "9":
        publish_command(argparse.Namespace(message=None))
    else:
        raise SystemExit("Choix invalide.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Outil simple pour gérer le site")
    sub = parser.add_subparsers(dest="command")

    news = sub.add_parser("news", help="Créer une nouvelle news")
    news.add_argument("--title")
    news.add_argument("--slug")
    news.add_argument("--description")
    news.add_argument("--image")
    news.add_argument("--categories")
    news.add_argument("--tags")
    news.add_argument("--translate-now", action="store_true")
    news.add_argument("--dry-run", action="store_true")
    news.add_argument("--force", action="store_true")
    news.set_defaults(func=create_news)

    rootme = sub.add_parser("rootme", help="Ajouter un challenge Root-Me")
    rootme.add_argument("url", nargs="?")
    rootme.add_argument("--manual-id")
    rootme.set_defaults(func=add_rootme)

    sadservers = sub.add_parser("sadservers", help="Ajouter un scenario SadServers")
    sadservers.add_argument("url", nargs="?")
    sadservers.set_defaults(func=add_sadservers)

    translate = sub.add_parser("translate", help="Traduire une page ou tout le contenu")
    translate.add_argument("path", nargs="?")
    translate.add_argument("--force", action="store_true")
    translate.set_defaults(func=translate_command)

    build = sub.add_parser("build", help="Builder le site")
    build.set_defaults(func=build_command)

    serve = sub.add_parser("serve", help="Lancer le serveur Hugo local")
    serve.add_argument("--port", type=int, default=1313)
    serve.set_defaults(func=serve_command)

    status = sub.add_parser("status", help="Voir les brouillons et traductions manquantes")
    status.set_defaults(func=status_command)

    publish = sub.add_parser("publish", help="Commit + push sur GitHub")
    publish.add_argument("message", nargs="?")
    publish.set_defaults(func=publish_command)

    return parser


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        menu()
        return
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
