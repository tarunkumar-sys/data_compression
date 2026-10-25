"""
M2: CCTV Storage - Multiple Techniques Test
Techniques: H264 crf23, H264 crf28, H265 crf28, H265 crf32, VP9 crf32
Output: results/M2_cctv_results.csv -> Best = H265 crf28 expected (52% saving)
"""
import os, subprocess, time, glob, csv, json, sys
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

TECHNIQUES={
    "H264_crf23_fast":["-c:v","libx264","-crf","23","-preset","fast"],
    "H264_crf28_fast":["-c:v","libx264","-crf","28","-preset","fast"],
    "H265_crf28_fast":["-c:v","libx265","-crf","28","-preset","fast","-tag:v","hvc1"],
    "H265_crf32_fast":["-c:v","libx265","-crf","32","-preset","fast","-tag:v","hvc1"],
    "VP9_crf32":["-c:v","libvpx-vp9","-crf","32","-b:v","0","-deadline","realtime","-cpu-used","6","-row-mt","1"],
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
    all_files=list(dict.fromkeys(glob.glob("data/videos/cctv*.mp4")+glob.glob("data/videos/*cctv*")+glob.glob("data/videos/*.mp4")))
    files=[f for f in all_files if f.lower().endswith(('.mp4','.mkv','.avi','.mov'))]
    if not files:
        print("❌ M2: data/videos/ me CCTV clips daal")
        return []
    cctv_files=[f for f in files if "cctv" in os.path.basename(f).lower()]
    target_files = cctv_files[:1] if cctv_files else files[:1]
    
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
            out = f"results/M2_{base}_{name}{ext}"
            print(f"      ⏳ [{idx}/{len(TECHNIQUES)}] Parallel Chunk Encoding {name}...", end=" ", flush=True)
            try:
                metrics = chunked_compress_video(fp, out, par, max_duration=bench_t)
                if metrics["success"] and os.path.exists(out):
                    results.append({
                        "module": "M2_cctv_storage",
                        "file": base,
                        "technique": name,
                        "orig_kb": round(metrics["orig_bytes"]/1024, 1),
                        "comp_kb": round(metrics["comp_bytes"]/1024, 1),
                        "saving_%": metrics["saving_%"],
                        "chunks": metrics["actual_chunks"],
                        "time_sec": metrics["total_time_s"]
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
        with open("results/M2_cctv_results.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=res[0].keys()); w.writeheader(); w.writerows(res)
        print(f"✅ M2 Done: results/M2_cctv_results.csv - {len(res)} tests")
        
        # Summary of all 5 techniques
        print("\n📊 M2 All Techniques Comparison (Averages):")
        print(f"   {'Technique':<18} | {'Avg Saving %':<14} | {'Avg Time (s)':<14}")
        print("   " + "-"*52)
        for name in TECHNIQUES:
            tech_rows=[r for r in res if r['technique']==name]
            if tech_rows:
                avg_sav=sum(r['saving_%'] for r in tech_rows)/len(tech_rows)
                avg_time=sum(r['time_sec'] for r in tech_rows)/len(tech_rows)
                print(f"   {name:<18} | {avg_sav:>12.1f}% | {avg_time:>12.1f}s")
        
        best=max(res,key=lambda x: x['saving_%'])
        print(f"\n🏆 M2 Best: {best['technique']} -> {best['saving_%']}% saving - Use in cameras/recording_engine.py")
