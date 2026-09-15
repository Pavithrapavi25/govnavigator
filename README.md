# 🇮🇳 GovNavigator

### AI-Powered Indian Government Service Navigator

GovNavigator is a full-stack web application that helps citizens discover and understand Indian government services, certificates, documents, schemes, eligibility requirements, and application procedures.

Instead of searching through multiple government websites, users can search for a service, select their state/UT, view relevant information, save important services, track their searches, and get AI-powered guidance.

> **Note:** GovNavigator is an independent prototype and is not affiliated with or operated by any Indian government department.

---

## 🌟 Features

### 🔎 Intelligent Government Service Search

* Natural-language search
* Exact service-name matching
* Keyword and phrase matching
* Search intent detection
* Synonym-based matching
* Relevance scoring
* State/UT filtering
* Top relevant results

### 🏛️ Government Service Coverage

* 36 States and Union Territories
* 22 major government-service categories
* 792 state/service records
* Official portal URLs for all service records
* 46 unique official government portals

### 🤖 AI Government Guidance

GovNavigator AI can help users understand:

* Which government service they may need
* Why the service may be relevant
* Common documents
* General application steps
* Important considerations

The AI is designed to avoid inventing government services, official URLs, fees, deadlines, or legal requirements.

### ⭐ Favorites

Users can:

* Save useful government services
* View saved services
* Remove services from favorites

### 🕘 Search History

Users can:

* View previous searches
* See matched services
* See match scores
* Delete individual history items
* Clear search history

### 📊 Search Analytics

The application provides:

* Total searches
* Successful searches
* Failed searches
* Search success rate
* Average match score
* Top queries
* Top services
* Top states
* Recent searches

### 🔐 Authentication

* User registration
* Secure login
* Password hashing with Argon2
* JWT-based authentication
* Protected user-specific features

### 🗄️ Production Database

* PostgreSQL
* SQLAlchemy ORM
* Neon PostgreSQL for cloud deployment
* Indexed service lookup for improved performance

### 🌐 Responsive Web Application

Designed for desktop and mobile-friendly use.

---

## 🧩 Application Flow

```text
User
  │
  ▼
Register / Login
  │
  ▼
Select State / UT
  │
  ▼
Search Government Service
  │
  ▼
Intelligent Matching
  │
  ├── Service Details
  ├── Eligibility
  ├── Documents
  ├── Steps
  └── Official Portal
  │
  ├── Favorite
  ├── Search History
  └── Analytics
  │
  ▼
AI Government Guidance
```

---

## 🛠️ Tech Stack

### Frontend

* React
* Vite
* JavaScript
* Axios
* CSS

### Backend

* Python
* FastAPI
* SQLAlchemy
* PyJWT
* pwdlib
* Argon2
* Google Gemini API

### Database

* PostgreSQL
* Neon PostgreSQL

### Deployment

* Render
* GitHub

---

## 🏗️ Architecture

```text
React + Vite Frontend
        │
        │ HTTP / REST API
        ▼
FastAPI Backend
        │
        ├──────────────► PostgreSQL / Neon
        │
        └──────────────► Gemini API
```

---

## 📁 Project Structure

```text
govnavigator/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed_data.py
│   ├── seed_services.py
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── .gitignore
├── README.md
└── ...
```

---

## 🚀 Live Demo

### Frontend

https://govnavigator.onrender.com

### Backend API

https://govnavigator-backend.onrender.com

### API Health Check

```text
https://govnavigator-backend.onrender.com/
```

Expected response:

```json
{
  "status": "online",
  "message": "GovNavigator AI backend is running.",
  "version": "5.2.0",
  "database": "postgresql"
}
```

---

## 💻 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Pavithrapavi25/govnavigator.git
cd govnavigator
```

### 2. Backend setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure environment variables

Create:

```text
backend/.env
```

Example:

```env
DATABASE_URL=your_postgresql_connection_string
JWT_SECRET=your_jwt_secret
GEMINI_API_KEY=your_gemini_api_key
APP_ENV=development
FRONTEND_URL=http://localhost:5173
```

Never commit real API keys, passwords, JWT secrets, or database credentials.

### 4. Start the backend

```powershell
uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

### 5. Frontend setup

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🗃️ Service Data Seeding

GovNavigator uses a dedicated service seeding script.

```powershell
cd backend
python seed_data.py
python seed_services.py
```

The production dataset is validated to contain:

```text
36 States/UTs
22 Services
792 State/Service Records
792 Records with Official URLs
0 Extra Service Records
```

---

## 🔐 Security

GovNavigator follows several security practices:

* Passwords are hashed using Argon2
* JWT authentication protects user-specific APIs
* Sensitive credentials are stored through environment variables
* API keys are not stored in source code
* User-specific favorites and search history require authentication
* Production database credentials are not committed to GitHub

---

## 🧪 Validation

The application has been tested across the major user workflow:

```text
Registration
      ↓
Login
      ↓
Service Search
      ↓
Service Details
      ↓
Favorite
      ↓
Search History
      ↓
Analytics
      ↓
Official Government Portal
      ↓
AI Guidance
```

The production database audit confirms:

```text
36/36 States and UTs ........ PASS
22/22 Services ............. PASS
792/792 Records ............ PASS
792/792 URLs ............... PASS
0 Extra Records ............ PASS
```

---

## ⚠️ Important Disclaimer

GovNavigator is an independent educational/prototype application.

Government services, requirements, fees, processing times, eligibility rules, and application procedures may change. Users should always verify the latest information through the relevant official government authority or portal before submitting an application.

GovNavigator does not submit government applications on behalf of users.

---

## 🎯 Future Improvements

Potential future enhancements include:

* Better multilingual support
* Telugu, Hindi and regional-language AI assistance
* More government services
* Improved government portal monitoring
* Automated URL health checks
* Advanced AI service recommendations
* Notifications and reminders
* Service comparison
* Accessibility improvements
* Production monitoring and observability

---

## 👩‍💻 Author

**Pavithra**

BE Graduate | AI & Data Science

Interested in:

* Data Science
* Artificial Intelligence
* Full-Stack Development
* Python
* SQL

---

## ⭐ Project Highlights

**GovNavigator demonstrates practical skills in:**

`React` • `FastAPI` • `Python` • `PostgreSQL` • `SQLAlchemy` • `JWT Authentication` • `REST APIs` • `AI Integration` • `Database Design` • `Search Algorithms` • `Cloud Deployment`

---

⭐ **If you find this project useful, consider giving the repository a star.**
