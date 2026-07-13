import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from agentforge.utils import ensure_config_dir

class CredentialVault:
    """Secure local storage for platform credentials and tokens using AES/Fernet encryption."""
    
    def __init__(self):
        self.config_dir = ensure_config_dir()
        self.key_path = self.config_dir / ".key"
        self.db_path = self.config_dir / "credentials.json"
        self.cipher = self._init_cipher()

    def _init_cipher(self) -> Fernet:
        """Initializes the Fernet cipher, generating a local key if none exists."""
        if not self.key_path.exists():
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            try:
                # Restrict key file to owner read/write only (0o600)
                self.key_path.chmod(0o600)
            except Exception:
                pass
        else:
            key = self.key_path.read_bytes()
        return Fernet(key)

    def _load_db(self) -> Dict[str, Dict[str, str]]:
        """Loads and decrypts the credential database."""
        if not self.db_path.exists():
            return {}
        try:
            encrypted_data = self.db_path.read_text()
            if not encrypted_data:
                return {}
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
            return json.loads(decrypted_bytes.decode())
        except Exception:
            return {}

    def _save_db(self, db: Dict[str, Dict[str, str]]) -> None:
        """Encrypts and saves the credential database."""
        serialized = json.dumps(db)
        encrypted_bytes = self.cipher.encrypt(serialized.encode())
        self.db_path.write_text(encrypted_bytes.decode())
        try:
            # Restrict db file to owner read/write only (0o600)
            self.db_path.chmod(0o600)
        except Exception:
            pass

    def set(self, platform: str, key: str, value: str) -> None:
        """Stores a credential value for a specific platform."""
        db = self._load_db()
        if platform not in db:
            db[platform] = {}
        db[platform][key] = value
        self._save_db(db)

    def get(self, platform: str, key: str) -> Optional[str]:
        """Retrieves a credential value for a specific platform."""
        db = self._load_db()
        return db.get(platform, {}).get(key)

    def get_all(self, platform: str) -> Dict[str, str]:
        """Retrieves all credentials for a specific platform."""
        db = self._load_db()
        return db.get(platform, {})

    def delete(self, platform: str, key: str) -> bool:
        """Deletes a credential key for a specific platform. Returns True if deleted."""
        db = self._load_db()
        if platform in db and key in db[platform]:
            del db[platform][key]
            if not db[platform]:
                del db[platform]
            self._save_db(db)
            return True
        return False

    def list_credentials(self) -> Dict[str, list]:
        """Lists all platforms and their configured credential keys (values hidden)."""
        db = self._load_db()
        return {platform: list(keys.keys()) for platform, keys in db.items()}
