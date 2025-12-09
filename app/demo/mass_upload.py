import csv
import json
import requests

login_url = "http://127.0.0.1:8500/login"
upload_url = "http://127.0.0.1:8500/inventory/add"


login_payload = {
    "username": "",  # Replace with a valid username
    "password": ""   # Replace with the corresponding password
}


session = requests.Session()


login_response = session.post(login_url, data=login_payload)
if login_response.status_code not in (200, 302):
    print("Login failed:", login_response.text)
    exit(1)
else:
    print("Login successful.")

# path to the CSV file 
csv_file_path = "Path to csv file"

with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        data = {
            "name": row["name"],
            "description": row.get("description", ""),
            "quantity": row["quantity"],
            "price": row["price"],
            "category": row["category"],
            "category_id": row.get("category_id", ""),
            "supplier": row.get("supplier", "")
        }
        response = session.post(upload_url, data=data)
        if response.status_code in (200, 302):
            print(f"Uploaded: {data['name']}")
        else:
            print(f"Failed to upload {data['name']}: {response.status_code} - {response.text}")
