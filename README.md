# Cloudflare Bulk DNS Automation

**Update 10,000+ domains safely. Sleep better.**

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare_API-F38020?style=flat-square&logo=cloudflare&logoColor=white)

## Why this exists
Managing DNS records for large portfolios (100s or 1000s of domains) is tedious and error-prone. One wrong move can take down email delivery.

This tool was built to automate **SPF** and **DMARC** hardening at scale, with a heavy focus on **safety** and **visibility**. It doesn't just "fire and forget"—it verifies every change and logs everything to Excel.

## What it does
1.  **Scans** your Cloudflare account for domains.
2.  **Checks** checks their current SPF/DMARC status.
3.  **Updates** them to your desired standard (e.g., `v=spf1 ... ~all`, `p=reject`).
4.  **Verifies** the update immediately via API.
5.  **Reports** results in a clean Excel file.

> **Safety Check:** It automatically skips domains with "messy" records (like multiple SPF entries) so you don't break complex setups.

## The Output (Excel)
You get a file `latest_domain_updates.xlsx` that looks like this:

| Domain | SPF Status | Previous Value | New Value | DMARC Status |
| :--- | :--- | :--- | :--- | :--- |
| `client-a.com` | ✅ **Updated** | `v=spf1 -all` | `v=spf1 ~all` | ✅ **Updated** |
| `client-b.com` | ⚪ **No Change** | `v=spf1 ~all` | `v=spf1 ~all` | ⚪ **No Change** |
| `legacy.net` | ⚠️ **Skipped** | *Multiple Records* | *--* | ⚠️ **Skipped** |

## Quick Start

### 1. Setup
```bash
git clone https://github.com/ShashankChinthirla/Cloudflare_dns_automation.git
cd Cloudflare_dns_automation
pip install -r requirements.txt
```

### 2. Config
Create a `.env` file with your Cloudflare API Token:
```ini
CLOUDFLARE_API_TOKEN=your_token_here
```

### 3. Run
**Dry Run** (SAFE - No changes applied):
```bash
python main.py
```

**Live Run** (Apply changes):
```bash
python main.py --apply
```

## Features for Ops
-   **Resumable**: Crashed? Internet died? Just run it again. It skips what's already done (via `processed_domains.csv`).
-   **Rate Limit Aware**: Handles Cloudflare's `429` errors with exponential backoff.
-   **Audit Trail**: Logs every single API call to `automation.log` for debugging.

---
*Maintained by Shashank Chinthirla.*
