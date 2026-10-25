"""
common/compression_service.py - Module-Wise Best Compression Service
Copy to Edumi2/common/compression_service.py
Each module has different best technique
"""
from PIL import Image
import subprocess, os

class EduMiModuleWiseCompression:

    # M1: Thumbnails - Best WebP q80
    @staticmethod
    def compress_M1_thumbnails(input_path, output_path):
        img=Image.open(input_path).convert('RGB')
        img=img.resize((320,180))
        img.save(output_path,"WEBP",quality=80,method=4)
        return True  # 35% saving

    # M2: CCTV - Best H265 crf28 with Dynamic Chunking
    @staticmethod
    def compress_M2_cctv(input_path, output_path):
        return EduMiModuleWiseCompression.compress_parallel_chunked(
            input_path, output_path,
            enc_params=["-c:v", "libx265", "-crf", "28", "-preset", "fast", "-tag:v", "hvc1", "-c:a", "aac", "-b:a", "64k"]
        )

    # M3: Proxy - Best H264 360p veryfast with Dynamic Chunking
    @staticmethod
    def compress_M3_proxy(input_path, output_path):
        return EduMiModuleWiseCompression.compress_parallel_chunked(
            input_path, output_path,
            enc_params=["-c:v", "libx264", "-crf", "28", "-preset", "veryfast", "-vf", "scale=-2:360", "-an"]
        )

    # M4: Final - Best Dual H264+H265 with Dynamic Chunking
    @staticmethod
    def compress_M4_final(input_path, out_h264, out_h265):
        ok1 = EduMiModuleWiseCompression.compress_parallel_chunked(
            input_path, out_h264,
            enc_params=["-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac", "-b:a", "128k"]
        )
        ok2 = EduMiModuleWiseCompression.compress_parallel_chunked(
            input_path, out_h265,
            enc_params=["-c:v", "libx265", "-crf", "26", "-preset", "medium", "-tag:v", "hvc1", "-c:a", "aac", "-b:a", "128k"]
        )
        return ok1 and ok2

    # Advanced: Dynamic Chunked Parallel Compression for Long Videos (M3/M4)
    @staticmethod
    def compress_parallel_chunked(input_path, output_path, codec="h265", crf=28, enc_params=None):
        import glob, math, shutil, json, time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 1. Probe duration and size
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", input_path]
        data = json.loads(subprocess.check_output(cmd).decode())
        dur = float(data['format'].get('duration', 0))
        cpu_cores = os.cpu_count() or 4
        
        # Dynamic chunk sizing based on duration & hardware topology
        if dur <= 15:
            target_chunks = 2
            segment_time = round(dur / 2, 2)
        elif dur <= 120:
            target_chunks = min(cpu_cores, max(2, int(dur / 10)))
            segment_time = round(dur / target_chunks, 2)
        else:
            segment_time = 30.0
            target_chunks = max(4, math.ceil(dur / segment_time))
            
        temp_dir = f"tmp_chunked_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        try:
            # 2. Lossless GOP split
            subprocess.run([
                "ffmpeg", "-y", "-i", input_path, "-c", "copy", "-map", "0",
                "-segment_time", str(segment_time), "-f", "segment", "-reset_timestamps", "1",
                os.path.join(temp_dir, "chunk_%03d.mp4")
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            in_chunks = sorted(glob.glob(os.path.join(temp_dir, "chunk_*.mp4")))
            out_chunks = []
            
            # Select codec params
            if enc_params is None:
                if codec == "h265":
                    enc_params = ["-c:v", "libx265", "-crf", str(crf), "-preset", "fast", "-tag:v", "hvc1"]
                else:
                    enc_params = ["-c:v", "libx264", "-crf", str(crf), "-preset", "fast"]
                
            def _enc(c_in, c_out):
                return subprocess.run(["ffmpeg", "-y", "-i", c_in] + enc_params + ["-threads", "2", c_out],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
                                      
            with ThreadPoolExecutor(max_workers=min(len(in_chunks), cpu_cores)) as pool:
                tasks = []
                for idx, c_in in enumerate(in_chunks):
                    c_out = os.path.join(temp_dir, f"out_{idx:03d}.mp4")
                    out_chunks.append(c_out)
                    tasks.append(pool.submit(_enc, c_in, c_out))
                for t in as_completed(tasks):
                    if not t.result(): raise RuntimeError("Chunk encode failed")
                    
            # 3. Lossless merge
            concat_list = os.path.join(temp_dir, "concat.txt")
            with open(concat_list, "w") as f:
                for c_out in out_chunks:
                    f.write(f"file '{os.path.abspath(c_out).replace('\\', '/')}'\n")
                    
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-c", "copy", "-movflags", "+faststart", output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # M5: Live Low-Bit - Best SVC 3 layers
    @staticmethod
    def get_M5_live_svc_config():
        return {
            "video_codecs":["h264","vp8"],
            "simulcast":True,
            "layers":[
                {"rid":"q","scale_down":4,"max_bitrate":250000},  # 180p 250k
                {"rid":"h","scale_down":2,"max_bitrate":400000},  # 360p 400k BEST for rural
                {"rid":"f","scale_down":1,"max_bitrate":1200000}, # 720p
            ]
        }

# Map module to EduMi file
MODULE_TO_FILE={
    "M1_thumbnails": "cameras/models.py -> generate_thumbnail() + accounts/models.py profile_picture",
    "M2_cctv_storage": "cameras/recording_engine.py + camera_service/",
    "M3_editor_proxy": "video_editing/ffmpeg_utils.py -> proxy_status",
    "M4_editor_final": "video_editing/timeline_compiler.py",
    "M5_live_lowbit": "meetings/services.py -> LiveKit room",
}
