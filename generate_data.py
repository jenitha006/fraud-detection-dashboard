import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

n_transactions = 5000

# Customer pool (200 unique customers)
customer_ids = [f"CUST{str(i).zfill(4)}" for i in range(1, 201)]

# Merchant categories
merchant_categories = ['Grocery', 'Electronics', 'Travel', 'Dining', 'Fuel', 
                        'Online Shopping', 'Jewelry', 'Entertainment', 'ATM Withdrawal', 'Utilities']

# Locations (countries) - mostly normal, few blacklisted
normal_countries = ['India', 'USA', 'UK', 'Germany', 'Singapore', 'UAE', 'Australia']
blacklisted_countries = ['North Korea', 'Iran', 'Syria']

# Transaction types
transaction_types = ['POS', 'Online', 'ATM', 'Wire Transfer', 'Mobile Payment']

# Device IDs (each customer usually has 1-2 devices)
device_pool = {cust: [f"DEV{random.randint(1000,9999)}" for _ in range(random.randint(1,2))] 
               for cust in customer_ids}

# Generate base timestamp range (last 30 days)
start_date = datetime.now() - timedelta(days=30)

rows = []
for i in range(n_transactions):
    customer = random.choice(customer_ids)
    
    # Most transactions normal, 3% are fraud-injected
    is_fraud_injection = random.random() < 0.03
    
    timestamp = start_date + timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    
    if is_fraud_injection:
        amount = round(random.uniform(5000, 50000), 2)
        country = random.choice(blacklisted_countries + normal_countries)
        hour = random.choice([1, 2, 3, 4])  # odd hours
        timestamp = timestamp.replace(hour=hour)
    else:
        amount = round(random.uniform(10, 3000), 2)
        country = random.choice(normal_countries)
    
    row = {
        'TransactionID': f"TXN{str(i+1).zfill(6)}",
        'CustomerID': customer,
        'Amount': amount,
        'Date': timestamp.strftime('%Y-%m-%d'),
        'Time': timestamp.strftime('%H:%M:%S'),
        'Merchant': random.choice(merchant_categories),
        'Location': country,
        'TransactionType': random.choice(transaction_types),
        'AccountBalance': round(random.uniform(1000, 100000), 2),
        'DeviceID': random.choice(device_pool[customer])
    }
    rows.append(row)

df = pd.DataFrame(rows)
df = df.sort_values(['CustomerID', 'Date', 'Time']).reset_index(drop=True)
df.to_csv('synthetic_transactions.csv', index=False)

print(f"Generated {len(df)} transactions")
print(f"Fraud-pattern transactions injected: ~{int(n_transactions*0.03)}")
print(df.head())