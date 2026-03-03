import bcrypt
from dataclasses import dataclass

from messageboard.errors import Error


@dataclass
class UserData:
    name: str
    password_hash: bytes
    disabled: bool = False


class InMemoryAuthentication:
    def __init__(self, secret: str, add_demo_users: bool = True):
        self.users: dict[str, UserData] = {}
        self.demo_users = add_demo_users
        self._add_demo_users()

    @staticmethod
    def _to_canonical_name(name: str) -> str:
        return name.lower().strip()

    @staticmethod
    def _hash(password: str) -> bytes:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def _add_hashed(self, name: str, password: str, disabled: bool = False):
        """Interner Helper für __init__ ohne Duplikatprüfung."""
        self.users[name] = UserData(
            name=name,
            password_hash=self._hash(password),
            disabled=disabled,
        )
        
    def _add_demo_users(self):
        if self.demo_users:
            self._add_hashed("alice", "password123")
            self._add_hashed("bob", "password123")
            self._add_hashed("charlie", "password123", disabled=True)  # für 403-Tests
        

    def reset(self) -> None:
        """Nutzer auf Demo-Daten zurücksetzen (/admin/reset)."""
        self.users.clear()
        self._add_demo_users()

    def add_user(self, name: str, password: str):
        name = self._to_canonical_name(name)
        if name in self.users:
            raise Error.USER_ALREADY_EXISTS(name)  # → 409
        self.users[name] = UserData(name=name, password_hash=self._hash(password))

    def check_password(self, name: str, password: str) -> bool:
        """
        Prüft Zugangsdaten. Reihenfolge bewusst gewählt:
        1. Existiert der Nutzer? → 401 (vage Fehlermeldung, verhindert User-Enumeration)
        2. Ist das Konto deaktiviert? → 403 (erst nach Passwort-Prüfung, timing-neutral)
        3. Ist das Passwort korrekt? → bool
        """
        name = self._to_canonical_name(name)

        if name not in self.users:
            raise Error.INVALID_CREDENTIALS()  # → 401

        user = self.users[name]
        password_ok = bcrypt.checkpw(password.encode(), user.password_hash)

        if not password_ok:
            raise Error.INVALID_CREDENTIALS()  # → 401

        if user.disabled:
            raise Error.USER_DISABLED(name)  # → 403

        return True