"""
Run All Module Tests - Each Module Multiple Techniques
Har module ka alag test, har module ka best alag
"""
import os, csv, json, glob, subprocess, sys

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

os.makedirs("results", exist_ok=True)

print("🚀 EduMi Module-Wise Compression Testing - Each Module Multiple Techniques")
print("="*80)

modules=[
    ("M1_thumbnails","modules/test_thumbnails.py","Thumbnails & Images - WebP q80 expected"),
    ("M2_cctv_storage","modules/test_cctv.py","CCTV Storage - H265 crf28 expected"),
    ("M3_editor_proxy","modules/test_editor_proxy.py","Editor Proxy - H264 360p veryfast expected"),
    ("M4_editor_final","modules/test_editor_final.py","Editor Final - Dual H264+H265 expected"),
    ("M5_live_lowbit","modules/test_live_lowbit.py","Live Low-Bit - SVC 3 layers expected"),
]

sub_env = dict(os.environ, PYTHONIOENCODING="utf-8")
all_results=[]
for mid, script, desc in modules:
    print(f"\n📦 Testing {mid}: {desc}")
    print(f"   Running {script}...")
    try:
        subprocess.run([sys.executable, script], check=True, env=sub_env)
    except Exception as e:
        print(f"   Error in {mid}: {e}")

# Combine summary
print("\n" + "="*80)
print("📊 SUMMARY - Har Module Ke Saare Techniques Ka Comparison")
print("="*80)

summary={}
result_files=sorted(glob.glob("results/M*.csv"))
for rf in result_files:
    try:
        with open(rf, encoding='utf-8') as f:
            reader=csv.DictReader(f)
            rows=list(reader)
            if not rows: continue
            
            module_name = rows[0].get('module', os.path.basename(rf).replace('_results.csv',''))
            print(f"\n📦 {module_name}:")
            print(f"   {'Technique':<25} | {'Avg Saving %':<14} | {'Tests Run':<10}")
            print("   " + "-"*55)
            
            # Group by technique
            tech_groups={}
            for r in rows:
                t = r.get('technique', 'unknown')
                tech_groups.setdefault(t, []).append(r)
            
            for t_name, t_rows in tech_groups.items():
                savs=[float(r['saving_%']) for r in t_rows if r.get('saving_%','').replace('.','',1).replace('-','',1).isdigit()]
                avg_sav=sum(savs)/len(savs) if savs else 0.0
                print(f"   {t_name:<25} | {avg_sav:>12.1f}% | {len(t_rows):>9}")
            
            # Find best per module based on saving%
            best=max(rows, key=lambda x: float(x.get('saving_%',0)) if x.get('saving_%','').replace('.','',1).replace('-','',1).isdigit() else -999)
            summary[module_name]={
                "best_technique": best.get('technique',''),
                "saving_%": best.get('saving_%',''),
                "details": best
            }
            print(f"   👉 Best: {best.get('technique')} ({best.get('saving_%')}% saving)")
    except Exception as e:
        print(f"Error reading {rf}: {e}")

# Save summary
os.makedirs("results",exist_ok=True)
with open("results/summary_best_per_module.json","w", encoding='utf-8') as f:
    json.dump(summary,f,indent=2)

print(f"\n✅ All module tests done!")
print(f"📁 Full CSVs saved in results/ folder:")
for rf in result_files:
    print(f"   - {rf}")
print(f"   - results/summary_best_per_module.json")

print("\n🏆 FINAL - Har Module Me Best Wala Lagao:")
for mod, info in summary.items():
    print(f"   {mod}: {info['best_technique']} ({info['saving_%']}% saving)")

print("\n📘 Next: Check integration/compression_service.py for EduMi code changes")
