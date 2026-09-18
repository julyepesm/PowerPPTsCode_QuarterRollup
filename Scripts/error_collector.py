
class ErrorCollector:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorCollector, cls).__new__(cls)
            cls._instance.errors = []
        return cls._instance
    
    def add_error(self, brand, market, tactic, month, message, value=None):
        """
        Record a data validation error.
        
        Args:
            brand (str): Brand name
            market (str): Market name
            tactic (str): Tactic name
            month (str): Month/Year context
            message (str): Description of the error
            value (any, optional): The problematic value
        """
        error_record = {
            'brand': brand,
            'market': market,
            'tactic': tactic,
            'month': month,
            'message': message,
            'value': value
        }
        self.errors.append(error_record)
        print(f"  [DATA ERROR] {market} - {tactic}: {message}")

    def get_errors(self):
        return self.errors

    def clear(self):
        self.errors = []
