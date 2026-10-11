"""Lecture d'un recu de caisse avec Gemini (cle gratuite Google AI Studio).

Fonction principale : extract(image_path, api_key) -> dict
  {"amount": float, "date": "AAAA-MM-JJ" ou "", "merchant": str, "category": str}
Leve ReceiptError avec un message en francais pret a afficher.
"""
import base64
import io
import json
import re
import ssl
import urllib.error
import urllib.request

MODELS = ("gemini-flash-latest", "gemini-2.5-flash")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_SIDE = 1600

CATEGORIES = ["Logement", "Alimentation", "Enfants / famille", "Transport",
              "Eau / électricité / gaz", "Communication", "Santé / imprévus",
              "Aide aux parents", "Dîme", "Épargne", "Projets / autres"]

PROMPT = (
    "Tu lis la photo d'un reçu ou d'une facture (souvent en francs CFA, FCFA / XOF). "
    "Réponds UNIQUEMENT par un objet JSON avec ces clés : "
    '"amount" (le TOTAL final à payer, nombre sans espaces ni séparateurs de milliers, '
    'point pour les décimales, null si illisible), '
    '"date" (date du reçu au format AAAA-MM-JJ, chaîne vide si absente), '
    '"merchant" (nom du commerce, chaîne vide si absent), '
    '"category" (exactement une valeur parmi : ' + " | ".join(CATEGORIES) + "). "
    "Si ce n'est pas un reçu, mets amount à null."
)


class ReceiptError(Exception):
    pass


def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _prepare(path):
    """Retourne (octets, mime). Reduit l'image si Pillow est disponible."""
    try:
        from PIL import Image, ImageOps
        img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        img.thumbnail((MAX_SIDE, MAX_SIDE))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"
    except ImportError:
        pass
    except Exception as exc:
        raise ReceiptError("Image illisible : " + str(exc))
    with open(path, "rb") as f:
        data = f.read()
    if len(data) > 12_000_000:
        raise ReceiptError("Photo trop lourde. Utilisez une photo plus petite.")
    low = path.lower()
    mime = "image/png" if low.endswith(".png") else "image/jpeg"
    return data, mime


def parse_reply(text):
    """Transforme la reponse du modele en dict propre."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ReceiptError("Réponse non comprise. Réessayez avec une photo plus nette.")
    try:
        data = json.loads(m.group(0))
    except ValueError:
        raise ReceiptError("Réponse non comprise. Réessayez avec une photo plus nette.")
    amount = data.get("amount")
    if isinstance(amount, str):
        s = re.sub(r"[^\d,.\-]", "", amount).replace(",", ".")
        try:
            amount = float(s)
        except ValueError:
            amount = None
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ReceiptError("Montant introuvable. Prenez la photo plus près, bien à plat.")
    date = str(data.get("date") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        date = ""
    cat = str(data.get("category") or "")
    if cat not in CATEGORIES:
        cat = "Projets / autres"
    return {"amount": float(amount), "date": date,
            "merchant": str(data.get("merchant") or "").strip(), "category": cat}


def extract(path, api_key, timeout=60):
    api_key = (api_key or "").strip()
    if not api_key:
        raise ReceiptError("Aucune clé Gemini enregistrée.")
    img, mime = _prepare(path)
    body = json.dumps({
        "contents": [{"parts": [
            {"text": PROMPT},
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(img).decode()}}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }).encode()
    last = None
    for model in MODELS:
        req = urllib.request.Request(
            URL.format(model=model), data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
                payload = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 401, 403):
                raise ReceiptError("Clé Gemini refusée. Vérifiez-la dans les réglages du scan.")
            if exc.code == 429:
                raise ReceiptError("Limite gratuite atteinte. Réessayez plus tard.")
            last = ReceiptError(f"Service indisponible (code {exc.code}).")
            continue
        except (urllib.error.URLError, OSError):
            raise ReceiptError("Pas de connexion internet.")
        try:
            return parse_reply(payload["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError):
            raise ReceiptError("Le reçu n'a pas pu être lu. Réessayez.")
    raise last or ReceiptError("Service indisponible.")
