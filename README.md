# Browser Artifact Framework (BAF)

**Browser Artifact Framework** is a powerful Python-based tool designed to extract and decrypt sensitive data from major web browsers on Windows. It supports modern encryption standards, including the latest **App-Bound Encryption (v20)** used by Chromium-based browsers, utilizing advanced DLL injection techniques.

## 🚀 Features

*   **Multi-Browser Support**: 
    *   **Chromium**: Google Chrome, Microsoft Edge, Brave, Opera, Opera GX, Vivaldi.
    *   **Gecko**: Mozilla Firefox.
*   **Data Extraction**:
    *   🔐 **Passwords / logins** (Decrypted)
    *   🍪 **Cookies**
    *   📜 **Browsing History**
    *   🔖 **Bookmarks**
    *   💳 **Credit Cards**
    *   📝 **Autofill Data**
*   **Advanced Decryption**:
    *   Handles **DPAPI** (legacy).
    *   Handles **AES-256-GCM** (v10).
    *   Handles **App-Bound Encryption** (v20) via **DLL Injection** (bypassing the need for system privileges or elevation in many cases).
*   **Web Dashboard**: A clean Flask-based interface to trigger extractions and view collected statistics.
*   **Structured Output**: All data is saved as structured JSON files in the `dumps/` directory.

## 🛠️ Installation

### Prerequisites
*   Windows 10/11.
*   Python 3.8+.
*   [C++ Redistributables](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (May be required for the DLL).

### Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/mahaveer-choudhary/Browser_Artifact_Framework.git
    
    ```
    ```bash
    cd Browser_Artifact_Framework
    ```

2.  **Install Dependencies**:
    ```bash
    pip install flask pywin32
    ```

## 💻 Usage

### 1. The Dashboard (Recommended)
Run the web-based dashboard to easily manage extractions.

```bash
python dashboard.py
```
*   Opens automatically at `http://127.0.0.1:5000`.
*   Click **"Extract"** on any browser card to dump data.
*   View stats and file lists directly in the UI.

### 2. Auto-Extract All (One-Click)
Run the Python script to extract data from all detected browsers sequentially.

```bash
python run_all_browsers.py
```
*   This will kill running browser processes (required for database access) and dump data to `dumps/`.

### 3. CLI Manual Usage
Use `main.py` for granular control.

```bash
# Syntax
python main.py /b:<browser_name> [/f:<output_file>]

# Examples
python main.py /b:chrome                  # Extract Chrome to dumps/BrowserData.json
python main.py /b:edge /f:edge_dump.json  # Extract Edge to dumps/edge_dump.json
python main.py /b:firefox                 # Extract Firefox
python main.py /all                       # Extract everything
```

## 📂 Project Structure

```
Browser-Artifact-Framework/
├── dashboard.py           # Web Dashboard entry point
├── main.py                # Core extraction logic (CLI)
├── run_all_browsers.py    # Batch runner script
├── dumps/                 # Output folder for JSON artifacts
├── dashboard/             # Web App assets (HTML/CSS/JS)
├── browsers/              # Browser-specific extraction modules
│   ├── chromium.py
│   └── firefox.py
└── utils/                 # Configuration and Helpers
    ├── config.py
    ├── common.py
    ├── injector.py
    └── DllExtractChromiumSecrets.dll  # Critical binary for v20 decryption
```

## ⚠️ Disclaimer

**This tool is for EDUCATIONAL and FORENSIC purposes only.**
The usage of this code to extract data from systems without explicit permission is illegal. The author takes no responsibility for any misuse of this software.

---
*Created by Mahaveer Choudhary*
