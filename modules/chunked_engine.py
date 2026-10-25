"""
Industry-Grade Dynamic Chunk-Based Parallel Video Compression Engine
Architecture:
1. Dynamic Split: Lossless GOP Keyframe division into manageable chunks (zero re-encode).
2. Parallel Transcoding: Worker pool distributes chunks across all available CPU cores.
3. Lossless Concat: Merges compressed chunks back into final video without freezes or quality loss.
4. Comprehensive Metrics: Compression ratio, real-time speedup, and timing breakdowns.
"""

import os, sys, time, glob, json, math, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_video_info(path):
    """Probes video metadata: duration, bitrate, resolution, and fps."""
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
        out = subprocess.check_output(cmd).decode("utf-8", errors="replace")
        data = json.loads(out)
        duration = float(data.get('format', {}).get('duration', 0.0))
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
    except Exception as ex:
        size_bytes = os.path.getsize(path) if os.path.exists(path) else 0
        return {
            "duration": 0.0,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "width": 0,
            "height": 0,
            "fps": 25.0,
            "error": str(ex)
        }

def calculate_dynamic_plan(info, target_chunk_s=10.0):
    """
    Dynamically determines chunk duration & worker thread count
    based on video length, file size, and hardware CPU topology.
    """
    dur = info.get('duration', 0.0)
    cpu_cores = os.cpu_count() or 4
    
    if dur <= 0:
        return {"segment_time": 10.0, "workers": 2, "target_chunks": 1, "cpu_cores": cpu_cores}

    # Dynamic chunk sizing
    if dur <= 15:
        target_chunks = 2
        segment_time = round(dur / 2, 2)
    elif dur <= 60:
        target_chunks = min(cpu_cores, max(2, int(dur / 8)))
        segment_time = round(dur / target_chunks, 2)
    elif dur <= 300:
        segment_time = 15.0
        target_chunks = max(3, math.ceil(dur / segment_time))
    else:
        # Long lecture / 24x7 CCTV clip (>5 min)
        segment_time = 25.0
        target_chunks = max(4, math.ceil(dur / segment_time))

    workers = min(target_chunks, max(2, cpu_cores))
    return {
        "segment_time": max(3.0, segment_time),
        "workers": workers,
        "target_chunks": target_chunks,
        "cpu_cores": cpu_cores
    }

def _encode_single_chunk(chunk_path, out_chunk_path, codec_params):
    """Encodes a single video chunk on an allocated thread worker."""
    cmd = ["ffmpeg", "-y", "-i", chunk_path] + codec_params + ["-threads", "2", out_chunk_path]
    s = time.time()
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_chunk_path, time.time() - s, res.returncode == 0

def chunked_compress_video(input_path, output_path, codec_params, max_duration=None, target_chunk_s=10.0, progress_cb=None):
    """
    Full Industry-Standard Pipeline:
    1. Lossless Keyframe GOP Split (No re-encode)
    2. Parallel Chunk Compression across multi-core worker pool
    3. Lossless Concat into single final output file
    4. Auto cleanup of temporary chunk artifacts
    """
    info = get_video_info(input_path)
    dur = info.get('duration', 0.0)
    effective_dur = min(max_duration, dur) if (max_duration and dur > 0) else dur
    
    plan_info = dict(info)
    plan_info['duration'] = effective_dur
    plan = calculate_dynamic_plan(plan_info, target_chunk_s=target_chunk_s)
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_ext = os.path.splitext(output_path)[1].lower() or ".mp4"
    in_ext = os.path.splitext(input_path)[1].lower() or ".mp4"

    temp_dir = os.path.join(os.path.dirname(output_path) or ".", f"tmp_chunk_{base_name}_{int(time.time()*1000)%100000}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    t_start = time.time()
    try:
        # ============================================================
        # PHASE 1: Fast Lossless GOP Keyframe Split
        # ============================================================
        t_split_start = time.time()
        chunk_input_pattern = os.path.join(temp_dir, f"chunk_%04d{in_ext}")
        split_cmd = ["ffmpeg", "-y"]
        if max_duration and dur > max_duration:
            split_cmd.extend(["-t", str(max_duration)])
        split_cmd.extend([
            "-i", input_path,
            "-c", "copy",
            "-map", "0",
            "-segment_time", str(plan['segment_time']),
            "-f", "segment",
            "-reset_timestamps", "1",
            chunk_input_pattern
        ])
        subprocess.run(split_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        t_split = time.time() - t_split_start

        input_chunks = sorted(glob.glob(os.path.join(temp_dir, f"chunk_*{in_ext}")))
        if not input_chunks:
            # Fallback if segmenter produced single or unpatterned
            input_chunks = [input_path]

        actual_chunks = len(input_chunks)
        if progress_cb:
            progress_cb("split", actual_chunks, plan['workers'], t_split)

        # ============================================================
        # PHASE 2: Parallel Multi-Core Transcoding
        # ============================================================
        t_enc_start = time.time()
        output_chunks = []
        tasks = []
        with ThreadPoolExecutor(max_workers=plan['workers']) as executor:
            for idx, c_path in enumerate(input_chunks):
                out_chunk = os.path.join(temp_dir, f"comp_{idx:04d}{out_ext}")
                output_chunks.append(out_chunk)
                tasks.append(executor.submit(_encode_single_chunk, c_path, out_chunk, codec_params))

            done_count = 0
            for future in as_completed(tasks):
                c_out, c_time, ok = future.result()
                if not ok:
                    raise RuntimeError(f"Chunk encoding failed for {c_out}")
                done_count += 1
                if progress_cb:
                    progress_cb("chunk_done", done_count, actual_chunks, c_time)

        t_parallel_enc = time.time() - t_enc_start

        # ============================================================
        # PHASE 3: Lossless Concat Demuxer
        # ============================================================
        t_merge_start = time.time()
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for c_path in output_chunks:
                safe_path = os.path.abspath(c_path).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Concat command
        merge_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy"
        ]
        if out_ext in [".mp4", ".mov", ".m4v"]:
            merge_cmd.extend(["-movflags", "+faststart"])
        merge_cmd.append(output_path)

        subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        t_merge = time.time() - t_merge_start
        total_time = time.time() - t_start

        # Measure Output
        final_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        if max_duration and dur > max_duration:
            orig_size = int(info['size_bytes'] * (effective_dur / dur))
        else:
            orig_size = info['size_bytes']
        saving = round((1.0 - (final_size / orig_size)) * 100.0, 2) if orig_size > 0 else 0.0

        return {
            "success": True,
            "output_path": output_path,
            "orig_bytes": orig_size,
            "orig_mb": round(orig_size / (1024 * 1024), 2),
            "comp_bytes": final_size,
            "comp_mb": round(final_size / (1024 * 1024), 2),
            "comp_kb": round(final_size / 1024, 1),
            "saving_%": saving,
            "actual_chunks": actual_chunks,
            "workers": plan['workers'],
            "split_time_s": round(t_split, 2),
            "parallel_enc_time_s": round(t_parallel_enc, 2),
            "merge_time_s": round(t_merge, 2),
            "total_time_s": round(total_time, 2)
        }

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
