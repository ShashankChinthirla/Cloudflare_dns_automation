# Cloudflare DNS Automator ⚡

**Because updating 11,000 SPF records manually is not a vibe.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Cloudflare](https://img.shields.io/badge/Cloudflare_API-Ready-orange?style=flat-square&logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/api/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 🛑 The Problem
Managing DNS for a few domains? Easy. managing 100+ or 1,000+? That’s a nightmare. 

I needed a way to audit and update SPF/DMARC records across **thousands of domains** without:
1.  Clicking through the Cloudflare UI forever.
2.  Accidentally breaking email deliverability.
3.  Losing track of what changed.

## ✅ The Solution
A Python script that talks to Cloudflare, checks your records, fixes them, and **proves it worked**.

It’s built for **safety over speed**. It checks, updates, verifies, and logs everything. If the API flakes out, it retries. If it crashes, it remembers where it left off.

---

## 📊 What You Get (The "Receipts")
The script generates an Excel report that looks like this, so you always have a paper trail:

| Domain | SPF Status | Old Record | New Record |
| :--- | :--- | :--- | :--- |
| `client-site.com` | **Updated** 🟢 | `v=spf1 -all` | `v=spf1 include:_spf.google.com ~all` |
| `my-portfolio.io` | **No Change** ⚪ | `v=spf1 ~all` | `v=spf1 ~all` |
| `weird-setup.net` | **Skipped** ⚠️ | *Multiple Records* | *Manual Review Needed* |

---

## 🔥 Key Features

*   **Dry Run Mode**: Default is "look but don't touch". See exactly what *would* happen first.
*   **Resume Capability**: Stop script? Internet died? No problem. It picks up right where it left off.
*   **Smart Safety**: It won't touch domains with weird setups (like multiple SPF records). It flags them for you instead.
*   **Bulk Ready**: Designed to handle thousands of domains without hitting Cloudflare's rate limits.

---

## 🚀 Quick Start

**1. Clone & Install**
```bash
git clone https://github.com/ShashankChinthirla/Cloudflare_dns_automation.git
cd Cloudflare_dns_automation
pip install -r requirements.txt
```

**2. Configure**
Create a `.env` file and add your API Token:
```ini
CLOUDFLARE_API_TOKEN=your_token_here
```

**3. Run It**

👀 **See what happens (Safe Mode):**
```bash
python main.py
```

⚡ **Actually do it:**
```bash
python main.py --apply
```

---

## 📂 How It Works
1.  **Iterates** through all zones in your Cloudflare account.
2.  **Analyzes** current SPF/DMARC records.
3.  **Compares** against your target policy (e.g., `v=spf1 include:_spf.google.com ~all`).
4.  **Updates** only if necessary.
5.  **Verifies** the update instantly via API.
6.  **Logs** the result to Excel & CSV.

---

### *Disclaimer*
*Always run in `--dry-run` first. DNS propagation is fast, but mistakes are annoying.*
