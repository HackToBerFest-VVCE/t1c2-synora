
from ai_helper import get_bill_insights

sample_bill = {
    "previous_bill": 800,
    "current_bill": 1100,
    "previous_units": 120,
    "current_units": 160
}

result = get_bill_insights(sample_bill)

print("\n--- BillSense AI Insights ---\n")
print(result)
