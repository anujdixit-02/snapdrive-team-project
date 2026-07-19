# SnapDrive – Python Automation Module

**Branch:** `anuj-python-automation`

This branch contains my assigned contribution to the **SnapDrive – Cloud File Storage & Sharing Platform** developed during my **Cloud + Python Internship at SnapWeaz**.

> **Note:** This is not the complete project. It contains only the Python Automation module assigned to me. Other modules are being developed by different team members.

---

# Developer

**Name:** Anuj Dixit

**Role:** Cloud + Python Intern

**Module:** Python Automation

**GitHub:** https://github.com/anujdixit-02

**LinkedIn:** https://www.linkedin.com/in/anuj-dixit-6972793b3/

---

# Responsibilities

This branch includes the implementation of:

- File Upload Module
- File Download Module
- File Search Functionality
- Storage Management Logic
- Activity Logging
- Database Integration
- API Integration & Testing

---

# Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- REST APIs
- Git
- GitHub

---

# Project Structure

```text
.
├── activity_service.py
├── database.py
├── file_service.py
├── main.py
├── models.py
├── storage_service.py
├── requirements.txt
├── uploads/
├── snapdrive.db
└── README.md
```

---

# Features Implemented

## File Upload

- Upload files securely
- Validate supported file types
- Check file size limit
- Generate unique filenames
- Save metadata to the database

---

## File Download

- Download uploaded files
- Verify file exists
- Handle missing file errors

---

## File Search

- Search uploaded files
- User-specific search
- Ignore deleted files

---

## Storage Management

- Track storage usage
- Calculate remaining storage
- Enforce storage limits

Current Limits

- Maximum Storage per User: **1 GB**
- Maximum Upload Size: **50 MB**

---

## Activity Logging

Automatically records:

- File Upload
- File Download
- File Search
- Storage Operations

---

# Database

SQLite is used for development.

Tables:

- files
- activity_logs

SQLAlchemy ORM is used for database operations.

---

# How to Run

## Clone Repository

```bash
git clone https://github.com/anujdixit-02/snapdrive-team-project.git
```

## Switch to Branch

```bash
git checkout anuj-python-automation
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
uvicorn main:app --reload
```

Open the following URL in your browser:

```
http://127.0.0.1:8000/docs
```

Swagger UI will be available for testing the APIs.

---

# API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/upload` | Upload File |
| GET | `/download/{id}` | Download File |
| GET | `/search` | Search Files |
| GET | `/storage` | Storage Details |

---
