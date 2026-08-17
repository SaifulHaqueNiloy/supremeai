"""SupremeAI Scraper Microservice — decoupled browser automation service.

Extracted from backend/tools/browser/ and backend/api/routes/browser.py.
Runs on Render free tier as a separate web service (port 8081).
Communicates with the main backend via Supabase ai_memory table.
"""
