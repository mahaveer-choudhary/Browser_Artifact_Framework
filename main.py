import argparse
import sys
import json
import os
from utils.config import BrowserType, BROWSER_NAMES
from browsers.chromium import ChromiumExtractor
from browsers.firefox import FirefoxExtractor
from utils.forensics import log_chain_of_custody

def main():
    # Preprocess sys.argv to handle /opt:val syntax
    cleaned_args = []
    for arg in sys.argv[1:]:
        if arg.startswith("/") and ":" in arg:
            key, val = arg.split(":", 1)
            cleaned_args.extend([key, val])
        else:
            cleaned_args.append(arg)

    parser = argparse.ArgumentParser(description="DumpBrowserSecrets Python Implementation", prefix_chars='-/')
    parser.add_argument("/b", "--browser", "-b", dest="browser", help="Target Browser: chrome, edge, brave, opera, operagx, vivaldi, firefox, all")
    parser.add_argument("/o", "--output", "/f", "--file", "-o", "-f", dest="output", help="Output JSON File")
    parser.add_argument("/all", "--export-all", dest="export_all", action="store_true", help="Export All Entries")
    parser.add_argument("--stealth", action="store_true", help="Run extraction silently without console output.")
    
    args, unknown = parser.parse_known_args(cleaned_args)
    
    if args.stealth:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    
    # Map input string to enum
    target_browser = args.browser.lower() if args.browser else None
    
    browsers_to_process = []
    
    if target_browser == "all":
        browsers_to_process = [
            BrowserType.CHROME, BrowserType.EDGE, BrowserType.BRAVE, 
            BrowserType.OPERA, BrowserType.OPERA_GX, BrowserType.VIVALDI, 
            BrowserType.FIREFOX
        ]
    elif target_browser in BROWSER_NAMES.keys() or target_browser == "firefox":
        browsers_to_process = [target_browser]
    else:
        # Default behavior? System default? Let's just do Chrome as default for demo
        browsers_to_process = [BrowserType.CHROME]

    full_data = {}

    for b in browsers_to_process:
        print(f"\n--- Processing {b} ---")
        
        if b == BrowserType.FIREFOX:
            extractor = FirefoxExtractor()
            logins = extractor.extract_logins()
            if logins:
                cookies = extractor.extract_cookies()
                history = extractor.extract_history()
                extensions = extractor.extract_extensions()
                
                from utils.intelligence import BAFIntelligence
                intel = BAFIntelligence(b)
                cloud_tokens = intel.identify_cloud_tokens(cookies)
                iocs = intel.scan_iocs(history)
                
                full_data[b] = {
                    "logins": logins,
                    "cookies": cookies,
                    "history": history,
                    "intelligence": {
                        "extensions": extensions,
                        "cloud_tokens": cloud_tokens,
                        "iocs": iocs,
                        "deleted_history": []
                    }
                }
                print(f"[+] Extracted {len(logins)} logins, {len(cookies)} cookies, {len(history)} history items.")
            else:
                print("[-] No Firefox data found or decryption failed.")
        else:
            extractor = ChromiumExtractor(b)
            if extractor.get_keys():
                cookies = extractor.extract_cookies()
                logins = extractor.extract_logins()
                history = extractor.extract_history()
                web_data = extractor.extract_web_data()
                bookmarks = extractor.extract_bookmarks()
                
                from utils.intelligence import BAFIntelligence
                intel = BAFIntelligence(b)
                extensions = intel.analyze_extensions()
                cloud_tokens = intel.identify_cloud_tokens(cookies)
                iocs = intel.scan_iocs(history)
                deleted = getattr(extractor, 'deleted_history', [])
                
                full_data[b] = {
                    "cookies": cookies,
                    "logins": logins,
                    "history": history,
                    "credit_cards": web_data.get("credit_cards", []),
                    "autofill": web_data.get("autofill", []),
                    "bookmarks": bookmarks,
                    "intelligence": {
                        "extensions": extensions,
                        "cloud_tokens": cloud_tokens,
                        "iocs": iocs,
                        "deleted_history": deleted
                    }
                }
                
                print(f"[+] Extracted {len(cookies)} cookies, {len(logins)} logins, {len(history)} history items, {len(bookmarks)} bookmarks.")
            else:
                print("[-] Could not retrieve keys. Skipping.")

    # Output
    # Ensure dumps directory exists
    dumps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dumps")
    if not os.path.exists(dumps_dir):
        os.makedirs(dumps_dir)

    output_file = args.output
    if not output_file:
        output_file = os.path.join(dumps_dir, "BrowserData.json")
    else:
        # If user provided a path, check if it's just a filename or path. 
        # If just filename, put in dumps. If path, respect it? 
        # Requirement says "the script should create a separate folder".
        # Let's enforce dumps folder if no path separator in argument, or just default to dumps/ if arg not provided.
        # User said "for dumps like file secrets_*.json, the script should create a separate folder". 
        # Assuming run_all_browsers handles naming. main.py is low level. 
        # But if main.py is run without args, it matches the requirement to use dumps.
        # If user passes -f file.json, I will prepend dumps/ unless it's absolute.
        if not os.path.dirname(output_file):
             output_file = os.path.join(dumps_dir, output_file)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)
        
    # Generate chain of custody hash
    file_hash = log_chain_of_custody(output_file, dumps_dir)
        
    print(f"\n[+] Data saved to {output_file}")
    
    from utils.intelligence import BAFIntelligence
    timeline_path = BAFIntelligence.generate_super_timeline(full_data, dumps_dir)
    if timeline_path:
        print(f"[+] Super Timeline CSV generated.")
        
    system_file = os.path.join(dumps_dir, "system_artifacts.json")
    if not os.path.exists(system_file):
        from utils.system_artifacts import SystemArtifacts
        sys_data = SystemArtifacts.run_all()
        with open(system_file, "w", encoding="utf-8") as f:
            json.dump(sys_data, f, indent=4)
        print("[+] System Artifacts extracted (sys_artifacts.json).")

    print(f"[+] SHA-256 Hash: {file_hash}")

if __name__ == "__main__":
    main()
