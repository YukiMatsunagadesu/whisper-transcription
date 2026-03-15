#!/usr/bin/env python3
"""
Whisper文字起こしコマンドラインツール
"""

import os
import sys
import time
import argparse
import subprocess
import tempfile
import whisper

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".mts"}

def is_video_file(filepath):
    _, ext = os.path.splitext(filepath)
    return ext.lower() in VIDEO_EXTENSIONS

def extract_audio_from_video(video_path):
    """FFmpegで動画から音声をWAVとして一時ファイルに抽出する"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",              # 映像を除外
        "-acodec", "pcm_s16le",
        "-ar", "16000",     # Whisperは16kHz推奨
        "-ac", "1",         # モノラル
        tmp.name
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        os.unlink(tmp.name)
        raise RuntimeError(f"FFmpegによる音声抽出に失敗しました:\n{result.stderr.decode()}")
    return tmp.name

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Whisper文字起こしツール（音声・動画対応）")
    parser.add_argument("--file", required=True, help="文字起こしを行う音声または動画ファイルへのパス")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="使用するWhisperモデルのサイズ")
    parser.add_argument("--language", help="音声の言語（例: ja, en）。指定しない場合は自動検出")
    parser.add_argument("--output", help="出力テキストファイルのパス。指定しない場合は標準出力")

    args = parser.parse_args()

    # ファイルの存在確認
    if not os.path.exists(args.file):
        print(f"エラー: ファイル '{args.file}' が見つかりません。", file=sys.stderr)
        return 1

    audio_file = args.file
    temp_audio = None

    # 動画ファイルの場合は音声を抽出
    if is_video_file(args.file):
        print("動画ファイルを検出しました。音声を抽出中...", file=sys.stderr)
        try:
            temp_audio = extract_audio_from_video(args.file)
            audio_file = temp_audio
            print("音声抽出完了", file=sys.stderr)
        except RuntimeError as e:
            print(f"エラー: {e}", file=sys.stderr)
            return 1

    print(f"モデル '{args.model}' をロード中...", file=sys.stderr)
    start_time = time.time()

    # モデルのロード
    model = whisper.load_model(args.model)

    print(f"モデルロード完了（{time.time() - start_time:.2f}秒）", file=sys.stderr)
    print("文字起こし処理中...", file=sys.stderr)

    # 文字起こしオプション
    options = {}
    if args.language:
        options["language"] = args.language

    try:
        # 文字起こし実行
        result = model.transcribe(audio_file, **options)
    finally:
        if temp_audio and os.path.exists(temp_audio):
            os.unlink(temp_audio)

    # 結果の出力
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"文字起こし結果を '{args.output}' に保存しました。", file=sys.stderr)
    else:
        print("\n" + "="*80, file=sys.stderr)
        print("文字起こし結果:", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(result["text"])

    print(f"\n処理時間: {time.time() - start_time:.2f}秒", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())