# Project Proposal - Oct 30 Submission
## Title: Comparative Study of Compression Techniques for EduMi

**Course:** Multimedia Processing & Communication
**Submission:** Google Classroom (DEI) / Moodle (IITD)
**Deadline:** Oct 30, 2026

### Selected Topic:
"Implementation and Comparative Analysis of Image & Video Compression Techniques (JPEG, JPEG2000, WebP, H.264, H.265, VP9, Motion Estimation, SVC, MDC) for Optimized Storage and Low-Bandwidth Communication in EduMi On-Premise Academic OS"

**Short Title:** Compression Optimization for EduMi

### Why This Topic from Suggested List?
Covers 6 suggested topics:
1. JPEG Implementation
2. JPEG 2000
3. Motion Estimation (MPEG)
4. Multiple Descriptions Coding (MDC)
5. Scalable Video Coding (SVC)
6. Low Bit Video Conferencing

### How it Fits into Existing EduMi (No New Project):
EduMi already has:
- cameras/recording_engine.py - CCTV recordings (H264)
- cameras/models.py - thumbnails (JPEG)
- video_editing/ffmpeg_utils.py - video editor (H264)
- meetings/services.py - LiveKit (single quality)

We will add compression optimization per use-case.

### Two-Phase Approach (Friend's Idea):

**Phase A: Separate Lab Testing (Oct 31 - Nov 10)**
- Create compression_lab/
- Collect 20 images (profile_pics) + 3 videos (30 sec CCTV + lecture)
- Test per case:
  * Thumbnails: JPEG vs WebP
  * CCTV: H264 vs H265 vs VP9
  * Proxy: H264 veryfast vs ultrafast
  * Final: H264 vs H265 dual
  * Live Low-Bit: 360p 400k vs 180p 250k + SVC
  * Motion: Full Search vs TSS vs Diamond Search
- Metrics: File Size, PSNR, SSIM, Encode Time, Bitrate
- Output: CSV + Graphs (Rate-Distortion)

**Phase B: Integration into EduMi (Nov 11-17)**
- common/compression_service.py (new file)
- cameras/models.py: JPEG -> WebP q80 (35% saving)
- cameras/recording_engine.py: H264 -> H265 crf28 (52% saving)
- video_editing/ffmpeg_utils.py: Add proxy veryfast 360p
- meetings/services.py: Enable SVC simulcast 3 layers
- Expected: 40-60% storage saving

### Outcome Mapping:
1. Comparative study with original contribution - Real EduMi data, per-case best is original
2. Implementation with experimentation - FFmpeg + Python + CSV
3. Reading papers + implementation - JPEG, HEVC, SVC, MDC papers from IEEE Trans Multimedia
4. Survey products - Zoom vs EduMi, Hikvision vs EduMi

### Schedule:
- Oct 30: Proposal submit
- Oct 31-Nov 2: Data collection
- Nov 3-5: Image tests
- Nov 6-10: Video + Motion tests
- Nov 11-12: SVC/MDC simulation
- Nov 13-17: EduMi integration
- Nov 18-20: Report + Code
- Nov 25-29: Demo - Before/After storage + low-bit class at 400kbps

### Deliverables:
- Report PDF with 5 Tables + Graphs
- Code zip with compression_lab/ + edumi_integration/
- Demo video - Storage 1TB: 20 days -> 40 days, Class at 400kbps works
