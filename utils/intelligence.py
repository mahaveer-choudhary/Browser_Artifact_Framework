import os
import json
import sqlite3
import re
import csv
from datetime import datetime

class BAFIntelligence:
    def __init__(self, browser_type: str = None):
        self.browser_type = browser_type

    def get_extensions_path(self):
        try:
            from utils.common import get_browser_data_file
            history_path = get_browser_data_file(self.browser_type, "history")
            if history_path:
                return os.path.join(os.path.dirname(history_path), "Extensions")
        except Exception:
            pass
        return None

    def analyze_extensions(self):
        """Analyzes installed extensions for suspicious permissions."""
        ext_path = self.get_extensions_path()
        results = []
        if not ext_path or not os.path.exists(ext_path):
            return results

        suspicious_perms = ['nativeMessaging', 'webRequest', 'webRequestBlocking', 'clipboardWrite', 'cookies', '<all_urls>']
        
        for ext_id in os.listdir(ext_path):
            id_path = os.path.join(ext_path, ext_id)
            if os.path.isdir(id_path):
                for ver in os.listdir(id_path):
                    ver_path = os.path.join(id_path, ver)
                    manifest_path = os.path.join(ver_path, 'manifest.json')
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                            
                            name = manifest.get('name', 'Unknown')
                            if name.startswith('__MSG_'):
                                name = f"Localized Name ({ext_id})"
                                
                            perms = manifest.get('permissions', [])
                            if isinstance(perms, dict):
                                perms = list(perms.keys())
                            
                            flags = [p for p in perms if isinstance(p, str) and p in suspicious_perms]
                            is_suspicious = len(flags) > 0
                            
                            results.append({
                                "id": ext_id,
                                "name": name,
                                "version": manifest.get('version', 'Unknown'),
                                "suspicious": is_suspicious,
                                "flagged_permissions": flags
                            })
                        except Exception:
                            pass
        return results

    def carve_deleted_history(self, db_path, actual_urls):
        """Scans raw SQLite DB for URL strings not present in actual_urls (deleted)."""
        deleted = []
        if not os.path.exists(db_path):
            return deleted
            
        try:
            with open(db_path, 'rb') as f:
                raw_data = f.read()
                
            url_pattern = re.compile(b'https?://[\\w\\.-]+(?:/[\\w\\.-]*)*')
            found_urls = set(url_pattern.findall(raw_data))
            
            actual_url_bytes = set(u.encode('utf-8') for u in actual_urls if u)
            
            for url_b in found_urls:
                if url_b not in actual_url_bytes:
                    try:
                        decoded = url_b.decode('utf-8')
                        deleted.append(decoded)
                    except:
                        pass
        except Exception:
            pass
            
        return list(set(deleted))

    @staticmethod
    def identify_cloud_tokens(cookies):
        """Identifies active cloud session tokens from extracted cookies."""
        cloud_tokens = []
        targets = {
            ".google.com": ["SID", "HSID", "SSID", "OSID"],
            ".live.com": ["WLSSC"],
            ".dropbox.com": ["t"],
            ".slack.com": ["d"]
        }
        
        for cookie in cookies:
            host = cookie.get("host", "")
            name = cookie.get("name", "")
            val = cookie.get("value", "")
            if val == "<encrypted>": continue
            
            for domain, tokens in targets.items():
                if domain in host and name in tokens:
                    cloud_tokens.append({
                        "service": domain,
                        "token_name": name,
                        "token_value": val[:20] + "..." if len(val) > 20 else val,
                        "expires": cookie.get("expires", "")
                    })
        return cloud_tokens

    @staticmethod
    def scan_iocs(history_items):
        """Mock IOC scanner for demonstration purposes."""
        mock_bad_domains = ["evil.com", "phishing-bank.com", "darkweb-marketplace.onion", "bit.ly/malicious"]
        ioc_hits = []
        
        for item in history_items:
            url = item.get("url", "").lower()
            for bad in mock_bad_domains:
                if bad in url:
                    ioc_hits.append({
                        "url": item["url"],
                        "threat": "Known Malicious Domain (Mock Feed)",
                        "timestamp": item.get("last_visit_time", "")
                    })
                    break
        return ioc_hits

    @staticmethod
    def generate_super_timeline(full_data, dumps_dir):
        """Merges all history items across all browsers into a single CSV timeline."""
        timeline = []
        
        for browser, data in full_data.items():
            for item in data.get('history', []):
                t = item.get('last_visit_time', '')
                if t and t != '-':
                    timeline.append({
                        "timestamp": t,
                        "browser": browser,
                        "type": "History",
                        "event": f"Visited: {item.get('title', '')} ({item.get('url', '')})"
                    })
                    
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if not os.path.exists(dumps_dir):
            os.makedirs(dumps_dir)
            
        csv_path = os.path.join(dumps_dir, "super_timeline.csv")
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Browser", "Type", "Event"])
                for entry in timeline:
                    writer.writerow([entry['timestamp'], entry['browser'], entry['type'], entry['event']])
            return csv_path
        except Exception:
            return None
