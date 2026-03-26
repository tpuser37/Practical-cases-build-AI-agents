import csv
data = [
    # iPhone Data
    {
        "Product Name": "iPhone 15 Pro Max",
        "Vendor Name": "UNO.ma",
        "Product Title": "iPhone 15 Pro Max",
        "Price": 18990,
        "Currency": "MAD",
        "Bulk Discounts or Deals": "Available on request",
        "Vendor Website": "https://uno.ma",
        "Short Product Description": "Largest authorized Apple reseller network in Morocco with 12 sales points; offers a wide range of Apple products including latest iPhones.",
        "Minimum Order Quantity": 1,
        "Shipping Time": "1-3 days"
    },
    {
        "Product Name": "iPhone 17 Pro",
        "Vendor Name": "iSTYLE Morocco",
        "Product Title": "iPhone 17 Pro",
        "Price": 18390,
        "Currency": "MAD",
        "Bulk Discounts or Deals": "Possible for business clients",
        "Vendor Website": "https://istyle.ma",
        "Short Product Description": "Apple Premium Authorized Reseller in Casablanca offering authentic Apple products with full support.",
        "Minimum Order Quantity": 1,
        "Shipping Time": "1-3 days"
    },
    {
        "Product Name": "iPhone Air (various configurations)",
        "Vendor Name": "MAGIMAG (Wintek)",
        "Product Title": "iPhone Air (various configurations)",
        "Price": "16,990 to 23,990 MAD",
        "Currency": "MAD",
        "Bulk Discounts or Deals": "Available for wholesale buyers",
        "Vendor Website": "https://magimag.ma",
        "Short Product Description": "Official Apple distributor and reseller in Morocco specializing in hardware and software solutions nationwide.",
        "Minimum Order Quantity": 1,
        "Shipping Time": "Few days"
    },
    # Laptop Data
    {
        "Product Name": "Acer Predator Helios Neo 16 (Gaming Laptop)",
        "Vendor Name": "Nmar.ma",
        "Product Title": "Acer Predator Helios Neo 16 (Gaming Laptop)",
        "Price": 19500,
        "Currency": "MAD",
        "Bulk Discounts or Deals": "Available on inquiry",
        "Vendor Website": "https://nmar.ma",
        "Short Product Description": "Leading online tech store offering a wide range of laptops from gaming to professional models.",
        "Minimum Order Quantity": 1,
        "Shipping Time": "1-3 days"
    },
    {
        "Product Name": "Lenovo ThinkPad E16 Gen 2",
        "Vendor Name": "BitStore.ma",
        "Product Title": "Lenovo ThinkPad E16 Gen 2 – AMD Ryzen 7, 16GB DDR5, 512GB SSD",
        "Price": 11200,
        "Currency": "MAD",
        "Bulk Discounts or Deals": "Negotiable for corporate clients",
        "Vendor Website": "https://bitstore.ma/en/63-ordinateur",
        "Short Product Description": "Offers various laptops including gaming, professional, and workstation models with competitive pricing.",
        "Minimum Order Quantity": 1,
        "Shipping Time": "1-3 days"
    },
    {
        "Product Name": "Apple MacBook Air 13 pouces (puce M1) 256 Gb",
        "Vendor Name": "Ubuy.ma",
        "Product Title": "Apple MacBook Air 13 pouces (puce M1) 256 Gb",
        "Price": 12990,
        "Currency": "MAD",
        "Bulk Discounts or Deals": "Possible for large orders",
        "Vendor Website": "https://www.ubuy.ma/en/category/laptops-21457",
        "Short Product Description": "Wide selection of branded laptops including MacBooks and gaming laptops with easy online ordering.",
        "Minimum Order Quantity": 1,
        "Shipping Time": "Few days"
    }
]

# Writing to CSV
with open('data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = [
        "Product Name", "Vendor Name", "Product Title", "Price", "Currency",
        "Bulk Discounts or Deals", "Vendor Website", "Short Product Description",
        "Minimum Order Quantity", "Shipping Time"
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in data:
        writer.writerow(row)
        writer.writerow({})  # Blank line after each product