# Browser Artifact Framework (BAF)

**Browser Artifact Framework (BAF)** is a powerful Python-based forensic triage tool designed to extract and decrypt sensitive data from major web browsers on Windows. It supports modern encryption standards, including the latest **App-Bound Encryption (v20)** used by Chromium-based browsers, utilizing advanced DLL injection techniques without requiring elevated system privileges.

---

## 🚀 Advanced Features

### 1. 🌐 Multi-Browser Data Extraction
BAF decrypts and extracts critical forensic artifacts from **Chromium** (Chrome, Edge, Brave, Opera, Vivaldi) and **Gecko** (Firefox) engines:
*   🔐 **Saved Logins / Passwords** (Decrypted)
*   🍪 **Cookies**
*   📜 **Browsing & Search History**
*   🔖 **Bookmarks & Favorites**
*   💳 **Saved Credit Cards**
*   📝 **Autofill Metadata**

### 2. 🖥️ System & OS Artifacts Carvers
Beyond browsers, BAF extracts core triage items:
*   📶 **Saved Wi-Fi Profiles**: Recovers SSID networks and plaintext keys.
*   🔌 **USB Device History**: Audits Windows Registry (USBSTOR) to list every USB drive attached with serials.
*   🛡️ **Anti-Forensics Detection**: Automatically flags if user clears history on exit, or hosts privacy browsers (e.g., Tor), VPNs, and wipers.

### 3. 🔍 Intelligence & eDiscovery
*   🧠 **Threat Intel matched IOCs**: Connects to detection scanners to flag malicious extensions or items.
*   🔎 **Global Keyword Search**: Scanner interface to input items like numbers, cryptos, accomplice names and scan absolute artifact dumps.

### 4. 📊 Professional Forensics Reporting
*   📄 **Dynamic PDF Reporter**: Generates professional branded summaries containing wraps for long strings to avoid horizontal bleeding.
*   📊 **Multi-Sheet Excel Workbook Builder**: Partitions isolated worksheet modules (one tab per browser, one for System OS) safeguarding strict XML validation.

---

## 🛠️ Installation

### Prerequisites
*   Windows 10/11.
*   Python 3.8+.

### Setup

1.  **Clone & CD** into the repository:
    ```bash
    git clone https://github.com/mahaveer-choudhary/Browser_Artifact_Framework.git
    cd Browser_Artifact_Framework
    ```

2.  **Install Dependencies**:
    ```bash
    pip install flask pywin32 reportlab openpyxl
    ```

---

## 💻 Usage

### 🖥️ Dashboard View (Recommended)
Run the web dashboard for automated UI triggers and interactive reporting builders:
```bash
python dashboard.py
```
*   Dashboard opens automatically at `http://127.0.0.1:5000`.
*   Click **Extract** inside cards to dump files into `dumps/`.
*   Click **Export** to build conditions filtered formats.

### 🕵️ Stealth/Silent Mode (CLI)
To run fully in the background from a forensic flash drive without bringing up any frontend nodes or console outputs:
```bash
python main.py --stealth
```

---

## ⚠️ Disclaimer

**This tool is for EDUCATIONAL and FORENSIC AUDITING purposes only.**
The usage of this code to extract data from systems without explicit permission is absolute illegal. The author takes no responsibility for any misuse of this software.
