import settings

class Benchmarks:
    """Centralized benchmark values for all brands, tactics, and audiences"""
    
    def __init__(self):
        self.benchmarks = self._setup_benchmarks()
    
    def _setup_benchmarks(self):
        """Load benchmark values from settings configuration"""
        return settings.get_benchmarks()
    
    def get_benchmark(self, brand, tactic, audience, metric, date=None):
        """
        Get benchmark value for a specific brand, tactic, audience, and metric.
        Supports historical values if 'date' is provided.
        
        Args:
            brand: Brand name (e.g., 'GMC', 'Buick')
            tactic: Tactic name (e.g., 'FEP', 'BT Display')
            audience: Audience type (e.g., 'GEN', 'HIS')
            metric: Metric name (e.g., 'VCR', 'CPA')
            date: Optional date object or string to find historical benchmark
        
        Returns:
            Benchmark value as float, 'N/A' if explicitly set, or None if not found
        """
        try:
            if brand not in self.benchmarks:
                return None
            
            if tactic not in self.benchmarks[brand]:
                return None
            
            tactic_data = self.benchmarks[brand][tactic]
            
            # If tactic_data is a string (like "TBD" or "N/A"), return it directly
            if isinstance(tactic_data, str):
                return tactic_data
            
            # Handle audience nesting
            if isinstance(tactic_data, dict) and any(k in ['GEN', 'HIS', 'ASN'] for k in tactic_data.keys()):
                if audience in tactic_data:
                    metric_data = tactic_data[audience].get(metric)
                else:
                    return None
            else:
                # Direct metric structure
                metric_data = tactic_data.get(metric) if isinstance(tactic_data, dict) else None
                if metric_data is None and tactic_data == 'N/A':
                    return 'N/A'

            if metric_data is None:
                return None

            # Handle historical vs flat value
            if isinstance(metric_data, dict):
                # If it's a dict, check if keys are dates
                # Format: {"2023-01-01": 0.90, "2024-02-01": 0.95}
                if date is None:
                    # If no date provided, return the most recent one
                    latest_date = max(metric_data.keys())
                    return metric_data[latest_date]
                
                # Convert input date to string if it's a date object
                if not isinstance(date, str):
                    date_str = date.strftime('%Y-%m-%d')
                else:
                    date_str = date
                
                # Find the active benchmark for the given date
                # (Greatest date in config that is <= requested date)
                active_val = None
                sorted_dates = sorted(metric_data.keys())
                for d in sorted_dates:
                    if d <= date_str:
                        active_val = metric_data[d]
                    else:
                        break
                
                return active_val if active_val is not None else metric_data[sorted_dates[0]]

            return metric_data
                
        except Exception as e:
            print(f"Error getting benchmark for {brand} - {tactic} - {audience} - {metric}: {e}")
            return None
    
    def has_benchmark(self, brand, tactic, audience, metric):
        """
        Check if a numeric benchmark exists (not N/A)
        
        Returns:
            True if numeric benchmark exists, False if N/A or not found
        """
        benchmark = self.get_benchmark(brand, tactic, audience, metric)
        return benchmark is not None and benchmark != 'N/A'
    
    def get_tactic_benchmark_metric(self, tactic):
        """
        Get which benchmark metric to use for a given tactic
        
        Returns:
            Metric name (e.g., 'VCR', 'CPCV', 'CPA', 'ACR', 'CTR') or None if no benchmark
        """
        metric_mapping = {
            # Video tactics
            'FEP': 'VCR',
            'YouTube': 'CPCV',
            'PreRoll': 'VCR',
            'Meta Video': 'VCR',
            'Pinterest Video': 'VCR',
            'TikTok': 'CPCV',
            'Social Video': 'VCR',
            
            # Display tactics
            'BT Display': 'CPA',
            'Consideration Display': 'CPA',
            'Retargeting Display': 'CPA',
            'Meta Display': 'CPA',
            'Pinterest Display': 'CPA',
            'Search': 'CPC',
            
            # Audio
            'Audio': 'ACR'
        }
        
        return metric_mapping.get(tactic)