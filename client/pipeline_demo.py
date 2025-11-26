"""
Image Processing Client - Demonstrates the complete pipeline with batch processing
"""
import grpc
import sys
import os
import time
import shutil
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


def create_sample_image(width=1920, height=1080):
    """Create a sample image for processing"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    # Gradient background
    for y in range(height):
        r = int(255 * (y / height))
        g = int(128)
        b = int(255 * (1 - y / height))
        draw.rectangle([0, y, width, y + 1], fill=(r, g, b))
    
    # Shapes (scaled to image size)
    scale_x = width / 1920
    scale_y = height / 1080
    draw.rectangle([int(400*scale_x), int(300*scale_y), int(1500*scale_x), int(800*scale_y)], 
                   outline=(255, 255, 0), width=max(5, int(15*min(scale_x, scale_y))))
    draw.ellipse([int(600*scale_x), int(400*scale_y), int(1300*scale_x), int(700*scale_y)], 
                 fill=(0, 255, 255))
    
    # Text
    draw.text((width//2 - 100, height//2 - 30), "SAMPLE IMAGE", fill=(255, 255, 255))
    draw.text((width//2 - 120, height//2 + 30), "For gRPC Processing", fill=(255, 255, 255))
    
    return image

def process_image(stub, image_data, filename, target_width=0, target_height=0, filters=None, watermark_text=None, output_format=image_processing_pb2.PNG, output_quality=90):
    """Helper to send a request and print results"""
    if filters is None: filters = []
    
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
        
        print(f"✅ Success! Total: {response.stats.total_time_ms}ms | Saved: {filename}")
    else:
        print(f"❌ FAILED: {response.message}")


def run_pipeline_demo():
    print("\n" + "="*80)
    print("🎨 IMAGE PROCESSING PIPELINE - Batch Demo")
    print("="*80 + "\n")
    
    # Clean output folder
    output_dir = "output"
    if os.path.exists(output_dir):
        print(f"🧹 Cleaning output folder...")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"✅ Output folder ready\n")
    
    # Connect to Orchestrator
    print("🔌 Connecting to Orchestrator Service (port 50055)...")
    channel = grpc.insecure_channel('localhost:50055')
    stub = image_processing_pb2_grpc.OrchestratorServiceStub(channel)
    
    # Batch processing configuration
    NUM_IMAGES = 30
    successful = 0
    failed = 0
    total_start_time = time.time()
    
    print("\n" + "="*80)
    print(f"🚀 BATCH PROCESSING: {NUM_IMAGES} Images")
    print("="*80)
    
    try:
        for i in range(1, NUM_IMAGES + 1):
            print(f"\n🎯 IMAGE {i}/{NUM_IMAGES}: ", end='', flush=True)
            
            # Create sample image (vary the size for diversity)
            sizes = [(1920, 1080), (1280, 720), (1600, 900), (2560, 1440)]
            width, height = sizes[i % len(sizes)]
            sample_image = create_sample_image(width, height)
            
            # Convert to bytes
            img_buffer = BytesIO()
            sample_image.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            # Vary the processing parameters
            filter_sets = [
                [image_processing_pb2.BLUR, image_processing_pb2.SHARPEN],
                [image_processing_pb2.SEPIA],
                [image_processing_pb2.BRIGHTNESS, image_processing_pb2.CONTRAST],
                [image_processing_pb2.GRAYSCALE],
            ]
            filters = filter_sets[i % len(filter_sets)]
            
            watermarks = [
                f"Image #{i}",
                f"Batch Processing",
                f"Distributed Pipeline",
                f"gRPC Demo"
            ]
            watermark = watermarks[i % len(watermarks)]
            
            try:
                process_image(
                    stub,
                    img_bytes,
                    f"output/batch_{i:03d}.png",
                    target_width=1280,
                    target_height=720,
                    filters=filters,
                    watermark_text=watermark,
                    output_format=image_processing_pb2.PNG,
                    output_quality=90
                )
                successful += 1
            except Exception as e:
                print(f"❌ Image {i} failed: {str(e)}")
                failed += 1
        
        # Summary
        total_time = time.time() - total_start_time
        print("\n" + "="*80)
        print("✨ BATCH PROCESSING COMPLETE!")
        print("="*80)
        print(f"   Total Images:      {NUM_IMAGES}")
        print(f"   Successful:        {successful}")
        print(f"   Failed:            {failed}")
        print(f"   Total Time:        {total_time:.2f}s")
        print(f"   Avg Time/Image:    {total_time/NUM_IMAGES:.2f}s")
        print(f"   Throughput:        {NUM_IMAGES/total_time:.2f} images/second")
        print("="*80)
        print(f"\n📂 Output: output/batch_001.png to output/batch_{NUM_IMAGES:03d}.png")
        print("💡 Check worker terminals to see distributed processing activity!")
        print("="*80 + "\n")
        
    except grpc.RpcError as e:
        print(f"\n❌ Error: {e.details()}")
        print("\n🔧 Make sure all services are running!")
    
    finally:
        channel.close()


if __name__ == '__main__':
    run_pipeline_demo()
