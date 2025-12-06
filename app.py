#!/usr/bin/env python3
"""
Flask Web App - Instagram Carousel Editor
Browse carousels, test edits with NanaBanana, approve for ComfyUI batch processing
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import requests
import base64
import subprocess
import tempfile
import uuid
import json
import time
from datetime import datetime

load_dotenv('.env.local')

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# WaveSpeed NanaBanana API
WAVESPEED_API_KEY = os.getenv('WAVESPEED_API_KEY')
WAVESPEED_API_URL = os.getenv('WAVESPEED_API_URL')


@app.route('/')
def index():
    """Homepage - Show all carousels"""

    # Get all carousels, ordered by most recent
    result = supabase.table('instagram_carousels').select('*').order('posted_at', desc=True).execute()
    carousels = result.data

    # For each carousel, get first image
    for carousel in carousels:
        images = supabase.table('carousel_images').select('*').eq('carousel_id', carousel['id']).order('image_order').limit(1).execute()
        carousel['first_image'] = images.data[0] if images.data else None

    return render_template('index.html', carousels=carousels)


@app.route('/carousel/<carousel_id>')
def carousel_detail(carousel_id):
    """Carousel detail page - Show all images"""

    # Get carousel
    carousel_result = supabase.table('instagram_carousels').select('*').eq('id', carousel_id).execute()
    if not carousel_result.data:
        return "Carousel not found", 404

    carousel = carousel_result.data[0]

    # Get all images for this carousel
    images_result = supabase.table('carousel_images').select('*').eq('carousel_id', carousel_id).order('image_order').execute()
    images = images_result.data

    return render_template('carousel_detail.html', carousel=carousel, images=images)


@app.route('/test_edit/<image_id>')
def test_edit(image_id):
    """Edit test page - Enter prompt and send to NanaBanana"""

    # Get image
    image_result = supabase.table('carousel_images').select('*').eq('id', image_id).execute()
    if not image_result.data:
        return "Image not found", 404

    image = image_result.data[0]

    # Get carousel
    carousel_result = supabase.table('instagram_carousels').select('*').eq('id', image['carousel_id']).execute()
    carousel = carousel_result.data[0]

    return render_template('test_edit.html', image=image, carousel=carousel)


@app.route('/api/submit_edit', methods=['POST'])
def submit_edit():
    """API endpoint - Submit edit to NanaBanana"""

    data = request.json
    image_id = data.get('image_id')
    carousel_id = data.get('carousel_id')
    edit_prompt = data.get('edit_prompt')

    # Get image URL
    image_result = supabase.table('carousel_images').select('*').eq('id', image_id).execute()
    if not image_result.data:
        return jsonify({'error': 'Image not found'}), 404

    image = image_result.data[0]
    image_url = image.get('local_path') or image['image_url']

    # Create edit test record
    edit_test_data = {
        'carousel_id': carousel_id,
        'image_id': image_id,
        'edit_prompt': edit_prompt,
        'status': 'processing'
    }

    test_result = supabase.table('edit_tests').insert(edit_test_data).execute()
    test_id = test_result.data[0]['id']

    try:
        # Call NanaBanana API with correct payload
        print(f"Calling NanaBanana API with prompt: {edit_prompt}")

        payload = {
            "prompt": edit_prompt,
            "images": [image_url],
            "aspect_ratio": "1:1",
            "resolution": "1k",  # Using 1k for faster processing
            "output_format": "jpeg",
            "enable_sync_mode": True,  # Wait for completion
            "enable_base64_output": False
        }

        headers = {
            "Authorization": f"Bearer {WAVESPEED_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(WAVESPEED_API_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        result = response.json()

        # Extract result image URL from correct response structure
        if result.get('code') != 200:
            raise Exception(f"API returned error: {result.get('message', 'Unknown error')}")

        data = result.get('data', {})
        if not data.get('outputs') or len(data['outputs']) == 0:
            raise Exception(f"No image outputs in response: {result}")

        result_url = data['outputs'][0]

        # Update edit test with result
        supabase.table('edit_tests').update({
            'nanabana_result_url': result_url,
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }).eq('id', test_id).execute()

        return jsonify({
            'success': True,
            'test_id': test_id,
            'result_url': result_url,
            'original_url': image_url
        })

    except Exception as e:
        print(f"Error calling NanaBanana: {e}")

        # Update edit test with error
        supabase.table('edit_tests').update({
            'status': 'rejected',
            'notes': str(e)
        }).eq('id', test_id).execute()

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/review/<test_id>')
def review_edit(test_id):
    """Review page - Show before/after, approve or reject"""

    # Get edit test
    test_result = supabase.table('edit_tests').select('*').eq('id', test_id).execute()
    if not test_result.data:
        return "Test not found", 404

    test = test_result.data[0]

    # Get image
    image_result = supabase.table('carousel_images').select('*').eq('id', test['image_id']).execute()
    image = image_result.data[0]

    # Get carousel
    carousel_result = supabase.table('instagram_carousels').select('*').eq('id', test['carousel_id']).execute()
    carousel = carousel_result.data[0]

    # Get other images in carousel (for batch processing preview)
    other_images_result = supabase.table('carousel_images').select('*').eq('carousel_id', test['carousel_id']).neq('id', test['image_id']).order('image_order').execute()
    other_images = other_images_result.data

    return render_template('review.html', test=test, image=image, carousel=carousel, other_images=other_images)


@app.route('/api/approve_edit/<test_id>', methods=['POST'])
def approve_edit(test_id):
    """API endpoint - Approve edit and batch process remaining images with Workflow 4"""

    data = request.json or {}
    notes = data.get('notes', '')

    # RunPod/ComfyUI configuration
    COMFYUI_API_URL = "https://9io0dgfk3xonew-8188.proxy.runpod.net"
    RUNPOD_SSH_HOST = "203.57.40.245"
    RUNPOD_SSH_PORT = "10120"
    SSH_KEY_PATH = os.path.expanduser("~/.ssh/id_ed25519")

    # Update edit test status
    supabase.table('edit_tests').update({
        'status': 'approved',
        'approved_at': datetime.now().isoformat(),
        'notes': notes
    }).eq('id', test_id).execute()

    # Get test details
    test_result = supabase.table('edit_tests').select('*').eq('id', test_id).execute()
    test = test_result.data[0]

    # Get approved edited image URL (this will be our model image)
    model_image_url = test['nanabana_result_url']
    original_prompt = test['edit_prompt']

    # Get other images from same carousel (these are pose references)
    other_images = supabase.table('carousel_images').select('*').eq('carousel_id', test['carousel_id']).neq('id', test['image_id']).order('image_order').execute()

    if not other_images.data:
        return jsonify({
            'success': True,
            'message': 'Edit approved! No other images to process.'
        })

    # Create batch job record
    batch_data = {
        'edit_test_id': test_id,
        'carousel_id': test['carousel_id'],
        'status': 'processing',
        'images_to_process': [{'id': img['id'], 'url': img.get('local_path') or img['image_url'], 'order': img['image_order']} for img in other_images.data],
        'workflow_name': 'OpenPose Workflow 2 (Batch)'
    }

    batch_result = supabase.table('comfyui_batches').insert(batch_data).execute()
    batch_id = batch_result.data[0]['id']

    try:
        # 1. Download model image (NanaBanana edited image) to RunPod
        print(f"📥 Downloading model image to RunPod...")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_model:
            model_response = requests.get(model_image_url, timeout=30)
            model_response.raise_for_status()
            tmp_model.write(model_response.content)
            tmp_model_path = tmp_model.name

        model_filename = f"model_{uuid.uuid4().hex[:8]}.jpg"

        subprocess.run([
            'scp', '-P', RUNPOD_SSH_PORT, '-i', SSH_KEY_PATH,
            tmp_model_path,
            f'root@{RUNPOD_SSH_HOST}:/workspace/ComfyUI/input/{model_filename}'
        ], check=True, timeout=30)

        os.unlink(tmp_model_path)
        print(f"✅ Model image uploaded as {model_filename}")

        # 2. Create pose images folder on RunPod
        pose_folder = f"pose_{uuid.uuid4().hex[:8]}"
        subprocess.run([
            'ssh', '-p', RUNPOD_SSH_PORT, '-i', SSH_KEY_PATH,
            f'root@{RUNPOD_SSH_HOST}',
            f'mkdir -p /workspace/ComfyUI/input/{pose_folder}'
        ], check=True, timeout=10)

        # 3. Download all pose reference images to RunPod
        print(f"📥 Downloading {len(other_images.data)} pose images to RunPod...")

        for idx, img_data in enumerate(other_images.data):
            img_url = img_data.get('local_path') or img_data['image_url']

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_pose:
                pose_response = requests.get(img_url, timeout=30)
                pose_response.raise_for_status()
                tmp_pose.write(pose_response.content)
                tmp_pose_path = tmp_pose.name

            pose_filename = f"pose{idx + 1}.jpg"

            subprocess.run([
                'scp', '-P', RUNPOD_SSH_PORT, '-i', SSH_KEY_PATH,
                tmp_pose_path,
                f'root@{RUNPOD_SSH_HOST}:/workspace/ComfyUI/input/{pose_folder}/{pose_filename}'
            ], check=True, timeout=30)

            os.unlink(tmp_pose_path)

        print(f"✅ All pose images uploaded to {pose_folder}")

        # 4. Load Workflow 2 template (has OpenPose preprocessing)
        workflow_path = '/workspaces/business/OpenPose Workflow 2 - Jockerai (2).json'
        with open(workflow_path, 'r') as f:
            workflow_template = json.load(f)

        # 5. Trigger Workflow 2 for each pose image (hybrid approach)
        print(f"🚀 Triggering Workflow 2 for {len(other_images.data)} poses...")

        import random
        prompt_ids = []

        for pose_index, pose_img in enumerate(other_images.data):
            workflow = json.loads(json.dumps(workflow_template))  # Deep copy

            # Configure workflow for this specific pose
            workflow["67"]["inputs"]["unet_name"] = "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
            workflow["78"]["inputs"]["image"] = model_filename  # Model image (NanaBanana edit)
            workflow["179"]["inputs"]["image"] = f"{pose_folder}/pose{pose_index + 1}.jpg"  # This specific pose
            workflow["74"]["inputs"]["seed"] = random.randint(1000000000000, 9999999999999)
            workflow["94"]["inputs"]["filename_prefix"] = f"{batch_id}_pose{pose_index + 1}"

            # Trigger workflow
            payload = {"prompt": workflow}
            response = requests.post(f"{COMFYUI_API_URL}/prompt", json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if 'prompt_id' in result:
                prompt_ids.append(result['prompt_id'])
                print(f"  ✅ Pose {pose_index + 1}/{len(other_images.data)}: {result['prompt_id']}")

            time.sleep(1)  # Small delay between requests

        print(f"✅ All workflows triggered! Prompt IDs: {prompt_ids}")

        # Update batch status
        supabase.table('comfyui_batches').update({
            'status': 'processing'
        }).eq('id', batch_id).execute()

        # 6. Poll for completion and download results
        print(f"⏳ Waiting for all workflows to complete...")
        max_attempts = 60  # 60 * 5 seconds = 5 minutes total
        completed_images = []

        for idx, prompt_id in enumerate(prompt_ids):
            print(f"\n📊 Polling pose {idx + 1}/{len(prompt_ids)} (Prompt ID: {prompt_id})")
            attempt = 0
            output_filename = None

            while attempt < max_attempts:
                time.sleep(5)
                attempt += 1

                try:
                    # Check history via SSH
                    history_cmd = f"curl -s http://127.0.0.1:8188/history/{prompt_id}"
                    history_result = subprocess.run([
                        'ssh', '-p', RUNPOD_SSH_PORT, '-i', SSH_KEY_PATH,
                        f'root@{RUNPOD_SSH_HOST}', history_cmd
                    ], capture_output=True, text=True, timeout=10)

                    history_data = json.loads(history_result.stdout)

                    # Check if completed
                    if prompt_id in history_data and history_data[prompt_id].get('status', {}).get('completed'):
                        # Get output filename
                        outputs = history_data[prompt_id].get('outputs', {})
                        for node_id, node_output in outputs.items():
                            if 'images' in node_output:
                                output_filename = node_output['images'][0]['filename']
                                break
                        break

                    if attempt % 6 == 0:  # Log every 30 seconds
                        print(f"  Attempt {attempt}/{max_attempts} for pose {idx + 1}...")

                except Exception as poll_error:
                    print(f"  ⚠️  Poll error: {poll_error}")
                    continue

            if not output_filename:
                print(f"  ❌ Pose {idx + 1} timed out or failed")
                continue

            print(f"  ✅ Pose {idx + 1} complete!")

            # Download result image from RunPod via HTTP API
            try:
                # Construct the actual saved filename (not the temp one from history)
                actual_filename = f"{batch_id}_pose{idx + 1}_00001_.png"

                # Download via HTTP /api/view endpoint
                download_url = f"{COMFYUI_API_URL}/api/view?filename={actual_filename}&type=output&subfolder="
                print(f"  📥 Downloading: {download_url}")

                download_response = requests.get(download_url, timeout=60)
                download_response.raise_for_status()

                file_data = download_response.content

                # Upload to Supabase Storage
                storage_path = f"pose_transfers/{batch_id}_pose{idx + 1}.png"
                supabase.storage.from_('carousel-images').upload(
                    storage_path,
                    file_data,
                    file_options={"content-type": "image/png"}
                )

                # Get public URL
                public_url = supabase.storage.from_('carousel-images').get_public_url(storage_path)
                completed_images.append(public_url)

                print(f"  ✅ Downloaded and uploaded to Supabase: {storage_path}")

            except Exception as download_error:
                print(f"  ❌ Download/upload error for pose {idx + 1}: {download_error}")
                import traceback
                traceback.print_exc()
                continue

        # 7. Update batch with completed results
        if completed_images:
            supabase.table('comfyui_batches').update({
                'status': 'completed',
                'completed_images': completed_images,
                'completed_at': datetime.now().isoformat()
            }).eq('id', batch_id).execute()

            print(f"\n✅ Batch complete! {len(completed_images)}/{len(prompt_ids)} images generated")

            return jsonify({
                'success': True,
                'message': f'Edit approved! Generated {len(completed_images)}/{len(prompt_ids)} pose transfers.',
                'batch_id': batch_id,
                'completed_images': completed_images
            })
        else:
            supabase.table('comfyui_batches').update({
                'status': 'failed',
                'error_message': 'All workflows timed out or failed',
                'completed_at': datetime.now().isoformat()
            }).eq('id', batch_id).execute()

            return jsonify({
                'success': False,
                'error': 'All workflows timed out or failed. Check RunPod ComfyUI.',
                'batch_id': batch_id
            }), 500

    except Exception as e:
        print(f"❌ Batch processing error: {e}")

        # Update batch with error
        supabase.table('comfyui_batches').update({
            'status': 'failed',
            'error_message': str(e),
            'completed_at': datetime.now().isoformat()
        }).eq('id', batch_id).execute()

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reject_edit/<test_id>', methods=['POST'])
def reject_edit(test_id):
    """API endpoint - Reject edit"""

    data = request.json or {}
    notes = data.get('notes', '')

    supabase.table('edit_tests').update({
        'status': 'rejected',
        'notes': notes
    }).eq('id', test_id).execute()

    return jsonify({
        'success': True,
        'message': 'Edit rejected.'
    })


@app.route('/batches')
def batches():
    """Show all ComfyUI batch jobs"""

    result = supabase.table('comfyui_batches').select('*').order('created_at', desc=True).execute()
    batches = result.data

    return render_template('batches.html', batches=batches)


@app.route('/pose-transfer')
def pose_transfer():
    """Pose transfer tool - Upload images and generate with ComfyUI"""
    return render_template('pose_transfer.html')


@app.route('/api/pose-transfer', methods=['POST'])
def api_pose_transfer():
    """API endpoint - Process pose transfer with ComfyUI"""
    import tempfile
    import uuid
    from datetime import datetime

    data = request.json
    model_image_url = data.get('model_image_url')
    pose_image_url = data.get('pose_image_url')
    prompt = data.get('prompt', 'the person in image 1 adopts only the body pose and skeletal position from image 2. keep the exact same clothing, outfit, face, hair, and appearance from image 1. only change the body position and pose')

    if not model_image_url or not pose_image_url:
        return jsonify({'error': 'Both image URLs are required'}), 400

    try:
        # Download images
        print(f"Downloading model image: {model_image_url}")
        model_response = requests.get(model_image_url, timeout=30)
        model_response.raise_for_status()

        print(f"Downloading pose image: {pose_image_url}")
        pose_response = requests.get(pose_image_url, timeout=30)
        pose_response.raise_for_status()

        # Generate unique filenames
        job_id = str(uuid.uuid4())[:8]
        model_filename = f"model_{job_id}.jpg"
        pose_filename = f"pose_{job_id}.jpg"

        # Upload to RunPod ComfyUI input folder
        RUNPOD_HOST = "203.57.40.245"
        RUNPOD_PORT = "10120"
        RUNPOD_PATH = "/workspace/ComfyUI/input/"

        # Save temporarily and upload via SSH
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_model:
            tmp_model.write(model_response.content)
            tmp_model_path = tmp_model.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_pose:
            tmp_pose.write(pose_response.content)
            tmp_pose_path = tmp_pose.name

        # Use scp to upload (requires SSH key setup)
        import subprocess

        subprocess.run([
            'scp', '-P', RUNPOD_PORT, '-i', os.path.expanduser('~/.ssh/id_ed25519'),
            tmp_model_path, f'root@{RUNPOD_HOST}:{RUNPOD_PATH}{model_filename}'
        ], check=True)

        subprocess.run([
            'scp', '-P', RUNPOD_PORT, '-i', os.path.expanduser('~/.ssh/id_ed25519'),
            tmp_pose_path, f'root@{RUNPOD_HOST}:{RUNPOD_PATH}{pose_filename}'
        ], check=True)

        # Clean up temp files
        os.unlink(tmp_model_path)
        os.unlink(tmp_pose_path)

        # Trigger ComfyUI workflow via SSH
        workflow_payload = {
            "prompt": {
                "67": {"inputs": {"unet_name": "qwen_image_edit_2509_fp8_e4m3fn.safetensors", "weight_dtype": "fp8_e4m3fn"}, "class_type": "UNETLoader"},
                "69": {"inputs": {"vae_name": "qwen_image_vae.safetensors"}, "class_type": "VAELoader"},
                "74": {"inputs": {"seed": int(datetime.now().timestamp()), "steps": 8, "cfg": 1, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 0.97, "model": ["161", 0], "positive": ["163", 0], "negative": ["164", 0], "latent_image": ["178", 0]}, "class_type": "KSampler"},
                "76": {"inputs": {"samples": ["74", 0], "vae": ["69", 0]}, "class_type": "VAEDecode"},
                "78": {"inputs": {"image": model_filename}, "class_type": "LoadImage"},
                "88": {"inputs": {"PowerLoraLoaderHeaderWidget": {"type": "PowerLoraLoaderHeaderWidget"}, "lora_1": {"on": True, "lora": "Qwen-Image-Lightning-8steps-V2.0-bf16.safetensors", "strength": 1}, "model": ["67", 0], "clip": ["160", 0]}, "class_type": "Power Lora Loader (rgthree)"},
                "94": {"inputs": {"filename_prefix": f"pose_transfer_{job_id}", "images": ["76", 0]}, "class_type": "SaveImage"},
                "160": {"inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image", "device": "default"}, "class_type": "CLIPLoader"},
                "161": {"inputs": {"strength": 1, "model": ["162", 0]}, "class_type": "CFGNorm"},
                "162": {"inputs": {"shift": 3, "model": ["88", 0]}, "class_type": "ModelSamplingAuraFlow"},
                "163": {"inputs": {"prompt": prompt, "clip": ["88", 1], "vae": ["69", 0], "image1": ["176", 0], "image2": ["192", 0]}, "class_type": "TextEncodeQwenImageEditPlus"},
                "164": {"inputs": {"prompt": "", "clip": ["88", 1]}, "class_type": "TextEncodeQwenImageEditPlus"},
                "176": {"inputs": {"upscale_method": "nearest-exact", "megapixels": 1.1, "image": ["78", 0]}, "class_type": "ImageScaleToTotalPixels"},
                "178": {"inputs": {"pixels": ["176", 0], "vae": ["69", 0]}, "class_type": "VAEEncode"},
                "179": {"inputs": {"image": pose_filename}, "class_type": "LoadImage"},
                "189": {"inputs": {"upscale_method": "nearest-exact", "megapixels": 1.1, "image": ["179", 0]}, "class_type": "ImageScaleToTotalPixels"},
                "192": {"inputs": {"preprocessor": "OpenposePreprocessor", "resolution": 768, "image": ["189", 0]}, "class_type": "AIO_Preprocessor"},
                "193": {"inputs": {"images": ["192", 0]}, "class_type": "PreviewImage"}
            }
        }

        # Call ComfyUI API via SSH tunnel
        import json
        curl_cmd = f"curl -X POST http://127.0.0.1:8188/prompt -H 'Content-Type: application/json' -d '{json.dumps(workflow_payload)}'"

        result = subprocess.run([
            'ssh', '-p', RUNPOD_PORT, '-i', os.path.expanduser('~/.ssh/id_ed25519'),
            f'root@{RUNPOD_HOST}', curl_cmd
        ], capture_output=True, text=True, check=True)

        api_response = json.loads(result.stdout.split('\n')[-1])
        prompt_id = api_response.get('prompt_id')

        print(f"✅ Workflow triggered! Prompt ID: {prompt_id}")
        print(f"⏳ Waiting for generation to complete...")

        # Poll for completion (max 2 minutes)
        import time
        max_attempts = 40  # 40 * 3 seconds = 2 minutes
        attempt = 0
        output_filename = None

        while attempt < max_attempts:
            time.sleep(3)
            attempt += 1

            # Check history via SSH
            history_cmd = f"curl -s http://127.0.0.1:8188/history/{prompt_id}"
            history_result = subprocess.run([
                'ssh', '-p', RUNPOD_PORT, '-i', os.path.expanduser('~/.ssh/id_ed25519'),
                f'root@{RUNPOD_HOST}', history_cmd
            ], capture_output=True, text=True, timeout=10)

            history_data = json.loads(history_result.stdout)

            # Check if completed
            if prompt_id in history_data and history_data[prompt_id].get('status', {}).get('completed'):
                # Get output filename
                outputs = history_data[prompt_id].get('outputs', {})
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        output_filename = node_output['images'][0]['filename']
                        break
                break

            print(f"  Attempt {attempt}/{max_attempts}...")

        if not output_filename:
            return jsonify({
                'success': False,
                'error': 'Generation timed out or failed. Check RunPod ComfyUI manually.',
                'prompt_id': prompt_id,
                'job_id': job_id
            }), 500

        print(f"✅ Generation complete! Output: {output_filename}")

        # Download result image from RunPod
        output_path = f"/workspace/ComfyUI/output/{output_filename}"
        local_result_path = f"/tmp/result_{job_id}.png"

        subprocess.run([
            'scp', '-P', RUNPOD_PORT, '-i', os.path.expanduser('~/.ssh/id_ed25519'),
            f'root@{RUNPOD_HOST}:{output_path}', local_result_path
        ], check=True)

        print(f"✅ Downloaded result to {local_result_path}")

        # Upload to Supabase storage
        with open(local_result_path, 'rb') as f:
            file_data = f.read()

        storage_path = f"pose_transfers/{job_id}_{output_filename}"
        supabase.storage.from_('carousel-images').upload(
            storage_path,
            file_data,
            file_options={"content-type": "image/png"}
        )

        # Get public URL
        result_url = supabase.storage.from_('carousel-images').get_public_url(storage_path)

        # Clean up
        os.unlink(local_result_path)

        print(f"✅ Uploaded to Supabase: {result_url}")

        return jsonify({
            'success': True,
            'prompt_id': prompt_id,
            'job_id': job_id,
            'result_url': result_url,
            'message': 'Pose transfer completed successfully!'
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("🚀 Starting Instagram Carousel Editor")
    print("📍 Open in browser: http://localhost:5000")
    print("\nReady!")
    app.run(debug=True, host='0.0.0.0', port=5000)
