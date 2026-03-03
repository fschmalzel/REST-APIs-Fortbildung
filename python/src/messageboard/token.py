import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import jwt

from messageboard.errors import Error

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

ISSUER = "messageboard-api"
AUDIENCE = "messageboard-api"


class JWTHandler:
    def __init__(self, secret: str):
        self.secret = secret
        # Maps username → list[jti] der aktiven Refresh-Tokens
        self.user_to_refresh_tokens: dict[str, list[str]] = defaultdict(list)
        # Invalidierte jtis (Logout-Blacklist)
        self.invalidated_refresh_tokens: set[str] = set()

    def _encode(self, payload: dict) -> str:
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def _decode(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                audience=AUDIENCE,
                issuer=ISSUER,
            )
        except jwt.ExpiredSignatureError:
            raise Error.TOKEN_EXPIRED()      # → 401 "Token abgelaufen"
        except jwt.InvalidTokenError:
            raise Error.INVALID_TOKEN()      # → 401 "Ungültiger Token"

    def create_auth_token(self, name: str) -> str:
        """
        Erstellt einen kurzlebigen Access Token.

        Enthält alle Standard-Claims aus RFC 7519:
          iss  — Aussteller
          sub  — Nutzer-ID
          aud  — Zielgruppe
          iat  — Ausstellungszeitpunkt
          nbf  — Gültig ab (hier: sofort)
          exp  — Ablaufzeit
          jti  — Eindeutige Token-ID
        """
        now = datetime.now(timezone.utc)
        payload = {
            "iss": ISSUER,
            "sub": name,
            "aud": AUDIENCE,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": str(uuid.uuid4()),
            "type": "access",
        }
        return self._encode(payload)

    def create_refresh_token(self, name: str) -> str:
        """
        Erstellt einen langlebigen Refresh Token.

        Der jti wird intern gespeichert, um den Token bei Logout
        gezielt invalidieren zu können (Blacklist via jti).
        """
        now = datetime.now(timezone.utc)
        jti = str(uuid.uuid4())
        payload = {
            "iss": ISSUER,
            "sub": name,
            "aud": AUDIENCE,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": jti,
            "type": "refresh",
        }
        self.user_to_refresh_tokens[name].append(jti)
        return self._encode(payload)

    def check_auth_token(self, auth_token: str) -> str:
        """Validiert Access Token und gibt den Nutzernamen (sub) zurück."""
        payload = self._decode(auth_token)
        if payload.get("type") != "access":
            raise Error.NOT_ACCESS_TOKEN()
        return payload["sub"]

    def refresh_auth_token(self, refresh_token: str) -> str:
        """
        Gibt einen neuen Access Token zurück, wenn der Refresh Token gültig ist.

        Prüft zusätzlich die interne Blacklist — ein per Logout invalidierter
        Token wird abgelehnt, auch wenn die Signatur noch gültig ist.
        """
        payload = self._decode(refresh_token)
        if payload.get("type") != "refresh":
            raise Error.NOT_REFRESH_TOKEN()

        jti = payload.get("jti")
        if jti in self.invalidated_refresh_tokens:
            raise Error.REFRESH_TOKEN_INVALIDATED()

        return self.create_auth_token(payload["sub"])

    def reset(self) -> None:
        """Token-State zurücksetzen (/admin/reset) — alle Blacklist-Einträge und gespeicherten jtis löschen."""
        self.user_to_refresh_tokens.clear()
        self.invalidated_refresh_tokens.clear()

    def invalidate_refresh_token(self, name: str):
        """
        Invalidiert alle Refresh Tokens eines Nutzers (Logout).

        Kein Fehler, wenn der Nutzer keine aktiven Tokens hat —
        das Ergebnis (alle Tokens ungültig) ist bereits erreicht.
        """
        if name not in self.user_to_refresh_tokens:
            return
        for jti in self.user_to_refresh_tokens[name]:
            self.invalidated_refresh_tokens.add(jti)
        del self.user_to_refresh_tokens[name]