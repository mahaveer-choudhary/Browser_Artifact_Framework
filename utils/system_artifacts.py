import subprocess
import os
import winreg

class SystemArtifacts:
    @staticmethod
    def extract_wifi_profiles():
        profiles = []
        try:
            output = subprocess.check_output("netsh wlan show profiles", shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
            for line in output.split('\n'):
                if "All User Profile" in line:
                    profile_name = line.split(":")[1].strip()
                    try:
                        pwd_output = subprocess.check_output(f'netsh wlan show profile name="{profile_name}" key=clear', shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
                        password = "<none>"
                        for pwd_line in pwd_output.split('\n'):
                            if "Key Content" in pwd_line:
                                password = pwd_line.split(":")[1].strip()
                                break
                        profiles.append({"ssid": profile_name, "password": password})
                    except Exception:
                        profiles.append({"ssid": profile_name, "password": "<error>"})
        except Exception:
            pass
        return profiles

    @staticmethod
    def extract_usb_history():
        usb_devices = []
        try:
            key_path = r"SYSTEM\CurrentControlSet\Enum\USB"
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            for i in range(winreg.QueryInfoKey(reg_key)[0]):
                device_class = winreg.EnumKey(reg_key, i)
                try:
                    class_key = winreg.OpenKey(reg_key, device_class)
                    for j in range(winreg.QueryInfoKey(class_key)[0]):
                        device_id = winreg.EnumKey(class_key, j)
                        try:
                            dev_key = winreg.OpenKey(class_key, device_id)
                            # Fallback to DeviceDesc if FriendlyName is absent (common for non-storage USBs)
                            try:
                                name = winreg.QueryValueEx(dev_key, "FriendlyName")[0]
                            except:
                                try:
                                    name = winreg.QueryValueEx(dev_key, "DeviceDesc")[0]
                                    name = name.split(";")[-1] if ";" in name else name
                                except:
                                    name = "Unknown USB Device"
                                    
                            usb_devices.append({
                                "class": device_class,
                                "serial_number": device_id,
                                "name": name
                            })
                            winreg.CloseKey(dev_key)
                        except Exception:
                            usb_devices.append({
                                "class": device_class,
                                "serial_number": device_id,
                                "name": "Unknown"
                            })
                    winreg.CloseKey(class_key)
                except Exception:
                    pass
            winreg.CloseKey(reg_key)
        except Exception:
            pass
        return usb_devices

    @staticmethod
    def extract_bam():
        bam_entries = []
        try:
            key_path = r"SYSTEM\CurrentControlSet\Services\bam\UserSettings"
            users_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            for i in range(winreg.QueryInfoKey(users_key)[0]):
                user_sid = winreg.EnumKey(users_key, i)
                try:
                    user_key = winreg.OpenKey(users_key, user_sid)
                    for j in range(winreg.QueryInfoKey(user_key)[1]):
                        val_name, val_data, val_type = winreg.EnumValue(user_key, j)
                        if val_name not in ["Version", "SequenceNumber"]:
                            bam_entries.append({
                                "user_sid": user_sid,
                                "executable": val_name
                            })
                    winreg.CloseKey(user_key)
                except Exception:
                    pass
            winreg.CloseKey(users_key)
        except Exception:
            pass
        return bam_entries

    @staticmethod
    def extract_anti_forensics():
        flags = []
        user_profile = os.environ.get("USERPROFILE", "")
        system_drive = os.environ.get("SystemDrive", "C:")
        
        suspicious_paths = [
            (os.path.join(user_profile, r"Desktop\Tor Browser"), "Tor Browser"),
            (os.path.join(user_profile, r"Downloads\Tor Browser"), "Tor Browser"),
            (os.path.join(system_drive + "\\", r"Program Files\Mullvad VPN"), "Mullvad VPN"),
            (os.path.join(system_drive + "\\", r"Program Files\ProtonVPN"), "ProtonVPN"),
            (os.path.join(system_drive + "\\", r"Program Files\NordVPN"), "NordVPN"),
            (os.path.join(system_drive + "\\", r"Program Files (x86)\NordVPN"), "NordVPN"),
            (os.path.join(user_profile, r"AppData\Local\BraveSoftware\Brave-Browser\User Data\tor"), "Brave Tor Profile"),
            (os.path.join(system_drive + "\\", r"Program Files\BleachBit"), "BleachBit (Data Wiping)"),
            (os.path.join(system_drive + "\\", r"Program Files\CCleaner"), "CCleaner (Data Wiping)"),
            (os.path.join(user_profile, r"Downloads\rufus"), "Rufus (Bootable USBs)")
        ]
        
        for path, name in suspicious_paths:
            if os.path.exists(path):
                flags.append({
                    "category": "Anti-Forensics / Privacy Tool",
                    "name": name,
                    "path": path
                })
                
        # Simple Preference Check for Chrome
        chrome_prefs = os.path.join(user_profile, r"AppData\Local\Google\Chrome\User Data\Default\Preferences")
        if os.path.exists(chrome_prefs):
            try:
                import json
                with open(chrome_prefs, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
                    if prefs.get("profile", {}).get("default_content_setting_values", {}).get("cookies", 0) == 4:
                        flags.append({
                            "category": "Browser Hardening",
                            "name": "Chrome Configured to Clear Cookies",
                            "path": chrome_prefs
                        })
            except:
                pass
                
        return flags

    @staticmethod
    def run_all():
        return {
            "wifi_profiles": SystemArtifacts.extract_wifi_profiles(),
            "usb_history": SystemArtifacts.extract_usb_history(),
            "bam_execution_history": SystemArtifacts.extract_bam(),
            "anti_forensics": SystemArtifacts.extract_anti_forensics()
        }
