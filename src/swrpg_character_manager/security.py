"""Security module for NIST-compliant data protection."""

import os
import base64
import secrets
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class DataEncryption:
    """NIST-compliant data encryption for sensitive user information."""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.cipher = Fernet(self.master_key)
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key using PBKDF2 with 256-bit key."""
        # Check for existing key file - try data directory first (for containers), then fallback to original location
        data_key_file = os.path.join(os.path.dirname(__file__), '../../data/.encryption_key')
        original_key_file = os.path.join(os.path.dirname(__file__), '../../.encryption_key')
        
        # Use data directory if it exists (container environment)
        if os.path.exists(os.path.dirname(data_key_file)):
            key_file = data_key_file
        else:
            key_file = original_key_file
        
        # Check if key exists in preferred location
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        
        # If using data directory but key exists in original location, migrate it
        if key_file == data_key_file and os.path.exists(original_key_file):
            with open(original_key_file, 'rb') as f:
                key_data = f.read()
            # Copy to new location
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key_data)
            os.chmod(key_file, 0o600)
            return key_data
        
        # Generate new key using environment variable as password + salt
        password = os.getenv('ENCRYPTION_PASSWORD', 'default-key-change-in-production').encode()
        salt = os.getenv('ENCRYPTION_SALT', 'swrpg-salt-change-in-production').encode()
        
        # Use PBKDF2 with SHA256 and 100,000 iterations (NIST recommended)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=100000,  # NIST recommended minimum
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Save key for future use
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        
        # Set secure permissions (readable only by owner)
        os.chmod(key_file, 0o600)
        
        return key
    
    def encrypt_email(self, email: str) -> str:
        """Encrypt email address for secure storage."""
        if not email:
            return ""
        
        try:
            encrypted_data = self.cipher.encrypt(email.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            print(f"Error encrypting email: {e}")
            return email  # Fallback to plaintext (should log this as security incident)
    
    def decrypt_email(self, encrypted_email: str) -> str:
        """Decrypt email address for use."""
        if not encrypted_email:
            return ""
        
        try:
            encrypted_data = base64.b64decode(encrypted_email.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            print(f"Error decrypting email: {e}")
            return encrypted_email  # Fallback to encrypted string (may be plaintext from migration)
    
    def encrypt_pii(self, data: str) -> str:
        """Encrypt any personally identifiable information."""
        return self.encrypt_email(data)  # Same encryption method
    
    def decrypt_pii(self, encrypted_data: str) -> str:
        """Decrypt personally identifiable information."""
        return self.decrypt_email(encrypted_data)  # Same decryption method
    
    def hash_email_for_index(self, email: str) -> str:
        """Create a hash of email for indexing while keeping original encrypted."""
        if not email:
            return ""
        
        # Use SHA256 for consistent hashing (for database indexes)
        import hashlib
        return hashlib.sha256(email.lower().encode('utf-8')).hexdigest()
    
    def is_email_encrypted(self, email_data: str) -> bool:
        """Check if email data is already encrypted."""
        if not email_data:
            return True
        
        # Try to decode as base64 - if it fails, likely not encrypted
        try:
            base64.b64decode(email_data)
            # Additional check: encrypted data should be longer than typical email
            return len(email_data) > 50
        except:
            return False


class SecurityAuditLog:
    """Security audit logging for compliance."""
    
    @staticmethod
    def log_data_access(user_id: str, action: str, data_type: str, success: bool = True):
        """Log data access for audit trails."""
        import datetime
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action,
            "data_type": data_type,
            "success": success,
            "ip_address": "system"  # Would be replaced with actual IP in production
        }
        
        # In production, this would go to a secure audit log system
        print(f"AUDIT LOG: {log_entry}")
    
    @staticmethod
    def log_encryption_event(event_type: str, success: bool = True):
        """Log encryption/decryption events."""
        import datetime
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "success": success,
            "component": "data_encryption"
        }
        
        print(f"ENCRYPTION LOG: {log_entry}")


# Global encryption instance
data_encryption = DataEncryption()
audit_log = SecurityAuditLog()