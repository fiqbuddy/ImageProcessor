"""
Resize Service - Resizes images to specified dimensions
Computationally intensive: Uses Pillow for image manipulation
"""
import grpc
from concurrent import futures
import sys
import os
import time
from io import BytesIO
from PIL import Image

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add generated code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'generated'))

import image_processing_pb2
import image_processing_pb2_grpc


class ResizeServiceServicer(image_processing_pb2_grpc.ResizeServiceServicer):
    def ResizeImage(self, request, context):
        """Resize an image to target dimensions"""
        print(f"[ResizeService] Processing image_id={request.image_id}, target={request.target_width}x{request.target_height}")
        
        start_time = time.time()
        
        try:
            # Load image from bytes
            image = Image.open(BytesIO(request.image_data))
            original_size = image.size
            print(f"  Original size: {original_size[0]}x{original_size[1]}")
            
            # Calculate new dimensions
            if request.maintain_aspect_ratio:
                # Calculate aspect ratio
                aspect = original_size[0] / original_size[1]
                if request.target_width > 0 and request.target_height > 0:
                    # Use the dimension that results in smaller image
                    new_width = request.target_width
                    new_height = int(new_width / aspect)
                    if new_height > request.target_height:
                        new_height = request.target_height
                        new_width = int(new_height * aspect)
                elif request.target_width > 0:
                    new_width = request.target_width
                    new_height = int(new_width / aspect)
                else:
                    new_height = request.target_height
                    new_width = int(new_height * aspect)
            else:
                new_width = request.target_width if request.target_width > 0 else original_size[0]
                new_height = request.target_height if request.target_height > 0 else original_size[1]
            
            # Resize the image (use LANCZOS for high quality)
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output_buffer = BytesIO()
            resized_image.save(output_buffer, format=image.format or 'PNG')
            resized_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"{'='*60}")
            print(f"✅ RESIZE COMPLETE")
            print(f"{'='*60}")
            print(f"   Image ID:      {request.image_id}")
            print(f"   Original:      {original_size[0]}x{original_size[1]}")
            print(f"   Resized to:    {new_width}x{new_height}")
            print(f"   Input size:    {len(request.image_data):,} bytes")
            print(f"   Output size:   {len(resized_bytes):,} bytes")
            print(f"   Processing:    {processing_time}ms")
            print(f"{'='*60}\n")
            
            return image_processing_pb2.ResizeResponse(
                success=True,
                message=f"Resized from {original_size[0]}x{original_size[1]} to {new_width}x{new_height}",
                resized_image=resized_bytes,
                new_width=new_width,
                new_height=new_height,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return image_processing_pb2.ResizeResponse(
                success=False,
                message=f"Resize failed: {str(e)}",
                resized_image=b'',
                processing_time_ms=processing_time
            )
    
    def GetThumbnail(self, request, context):
        """Generate a square thumbnail"""
        print(f"[ResizeService] Creating thumbnail: size={request.size}")
        
        try:
            image = Image.open(BytesIO(request.image_data))
            
            # Create square thumbnail
            image.thumbnail((request.size, request.size), Image.Resampling.LANCZOS)
            
            # Convert to bytes
            output_buffer = BytesIO()
            image.save(output_buffer,format='PNG')
            thumb_bytes = output_buffer.getvalue()
            
            return image_processing_pb2.ImageData(
                data=thumb_bytes,
                width=image.width,
                height=image.height,
                format='PNG'
            )
            
        except Exception as e:
            print(f"  ❌ Thumbnail error: {str(e)}")
            return image_processing_pb2.ImageData(
                data=b'',
                width=0,
                height=0,
                format='ERROR'
            )


def serve(port=50052):
    """Start the Resize Service server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_ResizeServiceServicer_to_server(
        ResizeServiceServicer(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"🖼️  Resize Service started on port {port}\n")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
