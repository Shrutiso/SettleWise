"""
Currency Converter – Handles conversion of foreign currencies (USD, EUR, GBP) to INR.
Uses standard fixed exchange rates:
- 1 USD = 83.0 INR
- 1 EUR = 90.0 INR
- 1 GBP = 105.0 INR
"""

EXCHANGE_RATES = {
    "INR": 1.0,
    "USD": 83.0,
    "EUR": 90.0,
    "GBP": 105.0
}

def convert_to_inr(amount, from_currency):
    """
    Convert a given amount from a foreign currency to INR.
    If currency is unknown, returns the original amount.
    """
    if not from_currency:
        return amount
    
    currency_upper = str(from_currency).strip().upper()
    rate = EXCHANGE_RATES.get(currency_upper, 1.0)
    return round(amount * rate, 2)
