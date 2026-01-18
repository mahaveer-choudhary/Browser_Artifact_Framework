import os
import base64
import json
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Windows DPAPI structures
class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

_crypt32 = ctypes.windll.crypt32

def decrypt_dpapi(encrypted_data: bytes) -> Optional[bytes]:
    """Decrypt data using Windows DPAPI (CryptUnprotectData)."""
    try:
        blob_in = DATA_BLOB(len(encrypted_data), ctypes.cast(ctypes.create_string_buffer(encrypted_data), ctypes.POINTER(ctypes.c_byte)))
        blob_out = DATA_BLOB()
        
        ret = _crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out))
        if not ret:
            return None
        
        # Copy data from blob_out
        size = blob_out.cbData
        ptr = blob_out.pbData
        data = ctypes.string_at(ptr, size)
        
        # Free memory allocated by LocalAlloc (called by CryptUnprotectData)
        ctypes.windll.kernel32.LocalFree(ptr)
        return data
    except Exception as e:
        print(f"[!] DPAPI Decryption failed: {e}")
        return None

def decrypt_chromium_v10(key: bytes, ciphertext: bytes) -> Optional[bytes]:
    """Decrypt Chromium v10 (AES-GCM) data using the Master Key."""
    try:
        # Nonce is 12 bytes (IV)
        nonce = ciphertext[3:15]
        # Data is the rest (excluding tag which is handled by AESGCM automatically at the end)
        # However, cryptography AESGCM expects the tag appended.
        # Chromium format: v10 + IV(12) + Ciphertext + Tag(16)
        encrypted_payload = ciphertext[15:] 
        
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, encrypted_payload, None)
    except Exception as e:
        print(f"[VERBOSE DEBUG] V10/V20 Decryption failed: {e}") 
        return None

def decrypt_chromium_v20(app_bound_key: bytes, ciphertext: bytes) -> Optional[bytes]:
    """Decrypt Chromium v20 (App-Bound) data."""
    # App-Bound encryption:
    # v20 (3 bytes) + Identity (variable? usually empty or fixed size?) 
    # Actually, v20 format wraps the key with App-Bound key. 
    # But usually, the "ciphertext" we get for cookies/logins is encrypted with the key WE decrypted using App-Bound logic.
    # So this function behaves exactly like v10 (AES-GCM) but uses the App-Bound-decrypted key.
    # The prefix check is done by the caller.
    return decrypt_chromium_v10(app_bound_key, ciphertext)

# Firefox Crypto Helpers

def derive_key_pbkdf2(password: bytes, salt: bytes, iterations: int, key_len: int) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_len,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password)

def decrypt_aes_cbc(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data

def decrypt_3des_cbc(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    cipher = Cipher(algorithms.TripleDES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding (TripleDES block size is 64 bits = 8 bytes)
    unpadder = padding.PKCS7(64).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data

def sha1_hash(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
    digest.update(data)
    return digest.finalize()
