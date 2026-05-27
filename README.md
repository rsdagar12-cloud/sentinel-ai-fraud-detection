# Sentinel AI Fraud Detection Dashboard

An AI-assisted retail loss prevention prototype that detects suspicious reseller and fraud patterns across store transactions.

## Business Problem

Retail teams often only see what happens inside their own store. Coordinated reseller activity can look normal at the individual transaction level, but suspicious when viewed across stores, products, payment methods, timestamps, and cashier notes.

Sentinel AI helps loss-prevention and operations teams connect those weak signals earlier.

## What It Does

- Repeated gift card usage
- Cross-store purchasing patterns
- High-demand product targeting
- Suspicious cashier notes
- Coordinated reseller behavior
- Store-level risk concentration

## Workflow

1. Load transaction data
2. Analyze transaction risk indicators
3. Identify suspicious individual transactions
4. Detect linked payment-method networks
5. Generate structured JSON and CSV outputs
6. Present results in an interactive dashboard
7. Include responsible AI notes for human review

## Key Features

- Streamlit web app
- CSV upload workflow
- Transaction-level risk scoring
- Store-level risk summary
- Suspected network detection
- JSON and CSV report downloads
- Responsible AI note for human review

## Outputs

- Sentinel.json
- Sentinel.csv
- Sentinel_Dashboard.html
- Streamlit app dashboard

## Run the App Locally

streamlit run app.py

## Expected CSV Columns

txn_id, store_id, products, quantity, payment_method, cashier_note

## Responsible AI

This prototype flags behavioral risk indicators only. It does not prove fraud or illegal activity. All outputs require human review before any action is taken.

## Project Story

I built an AI-assisted retail loss-prevention workflow that uses structured outputs, validation, dashboarding, and an interactive app to convert transaction-level signals into explainable risk intelligence.
