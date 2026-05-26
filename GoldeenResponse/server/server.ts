import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import http from "http";
import { Server } from "socket.io";
import cors from "cors";
import mongoose from "mongoose";
import helmet from "helmet";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import jwt from "jsonwebtoken";

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST", "PUT", "DELETE"],
  },
});

const PORT = 3000;


app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors());
app.use(express.json());
app.use(morgan("dev"));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: "Too many requests, please try again later."
});
app.use("/api/", limiter);

// Mock Data
const mockBeds = Array.from({ length: 40 }).map((_, i) => ({
  _id: `bed_${Math.random().toString(36).substring(7)}`,
  bed_number: `B-${(i + 1).toString().padStart(3, '0')}`,
  bed_type: i < 10 ? "ICU" : i < 25 ? "GENERAL" : "EMERGENCY",
  occupancy_status: Math.random() > 0.4 ? "OCCUPIED" : "VACANT",
  ward: i < 10 ? "Intensive Care Unit" : "General Ward",
  updatedAt: new Date().toISOString()
}));

app.get("/api/health", (req, res) => {
  res.json({ status: "ok", db: mongoose.connection.readyState === 1 ? "connected" : "disconnected" });
});

const mockUsers = [
  { username: 'admin', password: 'admin123', role: 'admin', name: 'Admin User' }
];

app.post("/api/auth/login", (req, res) => {
  const { username, password } = req.body;
  const user = mockUsers.find(u => u.username === username && u.password === password);
  if (user) {
    const token = jwt.sign(
      { id: user.username, role: user.role },
      process.env.JWT_SECRET || 'fallback_secret',
      { expiresIn: '1d' }
    );
    res.json({ token, user: { username: user.username, role: user.role, name: user.name } });
  } else {
    res.status(401).json({ message: "Invalid username or password" });
  }
});

app.post("/api/auth/register", (req, res) => {
  const { name, username, password, role } = req.body;
  if (!username || !password) {
    return res.status(400).json({ message: "Username and password are required" });
  }
  if (mockUsers.find(u => u.username === username)) {
    return res.status(400).json({ message: "Username already exists" });
  }
  const newUser = { name: name || username, username, password, role: role || 'admin' };
  mockUsers.push(newUser);
  const token = jwt.sign(
    { id: newUser.username, role: newUser.role },
    process.env.JWT_SECRET || 'fallback_secret',
    { expiresIn: '1d' }
  );
  res.status(201).json({ token, user: { username: newUser.username, role: newUser.role, name: newUser.name } });
});

app.get("/api/stats", (req, res) => {
  const total = mockBeds.length;
  const occupied = mockBeds.filter(b => b.occupancy_status === "OCCUPIED").length;
  const icuTotal = mockBeds.filter(b => b.bed_type === "ICU").length;
  const icuOccupied = mockBeds.filter(b => b.bed_type === "ICU" && b.occupancy_status === "OCCUPIED").length;
  res.json({
    totalBeds: total,
    occupiedBeds: occupied,
    vacantBeds: total - occupied,
    occupancyRate: Math.round((occupied / total) * 100),
    icuTotal,
    icuOccupied,
    icuVacant: icuTotal - icuOccupied,
    icuOccupancyRate: Math.round((icuOccupied / icuTotal) * 100),
  });
});

app.get("/api/beds", (req, res) => {
  res.json(mockBeds);
});

app.post("/api/beds/:id/allocate", (req, res) => {
  const bed = mockBeds.find(b => b._id === req.params.id);
  if (!bed) return res.status(404).json({ error: "Bed not found" });
  if (bed.occupancy_status === "OCCUPIED") return res.status(400).json({ error: "Bed already occupied" });
  bed.occupancy_status = "OCCUPIED";
  bed.updatedAt = new Date().toISOString();
  io.emit("bedUpdated", bed);
  res.json(bed);
});

app.post("/api/beds/:id/discharge", (req, res) => {
  const bed = mockBeds.find(b => b._id === req.params.id);
  if (!bed) return res.status(404).json({ error: "Bed not found" });
  if (bed.occupancy_status === "VACANT") return res.status(400).json({ error: "Bed is already vacant" });
  bed.occupancy_status = "VACANT";
  bed.updatedAt = new Date().toISOString();
  io.emit("bedUpdated", bed);
  res.json(bed);
});

io.on("connection", (socket) => {
  console.log("Client connected:", socket.id);
  socket.on("disconnect", () => {
    console.log("Client disconnected:", socket.id);
  });
});

async function startServer() {
  if (process.env.MONGODB_URI) {
    try {
      await mongoose.connect(process.env.MONGODB_URI);
      console.log("Connected to MongoDB");
    } catch (err) {
      console.error("MongoDB connection error:", err);
    }
  } else {
    console.log("No MONGODB_URI provided. Running with mock data layer.");
  }

  if (process.env.NODE_ENV !== "production") {
    // Point Vite at the client/ folder (relative to workspace root)
    const clientRoot = path.join(process.cwd(), "client");
    const vite = await createViteServer({
      configFile: path.join(clientRoot, "vite.config.ts"),
      root: clientRoot,
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "client/dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
