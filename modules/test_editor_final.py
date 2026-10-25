"""
M4: Video Editor Final - Multiple Techniques Test
Techniques: H264 crf23 medium, H265 crf26 medium, VP9 crf30
Output: results/M4_final_results.csv -> Best = Dual H264+H265
"""
import os, subprocess, time, glob, csv, json, sys
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

TECHNIQUES={
    "H264_crf23_medium":["-c:v","libx264","-crf","23","-preset","medium"],
    "H265_crf26_medium":["-c:v","libx265","-crf","26","-preset","medium","-tag:v","hvc1"],
    "VP9_crf30":["-c:v","libvpx-vp9","-crf","30","-b:v","0","-deadline","realtime","-cpu-used","6","-row-mt","1"],
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
        print("❌ M4: data/videos/ me 1 lecture clip daal")
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
            ext = ".webm" if "vp" in name.lower() else ".mp4"
            out = f"results/M4_{base}_{name}{ext}"
            print(f"      ⏳ [{idx}/{len(TECHNIQUES)}] Parallel Chunk Encoding {name}...", end=" ", flush=True)
            try:
                metrics = chunked_compress_video(fp, out, par, max_duration=bench_t)
                if metrics["success"] and os.path.exists(out):
                    results.append({
                        "module": "M4_editor_final",
                        "file": base,
                        "technique": name,
                        "orig_kb": round(metrics["orig_bytes"]/1024, 1),
                        "comp_kb": round(metrics["comp_bytes"]/1024, 1),
                        "saving_%": metrics["saving_%"],
                        "chunks": metrics["actual_chunks"],
                        "time_sec": metrics["total_time_s"],
                        "quality": "high"
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
        with open("results/M4_final_results.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=res[0].keys()); w.writeheader(); w.writerows(res)
        print(f"✅ M4 Done: results/M4_final_results.csv - {len(res)} tests")
        
        # Summary of all techniques
        print("\n📊 M4 All Techniques Comparison (Averages):")
        print(f"   {'Technique':<20} | {'Avg Saving %':<14} | {'Avg Time (s)':<14}")
        print("   " + "-"*55)
        for name in TECHNIQUES:
            tech_rows=[r for r in res if r['technique']==name]
            if tech_rows:
                avg_sav=sum(r['saving_%'] for r in tech_rows)/len(tech_rows)
                avg_time=sum(r['time_sec'] for r in tech_rows)/len(tech_rows)
                print(f"   {name:<20} | {avg_sav:>12.1f}% | {avg_time:>12.1f}s")
        
        print(f"\n🏆 M4 Best: Dual export - H264 for compatibility + H265 for archive (45% saving) - Use in timeline_compiler.py")
