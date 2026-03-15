import os
import subprocess
import tempfile

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".mts"}


def is_video_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in VIDEO_EXTENSIONS


def extract_audio_from_video(video_path: str, progress_callback=None) -> str:
    """FFmpegで動画から音声をWAVとして一時ファイルに抽出する。抽出先のパスを返す。"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    if progress_callback:
        progress_callback("動画から音声を抽出中（大きいファイルは数分かかる場合があります）...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        tmp.name,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        os.unlink(tmp.name)
        raise RuntimeError(f"FFmpegによる音声抽出に失敗しました:\n{result.stderr.decode()}")
    return tmp.name


def format_timestamp(seconds: float) -> str:
    """秒数を HH:MM:SS.mmm 形式の文字列に変換する。"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
