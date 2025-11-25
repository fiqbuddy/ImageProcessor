# ✌️ 2-Device Test Setup Guide

This guide explains how to test the distributed system using just **2 computers**.

## 📋 Roles
*   **Device 1 (The Worker)**: Runs ALL processing containers (Resize, Filter, Watermark).
*   **Device 2 (The Master)**: Runs the Orchestrator and Client.

---

## 🛠️ Step 1: Find IP of Device 1
On Device 1, find its local IP address (e.g., `192.168.1.101`).
*   **Device 1 IP**: `___________________`

---

## 🚀 Step 2: Start Device 1 (Worker)
On Device 1, run the "Super Worker" configuration:
```bash
docker-compose -f docker-compose.worker.yml up --build
```
*This starts 8 containers (3 Resize, 3 Filter, 2 Watermark).*

---

## 🧠 Step 3: Start Device 2 (Master)
On Device 2, you need to point EVERYTHING to Device 1's IP.

**Windows (CMD):**
```cmd
REM Replace with Device 1's actual IP
set WORKER_IP=192.168.1.101

set RESIZE_SERVICE_HOSTS=%WORKER_IP%:50052,%WORKER_IP%:50062,%WORKER_IP%:50072
set FILTER_SERVICE_HOSTS=%WORKER_IP%:50053,%WORKER_IP%:50063,%WORKER_IP%:50073
set WATERMARK_SERVICE_HOSTS=%WORKER_IP%:50054,%WORKER_IP%:50064

python services/orchestrator_service.py
```

**Mac/Linux:**
```bash
# Replace with Device 1's actual IP
export WORKER_IP=192.168.1.101

export RESIZE_SERVICE_HOSTS=$WORKER_IP:50052,$WORKER_IP:50062,$WORKER_IP:50072
export FILTER_SERVICE_HOSTS=$WORKER_IP:50053,$WORKER_IP:50063,$WORKER_IP:50073
export WATERMARK_SERVICE_HOSTS=$WORKER_IP:50054,$WORKER_IP:50064

python services/orchestrator_service.py
```

---

## 🎮 Step 4: Run Client (Device 2)
Open a new terminal on Device 2:
```bash
python client/pipeline_demo.py
```

## 🔍 What to Expect
1.  Client sends image to Orchestrator (on Device 2).
2.  Orchestrator sends data to Device 1 for resizing.
3.  Device 1 processes and returns data.
4.  Orchestrator sends data to Device 1 for filtering.
5.  ...and so on.

**Success?** If this works, you have proven that:
1.  Network connectivity works.
2.  Orchestrator can talk to remote IPs.
3.  Docker port mapping is correct.
