import grpc
from concurrent import futures
import time
import os
import sys
from io import BytesIO
from PIL import Image

# Add generated code to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'generated'))

import image_processing_pb2
import image_processing_pb2_grpc

class FormatService(image_processing_pb2_grpc.FormatServiceServicer):
    def ConvertFormat(self, request, context):
        start_time = time.time()
        print(f"📦 Processing format request for image: {request.image_id}")
        
        try:
            # Load image from bytes
            image = Image.open(BytesIO(request.image_data))
            
            # Determine output format
            output_format = 'PNG' # Default
            if request.format == image_processing_pb2.JPEG:
                output_format = 'JPEG'
                # JPEG doesn't support RGBA (transparency), convert to RGB
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
            elif request.format == image_processing_pb2.WEBP:
                output_format = 'WEBP'
            
            # Save to bytes with specified quality
            output_buffer = BytesIO()
            
            # Quality handling
            quality = request.quality
            if quality <= 0 or quality > 100:
                quality = 85  # Default quality
                
            print(f"   Converting to {output_format} with quality={quality}...")
            
            if output_format == 'PNG':
                # PNG is lossless, optimize=True helps size
                image.save(output_buffer, format='PNG', optimize=True)
            else:
                image.save(output_buffer, format=output_format, quality=quality)
                
            formatted_data = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            print(f"✅ Format complete in {processing_time}ms. Size: {len(request.image_data)} -> {len(formatted_data)} bytes")
            
            return image_processing_pb2.FormatResponse(
                success=True,
                message="Format conversion successful",
                formatted_image=formatted_data,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            print(f"❌ Error formatting image: {str(e)}")
            return image_processing_pb2.FormatResponse(
                success=False,
                message=f"Format failed: {str(e)}",
                formatted_image=b"",
                processing_time_ms=0
            )

def serve(port=50056):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_FormatServiceServicer_to_server(FormatService(), server)
    
    # Enable reflection
    SERVICE_NAMES = (
        image_processing_pb2.DESCRIPTOR.services_by_name['FormatService'].full_name,
        grpc.reflection.SERVICE_NAME,
    )
    try:
        from grpc_reflection.v1alpha import reflection
        reflection.enable_server_reflection(SERVICE_NAMES, server)
    except ImportError:
        pass

    server.add_insecure_port(f'[::]:{port}')
    print(f"📦 Format Service started on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    # Allow port override via environment variable
    port = int(os.environ.get('PORT', 50056))
    serve(port)
