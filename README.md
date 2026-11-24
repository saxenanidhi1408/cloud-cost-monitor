# Cloud Cost Analysis and Budget Monitoring Tool

Minor Project, BCA, ITM University Gwalior (July-Dec 2026)
Guide: Mr. Manoj Kumar Sharma

A Python tool that reads cloud billing data, groups spend by service
category, detects cost spikes using statistics written from scratch, and
compares actual spend against a budget.

## Features
- Load billing CSV (date, service, cost) or use mock data
- Categories: Compute, Storage, Database, Network
- Anomaly detection: rolling Z-score and moving-average deviation
- Budget vs actual (monthly)
- Dashboard with charts and tables
- Export report as CSV and HTML

## Run locally
pip install -r requirements.txt
streamlit run app.py

## Live demo
https://share.streamlit.io/user/saxenanidhi1408

## Team
Nidhi Patel (BCAN1CA24097), Nidhi Saxena (BCAN1CA24098)
