"""
Image Processing Client - Demonstrates the complete pipeline
"""
import grpc
import sys
import os
import time
from PIL import Image, ImageDraw
from io import BytesIO

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add generated code to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'generated'))

import image_processing_pb2
import image_processing_pb2_grpc


def create_sample_image():
    """Create a sample image for processing"""
    width, height = 1920, 1080
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    # Gradient background
    for y in range(height):
        r = int(255 * (y / height))
        g = int(128)
        b = int(255 * (1 - y / height))
        draw.rectangle([0, y, width, y + 1], fill=(r, g, b))
    
    # Shapes
    draw.rectangle([400, 300, 1500, 800], outline=(255, 255, 0), width=15)
    draw.ellipse([600, 400, 1300, 700], fill=(0, 255, 255))
    
    # Text
    draw.text((width//2 - 200, height//2 - 50), "SAMPLE IMAGE", fill=(255, 255, 255))
    draw.text((width//2 - 250, height//2 + 50), "For gRPC Processing", fill=(255, 255, 255))
    
    return image

def process_image(stub, image_data, filename, target_width=0, target_height=0, filters=None, watermark_text=None, output_format=image_processing_pb2.PNG, output_quality=90):
    """Helper to send a request and print results"""
    if filters is None: filters = []
    
    print(f"📤 Sending request for {filename}...")
    
    # Create options
    options = image_processing_pb2.ProcessingOptions(
        target_width=target_width,
        target_height=target_height,
        filters=filters,
        add_watermark=bool(watermark_text),
        watermark_text=watermark_text or "",
        watermark_position="bottom-right",
        output_format=output_format,
        output_quality=output_quality
    )

    start = time.time()
    response = stub.ProcessImage(
        image_processing_pb2.ProcessRequest(
            filename=filename,
            image_data=image_data,
            options=options
        )
    )
    
    if response.success:
        # Save result
        result_img = Image.open(BytesIO(response.processed_image))
        result_img.save(filename)
        
        print(f"✅ Success! Saved as: {filename}")
        print(f"   Process ID: {response.process_id}")
        print(f"   📊 Stats:")
        print(f"      Total Time:  {response.stats.total_time_ms}ms")
        print(f"      - Resize:    {response.stats.resize_time_ms}ms")
        print(f"      - Filters:   {response.stats.filter_time_ms}ms")
        print(f"      - Watermark: {response.stats.watermark_time_ms}ms")
        print(f"      - Format:    {response.stats.format_time_ms}ms")
        print(f"      Size: {response.stats.original_size_bytes:,} -> {response.stats.processed_size_bytes:,} bytes")
        
        print(f"   🌍 Execution Trace:")
        for stage, host in response.stats.host_map.items():
            print(f"      - {stage}: {host}")
    else:
        print(f"❌ FAILED: {response.message}")


def run_pipeline_demo():
    print("\n" + "="*80)
    print("🎨 IMAGE PROCESSING PIPELINE - Full Demo")
    print("="*80 + "\n")
    
    # Create or load image
    print("📸 Step 1: Creating sample image (1920x1080)...")
    sample_image = create_sample_image()
    
    # Convert to bytes
    img_buffer = BytesIO()
    sample_image.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()
    print(f"   ✅ Image created: {len(img_bytes):,} bytes")
    
    # Connect to Orchestrator
    print("🔌 Step 2: Connecting to Orchestrator Service (port 50055)...")
    channel = grpc.insecure_channel('localhost:50055')
    stub = image_processing_pb2_grpc.OrchestratorServiceStub(channel)
    
    try:
        # Demo 1: Full Pipeline
        print("\n" + "─"*80)
        print("🎯 DEMO 1: Full Pipeline (Resize + Filters + Watermark)")
        print("─"*80)
        
        process_image(
            stub,
            img_bytes,
            "output_full_pipeline.png",
            target_width=1280,
            target_height=720,
            filters=[
                image_processing_pb2.BLUR,
                image_processing_pb2.SHARPEN,
                image_processing_pb2.SEPIA
            ],
            watermark_text="Processed by gRPC"
        )
        
        # Demo 2: Resize Only
        print("\n" + "─"*80)
        print("🎯 DEMO 2: Resize Only")
        print("─"*80)
        
        process_image(
            stub,
            img_bytes,
            "output_resize_only.png",
            target_width=800,
            target_height=600
        )
        
        # Demo 3: Heavy Filter Processing
        print("\n" + "─"*80)
        print("🎯 DEMO 3: Heavy Processing (Multiple Filters)")
        print("─"*80)
        
        process_image(
            stub,
            img_bytes,
            "output_heavy_filters.png",
            target_width=1024,
            target_height=768,
            filters=[
                image_processing_pb2.BLUR,
                image_processing_pb2.SHARPEN,
                image_processing_pb2.EDGE_DETECT,
                image_processing_pb2.SEPIA,
                image_processing_pb2.BRIGHTNESS
            ]
        )

        # Demo 4: Format Conversion (WEBP)
        print("\n" + "─"*80)
        print("🎯 DEMO 4: Format Conversion (WEBP Quality 80)")
        print("─"*80)
        
        process_image(
            stub,
            img_bytes,
            "output_converted.webp",
            target_width=1024,
            target_height=768,
            filters=[image_processing_pb2.BRIGHTNESS],
            watermark_text="WEBP FORMAT",
            output_format=image_processing_pb2.WEBP,
            output_quality=80
        )

        # Demo 5: High Compression JPEG
        print("\n" + "─"*80)
        print("🎯 DEMO 5: High Compression JPEG (Quality 10)")
        print("─"*80)
        
        process_image(
            stub,
            img_bytes,
            "output_compressed.jpg",
            target_width=1920,
            target_height=1080,
            filters=[],
            watermark_text="LOW QUALITY",
            output_format=image_processing_pb2.JPEG,
            output_quality=10
        )
        
        print("\n" + "="*80)
        print("✨ All Demos Completed Successfully!")
        print("="*80)
        
    except grpc.RpcError as e:
        print(f"\n❌ Error: {e.details()}")
        print("\n🔧 Make sure all services are running!")
    
    finally:
        channel.close()


if __name__ == '__main__':
    run_pipeline_demo()
