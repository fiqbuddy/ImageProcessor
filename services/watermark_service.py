"""
Watermark Service - Adds text or logo watermarks to images
"""
import grpc
from concurrent import futures
import sys
import os
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add generated code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'generated'))

import image_processing_pb2
import image_processing_pb2_grpc


class WatermarkServiceServicer(image_processing_pb2_grpc.WatermarkServiceServicer):
    
    def AddTextWatermark(self, request, context):
        """Add text watermark to image"""
        print(f"[WatermarkService] Adding text '{request.text}' at {request.position}")
        
        start_time = time.time()
        
        try:
            # Load image
            image = Image.open(BytesIO(request.image_data)).convert('RGBA')
            
            # Create transparent overlay
            overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", request.font_size)
            except:
                font = ImageFont.load_default()
            
            # Parse color (hex to RGB)
            color = request.color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            alpha = int(255 * request.opacity)
            rgba_color = rgb + (alpha,)
            
            # Calculate text position
            bbox = draw.textbbox((0, 0), request.text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if request.position == 'center':
                x = (image.width - text_width) // 2
                y = (image.height - text_height) // 2
            elif request.position == 'top-left':
                x, y = 20, 20
            elif request.position == 'top-right':
                x = image.width - text_width - 20
                y = 20
            elif request.position == 'bottom-left':
                x = 20
                y = image.height - text_height - 20
            elif request.position == 'bottom-right':
                x = image.width - text_width - 20
                y = image.height - text_height - 20
            else:
                x, y = 20, 20
            
            # Draw text
            draw.text((x, y), request.text, font=font, fill=rgba_color)
            
            # Composite overlay with original image
            watermarked = Image.alpha_composite(image, overlay)
            watermarked = watermarked.convert('RGB')
            
            # Convert to bytes
            output_buffer = BytesIO()
            watermarked.save(output_buffer, format='PNG')
            watermarked_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"{'='*60}")
            print(f"✅ WATERMARK COMPLETE")
            print(f"{'='*60}")
            print(f"   Text:          '{request.text}'")
            print(f"   Position:      {request.position}")
            print(f"   Opacity:       {request.opacity:.2f}")
            print(f"   Image ID:      {request.image_id}")
            print(f"   Input size:    {len(request.image_data):,} bytes")
            print(f"   Output size:   {len(watermarked_bytes):,} bytes")
            print(f"   Processing:    {processing_time}ms")
            print(f"{'='*60}\n")
            
            return image_processing_pb2.WatermarkResponse(
                success=True,
                message="Text watermark added",
                watermarked_image=watermarked_bytes,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return image_processing_pb2.WatermarkResponse(
                success=False,
                message=f"Watermark failed: {str(e)}",
                watermarked_image=b'',
                processing_time_ms=processing_time
            )
    
    def AddLogoWatermark(self, request, context):
        """Add logo watermark to image"""
        print(f"[WatermarkService] Adding logo at {request.position}")
        
        start_time = time.time()
        
        try:
            # Load base image and logo
            image = Image.open(BytesIO(request.image_data)).convert('RGBA')
            logo = Image.open(BytesIO(request.logo_data)).convert('RGBA')
            
            # Scale logo
            scaled_width = int(image.width * request.scale)
            scaled_height = int(logo.height * (scaled_width / logo.width))
            logo = logo.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            
            # Adjust logo opacity
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: int(p * request.opacity))
            logo.putalpha(alpha)
            
            # Calculate position
            if request.position == 'center':
                x = (image.width - logo.width) // 2
                y = (image.height - logo.height) // 2
            elif request.position == 'top-left':
                x, y = 20, 20
            elif request.position == 'top-right':
                x = image.width - logo.width - 20
                y = 20
            elif request.position == 'bottom-left':
                x = 20
                y = image.height - logo.height - 20
            elif request.position == 'bottom-right':
                x = image.width - logo.width - 20
                y = image.height - logo.height - 20
            else:
                x, y = 20, 20
            
            # Paste logo onto image
            image.paste(logo, (x, y), logo)
            watermarked = image.convert('RGB')
            
            # Convert to bytes
            output_buffer = BytesIO()
            watermarked.save(output_buffer, format='PNG')
            watermarked_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ✅ Logo watermark added in {processing_time}ms")
            
            return image_processing_pb2.WatermarkResponse(
                success=True,
                message="Logo watermark added",
                watermarked_image=watermarked_bytes,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return image_processing_pb2.WatermarkResponse(
                success=False,
                message=f"Logo watermark failed: {str(e)}",
                watermarked_image=b'',
                processing_time_ms=processing_time
            )


def serve(port=50054):
    """Start the Watermark Service server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_WatermarkServiceServicer_to_server(
        WatermarkServiceServicer(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"🏷️  Watermark Service started on port {port}\n")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
