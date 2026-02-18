# Cloudflare DNS Automation 🚀

Automated, bulk management of SPF and DMARC records across thousands of Cloudflare domains. Designed for scale, safety, and reliability.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Cloudflare](https://img.shields.io/badge/Cloudflare-API-orange) ![Status](https://img.shields.io/badge/Status-Production%20Ready-green)

## 🎯 What it Does
This tool automates the tedious process of updating DNS security records for large portfolios of domains.

- **Standardizes SPF**: Updates SPF records to include `include:_spf.google.com ~all` (or your config).
- **Enforces DMARC**: Sets DMARC to `p=reject` with custom reporting addresses (`rua`/`ruf`) based on the domain name.
- **Validates Changes**: Automatically verifies that changes propagate using Cloudflare's API.
- **Generates Reports**: Creates detailed Excel reports of every change made.

## 🛠️ How it Works
The script follows a safe, sequential process to ensure no downtime or misconfiguration:

1.  **Fetch & Filter**: Retrieves domains from Cloudflare, skipping any that are already in `processed_domains.csv`.
2.  **Analyze**: Checks existing DNS records.
    *   *Risk Check*: Skips domains with complex setups (e.g., multiple SPF records) to avoid breaking things.
    *   *Idempotency*: Skips domains that already match the desired configuration ("No Change Needed").
3.  **Update**: Applies changes via the Cloudflare API.
4.  **Verify**: Immediately queries the API again to confirm the update was successful.
5.  **Report**: Logs the result to an Excel file and tracking CSV.

## ✨ Key Features
*   **Bulk Processing**: Handles thousands of domains using pagination.
*   **Smart Resume**: Maintains a `processed_domains.csv` file so you can stop and restart the script without losing progress.
*   **Safety First**:
    *   **Dry Run Mode**: Preview changes without applying them.
    *   **Rate Limiting**: Intelligent backoff to respect Cloudflare API limits.
    *   **Error Handling**: Continues processing other domains even if one fails.
*   **Detailed Logging**: Comprehensive `automation.log` and Excel reports.

## 🚀 Usage

### 1. Setup
Make sure you have Python installed, then install dependencies:
```bash
pip install -r requirements.txt
```

Create a `.env` file with your Cloudflare credentials:
```ini
CLOUDFLARE_API_TOKEN=your_api_token_here
```

### 2. Run in Dry Run Mode (Safe)
See what *would* happen without making changes:
```bash
python main.py
```

### 3. Run in Live Mode
Apply changes to all domains:
```bash
python main.py --apply
```

### 4. Optional Flags
*   `--limit N`: Process only N domains (e.g., `--limit 10`).
*   `--domain example.com`: Process a single specific domain.
*   `--no-track`: Do not adding domains to the "processed" list (useful for testing).

## 📊 Results
After a run, you will find:
*   **`latest_domain_updates.xlsx`**: A full report of every action (Before/After values, Status).
*   **`processed_domains.csv`**: A list of all completed domains.
*   **`automation.log`**: Technical logs for debugging.

---
*Built for robustness and scale.*
