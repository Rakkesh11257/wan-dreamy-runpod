FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    diffusers==0.32.2 \
    transformers>=4.45.0 \
    accelerate>=0.33.0 \
    safetensors \
    huggingface_hub \
    peft \
    imageio[ffmpeg] \
    imageio-ffmpeg \
    opencv-python-headless \
    pillow \
    runpod \
    "numpy<2" \
    requests

# Copy handler
COPY handler.py /app/handler.py

# Pre-download models (optional - uncomment for faster cold starts, but larger image)
# RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('Wan-AI/Wan2.1-I2V-14B-480P')"
# RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('Wan-AI/Wan2.1-T2V-14B-480P')"

CMD ["python", "-u", "handler.py"]
