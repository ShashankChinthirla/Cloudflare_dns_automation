# 🌐 Cloudflare DNS Automation | Bulk SPF & DMARC Security Tool

**Automate thousands of DNS updates in minutes. Secure your email infrastructure with one command.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white) 
![Cloudflare](https://img.shields.io/badge/Cloudflare-API-orange?style=for-the-badge&logo=cloudflare&logoColor=white) 
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge) 
![Cybersecurity](https://img.shields.io/badge/Focus-Email%20Security-red?style=for-the-badge)

---

## 🚀 What This Tool Does
Managing DNS records for 10, 100, or 10,000 domains manually is impossible. This Python automation script talks directly to **Cloudflare's API** to:

1.  **🔍 Audit**: Scans all your domains for missing or weak SPF/DMARC records.
2.  **🛡️ Secure**: Automatically updates them to industry standards (`v=spf1 ... ~all`, `p=reject`).
3.  **✅ Verify**: Instantly checks if the update was successful.
4.  **📊 Report**: Generates a **beautiful Excel report** of every single change.

**Perfect for:** MSPs, Domain Investors, Agencies, and DevOps Engineers managing large portfolios.

---

## 📊 Visual Reporting (The "Excel Magic")
Forget scrolling through terminal logs. This tool generates a professional `latest_domain_updates.xlsx` report that looks like this:

| Domain | SPF Status | Previous SPF | New SPF | DMARC Status | Previous DMARC | New DMARC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `example.com` | **Updated** 🟢 | `v=spf1 -all` | `v=spf1 ~all` | **Updated** 🟢 | *Missing* | `v=DMARC1; p=reject...` |
| `demo-site.io` | **No Change** ⚪ | `v=spf1 ~all` | `v=spf1 ~all` | **No Change** ⚪ | `p=reject` | `p=reject` |
| `risky-domain.net` | **Skipped** ⚠️ | *Critical Risk* | *N/A* | **Skipped** ⚠️ | *Multiple Records* | *N/A* |

*> You get a clear, audit-ready file to show clients or keep for compliance.*

---

## ✨ Key Features
*   **⚡ Blazing Fast**: Processes domains in parallel (multi-threaded).
*   **🛡️ Safety First**:
    *   **Dry Run Mode**: See exactly what *will* happen without changing anything.
    *   **Smart Risk Logic**: Automatically skips domains with complex/broken setups to prevent downtime.
*   **💾 Crash-Proof**:
    *   **Resume Capability**: Stop and start anytime; it interacts with `processed_domains.csv` to remember where it left off.
    *   **Auto-Save**: Saves the Excel report after every batch (never lose data).
*   **📉 Rate Limit Handling**: Built-in exponential backoff handles Cloudflare API limits (429 errors) gracefully.

---

## 🛠️ Installation & Usage

### 1. Clone the Repo
```bash
git clone https://github.com/ShashankChinthirla/Cloudflare_dns_automation.git
cd Cloudflare_dns_automation
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Configure API Token
Create a `.env` file (copied from `.env.template`) and add your Cloudflare API Token:
```ini
CLOUDFLARE_API_TOKEN=your_secure_api_token_here
```

### 4. Run the Script

**🧪 Dry Run (Safe Mode - Default)**
Preview changes without applying them:
```bash
python main.py
```

**🚀 Live Mode (Apply Changes)**
Actually update your DNS records:
```bash
python main.py --apply
```

**🎯 Single Domain Mode**
Test on just one domain:
```bash
python main.py --domain example.com
```

---

## 📂 Project Structure
*   `main.py`: The brain of the operation. Handles logic, risk checks, and reporting.
*   `cloudflare_client.py`: Handles all API communication with retry logic.
*   `dns_logic.py`: The "intelligence" ensuring your SPF/DMARC records are syntactically correct.
*   `processed_domains.csv`: Tracks progress so you can resume large jobs.

---

## 🙋‍♂️ FAQ
**Q: Will this break my website?**
A: No! The script includes a **Risk Check** system. If it detects existing complex records (like multiple SPF entries), it **skips** that domain and flags it in the report for manual review.

**Q: Can I run this on Windows/Mac/Linux?**
A: Yes! It's pure Python. Works everywhere.

**Q: Is my API Token safe?**
A: Yes. It is loaded from a `.env` file which is **ignored by Git**, so it never gets uploaded to the repository.

---

### 🔗 Keywords for Search
Cloudflare API Python, Bulk DNS Update Tool, Automate SPF DMARC, Email Security Automation, Python DNS Script, Cloudflare Mass Update, MSP Tools.

---
*Created by [Shashank Chinthirla](https://github.com/ShashankChinthirla)*
