#for the security of the app, encrypt all the prompts

import os
import base64
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import logging

class RenderPromptEncryption:
    def __init__(self):
        self.master_key = os.environ.get('ENCRYPTION_MASTER_KEY')
        self.key_version = int(os.environ.get('ENCRYPTION_KEY_VERSION', 1))
        
        if not self.master_key:
            raise ValueError("ENCRYPTION_MASTER_KEY environment variable required")
        
        self.fernet = Fernet(self.master_key.encode())
    
    def encrypt_prompt(self, prompt_text):
        """Encrypt user prompt"""
        try:
            encrypted_bytes = self.fernet.encrypt(prompt_text.encode('utf-8'))
            return {
                'encrypted_data': base64.b64encode(encrypted_bytes).decode('utf-8'),
                'key_version': self.key_version,
                'encrypted_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_prompt(self, encrypted_data, key_version=None):
        """Decrypt user prompt"""
        try:
            # Handle key version differences if you rotate keys later
            decryption_key = self._get_key_for_version(key_version or self.key_version)
            
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = decryption_key.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
            raise
    
    def _get_key_for_version(self, version):
        """Get appropriate key for decryption"""
        if version == self.key_version:
            return self.fernet
        else:
            # Handle old key versions - you'd add this logic during key rotation
            old_key = os.environ.get(f'ENCRYPTION_KEY_V{version}')
            if old_key:
                return Fernet(old_key.encode())
            else:
                raise ValueError(f"Key for version {version} not found")