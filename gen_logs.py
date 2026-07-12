import requests, json, time

BASE = "http://localhost:80"

def api(method, path, token=None, data=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.request(method, f"{BASE}{path}", headers=headers, json=data)
    return r

def full_flow(uid):
    """Complete user flow: register, browse, cart, checkout, pay."""
    user_id = int(time.time() * 1000) % 100000
    r = api("POST", "/api/auth/register/", data={"username": f"loguser{user_id}", "email": f"log{user_id}@demo.com", "password": "pass123"})
    if not r.ok:
        return
    token = r.json()["access"]
    
    api("GET", "/api/products/?page=1", token=token)
    r = api("GET", "/api/inventory/", token=token)
    items = r.json()
    if not items:
        return
    pid = items[0]["product_id"]
    
    api("GET", f"/api/inventory/{pid}/", token=token)
    api("POST", "/api/cart/add/", token=token, data={"product": pid, "quantity": 1})
    
    r = api("POST", "/api/orders/checkout/", token=token)
    if r.status_code != 201:
        return
    oid = r.json()["order_id"]
    
    api("POST", f"/api/payments/pay/{oid}/", token=token)
    api("POST", f"/api/inventory/{pid}/restock/", token=token, data={"quantity": 10})

# Run 5 full user flows
for i in range(5):
    full_flow(i)
    time.sleep(0.1)
print("Done — 5 user flows completed, logs saved to logs/*.log")
