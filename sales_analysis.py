import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Charts folder
charts_dir = os.path.join(BASE_DIR, "charts")

# Create folder if missing
os.makedirs(charts_dir, exist_ok=True)

print("Charts folder:", charts_dir)

df = pd.read_csv("realistic_e_commerce_sales_data.csv")

#load and clean data
df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]
 
# Parse dates
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
 
# Drop rows with nulls in critical columns
critical = ["customer_id", "order_date", "product_name", "total_price"]
before = len(df)
df.dropna(subset=critical, inplace=True)
print(f"[CLEAN] Dropped {before - len(df)} rows with nulls in critical columns")
 
# Fill non-critical nulls
df["region"] = df["region"].fillna("Unknown")
df["age"]    = df["age"].fillna(df["age"].median())
df["shipping_status"] = df["shipping_status"].fillna("Unknown")
 
# Validate numeric columns
df = df[df["total_price"] > 0]
df = df[df["quantity"] > 0]
 
# Derive time features
df["year"]       = df["order_date"].dt.year
df["month"]      = df["order_date"].dt.month
df["month_name"] = df["order_date"].dt.strftime("%b")
df["year_month"] = df["order_date"].dt.to_period("M").astype(str)
df["quarter"]    = df["order_date"].dt.to_period("Q").astype(str)
 
# Age groups
df["age_group"] = pd.cut(
    df["age"],
    bins=[0, 25, 35, 45, 55, 100],
    labels=["<25", "25-34", "35-44", "45-54", "55+"]
)
 
print(f"[CLEAN] Final shape  : {df.shape}")
print(f"[CLEAN] Date range   : {df['order_date'].min().date()} → {df['order_date'].max().date()}")
print(f"[CLEAN] Null check   : {df[critical].isnull().sum().sum()} nulls remaining\n")

# Profit Stimulation
df["estimated_cost"] = (
    df["total_price"] * np.random.uniform(0.55, 0.80, len(df))
)

# Profit calculation
df["profit"] = (
    df["total_price"]
    - df["estimated_cost"]
    - df["shipping_fee"]
)

# Profit margin %
df["profit_margin"] = (
    df["profit"] / df["total_price"]
) * 100


# KPI Summary

total_revenue   = df["total_price"].sum()
total_profit = df["profit"].sum()
avg_profit_margin = df["profit_margin"].mean()
total_orders    = len(df)
avg_order_value = df["total_price"].mean()
total_units     = df["quantity"].sum()
return_rate     = (df["shipping_status"] == "Returned").mean() * 100
delivered_rate  = (df["shipping_status"] == "Delivered").mean() * 100
 
print("=" * 55)
print("  KPI SUMMARY")
print("=" * 55)
print(f"  Total Revenue      : ${total_revenue:>12,.2f}")
print(f"  Total Profit       : ${total_profit:>12,.2f}")
print(f"  Avg Profit Margin  : {avg_profit_margin:>11.1f}%")
print(f"  Total Orders       : {total_orders:>12,}")
print(f"  Avg Order Value    : ${avg_order_value:>12,.2f}")
print(f"  Total Units Sold   : {total_units:>12,}")
print(f"  Return Rate        : {return_rate:>11.1f}%  ")
print(f"  Delivery Rate      : {delivered_rate:>11.1f}%")
print("=" * 55)
 

# Top Products
product_summary = (
    df.groupby("product_name")
    .agg(
        revenue=("total_price", "sum"),
        orders=("customer_id", "count"),
        units=("quantity", "sum"),
        avg_price=("unit_price", "mean"),
    )
    .round(2)
    .reset_index()
    .sort_values("revenue", ascending=False)
)
product_summary["revenue_share_%"] = (product_summary["revenue"] / total_revenue * 100).round(1)
 
print("\n PRODUCTS BY REVENUE:")
print(product_summary[["product_name", "revenue", "orders", "units", "revenue_share_%"]].to_string(index=False))
 
 

# Loss-making products
loss_products = (
    df.groupby("product_name")
    .agg(
        revenue=("total_price", "sum"),
        profit=("profit", "sum"),
        orders=("customer_id", "count")
    )
    .round(2)
    .reset_index()
    .sort_values("profit")
)

print("\n LOSS-MAKING PRODUCTS:")
print(loss_products.head(10).to_string(index=False))


category_summary = (
    df.groupby("category")
    .agg(revenue=("total_price", "sum"), orders=("customer_id", "count"))
    .round(2)
    .reset_index()
    .sort_values("revenue", ascending=False)
)
category_summary["share_%"] = (category_summary["revenue"] / total_revenue * 100).round(1)
 
print("\n CATEGORY BREAKDOWN:")
print(category_summary.to_string(index=False))
 
# ─────────────────────────────────────────────────────────────────────────────
# Top Products Chart
# ─────────────────────────────────────────────────────────────────────────────

top_products = product_summary.head(10)

plt.figure(figsize=(10, 6))

sns.barplot(
    data=top_products,
    x="revenue",
    y="product_name"
)

plt.title("Top 10 Products by Revenue")

plt.tight_layout()

# FULL SAVE PATH
chart_path = os.path.join(charts_dir, "top_products.png")

print("Saving:", chart_path)

plt.savefig(chart_path)

plt.close()

# Region Analysis
region_summary = (
    df.groupby("region")
    .agg(revenue=("total_price", "sum"), orders=("customer_id", "count"), units=("quantity", "sum"))
    .round(2)
    .reset_index()
    .sort_values("revenue", ascending=False)
)
region_summary["revenue_share_%"] = (region_summary["revenue"] / total_revenue * 100).round(1)
 
print("\n  REGION ANALYSIS:")
print(region_summary.to_string(index=False))

# Visualize revenue by region
plt.figure(figsize=(8, 5))

sns.barplot(
    data=region_summary,
    x="region",
    y="revenue"
)

plt.title("Revenue by Region")
plt.tight_layout()

plt.savefig(os.path.join(charts_dir, "region_revenue.png"))
plt.close()

#time Series
monthly = (
    df.groupby("year_month")
    .agg(revenue=("total_price", "sum"), orders=("customer_id", "count"))
    .round(2)
    .reset_index()
    .sort_values("year_month")
)
monthly["revenue_ma3"] = monthly["revenue"].rolling(3, min_periods=1).mean().round(2)
monthly["growth_%"] = (
    monthly["revenue"].pct_change() * 100
).round(1)
 
quarterly = (
    df.groupby("quarter")
    .agg(revenue=("total_price", "sum"), orders=("customer_id", "count"))
    .round(2)
    .reset_index()
    .sort_values("quarter")
)

print("\n MONTHLY REVENUE:")
print(monthly[[
    "year_month",
    "revenue",
    "orders",
    "revenue_ma3",
    "growth_%"
]].to_string(index=False))
 
print("\n QUARTERLY:")

print(quarterly.to_string(index=False))

# Monthly Revenue Trend Chart
plt.figure(figsize=(10, 5))

sns.lineplot(
    data=monthly,
    x="year_month",
    y="revenue",
    marker="o"
)

plt.title("Monthly Revenue Trend")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(os.path.join(charts_dir, "monthly_revenue_trend.png"))
plt.close()


#Customer Demographic
gender_rev = (
    df.groupby("gender")
    .agg(revenue=("total_price", "sum"), orders=("customer_id", "count"))
    .round(2)
    .reset_index()
)
 
age_rev = (
    df.groupby("age_group", observed=True)
    .agg(revenue=("total_price", "sum"), orders=("customer_id", "count"))
    .round(2)
    .reset_index()
)
 
shipping_counts = df["shipping_status"].value_counts().reset_index()
shipping_counts.columns = ["status", "count"]
shipping_counts["rate_%"] = (shipping_counts["count"] / total_orders * 100).round(1)
 
print("\n GENDER REVENUE:")
print(gender_rev.to_string(index=False))
 
print("\n AGE GROUP REVENUE:")
print(age_rev.to_string(index=False))
 
print("\n SHIPPING STATUS:")
print(shipping_counts.to_string(index=False))

# Visualize shipping status distribution
plt.figure(figsize=(6, 6))

plt.pie(
    shipping_counts["count"],
    labels=shipping_counts["status"],
    autopct="%1.1f%%"
)

plt.title("Shipping Status Distribution")

plt.savefig(os.path.join(charts_dir, "shipping_status.png"))
plt.close()


# Customer Analysis
customer_summary = (
    df.groupby("customer_id")
    .agg(
        revenue=("total_price", "sum"),
        profit=("profit", "sum"),
        orders=("order_date", "count")
    )
    .round(2)
    .reset_index()
    .sort_values("revenue", ascending=False)
)

print("\n TOP CUSTOMERS:")
print(customer_summary.head(10).to_string(index=False))


# Bussiness Recommendations
recommendations = []

if return_rate > 10:
    recommendations.append(
        "High return rate detected. Review shipping quality and product expectations."
    )

top_region = region_summary.iloc[0]["region"]

recommendations.append(
    f"Increase marketing investment in {top_region}, the highest revenue region."
)

low_profit_products = loss_products.head(3)["product_name"].tolist()

recommendations.append(
    f"Investigate pricing and operational costs for: {', '.join(low_profit_products)}."
)

print("\n BUSINESS RECOMMENDATIONS:")
for r in recommendations:
    print(f"- {r}")


# Export
charts_dir = os.path.join(BASE_DIR, "charts")

os.makedirs(charts_dir, exist_ok=True)
 
# Cleaned CSV
df.to_csv(os.path.join( BASE_DIR, "sales_clean.csv"), index=False)

product_summary.to_csv(
    os.path.join(BASE_DIR, "top_products.csv"),
    index=False
)

region_summary.to_csv(
    os.path.join(BASE_DIR, "region_summary.csv"),
    index=False
)

monthly.to_csv(
    os.path.join(BASE_DIR, "monthly_summary.csv"),
    index=False
)
 
# JSON for dashboard
dashboard_data = {
    "kpis": {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "avg_profit_margin": round(avg_profit_margin, 1),
        "total_orders": int(total_orders),
        "avg_order_value": round(avg_order_value, 2),
        "total_units": int(total_units),
        "return_rate": round(return_rate, 1),
        "delivered_rate": round(delivered_rate, 1),
    },
    "products": product_summary.to_dict(orient="records"),
    "loss_products": loss_products.to_dict(orient="records"),
    "customers": customer_summary.to_dict(orient="records"),
    "recommendations": recommendations,
    "categories": category_summary.to_dict(orient="records"),
    "regions": region_summary.to_dict(orient="records"),
    "monthly": monthly.to_dict(orient="records"),
    "quarterly": quarterly.to_dict(orient="records"),
    "gender": gender_rev.to_dict(orient="records"),
    "age_groups": age_rev.to_dict(orient="records"),
    "shipping": shipping_counts.to_dict(orient="records"),
}
 
with open(os.path.join(BASE_DIR, "dashboard_data.json"), "w") as f:
    json.dump(dashboard_data, f, indent=2, default=str)
 
print("\n Exported: sales_clean.csv")
print("Exported: dashboard_data.json")
print("\nAll steps complete.")