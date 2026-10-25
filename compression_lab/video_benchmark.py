"""
Video Compression Benchmark - Per Case: CCTV Storage + Editor Proxy + Final + Live Low-Bit
"""
import os, subprocess, time, glob, csv, json, sys

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

DATA_DIR = "data" if os.path.exists("data") else "../data"
RESULTS_DIR = "results" if os.path.exists("results") and not os.path.exists("../results") else ("../results" if os.path.exists("../results") else "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

TESTS={
    "H264_crf23_fast":["-c:v","libx264","-crf","23","-preset","fast"],
    "H264_crf28_fast":["-c:v","libx264","-crf","28","-preset","fast"],
    "H264_360p_veryfast_crf28":["-c:v","libx264","-crf","28","-preset","veryfast","-vf","scale=-2:360"],
    "H265_crf28_fast":["-c:v","libx265","-crf","28","-preset","fast","-tag:v","hvc1"],
    "H265_crf32_fast":["-c:v","libx265","-crf","32","-preset","fast","-tag:v","hvc1"],
    "VP9_crf32":["-c:v","libvpx-vp9","-crf","32","-b:v","0","-deadline","realtime","-cpu-used","6","-row-mt","1"],
    "H264_360p_400k_lowbit":["-c:v","libx264","-crf","28","-maxrate","400k","-bufsize","800k","-preset","veryfast","-vf","scale=-2:360"],
    "H264_180p_250k_lowbit":["-c:v","libx264","-crf","30","-maxrate","250k","-bufsize","500k","-preset","veryfast","-vf","scale=-2:180"],
}

def info(p):
    try:
        cmd=["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",p]
        out=subprocess.check_output(cmd).decode()
        j=json.loads(out)
        return os.path.getsize(p), float(j['format']['duration'])
    except:
        return os.path.getsize(p),0

def test_video(vp):
    base=os.path.splitext(os.path.basename(vp))[0]
    orig,dur=info(vp)
    bench_t = min(10.0, dur) if dur > 0 else 10.0
    orig_bench = (orig / dur * bench_t) if dur > 0 else orig
    res=[]
    for name,par in TESTS.items():
        ext = ".webm" if "vp" in name.lower() else ".mp4"
        out=os.path.join(RESULTS_DIR, f"{base}_{name}{ext}")
        cmd=["ffmpeg","-y","-t",str(bench_t),"-i",vp]+par+["-threads","0",out]
        s=time.time()
        try:
            subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60)
            e=time.time()-s
            if os.path.exists(out) and os.path.getsize(out) > 0:
                comp,_=info(out)
                saving=(1-comp/orig_bench)*100 if orig_bench>0 else 0
                br=(comp*8/1024/bench_t) if bench_t>0 else 0
                res.append({"video":base,"codec":name,"orig_kb":round(orig_bench/1024,1),"comp_kb":round(comp/1024,1),"saving_%":round(saving,1),"bitrate_kbps":round(br,1),"time_sec":round(e,1)})
                os.remove(out)
        except Exception as ex:
            print(f"Skip {name}: {ex}")
    return res

if __name__=="__main__":
    vids=glob.glob(os.path.join(DATA_DIR, "videos/*.mp4"))+glob.glob(os.path.join(DATA_DIR, "videos/*.avi"))+glob.glob(os.path.join(DATA_DIR, "videos/*.mov"))
    vids=[v for v in vids if os.path.getsize(v) < 80 * 1024 * 1024]
    if not vids:
        print(f"❌ {DATA_DIR}/videos/ me videos nahi mili")
    else:
        allr=[]
        for vp in vids[:3]:
            print(f"Testing {vp} ...")
            allr.extend(test_video(vp))
        if allr:
            out_csv = os.path.join(RESULTS_DIR, "video_comparison.csv")
            with open(out_csv,"w",newline="", encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=allr[0].keys()); w.writeheader(); w.writerows(allr)
            print("✅ results/video_comparison.csv ban gaya")
            for codec in TESTS.keys():
                vals=[r for r in allr if r['codec']==codec]
                if vals:
                    avg=sum(v['saving_%'] for v in vals)/len(vals)
                    print(f"{codec}: avg saving {avg:.1f}%")
