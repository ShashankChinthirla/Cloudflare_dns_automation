import logging
import argparse
import pandas as pd
import os
import sys
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient

# Local imports
from config import config
from cloudflare_client import CloudflareClient
from dns_logic import generate_updated_spf, generate_updated_dmarc

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_mongo_client():
    if not config.MONGODB_URI:
        logger.warning("⚠️ MONGODB_URI not found in environment. User mapping will be skipped.")
        return None
    try:
        client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        return client
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return None

def fetch_user_mapping(mongo_client, domain):
    if not mongo_client:
        return "N/A (No MongoDB)"
    try:
        db = mongo_client[config.DB_NAME]
        collection = db[config.COLLECTION_NAME]
        doc = collection.find_one({"domain": {"$regex": f"^{domain}$", "$options": "i"}})
        if doc:
            user = doc.get("user")
            if user: return str(user)
            contacts = doc.get("contactDetails", [])
            if contacts and isinstance(contacts, list) and len(contacts) > 0:
                return str(contacts[0].get("email", "Unknown Email"))
            return "Domain Found (No User Info)"
        return "Not Found"
    except Exception as e:
        return "Error"

def load_processed_domains():
    if os.path.exists(config.TRACKING_CSV_PATH):
        try:
            with open(config.TRACKING_CSV_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return {row['domain'].strip().lower() for row in reader if row.get('domain')}
        except Exception as e:
            logger.error(f"Error loading tracking CSV: {e}")
            return set()
    return set()

def save_processed_domain(domain):
    try:
        file_exists = os.path.exists(config.TRACKING_CSV_PATH)
        with open(config.TRACKING_CSV_PATH, mode='a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['domain'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({'domain': domain})
    except Exception as e:
        logger.error(f"Error saving processed domain {domain}: {e}")

def generate_report(results_list, report_path):
    if not results_list:
        logger.info("No results to report.")
        return

    try:
        df = pd.DataFrame(results_list)
        desired_order = [
            'domain', 'mapped user', 'risk', 'previous spf', 'new spf[updated]',
            'previous dmarc', 'new dmarc[updated]', 'spf status', 'dmarc status', 'zone_id'
        ]
        available_cols = [col for col in desired_order if col in df.columns]
        df = df[available_cols]
        
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Update Report')
            worksheet = writer.sheets['Update Report']
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except: pass
                worksheet.column_dimensions[column].width = min(max_length + 2, 60)

        logger.info(f"📊 Detailed report generated: {report_path}")
    except Exception as e:
        logger.error(f"Error generating Excel report: {e}")

def process_domain(client, zone, processed_set, mongo_client=None, dry_run=True):
    domain = zone['name']
    zone_id = zone['id']
    
    if domain.lower() in processed_set:
        return None
    
    logger.info(f"{'🔍 [DRY RUN]' if dry_run else '🔄'} Processing: {domain}")
    
    records = client.get_dns_records(zone_id, "TXT")
    mapped_user = fetch_user_mapping(mongo_client, domain)
    
    # If fetch failed (None), don't say "Missing", say "API Error"
    if records is None:
        return {
            "domain": domain, "mapped user": mapped_user, "risk": "API Fetch Error",
            "previous spf": "Error", "new spf[updated]": "N/A",
            "previous dmarc": "Error", "new dmarc[updated]": "N/A",
            "spf status": "Skipped (API Error)", "dmarc status": "Skipped (API Error)", "zone_id": zone_id
        }

    spf_records = [r for r in records if "v=spf1" in r['content']]
    dmarc_records = [r for r in records if r['content'].startswith("v=DMARC1") or r['name'].startswith("_dmarc")]
    
    raw_spf = spf_records[0]['content'] if spf_records else "Missing"
    raw_dmarc = dmarc_records[0]['content'] if dmarc_records else "Missing"
    
    risk_list = []
    if not spf_records: risk_list.append("Missing SPF")
    elif len(spf_records) > 1: risk_list.append(f"Multiple SPF ({len(spf_records)})")
    if not dmarc_records: risk_list.append("Missing DMARC")
    elif len(dmarc_records) > 1: risk_list.append(f"Multiple DMARC ({len(dmarc_records)})")
    
    risk_msg = ", ".join(risk_list) if risk_list else "None"
    new_spf = generate_updated_spf(raw_spf)
    new_dmarc = generate_updated_dmarc(raw_dmarc, domain)
    
    res_details = {
        "domain": domain, "mapped user": mapped_user, "risk": risk_msg,
        "previous spf": raw_spf, "new spf[updated]": new_spf,
        "previous dmarc": raw_dmarc, "new dmarc[updated]": new_dmarc,
        "spf status": "No Change Needed", "dmarc status": "No Change Needed", "zone_id": zone_id
    }
    
    # Apply SPF Update with Verification and Tagging
    if new_spf != raw_spf:
        spf_risk = [r for r in risk_list if "SPF" in r]
        if spf_risk:
            res_details['spf status'] = f"Skipped ({spf_risk[0]})"
        elif dry_run:
            res_details['spf status'] = "Dry Run: Would Update"
        else:
            existing_id = spf_records[0]['id']
            existing_name = spf_records[0]['name']
            logger.info(f"📤 Updating SPF for {domain}: {raw_spf} -> {new_spf}")
            success = client.update_dns_record(
                zone_id, 
                existing_id, 
                "TXT", 
                existing_name, 
                new_spf, 
                comment="Updated by Automation"
            )
            if success:
                # IMMEDIATE VERIFICATION
                verification_records = client.get_dns_records(zone_id, "TXT")
                if verification_records is None:
                    res_details['spf status'] = "Updated (Verification Failed - API Timeout)"
                    logger.warning(f"⚠️ SPF Verification skipped for {domain} due to API Timeout.")
                else:
                    match = next((r for r in verification_records if r['id'] == existing_id), None)
                    if match and match['content'] == new_spf:
                        res_details['spf status'] = "Updated"
                        logger.info(f"✅ SPF Verified and Tagged for {domain}")
                    else:
                        res_details['spf status'] = "Update Failed (Verification Failed)"
                        logger.error(f"❌ SPF Verification FAILED for {domain} - Content unchanged after update.")
            else:
                res_details['spf status'] = "Update Failed"
                logger.error(f"❌ SPF Update FAILED for {domain}")
    
    # Apply DMARC Update with Verification and Tagging
    if new_dmarc != raw_dmarc:
        dmarc_risk = [r for r in risk_list if "DMARC" in r]
        if dmarc_risk:
            res_details['dmarc status'] = f"Skipped ({dmarc_risk[0]})"
        elif dry_run:
            res_details['dmarc status'] = "Dry Run: Would Update"
        else:
            existing_id = dmarc_records[0]['id']
            existing_name = dmarc_records[0]['name']
            logger.info(f"📤 Updating DMARC for {domain}: {raw_dmarc} -> {new_dmarc}")
            success = client.update_dns_record(
                zone_id, 
                existing_id, 
                "TXT", 
                existing_name, 
                new_dmarc, 
                comment="Updated by Automation"
            )
            if success:
                # IMMEDIATE VERIFICATION
                verification_records = client.get_dns_records(zone_id, "TXT")
                if verification_records is None:
                    res_details['dmarc status'] = "Updated (Verification Failed - API Timeout)"
                    logger.warning(f"⚠️ DMARC Verification skipped for {domain} due to API Timeout.")
                else:
                    match = next((r for r in verification_records if r['id'] == existing_id), None)
                    if match and match['content'] == new_dmarc:
                        res_details['dmarc status'] = "Updated"
                        logger.info(f"✅ DMARC Verified and Tagged for {domain}")
                    else:
                        res_details['dmarc status'] = "Update Failed (Verification Failed)"
                        logger.error(f"❌ DMARC Verification FAILED for {domain} - Content unchanged after update.")
            else:
                res_details['dmarc status'] = "Update Failed"
                logger.error(f"❌ DMARC Update FAILED for {domain}")
        
    return res_details

import time

def main():
    parser = argparse.ArgumentParser(description="Cloudflare DNS Automation Pipeline")
    parser.add_argument("--apply", action="store_true", help="Apply changes to Cloudflare")
    parser.add_argument("--limit", type=int, help="Limit total processing to N domains")
    parser.add_argument("--report-name", type=str, help="Custom report filename (Excel)")
    parser.add_argument("--no-track", action="store_true", help="Do not update the tracking CSV")
    parser.add_argument("--domain", type=str, help="Process only this specific domain")
    args = parser.parse_args()
    
    dry_run = not args.apply
    report_path = args.report_name if args.report_name else config.REPORT_EXCEL_PATH
    
    logger.info(f"🚀 Starting automation in {'DRY RUN' if dry_run else 'LIVE'} mode...")
    if args.domain: logger.info(f"🎯 Target domain: {args.domain}")

    try: config.validate()
    except ValueError as e:
        logger.error(f"Config error: {e}"); return

    cf_client = CloudflareClient(config.CLOUDFLARE_API_TOKEN)
    mongo_client = get_mongo_client()
    
    try:
        processed_domains = load_processed_domains()
        total_processed_in_run = 0
        all_results = []
        
        if args.domain:
            # Single domain processing
            url = f"{cf_client.base_url}/zones"
            params = {"name": args.domain}
            resp = cf_client.session.get(url, params=params)
            resp.raise_for_status()
            zones = resp.json().get('result', [])
            if not zones:
                logger.error(f"❌ Domain {args.domain} not found.")
                return
            
            logger.info(f"📦 Processing Single Domain: {args.domain}")
            # Execute immediately for single domain
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(process_domain, cf_client, zones[0], processed_domains, mongo_client, dry_run)
                res = future.result()
                if res:
                    all_results.append(res)
                    if not dry_run and not args.no_track and (res.get('spf status') == "Updated" or res.get('dmarc status') == "Updated"):
                        save_processed_domain(res['domain'])
                        processed_domains.add(res['domain'].lower())

        else:
            # Multi-domain bulk processing
            logger.info("📡 Starting paginated zone fetch and process cycle...")
            page = 1
            while True:
                # Fetch a page of zones (default 50 per page from Cloudflare)
                zones_on_page, result_info = cf_client.fetch_page(f"{cf_client.base_url}/zones", page)
                if not zones_on_page:
                    break
                
                # Filter out already processed domains
                batch_to_process = [z for z in zones_on_page if z['name'].lower() not in processed_domains]
                
                if batch_to_process:
                    logger.info(f"📦 Processing Batch (Page {page}): {len(batch_to_process)} domains")
                    
                    batch_results = []
                    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
                        futures = {executor.submit(process_domain, cf_client, zone, processed_domains, mongo_client, dry_run): zone for zone in batch_to_process}
                        for future in as_completed(futures):
                            res = future.result()
                            if res:
                                batch_results.append(res)
                                # Global tracking
                                spf_final = res.get('spf status', '')
                                dmarc_final = res.get('dmarc status', '')
                                trackable_statuses = ["Updated", "No Change Needed"]
                                
                                if not dry_run and not args.no_track:
                                    # Track if either record was Updated OR No Change Needed (meaning we checked it and it's done)
                                    # We avoid tracking 'Skipped' or 'Error' statuses so they can be retried.
                                    if (spf_final in trackable_statuses or dmarc_final in trackable_statuses):
                                        save_processed_domain(res['domain'])
                                        processed_domains.add(res['domain'].lower())
                    
                    all_results.extend(batch_results)
                    total_processed_in_run += len(batch_to_process)
                    
                    # SAVE REPORT INCREMENTALLY
                    if all_results:
                        try:
                            generate_report(all_results, report_path)
                            logger.info(f"💾 Report saved (Partial): {len(all_results)} updates -> {report_path}")
                        except Exception as e:
                            logger.error(f"Error saving incremental report: {e}")

                    # Check limit
                    if args.limit and total_processed_in_run >= args.limit:
                        logger.info(f"🛑 Reached total limit of {args.limit} domains.")
                        break
                    
                    # Cooldown between batches if not the last page
                    if page < result_info.get('total_pages', 0):
                        logger.info(f"😴 Batch complete. Cooling down for {config.COOLDOWN_SLEEP}s...")
                        time.sleep(config.COOLDOWN_SLEEP)
                else:
                    logger.info(f"⏭️ Skipping page {page} - all domains already processed.")

                if page >= result_info.get('total_pages', 0):
                    break
                page += 1

        if all_results:
            generate_report(all_results, report_path)
        logger.info(f"✨ Process complete. Total domains handled in this run: {len(all_results)}")
        
    finally:
        if mongo_client: mongo_client.close()

if __name__ == "__main__":
    main()
