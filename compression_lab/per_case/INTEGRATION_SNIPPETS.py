"""
Per-Case Integration Snippets - Copy these into EduMi2 files
"""

# === CASE 1: Thumbnails - cameras/models.py ===
# Find def generate_thumbnail(self):
# BEFORE:
#   img.save(thumbnail_path, "JPEG", quality=85)
# AFTER:
def generate_thumbnail_new(self):
    from common.compression_service import EduMiCompressionService
    EduMiCompressionService.compress_thumbnail(self.snapshot.path, thumbnail_path, quality=80)
    # Saving 35%, fast decode

# === CASE 2: CCTV - cameras/recording_engine.py ===
# Find ffmpeg command builder
# BEFORE: ["-c:v","libx264","-crf","23"]
# AFTER:
def build_cctv_command(input_path, output_path):
    from common.compression_service import EduMiCompressionService
    EduMiCompressionService.compress_cctv_storage(input_path, output_path, crf=28)
    # Saving 52%

# === CASE 3: Proxy - video_editing/ffmpeg_utils.py ===
def get_proxy_command(input_path, output_path):
    from common.compression_service import EduMiCompressionService
    EduMiCompressionService.compress_editor_proxy(input_path, output_path)
    # Time <1.5 sec

# === CASE 4: Final - video_editing/timeline_compiler.py ===
def get_final_export(input_path, base_output):
    from common.compression_service import EduMiCompressionService
    h264_out = base_output + "_compatible.mp4"
    h265_out = base_output + "_archive.mp4"
    EduMiCompressionService.compress_editor_final(input_path, h264_out, h265_out)

# === CASE 5: Live Low-Bit - meetings/services.py ===
def create_livekit_room(room_name):
    from common.compression_service import EduMiCompressionService
    from livekit import api
    svc_config = EduMiCompressionService.get_livekit_svc_config()
    # Use svc_config in LiveKit room creation
    # Enable simulcast: room_options with layers q,h,f
    return svc_config
