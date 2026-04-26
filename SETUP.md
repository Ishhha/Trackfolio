# 🚀 Stock Portfolio Tracker Setup Instructions

This guide will walk you through the steps required to get the Stock Portfolio Tracker running on your local machine.

## Prerequisites
- **Python 3.10+** installed on your machine.
- **Git** (optional, for cloning the repository).
- **Postman** (for testing the API).

---

## 1. Environment Setup

It is highly recommended to use a virtual environment to manage your dependencies. 

Open your terminal (PowerShell or Command Prompt) and navigate to the project root directory (`stock_tracker`), then run:

```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

---

## 2. Install Dependencies

With your virtual environment activated, install all the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

*Note: The system uses local in-memory solutions (SQLite and CacheTools) so you do NOT need to install or run Redis, PostgreSQL, or Docker.*

---

## 3. Run the Application

Start the FastAPI application using Uvicorn. The `--reload` flag enables auto-reloading so the server automatically restarts when you make code changes.

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

If successful, you will see output indicating that the Uvicorn server is running at `http://127.0.0.1:8000`.

*Note: On the very first run, the system will automatically create the local `stock_tracker.db` SQLite database file in the root directory.*

---

## 4. Test the API

You can test the endpoints using **Postman**:

1. Open Postman.
2. Click **Import** (usually in the top left corner).
3. Select the `StockTracker.postman_collection.json` file located in the root of this project directory.
4. The collection uses variables to automatically save `PORTFOLIO_ID` and `STOCK_ID` when you create them, so you can easily run endpoints sequentially!
5. **Start by running the "Create Portfolio" request**, and then test the rest of the endpoints.

---

## 5. Explore the Documentation

FastAPI automatically generates interactive API documentation. While the server is running, you can view the Swagger UI in your browser at:
**[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
