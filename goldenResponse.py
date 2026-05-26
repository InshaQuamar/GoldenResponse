import os
import sys
import json
import time
import datetime
import hmac
import hashlib
import base64
import random
from typing import List, Dict, Any, Optional

# Attempt to import FastAPI and Uvicorn. 
# If they are not installed, we provide a clean message to the user.
try:
    from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
except ImportError:
    print("\n[!] Error: 'fastapi' and 'uvicorn' are required to run this full-stack Python application.")
    print("[*] Please install them using the following command:")
    print("    pip install fastapi uvicorn\n")
    sys.exit(1)

# Initialize FastAPI App
app = FastAPI(
    title="MedCore HBRMS - Python Edition",
    description="Enterprise Hospital Bed & Resource Management System translated completely to Python FastAPI + WebSockets.",
    version="1.0.0"
)

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Cryptographic Security (JWT & PBKDF2 Hashing in Pure Python)
# ---------------------------------------------------------
JWT_SECRET = os.environ.get("JWT_SECRET", "super_secure_enterprise_secret_key_2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours

def base64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').replace('=', '')

def base64_url_decode(data: str) -> bytes:
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def generate_jwt(payload: dict) -> str:
    """Generates a secure HMAC-SHA256 signature token following the JWT specification."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64_url_encode(json.dumps(header).encode('utf-8'))
    
    # Append expiration timestamp
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + JWT_EXPIRY_SECONDS
    payload_b64 = base64_url_encode(json.dumps(payload_copy).encode('utf-8'))
    
    signature_base = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), signature_base, hashlib.sha256).digest()
    signature_b64 = base64_url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def verify_jwt(token: str) -> Optional[dict]:
    """Verifies the token signature and expiration, returning the payload if valid."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        
        signature_base = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), signature_base, hashlib.sha256).digest()
        expected_sig_b64 = base64_url_encode(expected_sig)
        
        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return None
            
        payload = json.loads(base64_url_decode(payload_b64).decode('utf-8'))
        if "exp" in payload and payload["exp"] < time.time():
            return None  # Token expired
        return payload
    except Exception:
        return None

def hash_password(password: str) -> str:
    """Generates a secure PBKDF2-HMAC-SHA256 hash using 100,000 rounds and a random 16-byte salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(password: str, hashed_str: str) -> bool:
    """Verifies a password against the PBKDF2 hash using timing-safe comparison."""
    try:
        salt_hex, key_hex = hashed_str.split(':')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False

# ---------------------------------------------------------
# Rate Limiting Middleware (100 requests / 15 minutes per IP)
# ---------------------------------------------------------
rate_limit_store = {}
RATE_LIMIT_WINDOW = 15 * 60  # 15 minutes in seconds
RATE_LIMIT_MAX = 100

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    
    # Only rate limit API endpoints
    if request.url.path.startswith("/api/"):
        now = time.time()
        
        if client_ip not in rate_limit_store:
            rate_limit_store[client_ip] = []
            
        # Filter out timestamps older than the window
        rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW]
        
        if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "TOO_MANY_REQUESTS",
                        "message": "Too many requests from this IP, please try again after 15 minutes.",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                    }
                }
            )
        rate_limit_store[client_ip].append(now)
        
    return await call_next(request)

# Helper to generate formatted error response
def make_error_response(code: str, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        }
    )

# ---------------------------------------------------------
# Mock Database Layer (Beds, Users, Staff, Equipment)
# ---------------------------------------------------------
# Initial pre-hashed admin credentials
mock_users = [
    {
        "username": "admin",
        "password": hash_password("admin123"),
        "role": "admin",
        "name": "Admin User"
    }
]

# Generate mock hospital beds
mock_beds = []
random.seed(42)  # Consistent generation
for i in range(40):
    bed_type = "ICU" if i < 10 else "GENERAL" if i < 25 else "EMERGENCY" if i < 35 else "VENTILATOR"
    occupancy = "OCCUPIED" if random.random() > 0.45 else "VACANT"
    ward = "Intensive Care Unit" if bed_type in ["ICU", "VENTILATOR"] else "General Ward" if bed_type == "GENERAL" else "Emergency Wing"
    mock_beds.append({
        "_id": f"bed_{i+1:03d}",
        "bed_number": f"B-{i+1:03d}",
        "bed_type": bed_type,
        "occupancy_status": occupancy,
        "ward": ward,
        "updatedAt": datetime.datetime.utcnow().isoformat() + "Z"
    })

# Pre-populated staff scheduling roster
mock_staff = [
    {"id": "ST-001", "name": "Dr. Jane Doe", "role": "DOCTOR", "department": "Emergency", "status": "ON_SHIFT", "shift": "08:00 - 16:00"},
    {"id": "ST-002", "name": "Dr. John Smith", "role": "DOCTOR", "department": "ICU", "status": "OFF_SHIFT", "shift": "16:00 - 00:00"},
    {"id": "ST-003", "name": "Sarah Connor", "role": "NURSE", "department": "ICU", "status": "ON_SHIFT", "shift": "08:00 - 20:00"},
    {"id": "ST-004", "name": "Michael Chang", "role": "NURSE", "department": "General", "status": "ON_SHIFT", "shift": "08:00 - 16:00"},
    {"id": "ST-005", "name": "Emily Davis", "role": "DOCTOR", "department": "Surgery", "status": "ON_CALL", "shift": "24h Shift"},
    {"id": "ST-006", "name": "Robert Wilson", "role": "TECHNICIAN", "department": "Radiology", "status": "OFF_SHIFT", "shift": "08:00 - 16:00"}
]

# Pre-populated medical equipment roster
mock_equipment = [
    {"id": "EQ-001", "name": "Ventilator V-800", "type": "Ventilator Support", "location": "ICU-A", "status": "IN_USE", "condition": "GOOD", "nextMaintenance": "2026-07-15"},
    {"id": "EQ-002", "name": "Defibrillator D-20", "type": "Defibrillator", "location": "ER-Bay-2", "status": "STANDBY", "condition": "GOOD", "nextMaintenance": "2026-06-20"},
    {"id": "EQ-003", "name": "Portable X-Ray", "type": "ECG/Imaging", "location": "Radiology", "status": "MAINTENANCE", "condition": "REPAIR", "nextMaintenance": "2026-06-01"},
    {"id": "EQ-004", "name": "Patient Monitor PM-1", "type": "Oxygen Cylinder/Monitor", "location": "ICU-B", "status": "IN_USE", "condition": "GOOD", "nextMaintenance": "2026-08-10"},
    {"id": "EQ-005", "name": "Ventilator V-800", "type": "Ventilator Support", "location": "Storage-East", "status": "STANDBY", "condition": "NOTICE", "nextMaintenance": "2026-06-30"},
    {"id": "EQ-006", "name": "Infusion Pump", "type": "Other", "location": "Gen-01", "status": "IN_USE", "condition": "GOOD", "nextMaintenance": "2026-09-05"}
]

# ---------------------------------------------------------
# WebSocket Connection Manager (Real-time Broadcaster)
# ---------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                # Remove stale/broken connections
                self.disconnect(connection)

ws_manager = ConnectionManager()

# ---------------------------------------------------------
# JWT Route Verification Dependency
# ---------------------------------------------------------
def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header scheme. Expected 'Bearer <token>'."
        )
    token = auth_header.split(" ")[1]
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token verification failed."
        )
    return payload

# ---------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------
@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "Python FastAPI", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}

@app.post("/api/auth/register")
def register(payload: dict):
    name = payload.get("name")
    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role", "nurse")
    
    if not username or not password:
        return make_error_response("MALFORMED_PAYLOAD", "Username and password are required.", 400)
        
    # Check if user already exists
    if any(u["username"] == username for u in mock_users):
        return make_error_response("USER_EXISTS", "Username already exists in system database.", 400)
        
    new_user = {
        "username": username,
        "password": hash_password(password),
        "role": role,
        "name": name if name else username.capitalize()
    }
    mock_users.append(new_user)
    
    token = generate_jwt({"username": username, "role": role})
    return {
        "success": True,
        "token": token,
        "user": {"username": username, "role": role, "name": new_user["name"]}
    }

@app.post("/api/auth/login")
def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")
    
    user = next((u for u in mock_users if u["username"] == username), None)
    if user and verify_password(password, user["password"]):
        token = generate_jwt({"username": username, "role": user["role"]})
        return {
            "success": True,
            "token": token,
            "user": {"username": user["username"], "role": user["role"], "name": user["name"]}
        }
    else:
        return make_error_response("INVALID_CREDENTIALS", "Invalid username or password credentials.", 401)

@app.get("/api/stats")
def get_stats(user: dict = Depends(get_current_user)):
    total = len(mock_beds)
    occupied = len([b for b in mock_beds if b["occupancy_status"] == "OCCUPIED"])
    
    icu_beds = [b for b in mock_beds if b["bed_type"] == "ICU"]
    icu_total = len(icu_beds)
    icu_occupied = len([b for b in icu_beds if b["occupancy_status"] == "OCCUPIED"])
    
    ventilators = [b for b in mock_beds if b["bed_type"] == "VENTILATOR"]
    vent_total = len(ventilators)
    vent_occupied = len([b for b in ventilators if b["occupancy_status"] == "OCCUPIED"])
    
    return {
        "totalBeds": total,
        "occupiedBeds": occupied,
        "vacantBeds": total - occupied,
        "occupancyRate": int((occupied / total) * 100) if total > 0 else 0,
        "icuTotal": icu_total,
        "icuOccupied": icu_occupied,
        "icuVacant": icu_total - icu_occupied,
        "icuOccupancyRate": int((icu_occupied / icu_total) * 100) if icu_total > 0 else 0,
        "ventilatorTotal": vent_total,
        "ventilatorOccupied": vent_occupied,
        "ventilatorVacant": vent_total - vent_occupied
    }

@app.get("/api/beds")
def list_beds(user: dict = Depends(get_current_user)):
    return mock_beds

@app.post("/api/beds/{bed_id}/allocate")
async def allocate_bed(bed_id: str, user: dict = Depends(get_current_user)):
    # Check permissions
    if user.get("role") not in ["admin", "doctor", "nurse"]:
        raise HTTPException(status_code=403, detail="Unauthorized role permission.")
        
    bed = next((b for b in mock_beds if b["_id"] == bed_id), None)
    if not bed:
        return make_error_response("BED_NOT_FOUND", f"Bed with ID {bed_id} does not exist.", 404)
        
    if bed["occupancy_status"] == "OCCUPIED":
        return make_error_response("BED_ALREADY_OCCUPIED", f"Bed {bed['bed_number']} is currently occupied.", 400)
        
    bed["occupancy_status"] = "OCCUPIED"
    bed["updatedAt"] = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Push update real-time via WebSockets
    await ws_manager.broadcast({"type": "bedUpdated", "bed": bed})
    return bed

@app.post("/api/beds/{bed_id}/discharge")
async def discharge_bed(bed_id: str, user: dict = Depends(get_current_user)):
    # Check permissions
    if user.get("role") not in ["admin", "doctor", "nurse"]:
        raise HTTPException(status_code=403, detail="Unauthorized role permission.")
        
    bed = next((b for b in mock_beds if b["_id"] == bed_id), None)
    if not bed:
        return make_error_response("BED_NOT_FOUND", f"Bed with ID {bed_id} does not exist.", 404)
        
    if bed["occupancy_status"] == "VACANT":
        return make_error_response("BED_ALREADY_VACANT", f"Bed {bed['bed_number']} is already vacant.", 400)
        
    bed["occupancy_status"] = "VACANT"
    bed["updatedAt"] = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Push update real-time via WebSockets
    await ws_manager.broadcast({"type": "bedUpdated", "bed": bed})
    return bed

@app.get("/api/staff")
def list_staff(user: dict = Depends(get_current_user)):
    return mock_staff

@app.get("/api/equipment")
def list_equipment(user: dict = Depends(get_current_user)):
    return mock_equipment

# ---------------------------------------------------------
# WebSocket Connection Handler
# ---------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for client-sent pings
            data = await websocket.receive_text()
            # Just echoes back pings or handles client messages
            await websocket.send_json({"status": "received", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# ---------------------------------------------------------
# Single Page App (HTML, CSS, Alpine JS, Chart JS) Rendering
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MedCore HBRMS - Hospital Bed & Resource Management System</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Google Font Outfit -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Alpine JS CDN -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <!-- Chart JS CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Lucide Icons CDN -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body {
            font-family: 'Outfit', sans-serif;
        }
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen antialiased selection:bg-blue-600 selection:text-white" x-data="app" x-cloak>
    
    <!-- Login / Registration Page -->
    <div x-show="!isAuthenticated" class="min-h-screen bg-slate-950 flex items-center justify-center p-6 relative overflow-hidden">
        <!-- Background accents -->
        <div class="absolute w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -top-12 -left-12"></div>
        <div class="absolute w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -bottom-12 -right-12"></div>
        
        <div class="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl relative z-10">
            <div class="flex flex-col items-center mb-8">
                <div class="h-12 w-12 bg-blue-600/20 text-blue-500 rounded-2xl flex items-center justify-center border border-blue-500/30 mb-3 animate-pulse">
                    <i data-lucide="heart-pulse" class="w-7 h-7"></i>
                </div>
                <h1 class="text-2xl font-extrabold text-white tracking-tight">MedCore HBRMS</h1>
                <p class="text-slate-400 text-sm mt-1">Enterprise Resource Portal Access</p>
            </div>
            
            <!-- Login Form -->
            <div x-show="authTab === 'login'" class="space-y-5">
                <div x-show="loginError" class="p-3 bg-red-950/40 border border-red-800/40 text-red-400 rounded-xl text-xs font-semibold" x-text="loginError"></div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Username</label>
                    <input type="text" x-model="username" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" placeholder="admin">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Password</label>
                    <input type="password" x-model="password" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" placeholder="••••••••">
                </div>
                <button @click="login()" class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold tracking-wide transition-all shadow-lg shadow-blue-600/20 active:scale-[0.98]">
                    Authenticate
                </button>
                <div class="text-center mt-6">
                    <span class="text-xs text-slate-500">Need new credentials? <a @click="authTab = 'register'" class="text-blue-500 hover:underline cursor-pointer">Register here</a></span>
                </div>
            </div>

            <!-- Registration Form -->
            <div x-show="authTab === 'register'" class="space-y-5">
                <div x-show="registerError" class="p-3 bg-red-950/40 border border-red-800/40 text-red-400 rounded-xl text-xs font-semibold" x-text="registerError"></div>
                <div x-show="registerSuccess" class="p-3 bg-green-950/40 border border-green-800/40 text-green-400 rounded-xl text-xs font-semibold" x-text="registerSuccess"></div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Full Name</label>
                    <input type="text" x-model="registerName" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" placeholder="Dr. John Doe">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Username</label>
                    <input type="text" x-model="registerUsername" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" placeholder="johndoe">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Password</label>
                    <input type="password" x-model="registerPassword" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" placeholder="••••••••">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">System Role</label>
                    <select x-model="registerRole" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all">
                        <option value="admin">Administrator</option>
                        <option value="doctor">Lead Doctor</option>
                        <option value="nurse">Nurse Officer</option>
                    </select>
                </div>
                <button @click="register()" class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold tracking-wide transition-all shadow-lg active:scale-[0.98]">
                    Register Access
                </button>
                <div class="text-center mt-6">
                    <span class="text-xs text-slate-500">Back to <a @click="authTab = 'login'" class="text-blue-500 hover:underline cursor-pointer">Login Screen</a></span>
                </div>
            </div>
        </div>
    </div>

    <!-- Dashboard App Dashboard -->
    <div x-show="isAuthenticated" class="min-h-screen bg-slate-950 flex overflow-hidden">
        
        <!-- Sidebar Navigation -->
        <aside class="w-64 bg-slate-900 border-r border-slate-800 flex flex-col hidden md:flex h-screen shrink-0">
            <div class="h-16 flex items-center px-6 border-b border-slate-800 shrink-0">
                <div class="p-1.5 bg-blue-600/20 text-blue-500 border border-blue-500/20 rounded-lg mr-3">
                    <i data-lucide="heart-pulse" class="w-5 h-5"></i>
                </div>
                <span class="text-lg font-bold tracking-tight text-white">MedCore HBRMS</span>
            </div>
            
            <div class="p-4 flex-1 overflow-y-auto space-y-1">
                <button @click="activeTab = 'dashboard'" :class="activeTab === 'dashboard' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'" class="w-full flex items-center px-4 py-3 rounded-xl transition-colors font-medium">
                    <i data-lucide="layout-dashboard" class="w-5 h-5 mr-3"></i>
                    <span>Overview</span>
                </button>
                <button @click="activeTab = 'beds'" :class="activeTab === 'beds' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'" class="w-full flex items-center px-4 py-3 rounded-xl transition-colors font-medium">
                    <i data-lucide="bed" class="w-5 h-5 mr-3"></i>
                    <span>Bed Allocation</span>
                </button>
                <button @click="activeTab = 'staff'" :class="activeTab === 'staff' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'" class="w-full flex items-center px-4 py-3 rounded-xl transition-colors font-medium">
                    <i data-lucide="users" class="w-5 h-5 mr-3"></i>
                    <span>Personnel</span>
                </button>
                <button @click="activeTab = 'equipment'" :class="activeTab === 'equipment' ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20 font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'" class="w-full flex items-center px-4 py-3 rounded-xl transition-colors font-medium">
                    <i data-lucide="activity" class="w-5 h-5 mr-3"></i>
                    <span>Equipment</span>
                </button>
            </div>

            <!-- Profile Info -->
            <div class="p-6 border-t border-slate-800 flex items-center space-x-3 bg-slate-900/50">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white text-sm" x-text="userInitials"></div>
                <div class="flex flex-col">
                    <span class="text-sm font-semibold text-white" x-text="user.name"></span>
                    <span class="text-[10px] text-slate-500 uppercase tracking-widest font-bold" x-text="user.role"></span>
                </div>
            </div>
        </aside>

        <!-- Main Content Roster -->
        <main class="flex-1 flex flex-col h-screen overflow-hidden">
            <!-- Header -->
            <header class="h-16 bg-slate-900 border-b border-slate-800 px-8 flex items-center justify-between shrink-0 relative z-10">
                <div class="flex items-center">
                    <button class="md:hidden text-slate-400 hover:text-slate-200 mr-4">
                        <i data-lucide="menu" class="w-6 h-6"></i>
                    </button>
                    <div class="relative hidden sm:block">
                        <i data-lucide="search" class="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2"></i>
                        <input type="text" x-model="searchTerm" placeholder="Search beds, staff or serials..." class="pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-full text-xs w-64 md:w-80 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all">
                    </div>
                </div>

                <div class="flex items-center space-x-6">
                    <div class="flex items-center">
                        <span :class="isConnected ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'" class="px-3 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider flex items-center space-x-1.5">
                            <span :class="isConnected ? 'bg-green-500 animate-ping' : 'bg-red-500'" class="w-1.5 h-1.5 rounded-full inline-block mr-1.5"></span>
                            <span x-text="isConnected ? 'System Live' : 'Offline'"></span>
                        </span>
                    </div>

                    <!-- Alert Indicator -->
                    <div class="flex items-center space-x-1 text-red-500 cursor-pointer hover:opacity-80">
                        <i data-lucide="alert-triangle" class="w-4 h-4 mr-1"></i>
                        <span class="text-xs font-bold uppercase tracking-wider">Critical Alerts</span>
                    </div>

                    <!-- Notifications Dropdown Trigger -->
                    <div class="relative">
                        <button @click="showNotifications = !showNotifications" class="text-slate-400 hover:text-white transition-colors relative mt-1.5">
                            <i data-lucide="bell" class="w-5 h-5"></i>
                            <span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-600 rounded-full"></span>
                        </button>
                        
                        <div x-show="showNotifications" @click.away="showNotifications = false" class="absolute right-0 mt-3 w-80 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50">
                            <div class="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
                                <h3 class="font-bold text-white">Critical Alerts Feed</h3>
                                <span class="text-[10px] text-blue-400 font-bold hover:underline cursor-pointer">Clear items</span>
                            </div>
                            <div class="max-h-80 overflow-y-auto divide-y divide-slate-800/50">
                                <template x-for="alert in alerts">
                                    <div class="p-4 hover:bg-slate-800/30 transition-colors">
                                        <div class="flex items-start">
                                            <div :class="alert.severity === 'CRITICAL' ? 'bg-red-500' : 'bg-amber-500'" class="flex-shrink-0 w-2 h-2 mt-2 rounded-full mr-3"></div>
                                            <div>
                                                <p class="text-xs font-bold text-white" x-text="alert.title"></p>
                                                <p class="text-[10px] text-slate-400 mt-1" x-text="alert.desc"></p>
                                                <span class="text-[9px] text-slate-500 mt-2 block font-medium uppercase" x-text="alert.time"></span>
                                            </div>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </div>

                    <!-- Logout Button -->
                    <button @click="logout()" class="text-slate-400 hover:text-red-400 border-l border-slate-800 pl-6 flex items-center transition-colors font-semibold text-xs uppercase tracking-wider">
                        <i data-lucide="log-out" class="w-4 h-4 mr-2"></i>
                        <span>Exit</span>
                    </button>
                </div>
            </header>

            <!-- Main Canvas Roster -->
            <div class="flex-1 overflow-auto p-8 bg-slate-950">
                <div class="max-w-7xl mx-auto space-y-6">
                    
                    <!-- Overview Dashboard Tab -->
                    <div x-show="activeTab === 'dashboard'" class="space-y-6">
                        <div class="flex items-center justify-between">
                            <div>
                                <h1 class="text-2xl font-extrabold text-white tracking-tight">System Roster Overview</h1>
                                <p class="text-slate-400 text-xs mt-1">Consolidated realtime hospital capacity and scheduling parameters.</p>
                            </div>
                        </div>

                        <!-- Highlight Statistics Cards -->
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <div class="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-sm">
                                <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Total Bed Occupancy</p>
                                <div class="mt-4 flex items-baseline justify-between">
                                    <h2 class="text-3xl font-black text-white" x-text="stats.occupancyRate + '%'"></h2>
                                    <span class="text-blue-400 font-bold text-xs bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 flex items-center">
                                        <i data-lucide="arrow-up-right" class="w-3 h-3 mr-0.5"></i> 2.1%
                                    </span>
                                </div>
                                <div class="mt-4 w-full h-2 bg-slate-850 rounded-full overflow-hidden">
                                    <div class="h-full bg-blue-500 transition-all duration-500" :style="'width: ' + stats.occupancyRate + '%'"></div>
                                </div>
                            </div>
                            <div class="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-sm">
                                <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">ICU Bed Utilization</p>
                                <div class="mt-4 flex items-baseline justify-between">
                                    <h2 class="text-3xl font-black text-white" x-text="stats.icuOccupied + ' / ' + stats.icuTotal"></h2>
                                    <span :class="stats.icuOccupancyRate > 80 ? 'text-red-400 bg-red-500/10 border-red-500/20' : 'text-orange-400 bg-orange-500/10 border-orange-500/20'" class="text-xs font-bold px-2 py-0.5 rounded border" x-text="stats.icuOccupancyRate + '% Used'"></span>
                                </div>
                                <div class="mt-4 w-full h-2 bg-slate-850 rounded-full overflow-hidden">
                                    <div class="h-full transition-all duration-500" :class="stats.icuOccupancyRate > 80 ? 'bg-red-500' : 'bg-orange-500'" :style="'width: ' + stats.icuOccupancyRate + '%'"></div>
                                </div>
                            </div>
                            <div class="bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-sm">
                                <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Staff On Shift</p>
                                <div class="mt-4 flex items-baseline justify-between">
                                    <h2 class="text-3xl font-black text-white" x-text="activeStaffCount"></h2>
                                    <span class="text-slate-400 font-bold text-xs bg-slate-800 px-2 py-0.5 rounded">Active</span>
                                </div>
                                <div class="mt-4 flex -space-x-2">
                                    <img class="w-8 h-8 rounded-xl border-2 border-slate-900" src="https://ui-avatars.com/api/?name=Jane+Doe&background=eff6ff&color=1d4ed8" alt="Jane">
                                    <img class="w-8 h-8 rounded-xl border-2 border-slate-900" src="https://ui-avatars.com/api/?name=John+Smith&background=f0fdf4&color=15803d" alt="John">
                                    <img class="w-8 h-8 rounded-xl border-2 border-slate-900" src="https://ui-avatars.com/api/?name=Sarah+Connor&background=fef2f2&color=b91c1c" alt="Sarah">
                                    <div class="w-8 h-8 rounded-xl bg-slate-850 border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-slate-400">+3</div>
                                </div>
                            </div>
                            <div class="bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl p-6 shadow-lg text-white">
                                <p class="text-xs font-bold uppercase opacity-85 tracking-widest">Intake Protocols</p>
                                <div class="mt-3">
                                    <h2 class="text-2xl font-black">Nominal State</h2>
                                    <p class="text-[11px] mt-1 font-medium opacity-75">Diversion metrics and resource configurations active.</p>
                                </div>
                                <button class="mt-4 w-full py-2 bg-white/10 hover:bg-white/20 rounded-xl text-[11px] font-bold tracking-wide transition-all">Emergency Response Plan</button>
                            </div>
                        </div>

                        <!-- Graphical Panels -->
                        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                            <div class="col-span-1 lg:col-span-8 bg-slate-900 rounded-3xl border border-slate-800 shadow-sm p-6 flex flex-col h-[380px]">
                                <h3 class="font-bold text-white text-sm mb-4">Live Bed Utilization Trends</h3>
                                <div class="flex-1 w-full relative">
                                    <canvas id="admissionTrendsChart"></canvas>
                                </div>
                            </div>
                            <div class="col-span-1 lg:col-span-4 bg-slate-900 rounded-3xl border border-slate-800 shadow-sm p-6 flex flex-col h-[380px]">
                                <h3 class="font-bold text-white text-sm mb-4">Capacity Shares</h3>
                                <div class="flex-1 w-full relative flex items-center justify-center">
                                    <canvas id="capacityPieChart"></canvas>
                                    <div class="absolute flex flex-col items-center">
                                        <span class="text-3xl font-black text-white" x-text="stats.occupancyRate + '%'"></span>
                                        <span class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1">Occupied</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Bed Allocation Grid Tab -->
                    <div x-show="activeTab === 'beds'" class="space-y-6">
                        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                            <div>
                                <h1 class="text-2xl font-extrabold text-white tracking-tight">Critical Resource Bed Allocation</h1>
                                <p class="text-slate-400 text-xs mt-1">Manage inpatient admissions and vacant bed capacities in real-time.</p>
                            </div>
                            <div class="relative w-full sm:w-auto">
                                <i data-lucide="search" class="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2"></i>
                                <input type="text" x-model="searchTerm" placeholder="Search by Bed Number..." class="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs w-full sm:w-56 text-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                            </div>
                        </div>

                        <!-- Grid Filter Controls -->
                        <div class="flex flex-wrap gap-2">
                            <template x-for="f in ['ALL', 'VACANT', 'ICU', 'GENERAL', 'EMERGENCY', 'VENTILATOR']">
                                <button @click="filter = f" :class="filter === f ? 'bg-blue-600 border-blue-600 text-white shadow-sm' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'" class="px-4 py-2 text-xs font-bold rounded-xl border transition-all" x-text="f"></button>
                            </template>
                        </div>

                        <!-- Beds Roster Grid -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                            <template x-for="bed in filteredBeds()">
                                <div :class="bed.occupancy_status === 'OCCUPIED' ? 'border-slate-800 bg-slate-900/50' : 'border-emerald-900/40 bg-emerald-950/5'" class="rounded-2xl border p-5 transition-all duration-300 hover:scale-[1.02]">
                                    <div class="flex justify-between items-start mb-6">
                                        <div class="flex items-center">
                                            <div :class="bed.occupancy_status === 'OCCUPIED' ? 'bg-slate-800/80 text-slate-500' : 'bg-emerald-500/10 text-emerald-400'" class="p-2.5 rounded-xl mr-3 border border-slate-800">
                                                <i data-lucide="bed" class="w-5 h-5"></i>
                                            </div>
                                            <div>
                                                <h4 class="font-bold text-white text-sm" x-text="bed.bed_number"></h4>
                                                <span class="text-[9px] font-bold text-slate-500 uppercase tracking-widest" x-text="bed.ward"></span>
                                            </div>
                                        </div>
                                        <span :class="bed.bed_type === 'ICU' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : bed.bed_type === 'EMERGENCY' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-slate-800 text-slate-400 border-slate-800'" class="px-2 py-0.5 rounded text-[8px] font-bold tracking-widest uppercase border" x-text="bed.bed_type"></span>
                                    </div>
                                    <div class="flex gap-2">
                                        <template x-if="bed.occupancy_status === 'VACANT'">
                                            <button @click="allocateBed(bed._id)" :disabled="actionLoading === bed._id" class="w-full flex items-center justify-center py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50">
                                                <template x-if="actionLoading === bed._id">
                                                    <div class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                                </template>
                                                <template x-if="actionLoading !== bed._id">
                                                    <span>Admit Patient</span>
                                                </template>
                                            </button>
                                        </template>
                                        <template x-if="bed.occupancy_status === 'OCCUPIED'">
                                            <button @click="dischargeBed(bed._id)" :disabled="actionLoading === bed._id" class="w-full flex items-center justify-center py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition-all border border-slate-850 disabled:opacity-50">
                                                <template x-if="actionLoading === bed._id">
                                                    <div class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                                </template>
                                                <template x-if="actionLoading !== bed._id">
                                                    <span>Discharge</span>
                                                </template>
                                            </button>
                                        </template>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Staff Roster Roster Tab -->
                    <div x-show="activeTab === 'staff'" class="space-y-6">
                        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                            <div>
                                <h1 class="text-2xl font-extrabold text-white tracking-tight">Active Personnel Shifts</h1>
                                <p class="text-slate-400 text-xs mt-1">Manage personnel scheduler shifts and system duty statuses.</p>
                            </div>
                            <div class="relative w-full sm:w-auto">
                                <i data-lucide="search" class="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2"></i>
                                <input type="text" x-model="searchTerm" placeholder="Search by name or department..." class="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs w-full sm:w-56 text-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                            </div>
                        </div>

                        <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
                            <div class="overflow-x-auto">
                                <table class="w-full text-left text-xs whitespace-nowrap">
                                    <thead class="bg-slate-900/80 border-b border-slate-800">
                                        <tr>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Personnel Name</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Department</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Current Status</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Active Shift</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px] text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-slate-800/40">
                                        <template x-for="st in filteredStaff()">
                                            <tr class="hover:bg-slate-800/10 transition-colors">
                                                <td class="px-6 py-4">
                                                    <div class="flex items-center">
                                                        <div class="h-9 w-9 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center font-bold text-sm" x-text="st.name.split(' ').map(n=>n[0]).join('')"></div>
                                                        <div class="ml-4">
                                                            <div class="font-bold text-white" x-text="st.name"></div>
                                                            <div class="text-slate-500 text-[10px] tracking-wide mt-0.5" x-text="st.role"></div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td class="px-6 py-4">
                                                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-750" x-text="st.department"></span>
                                                </td>
                                                <td class="px-6 py-4">
                                                    <span :class="st.status === 'ON_SHIFT' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : st.status === 'ON_CALL' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-slate-850 text-slate-500 border-slate-800'" class="px-2 py-0.5 rounded text-[8px] font-bold tracking-widest border uppercase" x-text="st.status.replace('_', ' ')"></span>
                                                </td>
                                                <td class="px-6 py-4 text-slate-300 font-medium">
                                                    <span class="flex items-center">
                                                        <i data-lucide="clock" class="w-3.5 h-3.5 mr-2 text-slate-550"></i>
                                                        <span x-text="st.shift"></span>
                                                    </span>
                                                </td>
                                                <td class="px-6 py-4 text-right">
                                                    <button class="text-blue-400 hover:text-blue-500 font-bold">Reschedule</button>
                                                </td>
                                            </tr>
                                        </template>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <!-- Medical Equipment Tab -->
                    <div x-show="activeTab === 'equipment'" class="space-y-6">
                        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                            <div>
                                <h1 class="text-2xl font-extrabold text-white tracking-tight">Hospital Resources & Medical Equipment</h1>
                                <p class="text-slate-400 text-xs mt-1">Track mechanical device availability, location coordinates, and service reminders.</p>
                            </div>
                            <div class="relative w-full sm:w-auto">
                                <i data-lucide="search" class="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2"></i>
                                <input type="text" x-model="searchTerm" placeholder="Search device id or serials..." class="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs w-full sm:w-56 text-white focus:outline-none focus:ring-1 focus:ring-blue-500">
                            </div>
                        </div>

                        <!-- Stat counters -->
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div class="bg-slate-900 p-5 rounded-2xl border border-slate-800 flex items-center space-x-4">
                                <div class="h-12 w-12 bg-blue-500/10 text-blue-400 rounded-xl flex items-center justify-center border border-blue-500/20">
                                    <i data-lucide="activity" class="w-6 h-6"></i>
                                </div>
                                <div>
                                    <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Active Devices</p>
                                    <h3 class="text-2xl font-black text-white mt-1">342</h3>
                                </div>
                            </div>
                            <div class="bg-slate-900 p-5 rounded-2xl border border-slate-800 flex items-center space-x-4">
                                <div class="h-12 w-12 bg-emerald-500/10 text-emerald-400 rounded-xl flex items-center justify-center border border-emerald-500/20">
                                    <i data-lucide="check" class="w-6 h-6"></i>
                                </div>
                                <div>
                                    <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Active Standby</p>
                                    <h3 class="text-2xl font-black text-white mt-1">85</h3>
                                </div>
                            </div>
                            <div class="bg-slate-900 p-5 rounded-2xl border border-slate-800 flex items-center space-x-4">
                                <div class="h-12 w-12 bg-orange-500/10 text-orange-400 rounded-xl flex items-center justify-center border border-orange-500/20">
                                    <i data-lucide="alert-triangle" class="w-6 h-6"></i>
                                </div>
                                <div>
                                    <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Requires Service</p>
                                    <h3 class="text-2xl font-black text-white mt-1">14</h3>
                                </div>
                            </div>
                        </div>

                        <!-- Equipment Table Grid -->
                        <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
                            <div class="overflow-x-auto">
                                <table class="w-full text-left text-xs whitespace-nowrap">
                                    <thead class="bg-slate-900/80 border-b border-slate-800">
                                        <tr>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Medical Device Name</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Location Coordinate</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Utilization Status</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Technical Condition</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px]">Service Target</th>
                                            <th class="px-6 py-4 font-bold text-slate-400 uppercase tracking-widest text-[10px] text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-slate-800/40">
                                        <template x-for="eq in filteredEquipment()">
                                            <tr class="hover:bg-slate-800/10 transition-colors">
                                                <td class="px-6 py-4">
                                                    <div class="flex items-center">
                                                        <div class="h-9 w-9 rounded-xl bg-slate-850 text-slate-400 flex items-center justify-center border border-slate-800">
                                                            <i data-lucide="activity" class="w-4 h-4"></i>
                                                        </div>
                                                        <div class="ml-4">
                                                            <div class="font-bold text-white" x-text="eq.name"></div>
                                                            <div class="text-slate-500 text-[10px] font-mono mt-0.5" x-text="eq.id + ' • ' + eq.type"></div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td class="px-6 py-4 font-semibold text-slate-300" x-text="eq.location"></td>
                                                <td class="px-6 py-4">
                                                    <span :class="eq.status === 'IN_USE' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : eq.status === 'STANDBY' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-orange-500/10 text-orange-400 border-orange-500/20'" class="px-2 py-0.5 rounded text-[8px] font-bold tracking-widest border uppercase" x-text="eq.status.replace('_', ' ')"></span>
                                                </td>
                                                <td class="px-6 py-4">
                                                    <div class="flex items-center space-x-2">
                                                        <span :class="eq.condition === 'GOOD' ? 'bg-emerald-500' : eq.condition === 'NOTICE' ? 'bg-amber-500' : 'bg-red-500'" class="w-2 h-2 rounded-full inline-block"></span>
                                                        <span class="font-semibold text-slate-300" x-text="eq.condition"></span>
                                                    </div>
                                                </td>
                                                <td class="px-6 py-4 text-slate-400 font-medium" x-text="eq.nextMaintenance"></td>
                                                <td class="px-6 py-4 text-right">
                                                    <button class="text-blue-400 hover:text-blue-500 font-bold">Maintenance</button>
                                                </td>
                                            </tr>
                                        </template>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </main>
    </div>

    <script>
        document.addEventListener('alpine:init', () => {
            Alpine.data('app', () => ({
                // Auth States
                isAuthenticated: false,
                authTab: 'login',
                token: '',
                user: { username: '', role: '', name: '' },
                username: '',
                password: '',
                registerName: '',
                registerUsername: '',
                registerPassword: '',
                registerRole: 'admin',
                loginError: '',
                registerError: '',
                registerSuccess: '',
                
                // Operational States
                activeTab: 'dashboard',
                searchTerm: '',
                filter: 'ALL',
                actionLoading: null,
                showNotifications: false,
                isConnected: false,
                
                // Roster Data Arrays
                beds: [],
                stats: { totalBeds: 0, occupiedBeds: 0, vacantBeds: 0, occupancyRate: 0, icuTotal: 0, icuOccupied: 0, icuVacant: 0, icuOccupancyRate: 0 },
                staff: [],
                equipment: [],
                alerts: [
                    { title: "Ventilator Capacity Low", desc: "ICU Ventilators under 15% threshold configuration.", time: "12 mins ago", severity: "CRITICAL" },
                    { title: "Staff Handoff Delay", desc: "Shift transition delta delayed 15 mins.", time: "42 mins ago", severity: "WARNING" },
                    { title: "Oxygen Resupply Docked", desc: "Delivery truck received at Dock #4.", time: "1 hr ago", severity: "INFO" }
                ],
                
                // Charts handlers
                trendsChart: null,
                pieChart: null,

                init() {
                    // Check local session
                    const storedToken = localStorage.getItem('token');
                    const storedUser = localStorage.getItem('user');
                    if (storedToken && storedUser) {
                        this.token = storedToken;
                        this.user = JSON.parse(storedUser);
                        this.isAuthenticated = true;
                        this.bootstrapApp();
                    }
                    
                    // Hook Lucide Icons
                    setTimeout(() => { lucide.createIcons(); }, 100);
                },

                get userInitials() {
                    if (!this.user.name) return 'AD';
                    return this.user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                },

                get activeStaffCount() {
                    return this.staff.filter(s => s.status === 'ON_SHIFT').length || 42;
                },

                async login() {
                    this.loginError = '';
                    try {
                        const res = await fetch('/api/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username: this.username, password: this.password })
                        });
                        const data = await res.json();
                        
                        if (res.status === 200) {
                            localStorage.setItem('token', data.token);
                            localStorage.setItem('user', JSON.stringify(data.user));
                            this.token = data.token;
                            this.user = data.user;
                            this.isAuthenticated = true;
                            this.bootstrapApp();
                        } else {
                            this.loginError = data.error.message;
                        }
                    } catch (e) {
                        this.loginError = "Connection to authentication gateway failed.";
                    }
                },

                async register() {
                    this.registerError = '';
                    this.registerSuccess = '';
                    try {
                        const res = await fetch('/api/auth/register', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name: this.registerName,
                                username: this.registerUsername,
                                password: this.registerPassword,
                                role: this.registerRole
                            })
                        });
                        const data = await res.json();
                        
                        if (res.status === 200) {
                            this.registerSuccess = "Credential registered successfully! Please log in.";
                            this.authTab = 'login';
                            this.username = this.registerUsername;
                            this.password = '';
                        } else {
                            this.registerError = data.error.message;
                        }
                    } catch (e) {
                        this.registerError = "Registration request failed.";
                    }
                },

                logout() {
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    this.token = '';
                    this.user = { username: '', role: '', name: '' };
                    this.isAuthenticated = false;
                    this.activeTab = 'dashboard';
                    if (this.ws) {
                        this.ws.close();
                    }
                },

                bootstrapApp() {
                    // Start realtime synchronization
                    this.initRealtimeSync();
                    
                    // Load statistics and records
                    this.fetchStats();
                    this.fetchBeds();
                    this.fetchStaff();
                    this.fetchEquipment();
                    
                    // Render Graphics Canvas
                    setTimeout(() => {
                        this.renderCharts();
                        lucide.createIcons();
                    }, 500);
                },

                initRealtimeSync() {
                    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = wsProtocol + '//' + window.location.host + '/ws';
                    
                    this.ws = new WebSocket(wsUrl);
                    
                    this.ws.onopen = () => {
                        this.isConnected = true;
                        console.log("[*] MedCore Realtime WebSocket link operational.");
                    };
                    
                    this.ws.onmessage = (event) => {
                        try {
                            const message = JSON.parse(event.data);
                            if (message.type === 'bedUpdated') {
                                // Realtime bed update received
                                this.beds = this.beds.map(b => b._id === message.bed._id ? message.bed : b);
                                this.fetchStats(); // Update aggregated metrics & charts
                            }
                        } catch (e) {
                            console.error("Failed to parse WebSocket telemetry packet.", e);
                        }
                    };
                    
                    this.ws.onclose = () => {
                        this.isConnected = false;
                        // Auto reconnect schedule
                        setTimeout(() => {
                            if (this.isAuthenticated) this.initRealtimeSync();
                        }, 5000);
                    };
                },

                async fetchStats() {
                    try {
                        const res = await fetch('/api/stats', {
                            headers: { 'Authorization': 'Bearer ' + this.token }
                        });
                        if (res.status === 401) return this.logout();
                        const data = await res.json();
                        this.stats = data;
                        this.updateCharts();
                    } catch (e) {
                        console.error("Failed to retrieve statistics.", e);
                    }
                },

                async fetchBeds() {
                    try {
                        const res = await fetch('/api/beds', {
                            headers: { 'Authorization': 'Bearer ' + this.token }
                        });
                        const data = await res.json();
                        this.beds = data;
                        setTimeout(() => { lucide.createIcons(); }, 50);
                    } catch (e) {
                        console.error("Failed to load bed configurations.", e);
                    }
                },

                async fetchStaff() {
                    try {
                        const res = await fetch('/api/staff', {
                            headers: { 'Authorization': 'Bearer ' + this.token }
                        });
                        this.staff = await res.json();
                    } catch (e) {
                        console.error("Failed to load staff roster.", e);
                    }
                },

                async fetchEquipment() {
                    try {
                        const res = await fetch('/api/equipment', {
                            headers: { 'Authorization': 'Bearer ' + this.token }
                        });
                        this.equipment = await res.json();
                    } catch (e) {
                        console.error("Failed to load resource inventory.", e);
                    }
                },

                async allocateBed(id) {
                    this.actionLoading = id;
                    try {
                        const res = await fetch('/api/beds/' + id + '/allocate', {
                            method: 'POST',
                            headers: { 
                                'Authorization': 'Bearer ' + this.token,
                                'Content-Type': 'application/json' 
                            }
                        });
                        const data = await res.json();
                        if (res.status !== 200) {
                            alert(data.error.message);
                        }
                    } catch (e) {
                        console.error("Admission request exception.", e);
                    } finally {
                        this.actionLoading = null;
                    }
                },

                async dischargeBed(id) {
                    this.actionLoading = id;
                    try {
                        const res = await fetch('/api/beds/' + id + '/discharge', {
                            method: 'POST',
                            headers: { 
                                'Authorization': 'Bearer ' + this.token,
                                'Content-Type': 'application/json' 
                            }
                        });
                        const data = await res.json();
                        if (res.status !== 200) {
                            alert(data.error.message);
                        }
                    } catch (e) {
                        console.error("Discharge request exception.", e);
                    } finally {
                        this.actionLoading = null;
                    }
                },

                // Filters and Search routines
                filteredBeds() {
                    return this.beds.filter(b => {
                        const matchesSearch = b.bed_number.toLowerCase().includes(this.searchTerm.toLowerCase()) || 
                                              b.ward.toLowerCase().includes(this.searchTerm.toLowerCase());
                        
                        if (this.filter === 'ALL') return matchesSearch;
                        if (this.filter === 'VACANT') return b.occupancy_status === 'VACANT' && matchesSearch;
                        return b.bed_type === this.filter && matchesSearch;
                    });
                },

                filteredStaff() {
                    return this.staff.filter(st => {
                        return st.name.toLowerCase().includes(this.searchTerm.toLowerCase()) || 
                               st.department.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                               st.role.toLowerCase().includes(this.searchTerm.toLowerCase());
                    });
                },

                filteredEquipment() {
                    return this.equipment.filter(eq => {
                        return eq.name.toLowerCase().includes(this.searchTerm.toLowerCase()) || 
                               eq.id.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                               eq.location.toLowerCase().includes(this.searchTerm.toLowerCase());
                    });
                },

                renderCharts() {
                    const ctxTrends = document.getElementById('admissionTrendsChart');
                    const ctxPie = document.getElementById('capacityPieChart');
                    
                    if (ctxTrends) {
                        this.trendsChart = new Chart(ctxTrends, {
                            type: 'bar',
                            data: {
                                labels: ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'],
                                datasets: [
                                    {
                                        label: 'General Admissions',
                                        data: [15, 18, 20, 22, 21, 23, 24],
                                        backgroundColor: '#3b82f6',
                                        borderRadius: 8
                                    },
                                    {
                                        label: 'ICU Admissions',
                                        data: [5, 8, 4, 11, 3, 5, 10],
                                        backgroundColor: '#f59e0b',
                                        borderRadius: 8
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: { display: false }
                                },
                                scales: {
                                    y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
                                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                                }
                            }
                        });
                    }

                    if (ctxPie) {
                        this.pieChart = new Chart(ctxPie, {
                            type: 'doughnut',
                            data: {
                                labels: ['Occupied Beds', 'Vacant Beds'],
                                datasets: [{
                                    data: [this.stats.occupiedBeds || 0, this.stats.vacantBeds || 0],
                                    backgroundColor: ['#3b82f6', '#1e293b'],
                                    borderWidth: 0,
                                    hoverOffset: 4
                                }]
                            },
                            options: {
                                cutout: '75%',
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } }
                            }
                        });
                    }
                },

                updateCharts() {
                    if (this.pieChart) {
                        this.pieChart.data.datasets[0].data = [
                            this.stats.occupiedBeds || 0, 
                            this.stats.vacantBeds || 0
                        ];
                        this.pieChart.update();
                    }
                }

            }));
        });
    </script>
</body>
</html>
"""
    return html_content

# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    PORT = 3000
    print("\n" + "=" * 60)
    print("      MEDCORE HBRMS - FULL-STACK PYTHON GOLDEN ENGINE")
    print("=" * 60)
    print(f"[*] API Rate Limiter: Operational (100 req / 15 mins)")
    print(f"[*] Cryptographic Engine: PBKDF2 Password Hashing & HMAC JWT Tokens")
    print(f"[*] Live Telemetry Broker: WebSockets running")
    print(f"[*] Web Server Address: http://localhost:{PORT}")
    print("=" * 60 + "\n")
    
    # Run the uvicorn development server
    uvicorn.run(app, host="127.0.0.1" if sys.platform == "win32" else "0.0.0.0", port=PORT)

