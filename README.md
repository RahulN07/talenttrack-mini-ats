# TalentTrack Mini ATS

A mini Applicant Tracking System (ATS) built to manage candidate applications, track recruitment stages, and monitor hiring pipeline metrics through a dashboard.

## Features

- **Dashboard:** View total candidates and recruitment pipeline metrics.
- **Candidate Management:** Add, view, search, and filter candidates.
- **Stage Tracking:** Update candidate application stages.
- **Candidate Deletion:** Remove test or unwanted candidate records.
- **REST API:** Backend endpoints built with FastAPI.
- **Database:** PostgreSQL integration using SQLModel.
- **Database Migrations:** Alembic for managing schema changes.
- **Responsive Interface:** React-based frontend.

## Tech Stack

**Frontend**
- React
- Vite
- CSS
- Lucide React icons

**Backend**
- Python
- FastAPI
- SQLModel
- PostgreSQL
- Alembic

## Project Structure

```text
mini-ats/
├── backend/
│   ├── main.py
│   ├── alembic.ini
│   └── migrations/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10 or compatible version
- Node.js and npm
- PostgreSQL

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/RahulN07/talenttrack-mini-ats.git
cd talenttrack-mini-ats
```

### 2. Configure the backend

```bash
cd backend
python -m venv .venv
```

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the backend directory and configure your PostgreSQL connection using the variable name expected by the application.

**Never commit your `.env` file or database credentials.**

Run the database migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn main:app --reload
```

Backend API: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### 3. Configure the frontend

Open a second terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your terminal.

## API Capabilities

The backend supports candidate management, application-stage updates, candidate search and filtering, and dashboard metrics.

Use the interactive API documentation at `/docs` to explore the available endpoints.

## Future Improvements

- Candidate profile details and resume uploads
- Authentication and role-based access
- Recruitment analytics and reports
- Cloud deployment
- Automated tests and CI/CD

## Author

**Rahul Nayak**

GitHub: https://github.com/RahulN07

Project repository: https://github.com/RahulN07/talenttrack-mini-ats
