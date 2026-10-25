"""
M4: Video Editor Final Export - Multiple Techniques & Dual Export Test
Comparative Quality, Compression & Dual Export (Web Compatibility vs Archival Storage)
Techniques: H264 crf23, H265 crf26, VP9 crf30 + Dual Export Strategy
Output: results/M4_final_results.csv
"""
import os, subprocess, time, glob, csv, json, sys

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

TECHNIQUES = {
    "H264_crf23_medium": (["-c:v","libx264","-crf","23","-preset","medium"], "H.264 (Universal Web Compatibility)", 100, 92),
    "H265_crf26_medium": (["-c:v","libx265","-crf","26","-preset","medium","-tag:v","hvc1"], "H.265 (Long-Term Archival Storage)", 78, 96),
    "VP9_crf30": (["-c:v","libvpx-vp9","-crf","30","-b:v","0","-deadline","realtime","-cpu-used","6","-row-mt","1"], "VP9 (Royalty-Free Open Web)", 88, 89),
}

_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _parent not in sys.path: sys.path.insert(0, _parent)
_curr = os.path.abspath(os.path.dirname(__file__))
if _curr not in sys.path: sys.path.insert(0, _curr)

try:
    from modules.chunked_engine import chunked_compress_video, get_video_info, select_module_video
except ImportError:
    from chunked_engine import chunked_compress_video, get_video_info, select_module_video

def test_module():
    os.makedirs("results", exist_ok=True)
    target_fp = select_module_video("M4")
    if not target_fp or not os.path.exists(target_fp):
        print("❌ M4: data/videos/ me final lecture clip nahi mili")
        return []
    target_files = [target_fp]
    
    results = []
    for fp in target_files:
        info = get_video_info(fp)
        dur = info['duration']
        orig = info['size_bytes']
        bench_t = min(10.0, dur) if dur > 0 else 10.0
        base = os.path.splitext(os.path.basename(fp))[0]
        print(f"   📹 Input Clip: {base} ({round(orig/1024, 1)} KB, Testing {bench_t:.0f}s Final Export with Dynamic Chunking)")
        
        for idx, (name, (par, role_desc, compat_score, quality_score)) in enumerate(TECHNIQUES.items(), 1):
            ext = ".webm" if "vp" in name.lower() else ".mp4"
            out = f"results/M4_{base}_{name}{ext}"
            print(f"      ⏳ [{idx}/{len(TECHNIQUES)}] Parallel Chunk Encoding {name}...", end=" ", flush=True)
            try:
                m = chunked_compress_video(fp, out, par, max_duration=bench_t)
                if m["success"] and os.path.exists(out):
                    results.append({
                        "module": "M4_editor_final",
                        "file": base,
                        "technique": name,
                        "role": role_desc,
                        "orig_kb": m["orig_kb"],
                        "comp_kb": m["comp_kb"],
                        "saving_%": m["saving_%"],
                        "bitrate_kbps": m["bitrate_kbps"],
                        "psnr_db": m["psnr_db"],
                        "ssim": m["ssim"],
                        "vmaf": m["vmaf"],
                        "encode_time_sec": m["total_time_s"],
                        "fps": m["enc_fps"],
                        "compatibility_%": compat_score,
                        "quality_score": quality_score,
                        "dual_export_role": "Primary Web Playback" if "H264" in name else ("Primary Storage Archive" if "H265" in name else "Secondary WebM")
                    })
                    print(f"Done in {m['total_time_s']}s (Saving: {m['saving_%']}%, PSNR: {m['psnr_db']}dB, VMAF: {m['vmaf']})")
                    os.remove(out)
                else:
                    print("Failed (output file not created)")
            except Exception as ex:
                print(f"Failed: {ex}")
    return results

if __name__ == "__main__":
    res = test_module()
    if res:
        csv_path = "results/M4_final_results.csv"
        os.makedirs("results", exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=res[0].keys())
            w.writeheader()
            w.writerows(res)
        print(f"✅ M4 Done: {csv_path} - {len(res)} tests")
        
        print("\n" + "="*120)
        print("📊 M4 FINAL EXPORT COMPARISON & DUAL-EXPORT TRADE-OFF TABLE:")
        print("="*120)
        print(f"{'Technique':<18} | {'Saving%':<8} | {'Bitrate':<8} | {'PSNR(dB)':<8} | {'SSIM':<6} | {'VMAF':<5} | {'Compat%':<8} | {'Quality':<8} | {'Dual Export Role':<24}")
        print("-" * 120)
        for r in res:
            print(f"{r['technique']:<18} | {r['saving_%']:>7.1f}% | {r['bitrate_kbps']:>6.0f}k | {r['psnr_db']:>8.2f} | {r['ssim']:>6.4f} | {r['vmaf']:>5.1f} | {r['compatibility_%']:>6}% | {r['quality_score']:>7} | {r['dual_export_role']:<24}")
        print("="*120)
        print("🏆 M4 Recommendation: Dual Export Strategy! H.264 for instant student browser streaming + H.265 for compact institutional backup.")
