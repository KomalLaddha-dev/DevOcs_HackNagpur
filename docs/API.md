# SmartCare API Documentation

## Overview

SmartCare provides a RESTful API for patient queue management, triage assessment, and healthcare scheduling.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.smartcare.health/v1
```

## Authentication

SmartCare uses JWT (JSON Web Tokens) for authentication.

### Getting a Token

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Authentication

#### Register
```http
POST /auth/register
```
Create a new user account.

#### Login
```http
POST /auth/login
```
Authenticate and receive tokens.

#### Refresh Token
```http
POST /auth/refresh
```
Get new access token using refresh token.

---

### Patients

#### Get Profile
```http
GET /patients/me
Authorization: Bearer <token>
```

#### Submit Symptoms
```http
POST /patients/symptoms
Authorization: Bearer <token>
Content-Type: application/json

{
  "symptoms": ["fever", "cough", "headache"],
  "description": "Having high fever since yesterday with persistent cough",
  "duration": "days",
  "severity_self_assessment": 6
}
```

Response:
```json
{
  "triage_score": 3,
  "severity_level": "Moderate",
  "recommended_action": "Standard queue - In-person consultation",
  "estimated_wait_time": 45,
  "priority_score": 60.5,
  "explanation": "Based on symptoms (fever, cough), assessed as moderate severity."
}
```

---

### Queue

#### Get Queue Status
```http
GET /queue
```

Returns current queue with all entries.

#### Check In
```http
POST /queue/checkin
Content-Type: application/json

{
  "patient_id": 123,
  "symptoms": "fever and cough"
}
```

#### Get Position
```http
GET /queue/position/{patient_id}
```

Response:
```json
{
  "patient_id": 123,
  "token_number": "SC202601310042",
  "position": 5,
  "estimated_wait_time": 45,
  "status": "waiting",
  "triage_score": 3,
  "priority_score": 60.5,
  "people_ahead": 4
}
```

---

### Doctors

#### List Doctors
```http
GET /doctors?specialty=general&available=true
```

#### Get Doctor Schedule
```http
GET /doctors/{doctor_id}/schedule
```

---

### Admin

#### Get Analytics
```http
GET /admin/analytics?date_from=2026-01-01&date_to=2026-01-31
Authorization: Bearer <admin_token>
```

Response:
```json
{
  "total_patients_today": 145,
  "total_appointments": 120,
  "average_wait_time": 23.5,
  "triage_distribution": {
    "1": 15,
    "2": 45,
    "3": 52,
    "4": 28,
    "5": 5
  }
}
```

---

## WebSocket API

### Queue Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/queue');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Queue updated:', data);
};
```

Events:
- `queue:updated` - Queue order changed
- `patient:called` - Patient called to consultation
- `doctor:available` - Doctor became available

---

## Error Responses

```json
{
  "detail": "Error message here"
}
```

Common HTTP Status Codes:
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Rate Limiting

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

---

## Versioning

API version is included in the URL path (`/api/v1/`). Breaking changes will result in a new version.
