# 📈 Portfolio Tracker (Backend-Focused System Design Project)

## 🎯 Objective

Build a scalable, low-latency portfolio tracking system that allows users to monitor real-time Profit & Loss (P&L) across multiple stocks without requiring authentication.

---

# 🚀 Core Features (Scope of Implementation)

## 1. Anonymous Portfolio Tracking

* Users can create portfolios without login
* Each user is identified using a UUID stored on client-side
* Backend persists data mapped to UUID

---

## 2. Real-Time P&L Computation

* Users input:

  * stock symbol
  * quantity
  * average buy price
* System computes:

  * invested value
  * current value (using live prices)
  * total P&L

---

## 3. Redis-Based Caching Layer

* Store stock prices in Redis
* Avoid calling external APIs per request

### Redis Keys

```
STOCK:{symbol} -> { price, last_updated }
FX:{base}_{target} -> rate
```

---

## 4. Background Worker (Price Aggregation)

* Runs periodically (every 5–10 seconds)
* Fetches prices from external API (e.g., Yahoo Finance)
* Updates Redis cache

---

## 5. Historical Portfolio Tracking

### Goal

Track portfolio performance over time

### Implementation

#### Table: portfolio_snapshots

```
id
portfolio_id
timestamp
total_value
invested_value
pnl
```

### Worker Job

* Runs daily (or hourly)
* Computes portfolio value
* Stores snapshot

---

## 6. Portfolio Insights

### Metrics

* Top gainer / loser
* Sector distribution
* Portfolio allocation

### Data Requirement

#### Table: stock_metadata

```
symbol
sector
industry
```

### Computation

* Aggregate stock values by sector
* Identify max/min P&L stocks

---

## 7. Multi-Currency Support

### Features

* Support INR and USD portfolios
* Normalize all values to portfolio currency

### Implementation

#### Add Fields

```
portfolio.currency
stock.currency
```

### Conversion Logic

```
if stock.currency != portfolio.currency:
    price = price * FX_rate
```

### FX Rate Caching

* Stored in Redis
* Updated periodically via worker

---

## 8. Shareable Portfolio Links

### Features

* Public read-only access

#### Table Changes

```
portfolio:
    public_id (unique)
    is_public (boolean)
```

### API

```
GET /public/portfolio/{public_id}
```

---

## 9. Import / Export (CSV)

### Import

* Upload CSV
* Parse and validate
* Bulk insert stocks

### CSV Format

```
symbol,quantity,avg_price
INFY,10,1500
```

### Export

* Download portfolio as CSV

---

# 🧱 System Architecture

```
Frontend (React)
      |
Backend API (FastAPI / Node)
      |
-----------------------------
| PostgreSQL | Redis        |
-----------------------------
      |
Background Worker
      |
External APIs (Stock + FX)
```

---

# ⚙️ Backend Responsibilities

## API Layer

* CRUD for portfolios and stocks
* Compute P&L using cached prices
* Serve insights and history

## Worker Layer

* Fetch stock prices
* Fetch FX rates
* Update Redis
* Store snapshots

## Database Layer

* Persistent storage (source of truth)

## Cache Layer

* Fast access to frequently used data

---

# ⚡ Caching Strategy

| Data Type         | Source       | TTL       |
| ----------------- | ------------ | --------- |
| Stock Price       | External API | 5–10 sec  |
| FX Rate           | External API | 1–5 min   |
| Portfolio Summary | Computed     | On update |

---

# 📊 API Design (High-Level)

### Portfolio

```
POST /portfolio
GET /portfolio/{id}
GET /portfolio/{id}/history
```

### Stocks

```
POST /stocks
PATCH /stocks
DELETE /stocks
```

### Public Access

```
GET /public/portfolio/{public_id}
```

### Import/Export

```
POST /portfolio/import
GET /portfolio/export
```

---

# 🧮 P&L Calculation Logic

```
invested = sum(quantity * avg_price)
current = sum(quantity * current_price)
pnl = current - invested
```

---

# 📦 Database Schema (Simplified)

## portfolio

```
id
user_id
name
currency
public_id
is_public
```

## stock

```
id
portfolio_id
symbol
quantity
avg_buy_price
currency
```

## portfolio_snapshots

```
id
portfolio_id
timestamp
total_value
```

## stock_metadata

```
symbol
sector
```

---

# 📈 Scaling Strategy (Step-by-Step)

## Level 1: Basic Scale (0–5K users)

* Single backend instance
* Redis caching
* Single worker

---

## Level 2: Moderate Scale (5K–50K users)

* Add load balancer
* Multiple backend instances
* Optimize DB queries (indexes)

---

## Level 3: High Scale (50K–1L users)

* Scale Redis (memory + throughput)
* Add multiple workers
* Add DB read replicas

---

## Level 4: Advanced Scale (Optional)

* WebSockets for live updates
* Event-driven architecture
* Precomputed portfolio summaries

---

# 🛠️ Tech Stack (Suggested)

* Backend: FastAPI / Node.js
* Database: PostgreSQL
* Cache: Redis
* Worker: Celery / Cron
* Frontend: React
* Deployment: Docker + Cloud (Render / AWS / Vercel)

---

# 🧠 Key Design Principles

* Cache-first architecture
* Avoid external API calls per request
* Stateless backend (horizontal scaling)
* Derived values computed at runtime
* Background processing for heavy tasks

---

# ✅ Expected Outcome

A production-ready backend system capable of:

* Handling thousands of concurrent users
* Delivering low-latency responses
* Efficiently managing external API dependencies
* Supporting extensibility for future features

---

# 📌 Notes for LLM Implementation

* Implement modular services (API, Worker, Cache)
* Use clean architecture (controllers, services, repositories)
* Prioritize Redis integration and background jobs
* Ensure proper error handling and retries
* Use environment variables for configs

---

# 🚀 Future Enhancements (Optional)

* Alerts system
* WebSocket-based real-time updates
* Broker integrations
* Tax calculations

---

End of README
