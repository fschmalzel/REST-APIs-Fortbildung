from enum import Enum


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class Error(Enum):
    # ── Authentifizierung ────────────────────────────────────────────────────
    USER_ALREADY_EXISTS        = (409, "Benutzername '{}' ist bereits vergeben")
    INVALID_CREDENTIALS        = (401, "Ungültige Anmeldedaten")
    USER_DISABLED              = (403, "Konto '{}' ist deaktiviert")

    # ── Nachrichten ──────────────────────────────────────────────────────────
    MESSAGE_NOT_FOUND          = (404, "Nachricht {} nicht gefunden")
    NOT_MESSAGE_AUTHOR         = (403, "Keine Berechtigung — du bist nicht der Autor dieser Nachricht")

    # ── Token ────────────────────────────────────────────────────────────────
    MISSING_AUTH_HEADER        = (401, "Authorization Header fehlt oder kein Bearer Token")
    NOT_ACCESS_TOKEN           = (401, "Kein Access Token")
    NOT_REFRESH_TOKEN          = (401, "Kein Refresh Token")
    REFRESH_TOKEN_INVALIDATED  = (401, "Refresh Token wurde invalidiert (Logout)")
    INVALID_TOKEN              = (401, "Ungültiger Token")
    TOKEN_EXPIRED              = (401, "Token abgelaufen")

    # ── Admin ────────────────────────────────────────────────────────────────
    INVALID_RESET_PASSWORD     = (403, "Ungültiges Reset-Passwort")

    def __call__(self, *args: object) -> APIError:
        status, template = self.value
        return APIError(status, template.format(*args) if args else template)