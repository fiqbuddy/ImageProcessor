"""
Watermark Service - Adds text or logo watermarks to images
Now uses XML-RPC instead of gRPC
"""
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import Binary
import sys
import os
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class WatermarkService:
    
    def add_text_watermark(self, image_data, image_id, text, position, font_size, color, opacity):
        """Add text watermark to image"""
        print(f"[WatermarkService] Adding text '{text}' at {position}")
        
        start_time = time.time()
        
        try:
            # Decode binary data from XML-RPC
            image_bytes = image_data.data
            
            # Load image
            image = Image.open(BytesIO(image_bytes)).convert('RGBA')
            
            # Create transparent overlay
            overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Parse color (hex to RGB)
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            alpha = int(255 * opacity)
            rgba_color = rgb + (alpha,)
            
            # Calculate text position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if position == 'center':
                x = (image.width - text_width) // 2
                y = (image.height - text_height) // 2
            elif position == 'top-left':
                x, y = 20, 20
            elif position == 'top-right':
                x = image.width - text_width - 20
                y = 20
            elif position == 'bottom-left':
                x = 20
                y = image.height - text_height - 20
            elif position == 'bottom-right':
                x = image.width - text_width - 20
                y = image.height - text_height - 20
            else:
                x, y = 20, 20
            
            # Draw text
            draw.text((x, y), text, font=font, fill=rgba_color)
            
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
            print(f"   Text:          '{text}'")
            print(f"   Position:      {position}")
            print(f"   Opacity:       {opacity:.2f}")
            print(f"   Image ID:      {image_id}")
            print(f"   Input size:    {len(image_bytes):,} bytes")
            print(f"   Output size:   {len(watermarked_bytes):,} bytes")
            print(f"   Processing:    {processing_time}ms")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'message': "Text watermark added",
                'watermarked_image': Binary(watermarked_bytes),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return {
                'success': False,
                'message': f"Watermark failed: {str(e)}",
                'watermarked_image': Binary(b''),
                'processing_time_ms': processing_time
            }
    
    def add_logo_watermark(self, image_data, image_id, logo_data, position, scale, opacity):
        """Add logo watermark to image"""
        print(f"[WatermarkService] Adding logo at {position}")
        
        start_time = time.time()
        
        try:
            # Decode binary data from XML-RPC
            image_bytes = image_data.data
            logo_bytes = logo_data.data
            
            # Load base image and logo
            image = Image.open(BytesIO(image_bytes)).convert('RGBA')
            logo = Image.open(BytesIO(logo_bytes)).convert('RGBA')
            
            # Scale logo
            scaled_width = int(image.width * scale)
            scaled_height = int(logo.height * (scaled_width / logo.width))
            logo = logo.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            
            # Adjust logo opacity
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            logo.putalpha(alpha)
            
            # Calculate position
            if position == 'center':
                x = (image.width - logo.width) // 2
                y = (image.height - logo.height) // 2
            elif position == 'top-left':
                x, y = 20, 20
            elif position == 'top-right':
                x = image.width - logo.width - 20
                y = 20
            elif position == 'bottom-left':
                x = 20
                y = image.height - logo.height - 20
            elif position == 'bottom-right':
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
            
            return {
                'success': True,
                'message': "Logo watermark added",
                'watermarked_image': Binary(watermarked_bytes),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return {
                'success': False,
                'message': f"Logo watermark failed: {str(e)}",
                'watermarked_image': Binary(b''),
                'processing_time_ms': processing_time
            }


def serve(port=50054):
    """Start the Watermark Service server"""
    server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True, logRequests=False)
    server.register_instance(WatermarkService())
    print(f"🏷️  Watermark Service started on port {port}\n")
    server.serve_forever()


if __name__ == '__main__':
    serve()
