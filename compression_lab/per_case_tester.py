"""
Per-Case Tester - Har Use-Case Ka Alag Best Nikalo
Cases: thumbnails, cctv_storage, editor_proxy, editor_final, live_lowbit
"""
import os, subprocess, time, glob, csv, json, sys
from PIL import Image
import math

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _parent not in sys.path: sys.path.insert(0, _parent)
from modules.chunked_engine import chunked_compress_video, get_video_info

DATA_DIR = "data" if os.path.exists("data") else "../data"
RESULTS_DIR = "results" if os.path.exists("results") and not os.path.exists("../results") else ("../results" if os.path.exists("../results") else "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

CASES={
    "thumbnails": {"type":"image","desc":"Profile pics + CCTV thumbs","files":os.path.join(DATA_DIR, "images/*.*"),"codecs":[("JPEG_q85","JPEG",{"quality":85}),("WebP_q80","WEBP",{"quality":80}),("WebP_q70","WEBP",{"quality":70})]},
    "cctv_storage": {"type":"video","desc":"CCTV 24x7 storage","files":os.path.join(DATA_DIR, "videos/*.mp4"),"codecs":{"H264_crf23":["-c:v","libx264","-crf","23","-preset","fast"],"H265_crf28":["-c:v","libx265","-crf","28","-preset","fast","-tag:v","hvc1"],"H265_crf32":["-c:v","libx265","-crf","32","-preset","fast","-tag:v","hvc1"]}},
    "editor_proxy": {"type":"video","desc":"Editor quick preview 360p","files":os.path.join(DATA_DIR, "videos/*.mp4"),"codecs":{"H264_360p_veryfast_crf28":["-c:v","libx264","-crf","28","-preset","veryfast","-vf","scale=-2:360"],"H264_360p_ultrafast_crf30":["-c:v","libx264","-crf","30","-preset","ultrafast","-vf","scale=-2:360"]}},
    "editor_final": {"type":"video","desc":"Editor final high quality","files":os.path.join(DATA_DIR, "videos/*.mp4"),"codecs":{"H264_crf23_medium":["-c:v","libx264","-crf","23","-preset","medium"],"H265_crf26_medium":["-c:v","libx265","-crf","26","-preset","medium","-tag:v","hvc1"]}},
    "live_lowbit": {"type":"video","desc":"Live class 400kbps rural","files":os.path.join(DATA_DIR, "videos/*.mp4"),"codecs":{"H264_360p_400k":["-c:v","libx264","-crf","28","-maxrate","400k","-bufsize","800k","-preset","veryfast","-vf","scale=-2:360"],"H264_180p_250k":["-c:v","libx264","-crf","30","-maxrate","250k","-bufsize","500k","-preset","veryfast","-vf","scale=-2:180"]}},
}



if __name__=="__main__":
    all_results=[]
    for case_id, case in CASES.items():
        print(f"\n=== CASE: {case_id} - {case['desc']} ===")
        files=glob.glob(case['files'])
        if not files:
            print(f"  No files for {case['files']}, skipping")
            continue
        if case['type']=="image":
            for fp in files[:10]:
                try:
                    img=Image.open(fp).convert('RGB')
                except Exception as ex:
                    continue
                orig=os.path.getsize(fp)
                for name,fmt,par in case['codecs']:
                    out=os.path.join(RESULTS_DIR, f"{case_id}_{name}.tmp")
                    s=time.time()
                    try:
                        img.save(out,fmt,**par)
                        e=(time.time()-s)*1000
                        comp=os.path.getsize(out)
                        saving=(1-comp/orig)*100 if orig > 0 else 0
                        all_results.append({"case":case_id,"file":os.path.basename(fp),"codec":name,"orig_kb":round(orig/1024,1),"comp_kb":round(comp/1024,1),"saving_%":round(saving,1),"time_sec":round(e/1000,3),"time_ms":round(e,1)})
                        if os.path.exists(out): os.remove(out)
                    except Exception as ex:
                        print(f"Skip {name}: {ex}")
        else:
            video_files = [f for f in files if os.path.getsize(f) < 80 * 1024 * 1024]
            if not video_files: video_files = files[:1]
            for fp in video_files[:2]:
                info = get_video_info(fp)
                dur = info.get('duration', 0.0)
                bench_t = min(15.0, dur) if dur > 0 else 15.0
                for name,par in case['codecs'].items():
                    out=os.path.join(RESULTS_DIR, f"{case_id}_{name}.mp4")
                    try:
                        m = chunked_compress_video(fp, out, par, max_duration=bench_t)
                        if m["success"] and os.path.exists(out):
                            all_results.append({
                                "case": case_id,
                                "file": os.path.basename(fp),
                                "codec": name,
                                "orig_kb": round(m["orig_bytes"]/1024, 1),
                                "comp_kb": round(m["comp_bytes"]/1024, 1),
                                "saving_%": m["saving_%"],
                                "time_sec": m["total_time_s"],
                                "time_ms": round(m["total_time_s"]*1000, 1)
                            })
                            print(f"  -> {name}: {m['saving_%']}% saving in {m['total_time_s']}s ({m['actual_chunks']} chunks)")
                            os.remove(out)
                    except Exception as ex:
                        print(f"Skip {name}: {ex}")
    
    if all_results:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        csv_path = os.path.join(RESULTS_DIR, "per_case_comparison.csv")
        fieldnames = ["case", "file", "codec", "orig_kb", "comp_kb", "saving_%", "time_sec", "time_ms"]
        with open(csv_path,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fieldnames); w.writeheader(); w.writerows(all_results)
        print(f"\n✅ {csv_path} ban gaya")
        print("\n=== SUMMARY - Har Case Ka Best ===")
        for case_id in CASES.keys():
            vals=[r for r in all_results if r['case']==case_id]
            if vals:
                best=max(vals,key=lambda x: x['saving_%'])
                print(f"{case_id}: {best['codec']} -> {best['saving_%']}% saving")
