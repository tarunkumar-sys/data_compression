# 🎓 EduMi Compression Project - FULL PACKAGE (All-in-One)
## Each Module Multiple Techniques -> Best per Module -> Integrate into EduMi

> **Course:** Multimedia Processing & Communication  
> **Deadlines:** Oct 30 (Topic+Plan) | Nov 20 (Report) | Nov 25-29 (Demo)  
> **Core Concept:** Har module ka alag benchmark test, multiple compression techniques ka direct comparison, aur best-performing technique ko EduMi production me integrate karna.

---

## 📦 What's Inside This Package

```text
EDUMI_FULL_COMPRESSION_PACKAGE/
├── .gitignore                      # Git ignore rules for venv, caches, and temp videos
├── README.md                       # Main setup & execution guide
├── requirements.txt                # Python dependencies (Pillow, OpenCV, NumPy)
├── run_all_modules.py              # Single command runner for all 5 modules (M1-M5)
├── data/ -> compression_lab/data/  # Linked dataset (images and video clips)
├── modules/                        # Module-Wise Benchmarking Scripts
│   ├── test_thumbnails.py          # M1: Profile & CCTV Thumbnails (JPEG vs WebP)
│   ├── test_cctv.py                # M2: CCTV Storage (H.264 vs H.265 vs VP9)
│   ├── test_editor_proxy.py        # M3: Video Editor Proxy (Fast 360p/480p)
│   ├── test_editor_final.py        # M4: Video Editor Final Export (Dual H.264 + H.265)
│   ├── test_live_lowbit.py         # M5: Rural Live Class Low-Bitrate (H.264 vs VP8 vs SVC)
│   └── test_chunked_compression.py # 🚀 Advanced: Dynamic Multi-Core Parallel Transcoder
├── compression_lab/                # Interactive Lab Benchmarks
│   ├── image_benchmark.py          # Extended image benchmark (PSNR, time, size)
│   ├── video_benchmark.py          # General video codec comparison
│   ├── motion_benchmark.py         # Motion Estimation (ES vs TSS vs Diamond Search)
│   ├── per_case_tester.py          # Unified multi-case batch tester
│   └── per_case/
│       └── INTEGRATION_SNIPPETS.py # Code snippets for EduMi core files
├── integration/                    # Production Integration Helpers
│   ├── compression_service.py      # Ready-to-copy service class for Edumi2/common/
│   └── apply_best.py               # Automated configuration injector
├── docs/                           # Academic Submission Documentation
│   ├── PROPOSAL.md                 # Project Proposal (Ready for Oct 30 submission)
│   ├── REPORT_TEMPLATE.md          # Comprehensive Project Report template
│   └── MODULE_WISE_GUIDE.md        # In-depth module-by-module testing guide
├── results/                        # Generated Benchmark CSVs & JSON summaries
│   ├── summary_best_per_module.json# Winning technique summary per module
│   └── M1_*.csv ... M5_*.csv       # Detailed CSV metrics per test run
└── edumi_reference/
    └── SOFTWARE_REFERENCE.md       # Full EduMi architecture documentation
```

---

## 🎯 5 Core Modules + Dynamic Parallel Encoding

| Module | EduMi Target File | Techniques Compared | Recommended Best |
|---|---|---|---|
| **M1: Thumbnails** | `cameras/models.py` | JPEG q85, JPEG q75, WebP q80, WebP q70 | **WebP q70 / q80** (~30-35% saving, PSNR >36dB) |
| **M2: CCTV Storage** | `cameras/recording_engine.py` | H.264 crf23, H.264 crf28, H.265 crf28, H.265 crf32, VP9 crf32 | **H.265 crf32 fast** (High storage saving) |
| **M3: Editor Proxy** | `video_editing/ffmpeg_utils.py` | H.264 360p veryfast crf28, ultrafast crf30, 480p veryfast | **H.264 360p ultrafast** (Encode time <2s) |
| **M4: Editor Final** | `timeline_compiler.py` | H.264 crf23, H.265 crf26, VP9 crf30 | **Dual Export** (H.264 playback + H.265 archive) |
| **M5: Live Low-Bit** | `meetings/services.py` | H.264 360p 400k, H.264 180p 250k, VP8 360p 400k, SVC 3-layer | **H.264 180p/360p + SVC Simulcast** (Works at 400kbps) |
| **🚀 Parallel Chunking** | `timeline_compiler.py` | Standard Sequential vs Dynamic Chunked Multi-Core | **Dynamic Chunked Transcoding** (**3x-5x faster** on CPU) |

---

## 🚀 Quick Start Guide

### Step 1: Activate Virtual Environment
Virtual environment `venv` is pre-configured with `Pillow`, `OpenCV`, and `NumPy`:

**PowerShell (Windows):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Command Prompt (cmd.exe):**
```cmd
venv\Scripts\activate.bat
```

*(Ensure FFmpeg is installed and accessible in your system PATH).*

---

### Step 2: Run All 5 Modules Together
Runs all benchmarks sequentially and outputs an aggregated terminal comparison table + summary JSON:

```powershell
python run_all_modules.py
```

---

### Step 3: Run Modules Individually (Optional)
If you want to test and generate CSV for a specific module:

```powershell
python modules/test_thumbnails.py          # -> results/M1_thumbnails_results.csv
python modules/test_cctv.py                # -> results/M2_cctv_results.csv
python modules/test_editor_proxy.py        # -> results/M3_proxy_results.csv
python modules/test_editor_final.py        # -> results/M4_final_results.csv
python modules/test_live_lowbit.py         # -> results/M5_live_results.csv
python modules/test_chunked_compression.py # -> results/chunked_parallel_benchmark.csv
```

---

### Step 4: Run Compression Lab Interactive Benchmarks
For detailed image quality PSNR, motion estimation vectors, and multi-case testing:

```powershell
cd compression_lab
python image_benchmark.py
python video_benchmark.py
python motion_benchmark.py
python per_case_tester.py
cd ..
```

---

## 📊 Results & Output Files

All benchmark outputs are cleanly generated in the `results/` folder:
- `results/summary_best_per_module.json`: Automated JSON containing the winning technique and saving percentage for each module.
- `results/M1_thumbnails_results.csv`: Image test results with PSNR (dB), file size reduction, and encode times.
- `results/M2_cctv_results.csv`: CCTV video compression ratios and encoding durations.
- `results/M3_proxy_results.csv`: Proxy video generation speed and file sizes.
- `results/M4_final_results.csv`: Final video compiler performance.
- `results/M5_live_results.csv`: Low-bitrate streaming metrics and bitrates.
- `results/chunked_parallel_benchmark.csv`: Speedup multipliers of dynamic chunked transcoding over sequential encoding.

---

## 🔧 Integrating Best Techniques into EduMi

1. Copy [integration/compression_service.py](file:///c:/Users/USER/Downloads/EDUMI_FULL_COMPRESSION_PACKAGE/integration/compression_service.py) into `Edumi2/common/compression_service.py`.
2. Apply module updates:
   - **M1:** `cameras/models.py` & `accounts/models.py` -> Use WebP quality 70/80 for thumbnails.
   - **M2:** `cameras/recording_engine.py` -> Change `libx264 crf 23` to `libx265 crf 32 fast`.
   - **M3:** `video_editing/ffmpeg_utils.py` -> Add 360p ultrafast proxy generation.
   - **M4:** `video_editing/timeline_compiler.py` -> Use `EduMiModuleWiseCompression.compress_parallel_chunked()` for 3x-5x faster lecture export.
   - **M5:** `meetings/services.py` -> Enable LiveKit 3-layer simulcast (180p, 360p, 720p).

---

## 📄 Submission Checklist

- **Oct 30 (Proposal):** Submit [docs/PROPOSAL.md](file:///c:/Users/USER/Downloads/EDUMI_FULL_COMPRESSION_PACKAGE/docs/PROPOSAL.md).
- **Nov 20 (Report):** Fill out [docs/REPORT_TEMPLATE.md](file:///c:/Users/USER/Downloads/EDUMI_FULL_COMPRESSION_PACKAGE/docs/REPORT_TEMPLATE.md) using the generated CSV tables and graphs.
- **Nov 25-29 (Demo):** Run `python run_all_modules.py` live and show the 5x speedup demo using `python modules/test_chunked_compression.py`.

---

**Author:** Gaurav Singh — EduMi2 | DEI / IITD  
**Course:** Multimedia Processing & Communication  
