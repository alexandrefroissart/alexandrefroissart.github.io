#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any


def load_env(root_dir: Path) -> dict[str, str]:
    env_file = root_dir / ".env"
    env_vars: dict[str, str] = {}

    if env_file.exists():
        with env_file.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")

    env_vars.update(os.environ)
    return env_vars


def env_get(env: dict[str, Any], key: str, default: Any = None) -> Any:
    value = env.get(key)
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return default
    return value


def env_flag(env: dict[str, Any], key: str, default: bool = False) -> bool:
    value = env_get(env, key, None)
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def clean_env_value(env: dict[str, Any], key: str) -> str | None:
    value = env.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
    if not value:
        return None
    return str(value)


def build_rootme_cookies(env: dict[str, Any]) -> str:
    rootme_cookies = clean_env_value(env, "ROOTME_COOKIES")
    if rootme_cookies:
        return rootme_cookies

    parts = []
    spip = clean_env_value(env, "spip_session") or clean_env_value(env, "SPIP_SESSION") or clean_env_value(env, "ROOTME_SPIP_SESSION")
    phpsess = clean_env_value(env, "PHPSESSID") or clean_env_value(env, "ROOTME_PHPSESSID")
    anubis = clean_env_value(env, "anubis-cookie-auth") or clean_env_value(env, "ANUBIS_COOKIE_AUTH") or clean_env_value(env, "ROOTME_ANUBIS_COOKIE_AUTH")

    if spip:
        parts.append(f"spip_session={spip}")
    if phpsess:
        parts.append(f"PHPSESSID={phpsess}")
    if anubis:
        parts.append(f"anubis-cookie-auth={anubis}")

    return "; ".join(parts)


def normalize_space(text: Any) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def strip_accents(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def extract_last_path_slug(url: str) -> str:
    parts = [part for part in url.rstrip("/").split("/") if part]
    return parts[-1] if parts else ""
