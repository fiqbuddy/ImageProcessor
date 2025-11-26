"""
Image Processing Pipeline GUI - Control Panel
Now uses XML-RPC instead of gRPC
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from xmlrpc.client import ServerProxy, Binary
import sys
import os
import time
import shutil
from PIL import Image, ImageDraw
from io import BytesIO

# Filter and format constants (replacing protobuf enums)
FILTERS = {
    'BLUR': 'BLUR',
    'SHARPEN': 'SHARPEN',
    'SEPIA': 'SEPIA',
    'BRIGHTNESS': 'BRIGHTNESS',
    'CONTRAST': 'CONTRAST',
    'GRAYSCALE': 'GRAYSCALE'
}


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
    draw.text((width//2 - 120, height//2 + 30), "For XML-RPC Processing", fill=(255, 255, 255))
    
    return image


class PipelineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("XML-RPC Image Processing Pipeline - Control Panel")
        self.root.geometry("800x600")
        
        # Variables
        self.num_images_var = tk.IntVar(value=30)
        self.container_mode_var = tk.StringVar(value="single")
        self.is_running = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎨 Image Processing Pipeline", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Number of images
        ttk.Label(config_frame, text="Number of Images:").grid(row=0, column=0, sticky=tk.W, pady=5)
        num_images_spinbox = ttk.Spinbox(config_frame, from_=1, to=100, 
                                         textvariable=self.num_images_var, width=10)
        num_images_spinbox.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Container mode
        ttk.Label(config_frame, text="Container Mode:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        mode_frame = ttk.Frame(config_frame)
        mode_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Single Container (1 instance per service)", 
                       variable=self.container_mode_var, value="single").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Multi Container (Multiple instances per service)", 
                       variable=self.container_mode_var, value="multi").pack(anchor=tk.W)
        
        # Info label
        info_text = ("Single: Uses only port 50052, 50053, 50054, 50056\n"
                    "Multi: Uses multiple ports for load balancing")
        ttk.Label(config_frame, text=info_text, foreground="gray", 
                 font=('Arial', 8)).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="▶ Start Processing", 
                                       command=self.start_processing, width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="🧹 Clear Output", 
                                       command=self.clear_output, width=20)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=400)
        self.progress.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", font=('Arial', 10))
        self.status_label.grid(row=4, column=0, columnspan=2)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Processing Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=90, 
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
    def log(self, message):
        """Add message to log text area"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_output(self):
        """Clear output folder"""
        output_dir = "output"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            self.log("🧹 Output folder cleared")
        else:
            self.log("ℹ️  Output folder doesn't exist")
            
    def start_processing(self):
        """Start batch processing in a separate thread"""
        if self.is_running:
            self.log("⚠️  Processing already in progress!")
            return
            
        # Disable start button
        self.start_button.config(state='disabled')
        self.is_running = True
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start processing in thread
        thread = threading.Thread(target=self.run_batch_processing)
        thread.daemon = True
        thread.start()
        
    def run_batch_processing(self):
        """Run the batch processing"""
        try:
            num_images = self.num_images_var.get()
            mode = self.container_mode_var.get()
            
            self.log("="*80)
            self.log(f"🚀 BATCH PROCESSING: {num_images} Images | Mode: {mode.upper()}")
            self.log("="*80)
            
            # Clean output folder
            output_dir = "output"
            if os.path.exists(output_dir):
                self.log("🧹 Cleaning output folder...")
                shutil.rmtree(output_dir)
            os.makedirs(output_dir)
            self.log("✅ Output folder ready\n")
            
            # Update status
            self.status_label.config(text=f"Processing {num_images} images...")
            
            # Connect to Orchestrator
            self.log("🔌 Connecting to Orchestrator Service (port 50055)...")
            proxy = ServerProxy('http://localhost:50055', allow_none=True)
            
            successful = 0
            failed = 0
            total_start_time = time.time()
            
            # Reset progress
            self.progress['maximum'] = num_images
            self.progress['value'] = 0
            
            for i in range(1, num_images + 1):
                self.log(f"\n🎯 IMAGE {i}/{num_images}: Processing...")
                
                # Create sample image
                sizes = [(1920, 1080), (1280, 720), (1600, 900), (2560, 1440)]
                width, height = sizes[i % len(sizes)]
                sample_image = create_sample_image(width, height)
                
                img_buffer = BytesIO()
                sample_image.save(img_buffer, format='PNG')
                img_bytes = img_buffer.getvalue()
                
                # Vary filters
                filter_sets = [
                    ['BLUR', 'SHARPEN'],
                    ['SEPIA'],
                    ['BRIGHTNESS', 'CONTRAST'],
                    ['GRAYSCALE'],
                ]
                filters = filter_sets[i % len(filter_sets)]
                
                watermarks = [f"Image #{i}", "Batch Processing", "Distributed Pipeline", "XML-RPC Demo"]
                watermark = watermarks[i % len(watermarks)]
                
                try:
                    # Create options
                    options = {
                        'target_width': 1280,
                        'target_height': 720,
                        'filters': filters,
                        'add_watermark': True,
                        'watermark_text': watermark,
                        'watermark_position': "bottom-right",
                        'output_format': 'PNG',
                        'output_quality': 90
                    }
                    
                    response = proxy.process_image(
                        f"output/batch_{i:03d}.png",
                        Binary(img_bytes),
                        options
                    )
                    
                    if response['success']:
                        result_img = Image.open(BytesIO(response['processed_image'].data))
                        result_img.save(f"output/batch_{i:03d}.png")
                        self.log(f"✅ Success! Total: {response['stats']['total_time_ms']}ms")
                        successful += 1
                    else:
                        self.log(f"❌ FAILED: {response['message']}")
                        failed += 1
                        
                except Exception as e:
                    self.log(f"❌ Image {i} failed: {str(e)}")
                    failed += 1
                
                # Update progress
                self.progress['value'] = i
                
            # Summary
            total_time = time.time() - total_start_time
            self.log("\n" + "="*80)
            self.log("✨ BATCH PROCESSING COMPLETE!")
            self.log("="*80)
            self.log(f"   Total Images:      {num_images}")
            self.log(f"   Successful:        {successful}")
            self.log(f"   Failed:            {failed}")
            self.log(f"   Total Time:        {total_time:.2f}s")
            self.log(f"   Avg Time/Image:    {total_time/num_images:.2f}s")
            self.log(f"   Throughput:        {num_images/total_time:.2f} images/second")
            self.log("="*80)
            
            self.status_label.config(text=f"✅ Complete! {successful}/{num_images} successful")
            
        except Exception as e:
            self.log(f"\n❌ Error: {str(e)}")
            self.status_label.config(text="❌ Processing failed")
        
        finally:
            # Re-enable start button
            self.start_button.config(state='normal')
            self.is_running = False


def main():
    root = tk.Tk()
    app = PipelineGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
