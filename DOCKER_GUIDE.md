# Docker Parallel Processing Guide

## � Overview

This setup runs **11 containers** for maximum parallel processing:
- **3x Resize Services** (load balanced)
- **5x Filter Services** (bottleneck - needs most instances)
- **3x Watermark Services** (load balanced)
- **1x Orchestrator** (coordinates with round-robin load balancing)

## 📊 Architecture

```
                    docker-compose up
                           ↓
        ┌──────────────────┴──────────────────┐
        │                                      │
    Orchestrator (1 instance)                 │
    - Round-robin load balancer              │
    - Distributes work across instances       │
        │                                      │
        ├─────────┬─────────┬─────────────────┤
        │         │         │                  │
    Resize-1  Resize-2  Resize-3          Filter-1
    :50052    :50062    :50072           :50053
        │         │         │                  │
        └─────────┴─────────┘            Filter-2
              ↓                          :50063
         Load Balanced                      │
                                        Filter-3
                                        :50073
                                            │
                                        Filter-4
                                        :50083
                                            │
                                        Filter-5
                                        :50093
                                            │
                                    Load Balanced
                                            ↓
        ┌─────────┬─────────┬─────────────────┐
        │         │         │
  Watermark-1  Watermark-2  Watermark-3
    :50054      :50064      :50074
        │         │         │
        └─────────┴─────────┘
              ↓
         Load Balanced
```

## � Running the System

### Step 1: Build and Start All Containers

```bash
docker-compose up --build
```

This will:
- Build the Docker image
- Start all 11 containers
- Create the grpc-network
- Configure load balancing

### Step 2: Verify All Containers Running

```bash
docker ps
```

You should see:
```
resize-service-1
resize-service-2
resize-service-3
filter-service-1
filter-service-2
filter-service-3
filter-service-4
filter-service-5
watermark-service-1
watermark-service-2
watermark-service-3
orchestrator-service
```

### Step 3: Run the Client

```bash
python client/pipeline_demo.py
```

## 📈 Performance Comparison

### Single Service Instance (Baseline)
```
Full Pipeline: ~720ms per image
Throughput: ~1.4 images/second
```

### Docker with 11 Containers (Expected)
```
Full Pipeline: ~200-300ms per image (parallelization)
Throughput: ~3-5 images/second
Speedup: 3-4x
```

**Why the improvement?**
- Filter operations (the bottleneck) distributed across 5 instances
- Each filter in pipeline uses different container
- Round-robin ensures even load distribution

## 🔍 Monitoring

### View Orchestrator Logs (Shows Load Balancing)
```bash
docker logs orchestrator-service -f
```

You'll see output like:
```
🖼️  STAGE 1: Resizing image... (using resize-1:50052)
🎨 STAGE 2: Applying 3 filter(s)...
   [1/3] Applying BLUR... (using filter-1:50053)
   [2/3] Applying SHARPEN... (using filter-2:50053)
   [3/3] Applying SEPIA... (using filter-3:50053)
🏷️  STAGE 3: Adding watermark... (using watermark-1:50054)
```

Notice each filter uses a **different instance**!

### View Individual Service Logs
```bash
docker logs filter-service-1 -f
docker logs filter-service-2 -f
# etc...
```

### Check Resource Usage
```bash
docker stats
```

Shows CPU/memory usage per container - you'll see load distributed!

## 🧪 Testing Parallel Processing

Create a benchmark that processes **10 images concurrently**:

```python
import grpc
import concurrent.futures
from client.pipeline_demo import create_sample_image
import image_processing_pb2
import image_processing_pb2_grpc

def process_single_image(image_id):
    # ... (send to orchestrator)
    pass

# Process 10 images in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process_single_image, i) for i in range(10)]
    results = [f.result() for f in futures]

# Each image will use different service instances!
```

## 🎯 Multi-Device Setup (Advanced)

### Device 1: Resize Cluster (3 containers)
```bash
# Run only resize services
docker-compose up resize-1 resize-2 resize-3
```

### Device 2: Filter Cluster (5 containers)
```bash
# Run only filter services
docker-compose up filter-1 filter-2 filter-3 filter-4 filter-5
```

### Device 3: Watermark Cluster (3 containers)
```bash
# Run only watermark services
docker-compose up watermark-1 watermark-2 watermark-3
```

### Device 4: Orchestrator
```bash
# Set environment variables to point to other devices
export RESIZE_SERVICE_HOSTS="192.168.1.101:50052,192.168.1.101:50062,192.168.1.101:50072"
export FILTER_SERVICE_HOSTS="192.168.1.102:50053,192.168.1.102:50063,192.168.1.102:50073,192.168.1.102:50083,192.168.1.102:50093"
export WATERMARK_SERVICE_HOSTS="192.168.1.103:50054,192.168.1.103:50064,192.168.1.103:50074"

python services/orchestrator_service.py
```

## � Scaling Up/Down

### Scale Filter Service to 10 instances (manually edit docker-compose.yml)
Or use Docker Swarm/Kubernetes for dynamic scaling.

### Scale Down for Testing
```bash
# Run with fewer instances
docker-compose up resize-1 filter-1 watermark-1 orchestrator
```

## � Troubleshooting

**Problem**: `connection refused`  
**Solution**: Make sure all containers are healthy:
```bash
docker-compose ps
docker logs orchestrator-service
```

**Problem**: Uneven load distribution  
**Solution**: Check orchestrator logs to verify round-robin is working

**Problem**: Out of memory  
**Solution**: Reduce number of filter instances or increase Docker memory limit

## 📊 For Your Report

**Show these metrics:**
1. **Container count**: 11 containers working in parallel
2. **Load distribution**: Orchestrator logs showing different instances
3. **Throughput comparison**: 1.4 img/s → 3-5 img/s
4. **Resource usage**: `docker stats` showing distributed CPU load
5. **Scalability**: Easy to add more instances by editing docker-compose.yml

**Explain:**
- Round-robin load balancing ensures even distribution
- Filter service gets 5 instances because it's the bottleneck
- Each device can run a cluster of services
- Docker networking makes service discovery automatic
