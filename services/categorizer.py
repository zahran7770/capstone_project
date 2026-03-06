# services/categorizer.py

def categorize_transaction(description: str, amount: float) -> str:
    """
    Rule-based transaction categorization.
    Uses BOTH description text and transaction amount.
    """

    d = (description or "").lower()

    # -------------------------
    # TRANSFERS (income vs expense)
    # -------------------------
    if "transfer" in d:
        if amount > 0:
            return "Income"
        else:
            return "Transfer Out"

    # -------------------------
    # INSURANCE
    # -------------------------
    if "quotemehappyperth" in d:
        return "Car Insurance"

    # -------------------------
    # PETROL / FUEL
    # -------------------------
    if "essar" in d or "petrol" in d or "fuel" in d:
        return "Fuel"

    if "wolverhampton" in d and "essar" in d:
        return "Fuel"

    # -------------------------
    # SHOPPING
    # -------------------------
    if "aldi" in d:
        return "Shopping"

    # -------------------------
    # MONEY TRANSFER COMPANY
    # -------------------------
    if "altras.co.uk" in d or "altras" in d:
        return "Money Transfer"

    # -------------------------
    # GENERAL RULES
    # -------------------------
    if any(x in d for x in ["uber", "taxi", "train", "bus"]):
        return "Transport"

    if any(x in d for x in ["electric", "water", "gas", "bill"]):
        return "Bills"

    if any(x in d for x in ["restaurant", "cafe", "mcdonald", "kfc", "pizza"]):
        return "Food"

    if any(x in d for x in ["fee", "charge", "interest"]):
        return "Bank Fees"

    # -------------------------
    # DEFAULT FALLBACK
    # -------------------------
    return "Other"