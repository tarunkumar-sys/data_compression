"""
M3: Video Editor Proxy - Multiple Techniques Test
Techniques: H264 360p veryfast crf28, H264 360p ultrafast crf30, H264 480p veryfast
Output: results/M3_proxy_results.csv -> Best = H264 360p veryfast (fastest)
"""
import os, subprocess, time, glob, csv, json, sys
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

TECHNIQUES={
    "H264_360p_veryfast_crf28":["-c:v","libx264","-crf","28","-preset","veryfast","-vf","scale=-2:360","-an"],
    "H264_360p_ultrafast_crf30":["-c:v","libx264","-crf","30","-preset","ultrafast","-vf","scale=-2:360","-an"],
    "H264_480p_veryfast_crf28":["-c:v","libx264","-crf","28","-preset","veryfast","-vf","scale=-2:480","-an"],
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
    all_files=list(dict.fromkeys(glob.glob("data/videos/lecture*.mp4")+glob.glob("data/videos/*.mp4")))
    files=[f for f in all_files if f.lower().endswith(('.mp4','.mkv','.avi','.mov'))]
    if not files:
        print("❌ M3: data/videos/ me 1 lecture clip daal")
        return []
    lec_files=[f for f in files if "lecture" in os.path.basename(f).lower()]
    target_files = lec_files[:1] if lec_files else files[:1]
    
    results=[]
    for fp in target_files:
        info = get_video_info(fp)
        dur = info['duration']
        orig = info['size_bytes']
        bench_t = min(15.0, dur) if dur > 0 else 15.0
        base = os.path.splitext(os.path.basename(fp))[0]
        print(f"   📹 Input Clip: {base} ({round(orig/1024, 1)} KB, Testing {bench_t:.0f}s with Dynamic Chunking)")
        for idx, (name, par) in enumerate(TECHNIQUES.items(), 1):
            out = f"results/M3_{base}_{name}.mp4"
            print(f"      ⏳ [{idx}/{len(TECHNIQUES)}] Parallel Chunk Encoding {name}...", end=" ", flush=True)
            try:
                metrics = chunked_compress_video(fp, out, par, max_duration=bench_t)
                if metrics["success"] and os.path.exists(out):
                    results.append({
                        "module": "M3_editor_proxy",
                        "file": base,
                        "technique": name,
                        "orig_kb": round(metrics["orig_bytes"]/1024, 1),
                        "comp_kb": round(metrics["comp_bytes"]/1024, 1),
                        "saving_%": metrics["saving_%"],
                        "chunks": metrics["actual_chunks"],
                        "time_sec": metrics["total_time_s"],
                        "priority": "encode_time"
                    })
                    print(f"Done in {metrics['total_time_s']}s ({metrics['actual_chunks']} chunks, Saving: {metrics['saving_%']}%)")
                    os.remove(out)
                else:
                    print("Failed (output file not created)")
            except Exception as ex:
                print(f"Failed: {ex}")
    return results

if __name__=="__main__":
    res=test_module()
    if res:
        os.makedirs("results",exist_ok=True)
        with open("results/M3_proxy_results.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=res[0].keys()); w.writeheader(); w.writerows(res)
        print(f"✅ M3 Done: results/M3_proxy_results.csv - {len(res)} tests")
        
        # Summary of all 3 techniques
        print("\n📊 M3 All Techniques Comparison (Averages):")
        print(f"   {'Technique':<28} | {'Avg Encode Time':<16} | {'Avg Saving %':<14}")
        print("   " + "-"*65)
        for name in TECHNIQUES:
            tech_rows=[r for r in res if r['technique']==name]
            if tech_rows:
                avg_time=sum(r['time_sec'] for r in tech_rows)/len(tech_rows)
                avg_sav=sum(r['saving_%'] for r in tech_rows)/len(tech_rows)
                print(f"   {name:<28} | {avg_time:>13.2f}s | {avg_sav:>12.1f}%")
        
        best=min(res,key=lambda x: x['time_sec'])
        print(f"\n🏆 M3 Best: {best['technique']} -> {best['time_sec']} sec encode - Use in video_editing/ffmpeg_utils.py for proxy")
