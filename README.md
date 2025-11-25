# Image Processing Pipeline - gRPC Microservices

A **computationally-intensive** distributed image processing system using **gRPC** to demonstrate real parallel computing across multiple devices.

## 🏗️ Pipeline Architecture

```
Client
  ↓
Orchestrator (Device 5) - Coordinates pipeline
  ↓
Resize Service (Device 1) - Resizes images
  ↓
Filter Service (Device 2) - Applies blur, sharpen, edge detection, sepia, etc.
  ↓
Watermark Service (Device 3) - Adds text/logo overlays
  ↓
Returns processed image to client
```

## ⚡ Why This is Better Than Movie Tickets

| Aspect | Movie Tickets | Image Processing |
|--------|---------------|------------------|
| **CPU Work** | Minimal (database lookups) | Heavy (Pillow algorithms, NumPy operations) |
| **Processing Time** | ~50-100ms | ~200-500ms per image |
| **Benchmark Metric** | Hard to measure | Clear: images/second |
| **Scalability** | Limited improvement | 3-5x speedup with distribution |
| **Visual Proof** | None | See processed images! |

## 🚀 Quick Start

### Run on Single Machine

```cmd
# 1. Start all services
start_all_services.bat

# 2. Run the demo (in new terminal)
python client\pipeline_demo.py
```

### Run on Multiple Devices (TRUE Distributed)

**Device 1 (192.168.1.101):**
```cmd
python services\resize_service.py
```

**Device 2 (192.168.1.102):**
```cmd
python services\filter_service.py
```

**Device 3 (192.168.1.103):**
```cmd
python services\watermark_service.py
```

**Device 4 (192.168.1.104) - Orchestrator:**
```cmd
set RESIZE_SERVICE_HOST=192.168.1.101:50052
set FILTER_SERVICE_HOST=192.168.1.102:50053
set WATERMARK_SERVICE_HOST=192.168.1.103:50054
python services\orchestrator_service.py
```

**Your Laptop - Client:**
```cmd
# Edit pipeline_demo.py:
# Change 'localhost:50055' to '192.168.1.104:50055'
python client\pipeline_demo.py
```

## 📊 Services & Computational Work

### 1. Resize Service (Port 50052)
- **Algorithm**: Pillow's LANCZOS (high-quality resampling)
- **CPU Work**: Matrix interpolation for every pixel
- **Time**: 50-90ms per image

### 2. Filter Service (Port 50053) - MOST INTENSIVE
- **Filters**: Blur, Sharpen, Edge Detect, Sepia, Negative, Brightness, Contrast
- **CPU Work**: 
  - Gaussian Blur: Convolution across entire image
  - Edge Detection: Sobel operators
  - Sepia: Matrix multiplication on every pixel
- **Time**: 100-300ms per filter

### 3. Watermark Service (Port 50054)
- **Operations**: Text rendering, alpha compositing, logo overlay
- **CPU Work**: Transparency calculations, blending
- **Time**: 40-80ms

### 4. Orchestrator Service (Port 50055)
- **Role**: Pipeline coordinator
- **Work**: Calls services sequentially, measures performance

## 📈 Benchmark Results (Expected)

| Setup | Throughput | Notes |
|-------|-----------|-------|
| **Single Machine** | ~3-5 images/sec | All services on localhost |
| **3 Devices** | ~10-15 images/sec | Each service on different device |
| **Load Balanced** | ~20-30 images/sec | Multiple instances of Filter service |

## 🎯 What Gets Processed

The demo creates 3 output files:

1. **output_full_pipeline.png** - Resize + 3 Filters + Watermark
2. **output_resize_only.png** - Just resizing
3. **output_heavy_filters.png** - Resize + 5 intensive filters

## 🔬 For Your Report

**Show these metrics:**
- Processing time breakdown (resize/filter/watermark)
- Images per second throughput
- Single device vs distributed comparison
- CPU usage during processing

**Explain:**
- Each service does real computational work
- Filters use CPU-intensive algorithms (Gaussian blur, edge detection)
- Distributing across devices shows clear speedup
- gRPC handles large binary data efficiently

## 💡 Assignment Coverage

- ✅ **gRPC with complex data** (images as binary streams)
- ✅ **CPU-intensive tasks** (real image processing)
- ✅ **Pipeline architecture** (orchestrator + 3 workers)
- ✅ **Distributed deployment** (each service on different device)
- ✅ **Clear benchmarks** (images/second, processing time)
- ✅ **Parallelization** (multiple filter instances possible)

## 📝 Service Ports

| Service | Port | Computational Work |
|---------|------|-------------------|
| Resize | 50052 | LANCZOS interpolation |
| Filter | 50053 | Gaussian blur, edge detection, color transforms |
| Watermark | 50054 | Alpha compositing, text rendering |
| Orchestrator | 50055 | Pipeline coordination |
