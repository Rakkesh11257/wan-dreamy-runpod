import runpod
import torch
import base64
import os
import tempfile
from io import BytesIO
from PIL import Image
import imageio
import requests

# Global model cache
pipe_i2v = None
pipe_t2v = None

def load_i2v_model():
    """Load Image-to-Video model"""
    global pipe_i2v
    
    if pipe_i2v is None:
        from diffusers import DiffusionPipeline
        print("🎬 Loading Wan I2V 14B model...")
        pipe_i2v = DiffusionPipeline.from_pretrained(
            "Wan-AI/Wan2.1-I2V-14B-480P",
            torch_dtype=torch.float16,
            variant="fp16"
        )
        pipe_i2v.to("cuda")
        pipe_i2v.enable_model_cpu_offload()  # Save VRAM
        print("✅ I2V model loaded!")
    
    return pipe_i2v

def load_t2v_model():
    """Load Text-to-Video model"""
    global pipe_t2v
    
    if pipe_t2v is None:
        from diffusers import DiffusionPipeline
        print("🎬 Loading Wan T2V 14B model...")
        pipe_t2v = DiffusionPipeline.from_pretrained(
            "Wan-AI/Wan2.1-T2V-14B-480P",
            torch_dtype=torch.float16,
            variant="fp16"
        )
        pipe_t2v.to("cuda")
        pipe_t2v.enable_model_cpu_offload()  # Save VRAM
        print("✅ T2V model loaded!")
    
    return pipe_t2v

def download_image(url_or_base64):
    """Download image from URL or decode base64"""
    try:
        if url_or_base64.startswith('data:'):
            # Base64 data URL
            base64_data = url_or_base64.split(',')[1]
            image_data = base64.b64decode(base64_data)
            return Image.open(BytesIO(image_data)).convert('RGB')
        elif url_or_base64.startswith('http'):
            # URL
            response = requests.get(url_or_base64, timeout=60)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert('RGB')
        else:
            # Raw base64
            image_data = base64.b64decode(url_or_base64)
            return Image.open(BytesIO(image_data)).convert('RGB')
    except Exception as e:
        raise ValueError(f"Failed to load image: {str(e)}")

def frames_to_video(frames, fps, output_path):
    """Convert frames to MP4 video"""
    import numpy as np
    
    # Convert frames to numpy arrays if needed
    numpy_frames = []
    for frame in frames:
        if isinstance(frame, Image.Image):
            numpy_frames.append(np.array(frame))
        elif isinstance(frame, np.ndarray):
            numpy_frames.append(frame)
        else:
            numpy_frames.append(np.array(frame))
    
    # Write video
    imageio.mimwrite(output_path, numpy_frames, fps=fps, codec='libx264', quality=8)

def handler(job):
    """
    RunPod Serverless Handler for Wan Video Generation
    
    Supports:
    - image_to_video: Generate video from input image
    - text_to_video: Generate video from text prompt
    """
    job_input = job.get("input", {})
    
    # Get parameters with defaults
    mode = job_input.get("mode", "image_to_video")
    prompt = job_input.get("prompt", "smooth cinematic motion, high quality")
    negative_prompt = job_input.get("negative_prompt", "blurry, low quality, distorted, ugly, static, watermark")
    image_url = job_input.get("image")
    width = int(job_input.get("width", 480))
    height = int(job_input.get("height", 480))
    num_frames = int(job_input.get("num_frames", 16))
    num_inference_steps = int(job_input.get("num_inference_steps", 30))
    guidance_scale = float(job_input.get("guidance_scale", 7.5))
    fps = int(job_input.get("fps", 8))
    seed = int(job_input.get("seed", 0))
    
    # Ensure dimensions are divisible by 8
    width = (width // 8) * 8
    height = (height // 8) * 8
    width = max(256, min(720, width))
    height = max(256, min(720, height))
    
    print(f"🎬 Job received: mode={mode}, prompt={prompt[:50]}...")
    print(f"   Dimensions: {width}x{height}, frames={num_frames}, steps={num_inference_steps}")
    
    # Set up generator for reproducibility
    generator = torch.Generator("cuda")
    if seed > 0:
        generator.manual_seed(seed)
        actual_seed = seed
    else:
        actual_seed = generator.seed()
    
    try:
        if mode == "image_to_video":
            # Validate input
            if not image_url:
                return {"error": "Image URL required for image_to_video mode"}
            
            # Load model
            pipe = load_i2v_model()
            
            # Download and process image
            print("📥 Downloading input image...")
            image = download_image(image_url)
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            print(f"   Image resized to {width}x{height}")
            
            # Generate video
            print("🎬 Generating video...")
            output = pipe(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )
            
        elif mode == "text_to_video":
            # Validate input
            if not prompt:
                return {"error": "Prompt required for text_to_video mode"}
            
            # Load model
            pipe = load_t2v_model()
            
            # Generate video
            print("🎬 Generating video from text...")
            output = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )
        else:
            return {"error": f"Invalid mode: {mode}. Use 'image_to_video' or 'text_to_video'"}
        
        # Extract frames
        print("📹 Processing output frames...")
        frames = output.frames[0]  # List of PIL Images or numpy arrays
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            output_path = f.name
        
        # Convert frames to video
        frames_to_video(frames, fps, output_path)
        print(f"✅ Video saved: {output_path}")
        
        # Read and encode as base64
        with open(output_path, 'rb') as f:
            video_bytes = f.read()
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        # Get file size
        file_size_mb = len(video_bytes) / (1024 * 1024)
        print(f"   Video size: {file_size_mb:.2f} MB")
        
        # Cleanup temp file
        os.unlink(output_path)
        
        return {
            "video": f"data:video/mp4;base64,{video_base64}",
            "seed": actual_seed,
            "mode": mode,
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "fps": fps
        }
        
    except torch.cuda.OutOfMemoryError:
        # Clear CUDA cache and return error
        torch.cuda.empty_cache()
        return {"error": "GPU out of memory. Try reducing dimensions or num_frames."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# Start the serverless worker
runpod.serverless.start({"handler": handler})
