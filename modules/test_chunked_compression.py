"""
Dynamic Chunk-Based Parallel Video Compression Benchmark
Divides video dynamically based on size & duration, encodes chunks in parallel across CPU cores, and concatenates losslessly.
"""
import os, subprocess, time, glob, csv, json, sys, math, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

os.makedirs("results", exist_ok=True)

def get_video_info(path):
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
        out = subprocess.check_output(cmd).decode()
        data = json.loads(out)
        duration = float(data['format'].get('duration', 0))
        size_bytes = os.path.getsize(path)
        video_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), {})
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        fps_eval = video_stream.get('r_frame_rate', '25/1')
        num, den = map(int, fps_eval.split('/')) if '/' in fps_eval else (float(fps_eval), 1)
        fps = round(num / den, 2) if den else 25.0
        return {
            "duration": duration,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "width": width,
            "height": height,
            "fps": fps
        }
    except Exception as e:
        print(f"Error probing {path}: {e}")
        return {"duration": 0, "size_bytes": os.path.getsize(path), "size_mb": 0, "width": 0, "height": 0, "fps": 25}

def calculate_dynamic_chunks(info):
    """
    Dynamically decides chunk count and segment duration based on:
    - Video duration (seconds)
    - File size (MB)
    - Available CPU cores
    """
    dur = info['duration']
    size_mb = info['size_mb']
    cpu_cores = os.cpu_count() or 4

    if dur <= 12:
        # Short clip: 2 chunks to utilize at least 2 cores without over-segmenting
        target_chunks = 2
        segment_time = round(dur / 2, 2)
    elif dur <= 35:
        # 12s - 35s: distribute across available cores (up to 4)
        target_chunks = min(cpu_cores, max(2, int(dur / 7)))
        segment_time = round(dur / target_chunks, 2)
    elif dur <= 120:
        # 35s - 2 min: 8-12 second chunks
        target_chunks = min(cpu_cores * 2, max(4, int(dur / 10)))
        segment_time = round(dur / target_chunks, 2)
    elif dur <= 600:
        # 2 - 10 min: 15-20 second chunks
        segment_time = 20.0
        target_chunks = max(4, math.ceil(dur / segment_time))
    else:
        # Long lecture (>10 min): 30-45 second chunks
        segment_time = 30.0 if size_mb > 300 else 45.0
        target_chunks = max(4, math.ceil(dur / segment_time))

    workers = min(target_chunks, cpu_cores)
    return {
        "target_chunks": target_chunks,
        "segment_time": max(3.0, segment_time),
        "workers": workers,
        "cpu_cores": cpu_cores
    }

def encode_single_chunk(chunk_path, out_chunk_path, codec_params):
    cmd = ["ffmpeg", "-y", "-i", chunk_path] + codec_params + ["-threads", "2", out_chunk_path]
    s = time.time()
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_chunk_path, time.time() - s, res.returncode == 0

def run_chunked_parallel_compression(input_path, output_path, codec_params, chunk_cfg):
    temp_dir = os.path.join("results", f"tmp_{os.path.splitext(os.path.basename(input_path))[0]}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    segment_time = chunk_cfg['segment_time']
    workers = chunk_cfg['workers']

    # Phase 1: Lossless Keyframe Split
    t0 = time.time()
    chunk_pattern = os.path.join(temp_dir, "chunk_%03d.mp4")
    split_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(segment_time),
        "-f", "segment",
        "-reset_timestamps", "1",
        chunk_pattern
    ]
    subprocess.run(split_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    split_time = time.time() - t0

    input_chunks = sorted(glob.glob(os.path.join(temp_dir, "chunk_*.mp4")))
    actual_chunks = len(input_chunks)

    # Phase 2: Parallel Multi-Core Compression
    t_enc_start = time.time()
    tasks = []
    output_chunks = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for idx, cp in enumerate(input_chunks):
            out_cp = os.path.join(temp_dir, f"comp_{idx:03d}.mp4")
            output_chunks.append(out_cp)
            tasks.append(executor.submit(encode_single_chunk, cp, out_cp, codec_params))

        for future in as_completed(tasks):
            _, _, success = future.result()
            if not success:
                raise RuntimeError("Failed chunk encoding")

    parallel_enc_time = time.time() - t_enc_start

    # Phase 3: Fast Lossless Concatenation
    t_merge_start = time.time()
    concat_list_file = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list_file, "w") as f:
        for out_cp in output_chunks:
            # Format file path for FFmpeg concat demuxer
            safe_path = os.path.abspath(out_cp).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    merge_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    merge_time = time.time() - t_merge_start

    total_chunked_time = time.time() - t0

    # Cleanup temp directory
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    return {
        "actual_chunks": actual_chunks,
        "split_time": round(split_time, 2),
        "parallel_enc_time": round(parallel_enc_time, 2),
        "merge_time": round(merge_time, 2),
        "total_time": round(total_chunked_time, 2)
    }

def run_sequential_compression(input_path, output_path, codec_params):
    cmd = ["ffmpeg", "-y", "-i", input_path] + codec_params + ["-threads", "0", output_path]
    s = time.time()
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return round(time.time() - s, 2)

def benchmark_video(video_path):
    base = os.path.splitext(os.path.basename(video_path))[0]
    info = get_video_info(video_path)
    if info['duration'] <= 0:
        return None

    cfg = calculate_dynamic_chunks(info)

    print("\n" + "="*80)
    print(f"🎬 Video: {base} ({info['width']}x{info['height']} @ {info['fps']}fps, {info['duration']:.1f}s, {info['size_mb']} MB)")
    print(f"⚙️ Dynamic Chunking Plan:")
    print(f"   - Target Chunks: {cfg['target_chunks']} segments (~{cfg['segment_time']}s each)")
    print(f"   - Parallel Workers: {cfg['workers']} threads on {cfg['cpu_cores']} CPU cores")
    print("="*80)

    # Test with H.264 CRF28 (High compatibility) & H.265 CRF28 (High compression)
    codecs = [
        ("H264_crf28_fast", ["-c:v", "libx264", "-crf", "28", "-preset", "fast"]),
        ("H265_crf28_fast", ["-c:v", "libx265", "-crf", "28", "-preset", "fast", "-tag:v", "hvc1"]),
    ]

    results = []
    for codec_name, params in codecs:
        print(f"\n🔬 Testing Codec: {codec_name}")

        seq_out = f"results/seq_{base}_{codec_name}.mp4"
        chunk_out = f"results/chunked_{base}_{codec_name}.mp4"

        try:
            # 1. Sequential Mode
            print("   1️⃣ Running Standard Sequential Encoding...", end=" ", flush=True)
            t_seq = run_sequential_compression(video_path, seq_out, params)
            size_seq = os.path.getsize(seq_out) if os.path.exists(seq_out) else 0
            print(f"Done in {t_seq:.2f}s (Output: {round(size_seq/1024, 1)} KB)")

            # 2. Dynamic Chunked Parallel Mode
            print(f"   2️⃣ Running Dynamic Chunked Parallel Encoding ({cfg['workers']} workers)...", end=" ", flush=True)
            chunk_metrics = run_chunked_parallel_compression(video_path, chunk_out, params, cfg)
            size_chunk = os.path.getsize(chunk_out) if os.path.exists(chunk_out) else 0
            print(f"Done in {chunk_metrics['total_time']:.2f}s (Output: {round(size_chunk/1024, 1)} KB)")

            # Detailed breakdown
            speedup = round(t_seq / chunk_metrics['total_time'], 2) if chunk_metrics['total_time'] > 0 else 1.0
            saving = round((1 - size_chunk / info['size_bytes']) * 100, 1) if info['size_bytes'] > 0 else 0.0

            print(f"      ├─ Lossless Split Time: {chunk_metrics['split_time']}s ({chunk_metrics['actual_chunks']} chunks)")
            print(f"      ├─ Parallel Core Work:  {chunk_metrics['parallel_enc_time']}s")
            print(f"      ├─ Lossless Concat Time:{chunk_metrics['merge_time']}s")
            print(f"      🚀 SPEEDUP: {speedup}x FASTER than sequential! (Saving: {saving}%)")

            results.append({
                "video": base,
                "duration_s": round(info['duration'], 1),
                "orig_mb": info['size_mb'],
                "codec": codec_name,
                "chunks": chunk_metrics['actual_chunks'],
                "workers": cfg['workers'],
                "seq_time_s": t_seq,
                "chunk_time_s": chunk_metrics['total_time'],
                "speedup_factor": speedup,
                "saving_%": saving
            })
        finally:
            # Cleanup test output files
            if os.path.exists(seq_out):
                try: os.remove(seq_out)
                except Exception: pass
            if os.path.exists(chunk_out):
                try: os.remove(chunk_out)
                except Exception: pass

    return results

if __name__ == "__main__":
    print("🚀 EduMi Dynamic Chunk-Based Parallel Video Compression Benchmark")
    print("   Automatic Chunking based on Video Size, Duration & CPU Topology")

    # Find test videos (prefer lecture/cctv, exclude huge 270MB file unless no other)
    all_vids = glob.glob("data/videos/*.mp4")
    vids = [v for v in all_vids if os.path.getsize(v) < 80 * 1024 * 1024]
    if not vids and all_vids:
        vids = all_vids[:1]

    if not vids:
        print("❌ data/videos/ me koi video clip nahi mili")
        sys.exit(1)

    all_benchmarks = []
    for vp in vids[:2]:
        res = benchmark_video(vp)
        if res:
            all_benchmarks.extend(res)

    if all_benchmarks:
        csv_path = "results/chunked_parallel_benchmark.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=all_benchmarks[0].keys())
            w.writeheader()
            w.writerows(all_benchmarks)

        print("\n" + "="*80)
        print("📊 FINAL SUMMARY - Sequential vs Dynamic Chunked Parallel Compression")
        print("="*80)
        print(f"   {'Video':<12} | {'Codec':<16} | {'Chunks':<6} | {'Sequential':<11} | {'Parallel':<10} | {'Speedup':<8}")
        print("   " + "-"*75)
        for b in all_benchmarks:
            print(f"   {b['video'][:12]:<12} | {b['codec']:<16} | {b['chunks']:<6} | {b['seq_time_s']:>9.2f}s | {b['chunk_time_s']:>8.2f}s | {b['speedup_factor']:>6.2f}x")

        print(f"\n✅ Benchmark results saved to: {csv_path}")
