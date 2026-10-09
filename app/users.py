"""Foydalanuvchilar: ro'yxatdan o'tish / kirish.
Parollar pbkdf2 bilan heshlanadi, sessiyalar token orqali (users.json, sessions.json)."""
from __future__ import annotations
import hashlib
import json
import secrets
import time
from pathlib import Path


def _load(base: Path, name: str, default):
    try:
        return json.loads((base / name).read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(base: Path, name: str, data) -> None:
    (base / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def norm_phone(p) -> str:
    return "".join(ch for ch in str(p) if ch.isdigit())


def _hash(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 200_000).hex()


def public(u: dict) -> dict:
    return {"id": u["id"], "name": u["name"], "phone": u["phone"]}


def _new_session(base: Path, u: dict) -> dict:
    sessions = _load(base, "sessions.json", {})
    token = secrets.token_hex(24)
    sessions[token] = u["id"]
    _save(base, "sessions.json", sessions)
    return {"token": token, "user": public(u)}


def register(base: Path, name: str, phone: str, password: str) -> dict:
    name = name.strip()
    phone = norm_phone(phone)
    if len(name) < 2:
        raise ValueError("Ism juda qisqa")
    if len(phone) < 9:
        raise ValueError("Telefon raqam noto'g'ri")
    if len(password) < 4:
        raise ValueError("Parol kamida 4 belgidan iborat bo'lsin")
    users = _load(base, "users.json", [])
    if any(u["phone"] == phone for u in users):
        raise ValueError("Bu telefon ro'yxatda bor — Kirish qiling")
    salt = secrets.token_hex(8)
    u = {
        "id": int(time.time() * 1000) % 100000000,
        "name": name, "phone": phone,
        "salt": salt, "password_hash": _hash(password, salt),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    users.append(u)
    _save(base, "users.json", users)
    return _new_session(base, u)


def login(base: Path, phone: str, password: str) -> dict:
    phone = norm_phone(phone)
    users = _load(base, "users.json", [])
    u = next((x for x in users if x["phone"] == phone), None)
    if not u or u["password_hash"] != _hash(password, u["salt"]):
        raise ValueError("Telefon yoki parol noto'g'ri")
    return _new_session(base, u)


def me_by_token(base: Path, token: str):
    if not token:
        return None
    sessions = _load(base, "sessions.json", {})
    uid = sessions.get(token)
    if not uid:
        return None
    users = _load(base, "users.json", [])
    u = next((x for x in users if x.get("id") == uid), None)
    return public(u) if u else None


def logout(base: Path, token: str) -> None:
    sessions = _load(base, "sessions.json", {})
    sessions.pop(token, None)
    _save(base, "sessions.json", sessions)
