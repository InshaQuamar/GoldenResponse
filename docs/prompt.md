# Domain-Specific LLM Evaluation Prompt

## Prompt Category
Healthcare Infrastructure · MERN Stack · Full-Stack Engineering

---

## Purpose

This prompt is designed to evaluate and compare the capability of large language models (LLMs) on a realistic, complex, industry-grade software engineering task. It tests reasoning across system design, backend architecture, database modelling, real-time communication, frontend development, security, and DevOps — all within a single cohesive domain.

---

## Evaluation Constraints (Checkable)

An LLM response must satisfy **all** of the following to be considered complete:

1. **Functional completeness** — All five core modules must be implemented: Bed Management, Patient Admission, Staff Scheduling, Equipment Tracking, and Analytics Dashboard.
2. **Real-time requirement** — Socket.IO must be used for live bed status updates, shift change notifications, and critical shortage alerts. Polling is not acceptable.
3. **Security baseline** — JWT authentication, role-based access control (RBAC), bcrypt password hashing, API rate limiting, and input sanitisation must all be present.
4. **Schema correctness** — Every MongoDB schema must include all specified fields (see Core Requirements below). No field may be omitted or renamed without justification.
5. **Formatting requirement** — All API routes must be documented in a table listing method, endpoint, auth role required, and a one-line description. All MongoDB schemas must be shown as Mongoose schema definitions in fenced code blocks.
6. **Visualisation requirement** — The frontend dashboard must use Chart.js or Recharts for at minimum: bed occupancy trends, ICU utilisation, and staff workload distribution.
7. **Error handling** — The implementation must handle duplicate bed assignments, shift scheduling conflicts, and real-time connection failures with explicit error responses and logging middleware.

---

## The Prompt

---

### Hospital Bed and Resource Management System — MERN Stack

You are a senior MERN stack developer with 5+ years of experience in healthcare infrastructure. Your task is to design and implement a **scalable, real-time Hospital Bed and Resource Management System** for a multi-hospital healthcare network.

The platform must allow hospital administrators to monitor bed occupancy, manage staff shifts, track medical equipment, and respond to emergencies — all in real time.

---

### Context & Role

You are responsible for the full-stack architecture and implementation. The system must:

- Monitor hospital occupancy across multiple wards and hospital branches
- Track ICU bed capacity and ventilator availability
- Manage staff scheduling and detect shift conflicts automatically
- Provide real-time updates to all connected clients without page refresh
- Help hospitals optimise bed usage, reduce patient wait times, prevent resource shortages, and improve emergency response

---

### Objective

Develop a MERN stack application that:

- Tracks hospital bed availability in real time
- Manages staff shifts and schedules
- Logs patient intake and admission records
- Tracks medical equipment status and maintenance
- Displays occupancy analytics and shortage alerts on an admin dashboard

---

### Core Functional Requirements

#### 1. Hospital Bed Management

Implement functionality to track beds by availability and occupancy. Categorise beds as:

- ICU
- General Ward
- Emergency
- Private
- Ventilator Support

**Requirements:**
- Display live percentage of occupied and vacant beds per ward
- Prevent overbooking conflicts (a bed cannot be assigned to two patients simultaneously)
- Trigger an alert when bed availability drops below a configurable threshold
- Support real-time status updates pushed to all connected clients via Socket.IO

**Bed Schema (Mongoose):**

```js
{
  hospital_id:       ObjectId,   // ref: Hospital
  bed_id:            String,     // unique identifier
  ward_id:           ObjectId,   // ref: Ward
  bed_type:          String,     // enum: ICU | GENERAL | EMERGENCY | PRIVATE | VENTILATOR
  occupancy_status:  String,     // enum: VACANT | OCCUPIED | MAINTENANCE
  patient_id:        ObjectId,   // ref: Patient (nullable)
  admit_time:        Date,
  discharge_time:    Date
}
```

---

#### 2. Patient Intake & Admission Logs

Store and manage patient admission records in MongoDB.

**Patient Schema (Mongoose):**

```js
{
  patient_id:          String,   // unique
  patient_name:        String,
  age:                 Number,
  gender:              String,   // enum: MALE | FEMALE | OTHER
  symptoms:            [String],
  admission_priority:  String,   // enum: CRITICAL | HIGH | MEDIUM | LOW
  assigned_doctor:     ObjectId, // ref: Staff
  assigned_bed:        ObjectId, // ref: Bed
  discharge_status:    Boolean
}
```

**Requirements:**
- Validate all patient records before saving (required fields, type checks)
- Handle emergency admissions with priority override logic
- Maintain full admission history — records must never be hard-deleted

---

#### 3. Staff Shift & Scheduling Management

Develop a scheduling module covering Doctors, Nurses, Emergency Staff, and Technicians.

**Staff Schema (Mongoose):**

```js
{
  employee_id:         String,   // unique
  role:                String,   // enum: DOCTOR | NURSE | TECHNICIAN | EMERGENCY_STAFF
  department:          String,
  shift_start:         Date,
  shift_end:           Date,
  availability_status: String,   // enum: ON_SHIFT | OFF_SHIFT | ON_CALL
  assigned_patients:   [ObjectId] // ref: Patient
}
```

**Features:**
- Shift calendar management
- Automatic shift conflict detection (no staff member can be assigned overlapping shifts)
- Overtime tracking
- Real-time shift change notifications via Socket.IO

---

#### 4. Medical Equipment Tracking

Track critical hospital resources including: Ventilators, Oxygen Cylinders, ECG Machines, Wheelchairs, Defibrillators.

**Equipment Schema (Mongoose):**

```js
{
  equipment_id:          String,  // unique
  equipment_type:        String,
  availability_status:   String,  // enum: AVAILABLE | IN_USE | UNDER_MAINTENANCE
  maintenance_status:    String,  // enum: OK | DUE | OVERDUE
  assigned_department:   String,
  last_service_date:     Date
}
```

**Requirements:**
- Real-time availability updates pushed via Socket.IO
- Maintenance reminders when `last_service_date` exceeds a configurable interval
- Critical shortage alerts when available units of a type fall below threshold
- Full allocation tracking (which department has which equipment)

---

#### 5. Backend — Node.js + Express.js

Build a secure, scalable REST API. All routes must be documented in the following format:

| Method | Endpoint | Role Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/auth/login` | Public | Authenticate user, return JWT |
| POST | `/api/auth/register` | Admin | Register a new staff user |
| GET | `/api/beds` | Admin, Nurse | List all beds with current status |
| POST | `/api/beds/:id/allocate` | Admin, Nurse | Assign a patient to a bed |
| POST | `/api/beds/:id/discharge` | Admin, Nurse | Mark a bed as vacant |
| GET | `/api/patients` | Admin, Doctor | List all patient records |
| POST | `/api/patients` | Admin, Nurse | Create a new patient admission |
| GET | `/api/staff` | Admin | List all staff members |
| POST | `/api/staff` | Admin | Add a new staff member |
| PUT | `/api/staff/:id/shift` | Admin | Update shift assignment |
| GET | `/api/equipment` | Admin | List all equipment |
| PUT | `/api/equipment/:id` | Admin | Update equipment status |
| GET | `/api/stats` | Admin | Aggregated occupancy analytics |
| GET | `/api/alerts` | Admin, Nurse | List active shortage/critical alerts |

**API Requirements:**
- Full CRUD operations on all resources
- JWT authentication on all protected routes
- Role-based authorisation middleware (Admin / Doctor / Nurse / Technician)
- Request validation middleware (reject malformed payloads with descriptive errors)
- Centralised error handling middleware
- API rate limiting (100 requests / 15 min per IP)

---

#### 6. Database — MongoDB

Design optimised schemas for: Hospitals, Wards, Beds, Patients, Staff, Equipment, Alerts, Shift Schedules.

**Database requirements:**
- Proper indexing on frequently queried fields (`hospital_id`, `occupancy_status`, `bed_type`, `shift_start`)
- Aggregation pipelines for occupancy analytics and staff workload reports
- Efficient query design — avoid unbounded collection scans
- Schema must support multi-hospital data isolation

---

#### 7. Frontend — React.js

Build an interactive hospital administration dashboard.

**Dashboard features:**
- Live occupancy heatmap by ward and bed type
- ICU utilisation chart (Recharts or Chart.js — required)
- Staff shift calendar (React Calendar or equivalent)
- Resource shortage banners with severity levels
- Department-wise analytics panels
- Emergency alert notification centre
- Dark / light theme toggle

**UI components required:**
- Dynamic, sortable, filterable tables for beds, patients, staff, equipment
- Interactive shift calendar
- Search and filter system across all modules
- Responsive navigation sidebar
- Notification centre with unread count badge

**Visualisation requirements (all three are mandatory):**
- Bed occupancy trends over time (line or bar chart)
- Staff workload distribution by department (pie or bar chart)
- Equipment usage statistics (bar chart)

**Frontend tech stack:**
- React.js with functional components and hooks
- Redux Toolkit or Context API for global state
- Tailwind CSS or Material UI
- Axios for HTTP requests
- Socket.IO client for real-time updates
- Chart.js or Recharts for visualisations

---

#### 8. Security Requirements

Implement all of the following — none are optional:

- JWT authentication with token expiry and refresh strategy
- Role-based access control enforced at the middleware layer
- Bcrypt password hashing (minimum 10 salt rounds)
- API rate limiting via `express-rate-limit`
- Input sanitisation to prevent NoSQL injection and XSS
- Environment variable management via `.env` (no secrets in source code)

---

#### 9. Performance

Design the system to support multiple hospitals and thousands of concurrent users.

**Optimisation requirements:**
- Lazy loading for dashboard components
- Efficient Socket.IO room management (broadcast only to relevant clients)
- Optimised MongoDB queries with indexes and projection
- Pagination on all list endpoints (default page size: 20)

---

#### 10. Error Handling & Reliability

Implement robust handling for:

- Invalid admission attempts (missing required fields, invalid bed type)
- Duplicate bed assignments (bed already occupied)
- Shift scheduling conflicts (overlapping shifts for same employee)
- Missing patient records (graceful 404 with descriptive message)
- Real-time connection failures (reconnection logic on the client)

Provide:
- Logging middleware (Morgan or Winston) for all requests and errors
- Retry mechanisms for failed database operations
- Consistent API error response format:

```json
{
  "success": false,
  "error": {
    "code": "BED_ALREADY_OCCUPIED",
    "message": "Bed B-012 is currently occupied and cannot be assigned.",
    "timestamp": "2025-05-25T10:30:00Z"
  }
}
```

---

#### 11. Output Requirements

The platform must:

- Generate live hospital occupancy reports on the dashboard
- Display critical shortage alerts with severity classification
- Provide downloadable analytics reports (CSV or PDF)
- Export emergency resource summaries in JSON format
- Send in-app notifications for critical conditions (ICU full, ventilator shortage, etc.)

---

#### 12. DevOps & Deployment

Containerise and deploy the application using:

- **Docker** — separate containers for frontend, backend, and MongoDB
- **Docker Compose** — for local multi-container orchestration
- **GitHub Actions** — CI/CD pipeline for automated build, lint, and deploy
- **Cloud target** — AWS, Azure, or Google Cloud (choose one and justify)

Support:
- Environment-based configuration (development / staging / production)
- Production-ready deployment with health check endpoints
- Monitoring and logging integration (e.g., CloudWatch, Stackdriver, or equivalent)

---

### Deliverables

Provide the following in your response:

1. **System architecture diagram** (described in text or ASCII) showing frontend, backend, database, and WebSocket layers
2. **All Mongoose schemas** as fenced code blocks with field-level comments
3. **All API routes** documented in the table format specified above
4. **Core backend implementation** — Express server setup, auth middleware, at least one complete route handler per module
5. **Frontend dashboard structure** — component tree, state management approach, and at least one complete component with real-time Socket.IO integration
6. **Docker Compose file** for local development
7. **GitHub Actions workflow** for CI/CD
8. **Security checklist** confirming each security requirement is addressed and where in the codebase it is implemented

---

### Evaluation Criteria

Responses will be scored on:

| Criterion | Weight |
|---|---|
| Functional completeness (all modules present) | 25% |
| Code quality and architectural soundness | 20% |
| Real-time implementation correctness | 15% |
| Security implementation | 15% |
| Schema design and database optimisation | 10% |
| Frontend dashboard and visualisation | 10% |
| DevOps and deployment configuration | 5% |

A response that omits any of the seven checkable constraints listed at the top of this document is considered incomplete regardless of overall quality.
