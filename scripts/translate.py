#!/usr/bin/env python3
"""
Hugo Content Translator - Automatically translates French markdown content to English
using AI (OpenAI/DeepL/Google Translate).

Usage:
    python3 translate.py                    # Translate all content
    python3 translate.py --dry-run          # Show what would be translated
    python3 translate.py --file path/to.md  # Translate specific file
    python3 translate.py --provider deepl   # Use DeepL instead of OpenAI
"""

import os
import sys
import re
import argparse
from pathlib import Path

# Content directory relative to this script
CONTENT_DIR = Path(__file__).parent.parent / "content"

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and body from markdown content."""
    if not content.startswith("---"):
        return {}, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    # Simple YAML parsing
    frontmatter = {}
    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Handle arrays
            if value.startswith("["):
                value = value
            frontmatter[key] = value
    
    return frontmatter, body

def rebuild_markdown(frontmatter: dict, body: str, original_content: str) -> str:
    """Rebuild markdown file preserving original frontmatter format."""
    # Extract original frontmatter section
    parts = original_content.split("---", 2)
    if len(parts) < 3:
        return body
    
    original_fm = parts[1]
    return f"---{original_fm}---\n\n{body}"

def translate_with_openai(text: str, api_key: str) -> str:
    """Translate text using OpenAI GPT-4."""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional translator specializing in technical content.
Translate the following French markdown content to English.
- Keep all markdown formatting intact (headers, code blocks, links, images)
- Do NOT translate code within code blocks
- Keep technical terms accurate
- Maintain the same tone and style
- Return ONLY the translated text, no explanations"""
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except ImportError:
        print("Error: openai package not installed. Run: pip install openai")
        sys.exit(1)

def translate_with_deepl(text: str, api_key: str) -> str:
    """Translate text using DeepL API."""
    try:
        import deepl
        translator = deepl.Translator(api_key)
        result = translator.translate_text(text, source_lang="FR", target_lang="EN-US")
        return result.text
    except ImportError:
        print("Error: deepl package not installed. Run: pip install deepl")
        sys.exit(1)

def translate_with_google(text: str, api_key: str = None) -> str:
    """Translate text using Google Translate (free, no API key needed).
    Uses deep-translator library which is compatible with modern Python."""
    try:
        from deep_translator import GoogleTranslator
        
        # deep-translator has a 5000 char limit per request, so we split long texts
        max_chars = 4500
        if len(text) <= max_chars:
            return GoogleTranslator(source='fr', target='en').translate(text)
        
        # Split by paragraphs for long texts
        paragraphs = text.split('\n\n')
        translated_parts = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += para + '\n\n'
            else:
                if current_chunk:
                    translated = GoogleTranslator(source='fr', target='en').translate(current_chunk.strip())
                    translated_parts.append(translated)
                current_chunk = para + '\n\n'
        
        if current_chunk:
            translated = GoogleTranslator(source='fr', target='en').translate(current_chunk.strip())
            translated_parts.append(translated)
        
        return '\n\n'.join(translated_parts)
    except ImportError:
        print("Error: deep-translator package not installed. Run: pip install deep-translator")
        sys.exit(1)

def get_translator(provider: str):
    """Get the appropriate translation function."""
    translators = {
        "openai": translate_with_openai,
        "deepl": translate_with_deepl,
        "google": translate_with_google
    }
    return translators.get(provider, translate_with_openai)

def find_untranslated_files(force: bool = False) -> list[Path]:
    """Find all French markdown files without English translations (or all if force=True)."""
    untranslated = []
    
    for md_file in CONTENT_DIR.rglob("*.md"):
        # Skip files that are already translations
        if ".en." in md_file.name or ".fr." in md_file.name:
            continue
        
        # Skip _index.md files (section pages)
        if md_file.name == "_index.md":
            continue
        
        # Check if English version exists
        en_file = md_file.with_name(md_file.stem + ".en.md")
        if md_file.name == "index.md":
            en_file = md_file.parent / "index.en.md"
        
        if force or not en_file.exists():
            untranslated.append(md_file)
    
    return untranslated

def translate_file(file_path: Path, provider: str, api_key: str, dry_run: bool = False) -> bool:
    """Translate a single markdown file."""
    print(f"📄 Processing: {file_path.relative_to(CONTENT_DIR)}")
    
    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    
    if not body.strip():
        print("  ⏭️  Skipping: No content to translate")
        return False
    
    # Determine output path
    if file_path.name == "index.md":
        en_file = file_path.parent / "index.en.md"
    else:
        en_file = file_path.with_name(file_path.stem + ".en.md")
    
    if dry_run:
        print(f"  📝 Would create: {en_file.relative_to(CONTENT_DIR)}")
        print(f"  📊 Content length: {len(body)} characters")
        return True
    
    # Translate
    translate_func = get_translator(provider)
    try:
        translated_body = translate_func(body, api_key)
    except Exception as e:
        print(f"  ❌ Translation error: {e}")
        return False
    
    # Rebuild and save
    translated_content = rebuild_markdown(frontmatter, translated_body, content)
    en_file.write_text(translated_content, encoding="utf-8")
    print(f"  ✅ Created: {en_file.relative_to(CONTENT_DIR)}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Translate Hugo content from French to English")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated without doing it")
    parser.add_argument("--file", type=str, help="Translate a specific file")
    parser.add_argument("--force", action="store_true", help="Re-translate all files, even if English version exists")
    parser.add_argument("--provider", choices=["openai", "deepl", "google"], default="google", help="Translation provider (default: google - free & unlimited)")
    parser.add_argument("--api-key", type=str, help="API key (or set OPENAI_API_KEY/DEEPL_API_KEY env var)")
    
    args = parser.parse_args()
    
    # Get API key (not needed for google)
    api_key = args.api_key
    if not api_key and args.provider != "google":
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "deepl": "DEEPL_API_KEY",
        }
        env_var = env_vars.get(args.provider)
        if env_var:
            api_key = os.environ.get(env_var)
    
    if not api_key and args.provider != "google" and not args.dry_run:
        print(f"❌ Error: No API key provided. Set {env_vars[args.provider]} or use --api-key")
        sys.exit(1)
    
    # Find files to translate
    if args.file:
        files = [Path(args.file)]
    else:
        files = find_untranslated_files(force=args.force)
    
    if not files:
        print("✨ All content files already have English translations!")
        return
    
    print(f"\n🌐 Hugo Content Translator")
    print(f"   Provider: {args.provider}")
    print(f"   Files to translate: {len(files)}")
    if args.dry_run:
        print("   Mode: DRY RUN\n")
    else:
        print()
    
    translated = 0
    for file_path in files:
        if translate_file(file_path, args.provider, api_key, args.dry_run):
            translated += 1
    
    print(f"\n{'📋 Would translate' if args.dry_run else '✅ Translated'}: {translated}/{len(files)} files")

if __name__ == "__main__":
    main()