import requests
import pandas as pd
import time
from msal import PublicClientApplication
import settings

class PowerBIConnector:
    """Handles Power BI authentication and data retrieval"""
   
    def __init__(self, workspace_id, dataset_id, client_id):
        # Power BI Connection Settings
        self.workspace_id = workspace_id
        self.dataset_id = dataset_id
        self.client_id = client_id
       
        # Authentication settings (centralized in settings.py)
        self.authority = settings.AUTHORITY
        self.scope = settings.SCOPE
        self.base_url = settings.BASE_URL
       
        self.access_token = None
        self.token_expiry = 0
        self.app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority
        )
        
        # Use a session for connection pooling and robustness
        self.session = requests.Session()

    def authenticate(self, silent_only=False):
        """Authenticate with Power BI, reusing token if valid"""
        if self.access_token and self.token_expiry > time.time() + 60:
            return True

        # Try silent authentication first
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scope, account=accounts[0])
        else:
            result = None
       
        # If silent fails and not silent_only, use interactive
        if not result and not silent_only:
            print("Authenticating with Power BI (Interactive)...")
            result = self.app.acquire_token_interactive(scopes=self.scope)
       
        if result and "access_token" in result:
            self.access_token = result["access_token"]
            self.token_expiry = time.time() + result.get("expires_in", 3600)
            # Update session headers with the new token
            self.session.headers.update(self.get_headers())
            return True
        else:
            if not silent_only:
                print(f"Authentication failed: {result.get('error_description', 'Unknown error') if result else 'No accounts found'}")
            return False
    
    def get_headers(self):
        """Get API request headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
   
    def execute_dax_query(self, dax_query, max_retries=3):
        """
        Execute DAX query against Power BI dataset with retry logic
        
        Args:
            dax_query: The DAX query string to execute
            max_retries: Maximum number of retry attempts for network/rate-limit issues
        """
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
       
        payload = {
            "queries": [{"query": dax_query}]
        }
        
        retries = 0
        backoff_delay = 2 # Initial backoff in seconds
        
        while retries <= max_retries:
            try:
                # Use the persistent session
                response = self.session.post(url, json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    return self.parse_dax_result(result)
                
                elif response.status_code == 429: # Too Many Requests
                    print(f"  [API] Rate limit hit (429). Retrying in {backoff_delay}s... (Attempt {retries+1}/{max_retries})")
                    time.sleep(backoff_delay)
                    retries += 1
                    backoff_delay *= 2 # Exponential backoff
                    continue
                    
                else:
                    print(f"Query failed: {response.status_code} - {response.text}")
                    return None
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                # Handle connection reset or timeouts
                print(f"  [API] Connection issue: {e}. Retrying in {backoff_delay}s... (Attempt {retries+1}/{max_retries})")
                time.sleep(backoff_delay)
                retries += 1
                backoff_delay *= 2
                
                # If connection was reset, it's often good to re-establish the session
                self.session = requests.Session()
                if self.access_token:
                    self.session.headers.update(self.get_headers())
                continue
                
            except Exception as e:
                print(f"Unexpected error executing query: {e}")
                return None
        
        print(f"Max retries reached for query.")
        return None
   
    def parse_dax_result(self, result):
        """Convert DAX result to DataFrame"""
        try:
            tables = result['results'][0]['tables']
            if tables:
                table = tables[0]
                rows = table['rows']
                return pd.DataFrame(rows)
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error parsing results: {e}")
            return None
    
    def validate_data_completeness(self, df, required_columns):
        """Check if essential data is present for slide generation"""
        if df.empty:
            print("Warning: No data available")
            return False
       
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(f"Warning: Missing columns: {missing_cols}")
       
        return True
