# 🚀 5-Device Distributed Image Processing Setup

This guide explains how to deploy the Image Processing Pipeline across **5 physical devices**.

## 🏗️ Architecture

| Device | Role | Service | Port(s) | Docker File |
|--------|------|---------|---------|-------------|
| **Device 1** | **Resize Node** | Resize Service | 50052, 50062, 50072 | `docker-compose.resize.yml` |
| **Device 2** | **Filter Node** | Filter Service | 50053, 50063... | `docker-compose.filter.yml` |
| **Device 3** | **Watermark Node** | Watermark Service | 50054, 50064, 50074 | `docker-compose.watermark.yml` |
| **Device 4** | **Format Node** | Format Service | 50056, 50066, 50076 | `docker-compose.format.yml` |
| **Device 5** | **Master Node** | Orchestrator + Client | 50055 | `docker-compose.orchestrator.yml` |

---

## 📋 Prerequisites

1.  **5 Physical Computers** on the same network (Wi-Fi or Ethernet).
2.  **Docker Desktop** installed and running on ALL devices.
3.  **Python 3.9+** installed on Device 5 (for running the client).
4.  **Firewall Rules**: Ensure ports 50050-50100 are open on all devices.

---

## 🛠️ Step 1: Get IP Addresses

On **EACH** device, open a terminal and find the IP address:
*   **Windows**: `ipconfig` (Look for IPv4 Address)
*   **Mac/Linux**: `ifconfig` or `ip a`

Write them down:
*   **RESIZE_IP** (Device 1): `_________________`
*   **FILTER_IP** (Device 2): `_________________`
*   **WATERMARK_IP** (Device 3): `_________________`
*   **FORMAT_IP** (Device 4): `_________________`

---

## 🚀 Step 2: Start Worker Nodes (Devices 1-4)

### Device 1 (Resize Node)
1.  Copy the project folder to Device 1.
2.  Open terminal in folder.
3.  Run: `docker-compose -f docker-compose.resize.yml up --build`

### Device 2 (Filter Node)
1.  Copy the project folder to Device 2.
2.  Open terminal in folder.
3.  Run: `docker-compose -f docker-compose.filter.yml up --build`

### Device 3 (Watermark Node)
1.  Copy the project folder to Device 3.
2.  Open terminal in folder.
3.  Run: `docker-compose -f docker-compose.watermark.yml up --build`

### Device 4 (Format Node)
1.  Copy the project folder to Device 4.
2.  Open terminal in folder.
3.  Run: `docker-compose -f docker-compose.format.yml up --build`

---

## 🎮 Step 3: Start Master Node (Device 5)

1.  On Device 5, open a **PowerShell** terminal.
2.  Set the environment variables for the worker IPs (Replace with actual IPs):

```powershell
$env:RESIZE_IP="192.168.1.101"
$env:FILTER_IP="192.168.1.102"
$env:WATERMARK_IP="192.168.1.103"
$env:FORMAT_IP="192.168.1.104"
```

3.  Start the Orchestrator:
    ```powershell
    docker-compose -f docker-compose.orchestrator.yml up --build
    ```

4.  **Verify Connection**:
    The Orchestrator logs should show it connecting to the remote IPs, NOT `localhost`.

---

## 🧪 Step 4: Run the Client (Device 5)

1.  Open a **new** terminal on Device 5.
2.  Run the demo script:
    ```bash
    python client/pipeline_demo.py
    ```

You should see the pipeline executing stages across all 5 devices!

---

## 🐞 Troubleshooting

*   **"Method not found"**: You are likely connecting to an old version of the service. Rebuild containers with `docker-compose ... up --build --force-recreate`.
*   **"Unavailable" / Connection Refused**:
    *   Check IP addresses.
    *   **DISABLE FIREWALL** on worker nodes temporarily to test.
    *   Ping worker IPs from the Master node.
*   **Logs not showing**: Add `PYTHONUNBUFFERED=1` to environment variables (already done in compose files).
