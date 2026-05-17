# Stress Testing — Proof of Non-Functional Requirements

## 1. Zero Oversell Guarantee (Race Condition)

**File**: `stress_oversell.py`  
**JMeter**: `jmeter/01-OversellTest.jmx`  

**Proof Protocol**:
1. Seed: create a product with `quantity=5`
2. Create 100 users (each with Wallet balance=100)
3. Launch 100 concurrent `checkout` requests (same product, qty=1 each)
4. Assert: `success ≤ 5` and `inventory == 0`

**Expected JMeter Report**:
- 5 samples with HTTP 201 (`"order_id": ...`)
- 95 samples with HTTP 409 (`"insufficient stock"`)
- Final inventory query: stock = 0 (not -95)

**Run**:
```bash
# Python (unit-test style, no external deps):
python -m django test tests.stress_oversell --settings=config.settings.test

# JMeter (requires running server + Redis):
jmeter -n -t jmeter/01-OversellTest.jmx -l results-oversell.jtl
```

---

## 2. Distributed Caching (Redis)

**File**: `stress_cache.py`  
**JMeter**: `jmeter/02-CacheTest.jmx`  

**Proof Protocol**:
1. Ensure 50 products exist in DB
2. Clear Redis cache
3. Send 1000 `GET /api/products/` requests in 10 seconds
4. Measure latency of request #1 vs requests #2-#1000

**Expected JMeter Report**:
- First request: 100-300ms (cache miss, PostgreSQL query)
- All subsequent: <5ms (cache hit, Redis)
- Throughput: >500 req/s for cached requests

**Run**:
```bash
# Python:
python -m django test tests.stress_cache --settings=config.settings.test

# JMeter:
jmeter -n -t jmeter/02-CacheTest.jmx -l results-cache.jtl
```

---

## 3. Resource & Async Management (Celery)

**File**: `stress_async.py`  
**JMeter**: `jmeter/03-AsyncTest.jmx`  

**Proof Protocol**:
1. Create 100 users with cart items
2. Launch 100 concurrent checkout requests
3. Measure API response time (must be fast — Celery handles invoice/notify in BG)
4. Monitor CPU: Gunicorn (4 workers) + Celery (4 workers) must not hit 100%

**Expected**:
- 100/100 API calls return within 2000ms
- Celery workers process 100 invoices + 100 notifications in background
- CPU stays below 80% (Gunicorn workers=4 limits concurrency)

**Run**:
```bash
# Prerequisites: Redis + Celery worker running
celery -A config worker --loglevel=info --concurrency=4

# Python test:
python -m django test tests.stress_async --settings=config.settings.test

# JMeter:
jmeter -n -t jmeter/03-AsyncTest.jmx -l results-async.jtl
```

---

## Expected Proof Artifacts

| NFR | Tool | Artifact | Pass Criteria |
|-----|------|----------|--------------|
| No race condition | JMeter | `results-oversell.jtl` | Exactly 5/100 success. Inventory=0 |
| Caching | JMeter / Grafana | Latency graph | Hot requests <5ms avg |
| Resource mgmt | `top` / htop | CPU graph | Never 100% under 100 concurrent |
| Async queues | Celery logs | Worker stdout | 100 invoices + 100 notifications processed |
