import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import config

logger = logging.getLogger(__name__)

class CloudflareClient:
    def __init__(self, api_token):
        self.api_token = api_token
        self.session = self._create_session()
        self.base_url = "https://api.cloudflare.com/client/v4"

    def _create_session(self):
        session = requests.Session()
        # Retrying on 429 (Too Many Requests) is critical for bulk updates
        retry_strategy = Retry(
            total=10, 
            backoff_factor=2, # Exponential backoff: 2, 4, 8, 16...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "PUT", "POST"]
        )
        adapter = HTTPAdapter(
            pool_connections=config.MAX_WORKERS + 5,
            pool_maxsize=config.MAX_WORKERS + 10,
            max_retries=retry_strategy
        )
        session.mount("https://", adapter)
        session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        })
        return session

    def fetch_page(self, url, page, per_page=50):
        params = {'page': page, 'per_page': per_page}
        try:
            # Long-running timeouts for reliability
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('success'):
                return data.get('result', []), data.get('result_info', {})
            logger.error(f"API Error on page {page}: {data.get('errors')}")
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            return None, None # Return None to indicate ERROR, not just empty
        return [], {}

    def get_zones(self, limit=None, processed_set=None):
        """
        Fetch zones from Cloudflare. 
        If limit is provided, it will stop fetching pages once the limit is satisfied.
        """
        url = f"{self.base_url}/zones"
        all_zones = []
        page = 1
        
        while True:
            logger.info(f"Fetching zones page {page}...")
            results, result_info = self.fetch_page(url, page)
            if not results:
                break
            
            if processed_set is not None:
                # Only add domains not in processed_set
                filtered = [z for z in results if z['name'].lower() not in processed_set]
                all_zones.extend(filtered)
            else:
                all_zones.extend(results)
            
            if limit and len(all_zones) >= limit:
                logger.info(f"Reached limit of {limit} domains.")
                return all_zones[:limit]
            
            total_pages = result_info.get('total_pages', 0)
            if page >= total_pages:
                break
            page += 1
            
        return all_zones

    def get_all_zones(self):
        # Backward compatibility
        return self.get_zones()

    def get_dns_records(self, zone_id, record_type=None):
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        params = {"type": record_type, "per_page": 100} if record_type else {"per_page": 100}
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get('result', [])
        except Exception as e:
            logger.error(f"Error fetching DNS records for {zone_id}: {e}")
            return None # Return None to indicate FETCH FAILURE (distinguish from empty list)

    def update_dns_record(self, zone_id, record_id, record_type, name, content, ttl=1, comment=""):
        url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"
        payload = {
            "type": record_type, 
            "name": name, 
            "content": content, 
            "ttl": ttl,
            "comment": comment
        }
        try:
            resp = self.session.put(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json().get('success', False)
        except Exception as e:
            logger.error(f"Error updating DNS record {record_id} in {zone_id}: {e}")
            return False

    def create_dns_record(self, zone_id, record_type, name, content, ttl=1, comment=""):
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        payload = {
            "type": record_type, 
            "name": name, 
            "content": content, 
            "ttl": ttl,
            "comment": comment
        }
        try:
            resp = self.session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json().get('success', False)
        except Exception as e:
            logger.error(f"Error creating DNS record in {zone_id}: {e}")
            return False
