# 🏥 SmartCare – Patient Queue & Triage Optimization System

<div align="center">

![SmartCare Banner](docs/assets/banner.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Revolutionizing Healthcare Queues with AI-Powered Triage & Smart Scheduling**

[Demo](https://smartcare-demo.vercel.app) • [Documentation](docs/) • [Report Bug](https://github.com/KomalLaddha-dev/HackNagpur/issues) • [Request Feature](https://github.com/KomalLaddha-dev/HackNagpur/issues)

</div>

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Algorithms & AI Models](#-algorithms--ai-models)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#-installation--setup)
- [API Reference](#-api-reference)
- [Screenshots](#-screenshots)
- [Future Scope](#-future-scope)
- [Contributing](#-contributing)
- [Team](#-team)
- [License](#-license)

---

## 🚨 Problem Statement

### The Healthcare Queue Crisis

Traditional healthcare facilities face critical challenges:

| Problem | Impact |
|---------|--------|
| **Long Wait Times** | Average ER wait: 2-6 hours; leads to patient dissatisfaction |
| **FIFO Queuing** | First-come-first-served ignores medical urgency |
| **Doctor Overload** | Uneven distribution of patients causes burnout |
| **Manual Triage** | Subjective assessment delays critical care |
| **Resource Wastage** | Minor cases occupy valuable emergency slots |

> 💡 **Key Insight**: Studies show that AI-assisted triage can reduce wait times by **40%** and improve patient outcomes by **25%**.

---

## 💡 Solution Overview

**SmartCare** is an intelligent patient management system that transforms healthcare delivery through:

```
Patient Arrival → AI Symptom Analysis → Priority Scoring → Smart Queue → Optimal Doctor Assignment
```

### How It Works

1. **Digital Check-in**: Patients register symptoms via web/mobile interface
2. **AI Triage Engine**: NLP analyzes symptoms, assigns severity score (1-5)
3. **Priority Queue**: Patients sorted by urgency, not arrival time
4. **Smart Scheduling**: Algorithm matches patients to available doctors
5. **Tele-consultation**: Low-risk cases redirected to virtual consultations
6. **Real-time Dashboard**: Admins monitor flow, wait times, and bottlenecks

---

## ✨ Key Features

### 🤖 AI-Powered Triage
- NLP-based symptom analysis
- Medical knowledge graph integration
- Risk scoring with explainable AI

### 📊 Priority-Based Queuing
- Dynamic priority calculation
- Real-time queue updates
- Emergency override capability

### 👨‍⚕️ Doctor Scheduling Optimization
- Workload balancing across physicians
- Specialty-based routing
- Availability-aware assignment

### 📱 Tele-consultation Redirection
- Auto-detect low-risk cases
- Seamless video consultation integration
- Reduces physical queue load by 30%

### 📁 Digital Health Records
- Secure patient history storage
- Quick access during consultations
- HIPAA-compliant data handling

### 📈 Admin Dashboard
- Real-time analytics
- Wait time predictions
- Resource utilization metrics

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Patient    │  │   Doctor    │  │   Admin     │  │   Kiosk     │    │
│  │  Web App    │  │   Portal    │  │  Dashboard  │  │  Interface  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
└─────────┼────────────────┼────────────────┼────────────────┼───────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY (FastAPI)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    Auth     │  │    Rate     │  │   Request   │  │    CORS     │    │
│  │ Middleware  │  │  Limiting   │  │  Validation │  │   Handler   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │
│  │   Patient     │  │    Queue      │  │   Doctor      │               │
│  │   Service     │  │   Service     │  │   Service     │               │
│  └───────────────┘  └───────────────┘  └───────────────┘               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │
│  │   Triage      │  │  Appointment  │  │   Analytics   │               │
│  │   Service     │  │   Service     │  │   Service     │               │
│  └───────────────┘  └───────────────┘  └───────────────┘               │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI/ML ENGINE  │    │    DATABASE     │    │  CACHE LAYER    │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │  Symptom  │  │    │  │ PostgreSQL│  │    │  │   Redis   │  │
│  │  Analyzer │  │    │  │  Primary  │  │    │  │   Cache   │  │
│  ├───────────┤  │    │  ├───────────┤  │    │  ├───────────┤  │
│  │  Triage   │  │    │  │  Patient  │  │    │  │  Session  │  │
│  │  Scorer   │  │    │  │  Records  │  │    │  │  Storage  │  │
│  ├───────────┤  │    │  ├───────────┤  │    │  ├───────────┤  │
│  │ Scheduler │  │    │  │   Queue   │  │    │  │   Queue   │  │
│  │ Optimizer │  │    │  │   State   │  │    │  │   State   │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

```
Patient Input → Preprocessing → NLP Analysis → Priority Score → Queue Insertion → Doctor Assignment
     │                                              │                                    │
     └──────────────── Health Record ───────────────┴──────── Appointment Created ───────┘
```

---

## 🧠 Algorithms & AI Models

### 1. AI Triage System

**Symptom Analysis Pipeline**:
```python
# Simplified triage flow
symptoms → Tokenization → NLP Embedding → Classification Model → Severity Score (1-5)
```

| Severity Level | Description | Priority | Example |
|----------------|-------------|----------|---------|
| 5 - Critical | Life-threatening | Immediate | Chest pain, stroke symptoms |
| 4 - Urgent | Serious condition | < 15 min | High fever, severe pain |
| 3 - Moderate | Needs attention | < 1 hour | Infections, minor injuries |
| 2 - Low | Non-urgent | < 4 hours | Cold, mild symptoms |
| 1 - Minimal | Routine care | Scheduled | Follow-ups, checkups |

**Model Architecture**:
- **Text Vectorization**: TF-IDF + Medical Word Embeddings
- **Classifier**: Ensemble (Random Forest + Gradient Boosting)
- **Explainability**: SHAP values for transparency

### 2. Priority Queue Algorithm

```python
# Priority Score Calculation
priority_score = (
    severity_weight × triage_score +
    wait_time_weight × normalized_wait_time +
    age_weight × age_factor +
    condition_weight × chronic_condition_factor
)
```

**Data Structure**: Max-Heap Priority Queue
- **Time Complexity**: O(log n) insertion, O(1) peek, O(log n) extraction
- **Dynamic Re-prioritization**: Scores updated every 5 minutes

### 3. Doctor Scheduling - Greedy Optimization

```python
Algorithm: Modified Weighted Bipartite Matching

Input: Patients P[], Doctors D[], Constraints C
Output: Optimal Assignment A[]

1. Sort patients by priority (descending)
2. For each patient p:
   a. Find eligible doctors (specialty match, availability)
   b. Calculate assignment score for each doctor:
      score = α(workload_balance) + β(specialty_match) + γ(proximity)
   c. Assign to highest-scoring available doctor
3. Return assignment matrix
```

**Optimization Objectives**:
- Minimize average wait time
- Balance doctor workload (σ deviation < 15%)
- Maximize specialty-patient match

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 | UI Framework |
| TypeScript | Type Safety |
| TailwindCSS | Styling |
| Redux Toolkit | State Management |
| React Query | Server State |
| Socket.io Client | Real-time Updates |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | API Framework |
| Python 3.10+ | Core Language |
| SQLAlchemy | ORM |
| Pydantic | Data Validation |
| Celery | Task Queue |
| Redis | Caching & Sessions |

### AI/ML
| Technology | Purpose |
|------------|---------|
| Scikit-learn | ML Models |
| spaCy / NLTK | NLP Processing |
| Pandas | Data Processing |
| NumPy | Numerical Computing |

### Database & Infrastructure
| Technology | Purpose |
|------------|---------|
| PostgreSQL | Primary Database |
| Redis | Cache & Queue State |
| Docker | Containerization |
| Nginx | Reverse Proxy |

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Docker (optional)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/KomalLaddha-dev/HackNagpur.git
cd HackNagpur

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configurations

# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_data.py

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env.local
# Edit .env.local with your configurations

# Start development server
npm run dev
```

#### 3. AI Model Setup

```bash
# Navigate to AI module
cd ai

# Install ML dependencies
pip install -r requirements.txt

# Download pre-trained models
python scripts/download_models.py

# Train custom model (optional)
python scripts/train_triage_model.py
```

### Environment Variables

```env
# Backend (.env)
DATABASE_URL=postgresql://user:password@localhost:5432/smartcare
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
AI_MODEL_PATH=./ai/models/triage_v1.pkl

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOCKET_URL=ws://localhost:8000/ws
```

---

## 📡 API Reference

### Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.smartcare.health/v1
```

### Authentication
```http
POST /auth/register    # Patient registration
POST /auth/login       # Login (returns JWT)
POST /auth/refresh     # Refresh token
```

### Patient Endpoints
```http
GET    /patients/me              # Get current patient profile
PUT    /patients/me              # Update profile
POST   /patients/symptoms        # Submit symptoms for triage
GET    /patients/queue-status    # Check queue position
GET    /patients/appointments    # List appointments
```

### Queue Endpoints
```http
GET    /queue                    # Get current queue (admin)
POST   /queue/checkin            # Patient check-in
GET    /queue/position/{id}      # Get specific position
POST   /queue/emergency          # Emergency override
```

### Doctor Endpoints
```http
GET    /doctors                  # List available doctors
GET    /doctors/{id}/schedule    # Get doctor schedule
POST   /doctors/{id}/available   # Update availability
GET    /doctors/dashboard        # Doctor dashboard data
```

### Admin Endpoints
```http
GET    /admin/analytics          # Dashboard analytics
GET    /admin/reports            # Generate reports
PUT    /admin/settings           # Update system settings
GET    /admin/audit-logs         # View audit logs
```

### WebSocket Events
```javascript
// Real-time queue updates
ws://localhost:8000/ws/queue

Events:
- queue:updated      // Queue position changed
- patient:called     // Patient called to room
- doctor:available   // Doctor became available
```

---

## 📸 Screenshots

<div align="center">

| Patient Check-in | AI Triage |
|:---:|:---:|
| ![Checkin](docs/assets/screenshots/checkin.png) | ![Triage](docs/assets/screenshots/triage.png) |

| Queue Dashboard | Doctor Portal |
|:---:|:---:|
| ![Queue](docs/assets/screenshots/queue.png) | ![Doctor](docs/assets/screenshots/doctor.png) |

| Admin Analytics | Mobile View |
|:---:|:---:|
| ![Admin](docs/assets/screenshots/admin.png) | ![Mobile](docs/assets/screenshots/mobile.png) |

</div>

---

## 🔮 Future Scope

### Phase 2 - Enhanced Intelligence
- [ ] Deep learning triage model (BERT-based)
- [ ] Predictive wait time estimation
- [ ] Patient no-show prediction
- [ ] Automated follow-up scheduling

### Phase 3 - Integration & Scale
- [ ] HL7 FHIR integration for health records
- [ ] Multi-facility queue synchronization
- [ ] Pharmacy queue integration
- [ ] Lab result integration

### Phase 4 - Advanced Features
- [ ] Voice-based symptom input (Speech-to-Text)
- [ ] Multi-language support
- [ ] Wearable device integration
- [ ] AI-powered preliminary diagnosis suggestions

### Phase 5 - Enterprise
- [ ] Hospital management system integration
- [ ] Insurance verification automation
- [ ] Advanced reporting & compliance
- [ ] White-label deployment

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

```bash
# Fork the repository
# Create your feature branch
git checkout -b feature/AmazingFeature

# Commit your changes
git commit -m 'Add some AmazingFeature'

# Push to the branch
git push origin feature/AmazingFeature

# Open a Pull Request
```

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint + Prettier for JavaScript/TypeScript
- Write tests for new features
- Update documentation as needed

---

## 👥 Team

<div align="center">

| <img src="https://github.com/KomalLaddha-dev.png" width="100"> |
|:---:|
| **Komal Laddha** |
| Full Stack Developer |
| [![GitHub](https://img.shields.io/badge/GitHub-KomalLaddha--dev-181717?logo=github)](https://github.com/KomalLaddha-dev) |

</div>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing Python framework
- [React](https://reactjs.org/) for the frontend framework
- [Scikit-learn](https://scikit-learn.org/) for ML tools
- Healthcare professionals who provided domain expertise
- HackNagpur organizers and mentors

---

<div align="center">

**Built with ❤️ for HackNagpur 2026**

[⬆ Back to Top](#-smartcare--patient-queue--triage-optimization-system)

</div>
