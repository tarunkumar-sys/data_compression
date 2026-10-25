"""
integration/apply_best.py - Best per module ko EduMi me apply karo
Reads results/summary_best_per_module.json and prints integration steps
"""
import json, os

CONFIG={
    "M1_thumbnails": {"file": "cameras/models.py -> generate_thumbnail()", "change": "JPEG -> WEBP q80", "code": 'img.save(path, "WEBP", quality=80)'},
    "M2_cctv_storage": {"file": "cameras/recording_engine.py", "change": "libx264 crf23 -> libx265 crf28", "code": '["-c:v","libx265","-crf","28","-preset","fast"]'},
    "M3_editor_proxy": {"file": "video_editing/ffmpeg_utils.py", "change": "Add proxy veryfast 360p", "code": '["-c:v","libx264","-crf","28","-preset","veryfast","-vf","scale=-2:360","-an"]'},
    "M4_editor_final": {"file": "video_editing/timeline_compiler.py", "change": "Dual export H264+H265", "code": "Dual: H264 crf23 + H265 crf26"},
    "M5_live_lowbit": {"file": "meetings/services.py", "change": "Enable SVC simulcast 3 layers", "code": "layers: 180p@250k, 360p@400k, 720p@1200k"},
}

def main():
    summary_path="results/summary_best_per_module.json"
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            summary=json.load(f)
        print("🏆 Best per Module from Testing:")
        for mod, info in summary.items():
            cfg=CONFIG.get(mod,{})
            print(f"\n{mod}:")
            print(f"  Best Technique: {info.get('best_technique')}")
            print(f"  Saving: {info.get('saving_%')}")
            print(f"  EduMi File: {cfg.get('file')}")
            print(f"  Change: {cfg.get('change')}")
            print(f"  Code: {cfg.get('code')}")
    else:
        print("❌ results/summary_best_per_module.json nahi mila - pehle run_all_modules.py chala")
        print("\nExpected Best (without testing):")
        for mod,cfg in CONFIG.items():
            print(f"{mod}: {cfg['change']} in {cfg['file']}")

if __name__=="__main__":
    main()
