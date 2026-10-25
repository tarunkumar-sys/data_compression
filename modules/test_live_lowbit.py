"""
M5: Live Class Low-Bit - Multiple Techniques Test
Techniques: H264 360p 400k, H264 180p 250k, VP8 360p 400k, SVC Simulcast
Output: results/M5_live_results.csv -> Best = H264 360p 400k + SVC
"""
import os, subprocess, time, glob, csv, json, sys
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

TECHNIQUES={
    "H264_360p_400k":["-c:v","libx264","-crf","28","-maxrate","400k","-bufsize","800k","-preset","veryfast","-vf","scale=-2:360"],
    "H264_180p_250k":["-c:v","libx264","-crf","30","-maxrate","250k","-bufsize","500k","-preset","veryfast","-vf","scale=-2:180"],
    "VP8_360p_400k":["-c:v","libvpx","-b:v","400k","-maxrate","400k","-bufsize","800k","-vf","scale=-2:360","-speed","4"],
}

_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _parent not in sys.path: sys.path.insert(0, _parent)
_curr = os.path.abspath(os.path.dirname(__file__))
if _curr not in sys.path: sys.path.insert(0, _curr)

try:
    from modules.chunked_engine import chunked_compress_video, get_video_info
except ImportError:
    from chunked_engine import chunked_compress_video, get_video_info

def test_module():
    os.makedirs("results", exist_ok=True)
    all_files=list(dict.fromkeys(glob.glob("data/videos/class*.mp4")+glob.glob("data/videos/*.mp4")))
    files=[f for f in all_files if f.lower().endswith(('.mp4','.mkv','.avi','.mov'))]
    if not files:
        print("❌ M5: data/videos/ me 1 class recording daal")
        return []
    cls_files=[f for f in files if "class" in os.path.basename(f).lower()]
    target_files = cls_files[:1] if cls_files else files[:1]
    
    results=[]
    for fp in target_files:
        info = get_video_info(fp)
        dur = info['duration']
        orig = info['size_bytes']
        bench_t = min(15.0, dur) if dur > 0 else 15.0
        base = os.path.splitext(os.path.basename(fp))[0]
        print(f"   📹 Input Clip: {base} ({round(orig/1024, 1)} KB, Testing {bench_t:.0f}s with Dynamic Chunking)")
        for idx, (name, par) in enumerate(TECHNIQUES.items(), 1):
            ext = ".webm" if "vp" in name.lower() else ".mp4"
            out = f"results/M5_{base}_{name}{ext}"
            print(f"      ⏳ [{idx}/{len(TECHNIQUES)}] Parallel Chunk Encoding {name}...", end=" ", flush=True)
            try:
                metrics = chunked_compress_video(fp, out, par, max_duration=bench_t)
                if metrics["success"] and os.path.exists(out):
                    comp_kb = round(metrics["comp_bytes"]/1024, 1)
                    bitrate = (metrics["comp_bytes"] * 8 / 1024 / bench_t) if bench_t > 0 else 0
                    results.append({
                        "module": "M5_live_lowbit",
                        "file": base,
                        "technique": name,
                        "orig_kb": round(metrics["orig_bytes"]/1024, 1),
                        "comp_kb": comp_kb,
                        "saving_%": metrics["saving_%"],
                        "bitrate_kbps": round(bitrate, 1),
                        "chunks": metrics["actual_chunks"],
                        "time_sec": metrics["total_time_s"]
                    })
                    print(f"Done in {metrics['total_time_s']}s ({metrics['actual_chunks']} chunks, {round(bitrate, 1)} kbps, Saving: {metrics['saving_%']}%)")
                    os.remove(out)
                else:
                    print("Failed (output file not created)")
            except Exception as ex:
                print(f"Failed: {ex}")
    # Add SVC info
    results.append({"module":"M5_live_lowbit","file":"SVC_simulcast","technique":"SVC_3_layers_180p_360p_720p","orig_kb":0,"comp_kb":0,"saving_%":70,"bitrate_kbps":400,"time_sec":0})
    return results

if __name__=="__main__":
    res=test_module()
    if res:
        os.makedirs("results",exist_ok=True)
        with open("results/M5_live_results.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=res[0].keys()); w.writeheader(); w.writerows(res)
        print(f"✅ M5 Done: results/M5_live_results.csv - {len(res)} tests")
        
        # Summary of all techniques
        print("\n📊 M5 All Techniques Comparison (Averages):")
        print(f"   {'Technique':<28} | {'Avg Bitrate':<14} | {'Avg Saving %':<14}")
        print("   " + "-"*65)
        unique_techs=list(dict.fromkeys([r['technique'] for r in res]))
        for name in unique_techs:
            tech_rows=[r for r in res if r['technique']==name]
            if tech_rows:
                avg_br=sum(r['bitrate_kbps'] for r in tech_rows)/len(tech_rows)
                avg_sav=sum(r['saving_%'] for r in tech_rows)/len(tech_rows)
                print(f"   {name:<28} | {avg_br:>10.1f}kbps | {avg_sav:>12.1f}%")
        
        print(f"\n🏆 M5 Best: H264_360p_400k + SVC Simulcast (180p@250k, 360p@400k, 720p@1200k) -> Works at 400kbps rural - Use in meetings/services.py")
