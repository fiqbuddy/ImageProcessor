# Distributed Image Processing System - XML-RPC Microservices

A **computationally-intensive** distributed image processing pipeline using **XML-RPC** to demonstrate real parallel computing across multiple devices.

## 🏗️ Architecture

```
Client (GUI/CLI)
   ↓
Orchestrator Service (Port 50055)
   ├─→ Resize Service (Port 50052)
   ├─→ Filter Service (Port 50053)  
   ├─→ Watermark Service (Port 50054)
   └─→ Format Service (Port 50056)
```

**Pipeline Flow:** Resize → Filter → Watermark → Format

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

### Run Locally (Single Machine)

**Windows:**
```cmd
REM Terminal 1-5: Start all services  
start python services\resize_service.py
start python services\filter_service.py
start python services\watermark_service.py
start python services\format_service.py
start python services\orchestrator_service.py

REM Terminal 6: Run client
python client\pipeline_demo.py
```

Or use the batch script:
```cmd
start_all_services.bat
python client\pipeline_demo.py
```

### Run with GUI
```cmd
python client\pipeline_gui.py
```

---

## 📊 Services Overview

| Service | Port | Computational Work | Processing Time |
|---------|------|-------------------|-----------------|
| **Resize** | 50052 | LANCZOS interpolation (high-quality resampling) | 50-90ms |
| **Filter** | 50053 | Gaussian blur, edge detection, sepia, etc. | 100-300ms per filter |
| **Watermark** | 50054 | Text rendering, alpha compositing | 40-80ms |
| **Format** | 50056 | Format conversion, compression | 30-60ms |
| **Orchestrator** | 50055 | Pipeline coordination, load balancing | Minimal |

### Filter Service (Most Intensive)
Supported filters:
- `GRAYSCALE` - Convert to grayscale
- `BLUR` - Gaussian blur (CPU intensive)
- `SHARPEN` - Sharpen edges
- `EDGE_DETECT` - Sobel edge detection
- `SEPIA` - Sepia tone effect
- `NEGATIVE` - Invert colors
- `BRIGHTNESS` - Adjust brightness
- `CONTRAST` - Adjust contrast

---

## 🌐 Distributed Deployment

### Architecture for 5 Devices

| Device | Service | Static IP (Tailscale) | Port |
|--------|---------|-------------|------|
| Device 1 | Resize | 100.120.161.53 | 50052 |
| Device 2 | Filter | 100.71.209.102 | 50053 |
| Device 3 | Watermark | 100.115.248.53 | 50054 |
| Device 4 | Format | 100.71.185.127 | 50056 |
| Device 5 (Master) | Orchestrator + Client | 100.103.89.22 | 50055 |

### Setup Instructions

**Device 1-4 (Workers):**
```bash
# On each worker device, start the respective service
python services/resize_service.py      # Device 1
python services/filter_service.py      # Device 2
python services/watermark_service.py   # Device 3
python services/format_service.py      # Device 4
```

**Device 5 (Master):**
```powershell
# Set environment variables for worker IPs
$env:RESIZE_SERVICE_HOSTS="100.120.161.53:50052"
$env:FILTER_SERVICE_HOSTS="100.71.209.102:50053"
$env:WATERMARK_SERVICE_HOSTS="100.115.248.53:50054"
$env:FORMAT_SERVICE_HOSTS="100.71.185.127:50056"

# Start orchestrator
python services/orchestrator_service.py

# Run client (in new terminal)
python client/pipeline_demo.py
```

---

## 🐳 Docker Deployment

### Single Machine with Load Balancing

```bash
# Start all containers (11 total: 3 resize, 5 filter, 3 watermark)
docker-compose up --build

# Run client
python client/pipeline_demo.py
```

The Docker setup runs multiple instances of each service for parallel processing:
- **3x Resize Services** (ports 50052, 50062, 50072)
- **5x Filter Services** (ports 50053, 50063, 50073, 50083, 50093)
- **3x Watermark Services** (ports 50054, 50064, 50074)
- **1x Orchestrator** (port 50055) with round-robin load balancing

### Multi-Device Docker Deployment

**Device 1:**
```bash
docker-compose -f docker-compose.resize.yml up --build
```

**Device 2:**
```bash
docker-compose -f docker-compose.filter.yml up --build
```

**Device 3:**
```bash
docker-compose -f docker-compose.watermark.yml up --build
```

**Device 4:**
```bash
docker-compose -f docker-compose.format.yml up --build
```

**Device 5 (Master):**
```powershell
# Set worker IPs in environment
$env:RESIZE_IP="100.120.161.53"
$env:FILTER_IP="100.71.209.102"
$env:WATERMARK_IP="100.115.248.53"
$env:FORMAT_IP="100.71.185.127"

# Start orchestrator
docker-compose -f docker-compose.orchestrator.yml up --build
```

---

## 📈 Performance Benchmarks

### Expected Throughput

| Setup | Throughput | Notes |
|-------|-----------|-------|
| **Single Machine** | 3-5 images/sec | All services on localhost |
| **Distributed (5 Devices)** | 10-15 images/sec | Each service on different device |
| **Docker Load Balanced** | 20-30 images/sec | Multiple instances per service |

### Batch Processing
The `pipeline_demo.py` client processes 30 images by default, showing:
- Individual processing times for each stage
- Total pipeline time per image
- Overall throughput (images/second)
- Distribution across worker services

---

## 🔬 Testing

### Test Individual Services
```bash
# Test resize service
python test_resize.py

# Test connection to worker
python probe_connection.py
```

### Monitor Processing
Watch the orchestrator logs to see load balancing in action:
```
🖼  STAGE 1: Resizing image... (using localhost:50052)
🎨 STAGE 2: Applying 2 filter(s)...
   [1/2] Applying BLUR... (using localhost:50053)
   [2/2] Applying SHARPEN... (using localhost:50053)
🏷️  STAGE 3: Adding watermark... (using localhost:50054)
📦 STAGE 4: Formatting... (using localhost:50056)
✅ Pipeline Complete! Total time: 450ms
```

---

## 🛠️ Development

### Project Structure
```
ImageProcessor/
├── services/               # Microservices
│   ├── orchestrator_service.py
│   ├── resize_service.py
│   ├── filter_service.py
│   ├── watermark_service.py
│   └── format_service.py
├── client/                 # Client applications
│   ├── pipeline_demo.py   # CLI batch processor
│   └── pipeline_gui.py    # Tkinter GUI
├── docker-compose*.yml    # Docker configurations
├── Dockerfile
├── requirements.txt
└── README.md
```

### Key Technologies
- **XML-RPC**: Python's built-in `xmlrpc.server` and `xmlrpc.client`
- **Image Processing**: Pillow (PIL), NumPy
- **Binary Data**: Automatic base64 encoding via `Binary()` wrapper
- **Load Balancing**: Round-robin distribution in orchestrator

### Adding New Filters
Edit `services/filter_service.py` and add your filter logic to the `apply_filter_by_type()` method.

---

## 🐞 Troubleshooting

### Connection Refused
- **Local**: Ensure all services are running on the correct ports
- **Distributed**: Check firewall rules, verify static IPs are reachable
- Test connectivity: `python probe_connection.py`

### XML Parsing Errors
- Ensure all services are using the same XML-RPC protocol
- Check that Binary data is properly wrapped in `Binary()` wrapper

### Service Not Responding
```bash
# Check if service is running
netstat -an | findstr :50052

# Restart service
python services/resize_service.py
```

### Docker Issues
```bash
# Rebuild containers
docker-compose up --build --force-recreate

# Check container logs
docker logs orchestrator-service -f
docker logs resize-service-1 -f

# Check resource usage
docker stats
```

---

## 📊 For Academic Reports

### Key Metrics to Show
1. **Processing Time Breakdown**: Resize/Filter/Watermark/Format times
2. **Throughput**: Images per second (single vs distributed)
3. **Load Distribution**: Round-robin balancing across instances
4. **Scalability**: Performance improvement with more devices/containers
5. **CPU Usage**: Distributed computational load

### Why This Demonstrates Distributed Computing
- ✅ **Real computational work**: CPU-intensive image processing algorithms
- ✅ **Network communication**: XML-RPC for inter-service calls
- ✅ **Load balancing**: Orchestrator distributes work across instances
- ✅ **Scalability**: Easy to add more worker instances
- ✅ **Pipeline architecture**: Sequential processing across services
- ✅ **Binary data handling**: Efficient transfer of large image files
- ✅ **Clear benchmarks**: Measurable performance improvements

---

## 📝 License

This project is for educational purposes.

## 🤝 Contributing

This is a demonstration project for distributed systems coursework.

---

## Migration Notes (gRPC → XML-RPC)

This system was migrated from gRPC to XML-RPC for simplicity:
- **Removed**: Protocol Buffers, gRPC libraries, `.proto` files
- **Added**: Native Python XML-RPC (no extra dependencies)
- **Benefits**: Simpler architecture, easier debugging, Pythonic API
- **Trade-offs**: Slightly less efficient than gRPC for very large datasets

All functionality preserved, including load balancing and distributed deployment.
