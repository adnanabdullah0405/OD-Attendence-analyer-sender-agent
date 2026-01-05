
# Automated Attendance Summary Agent (LangGraph)

## Overview
This project is an agentic AI system that automates daily employee attendance reporting. The agent fetches attendance data from a Google Sheet, generates personalized attendance summaries, and emails each employee their daily attendance status.

This repository is a **public, sanitized version** of an internal HR automation system. All sensitive credentials, employee data, and company identifiers have been removed.

## Problem Solved
HR teams often spend time manually:
- Checking attendance sheets
- Preparing summaries
- Sending individual emails to employees

This agent fully automates the process, saving time and ensuring consistent communication.

## Workflow
1. Fetch attendance data from Google Sheets
2. Parse employee-wise attendance
3. Generate a concise attendance summary
4. Email personalized summaries to employees
5. Repeat automatically on a daily basis

## Architecture
- Agentic workflow orchestrated using **LangGraph**
- Modular steps for data fetch, processing, summarization, and email delivery

## Tech Stack
- Python
- LangGraph
- Google Sheets API
- SMTP (Email Automation)
- Environment-based secrets management

## Environment Variables
All sensitive values are stored in a `.env` file (not committed).

Example variables:
- Google Sheet ID
- HR email credentials
- SMTP configuration

See `.env.example` for required keys.

## Output
- Employees receive a daily email with their attendance summary
- HR gets a fully automated reporting pipeline

## Security Note
- `.env` is excluded via `.gitignore`
- Only sanitized logic is shared
- No real employee or company data is included

## Use Case
- HR Automation
- Internal Operations
- Enterprise AI Workflows
