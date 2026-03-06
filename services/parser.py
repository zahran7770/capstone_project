import io
import pandas as pd


def parse_csv_transactions(file_bytes: bytes) -> list[dict]:
    df = pd.read_csv(io.BytesIO(file_bytes))

    # normalize col names (strip spaces)
    df.columns = [c.strip() for c in df.columns]

    # detect columns (more forgiving)
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    desc_col = next((c for c in df.columns if "desc" in c.lower() or "memo" in c.lower() or "narrative" in c.lower() or "payee" in c.lower()), None)
    amt_col = next((c for c in df.columns if "amount" in c.lower() or "amt" in c.lower()), None)

    if not date_col or not desc_col or not amt_col:
        raise ValueError("CSV must contain Date, Description (or Memo/Payee), and Amount columns.")

    # parse date and amount safely
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[amt_col] = pd.to_numeric(df[amt_col], errors="coerce")
    df[desc_col] = df[desc_col].astype(str).str.strip()

    # drop rows with missing essential fields
    df = df.dropna(subset=[date_col, amt_col])
    df = df[df[desc_col].str.len() > 0]

    transactions = []
    for _, row in df.iterrows():
        transactions.append(
            {
                "date": row[date_col].date(),
                "description": row[desc_col],
                "amount": float(row[amt_col]),
            }
        )

    return transactions