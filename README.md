# Wan DR34ML4Y RunPod Serverless Deployment

## 🚀 Quick Start

### Step 1: Build Docker Image

```bash
# Login to Docker Hub
docker login

# Build the image (replace YOUR_USERNAME with your Docker Hub username)
docker build -t YOUR_USERNAME/wan-dreamy:latest .

# Push to Docker Hub
docker push YOUR_USERNAME/wan-dreamy:latest
```

### Step 2: Create RunPod Serverless Endpoint

1. Go to https://www.runpod.io/console/serverless
2. Click **"+ New Endpoint"**
3. Configure:
   - **Name:** `wan-dreamy-nsfw`
   - **Docker Image:** `YOUR_USERNAME/wan-dreamy:latest`
   - **GPU:** Select **A40 48GB** or **A100 80GB** (14B model needs VRAM)
   - **Max Workers:** 1-3
   - **Idle Timeout:** 60 seconds
   - **Flash Boot:** Enable (faster cold starts)
4. Click **Create**

### Step 3: Get Your Endpoint ID

After creation, copy the Endpoint ID (e.g., `abc123xyz`)

Add to your NEXUS AI Pro `.env` file:
```
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_DREAMY_ENDPOINT_ID=abc123xyz
```

---

## 📝 API Usage

### Image to Video

```json
{
  "input": {
    "mode": "image_to_video",
    "image": "https://example.com/image.jpg",
    "prompt": "smooth cinematic motion, the woman smiles",
    "negative_prompt": "blurry, low quality, static",
    "width": 480,
    "height": 480,
    "num_frames": 16,
    "num_inference_steps": 30,
    "guidance_scale": 7.5,
    "fps": 8,
    "seed": 0
  }
}
```

### Text to Video

```json
{
  "input": {
    "mode": "text_to_video",
    "prompt": "a beautiful woman walking on the beach, cinematic",
    "negative_prompt": "blurry, low quality, ugly",
    "width": 480,
    "height": 480,
    "num_frames": 16,
    "num_inference_steps": 30,
    "guidance_scale": 7.5,
    "fps": 8,
    "seed": 0
  }
}
```

### Response

```json
{
  "video": "data:video/mp4;base64,AAAA...",
  "seed": 12345,
  "mode": "image_to_video",
  "width": 480,
  "height": 480,
  "num_frames": 16,
  "fps": 8
}
```

---

## ⚙️ Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| mode | string | "image_to_video" | "image_to_video" or "text_to_video" |
| image | string | - | Image URL or base64 (required for I2V) |
| prompt | string | "smooth cinematic motion" | Motion/content description |
| negative_prompt | string | "blurry, low quality..." | What to avoid |
| width | int | 480 | Video width (256-720, divisible by 8) |
| height | int | 480 | Video height (256-720, divisible by 8) |
| num_frames | int | 16 | Number of frames (8-32) |
| num_inference_steps | int | 30 | Quality steps (10-50) |
| guidance_scale | float | 7.5 | Prompt adherence (1-20) |
| fps | int | 8 | Output video FPS (4-24) |
| seed | int | 0 | Random seed (0 = random) |

---

## 💡 Tips

1. **GPU Selection:** Use A40 48GB or A100 for best results
2. **Cold Starts:** First run takes 2-5 minutes to load models
3. **Dimensions:** Keep width/height at 480 for faster generation
4. **Frames:** 16 frames = ~2 second video at 8fps
5. **NSFW Content:** No filters - full creative freedom

---

## 🔧 Troubleshooting

### Out of Memory Error
- Reduce `width` and `height` to 480
- Reduce `num_frames` to 16
- Use A100 80GB GPU instead of A40

### Slow Generation
- Reduce `num_inference_steps` to 20
- Reduce `num_frames` to 12

### Model Loading Fails
- Check Docker image was pushed correctly
- Verify RunPod has access to Docker Hub
- Check RunPod logs for detailed errors
