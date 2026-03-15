#!/usr/bin/env python3
"""
Whisper文字起こしWebアプリ（Streamlit使用）
"""

import os
import sys
import time
import tempfile
import subprocess
import whisper
import torch
import streamlit as st
from datetime import datetime

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".mts"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}

def is_video_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in VIDEO_EXTENSIONS

def extract_audio_from_video(video_path, progress_placeholder=None):
    """FFmpegで動画から音声をWAVとして一時ファイルに抽出する"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    if progress_placeholder:
        progress_placeholder.text("動画から音声を抽出中（大きいファイルは数分かかる場合があります）...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        tmp.name
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        os.unlink(tmp.name)
        raise RuntimeError(f"FFmpegによる音声抽出に失敗しました:\n{result.stderr.decode()}")
    return tmp.name

# ページ設定
st.set_page_config(
    page_title="Whisper文字起こしツール",
    page_icon="🎤",
    layout="wide"
)

# キャッシュ設定（モデルを再ロードしないようにする）
@st.cache_resource
def load_whisper_model(model_name):
    """Whisperモデルをロードする（キャッシュ使用）"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model(model_name, device=device)

def check_ffmpeg():
    """FFmpegがインストールされているか確認"""
    if os.system("ffmpeg -version > /dev/null 2>&1") != 0:
        st.error("⚠️ FFmpegがインストールされていません。https://ffmpeg.org/download.html からダウンロードしてください。")
        st.stop()

def get_available_models():
    """利用可能なWhisperモデルの一覧を返す"""
    return ["tiny", "base", "small", "medium", "large"]

def main():
    """メイン関数"""
    st.title("🎤 Whisper文字起こしツール")
    st.markdown("""
    OpenAIのWhisperモデルを使用して、音声・動画ファイルからテキストへの文字起こしを行います。
    """)
    
    # FFmpegの確認
    check_ffmpeg()
    
    # サイドバー設定
    st.sidebar.title("設定")
    
    # モデル選択
    model_option = st.sidebar.selectbox(
        "モデルサイズを選択",
        options=get_available_models(),
        index=1,  # baseをデフォルトに
        help="大きいモデルほど精度が上がりますが、処理時間も増加します。"
    )
    
    # 言語選択
    language_option = st.sidebar.selectbox(
        "言語を選択（自動検出する場合は空欄）",
        options=["", "en", "ja", "zh", "de", "fr", "es", "ko", "ru"],
        index=0,
        format_func=lambda x: {
            "": "自動検出", "en": "英語", "ja": "日本語", "zh": "中国語",
            "de": "ドイツ語", "fr": "フランス語", "es": "スペイン語",
            "ko": "韓国語", "ru": "ロシア語"
        }.get(x, x),
        help="音声の言語を指定します。自動検出も可能です。"
    )
    
    # デバイス情報表示
    device = "GPU (CUDA)" if torch.cuda.is_available() else "CPU"
    st.sidebar.info(f"使用デバイス: {device}")
    
    if device == "CPU":
        st.sidebar.warning("GPUが検出されませんでした。処理が遅くなる可能性があります。")
    
    # サイドバーにGitHubリンク
    st.sidebar.markdown("---")
    st.sidebar.markdown("[GitHubリポジトリ](https://github.com/YukiMatsunagadesu/whisper-transcription)")
    
    # 入力方法の選択
    input_method = st.radio(
        "入力方法を選択",
        ["ファイルアップロード（〜200MB）", "ローカルファイルパスを指定（大容量動画向け）"],
        horizontal=True
    )

    uploaded_file = None
    local_file_path = None
    base_filename = None

    if input_method == "ファイルアップロード（〜200MB）":
        uploaded_file = st.file_uploader(
            "音声・動画ファイルをアップロード",
            type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "mkv", "avi", "mov", "wmv", "webm", "m4v"],
            help="対応フォーマット: MP3, WAV, M4A, OGG, FLAC, MP4, MKV, AVI, MOV, WMV, WEBM, M4V"
        )
        if uploaded_file is not None:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"ファイル: {uploaded_file.name} ({file_size_mb:.2f} MB)")
            base_filename = uploaded_file.name
            if not is_video_file(uploaded_file.name):
                st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")
    else:
        local_file_path = st.text_input(
            "ファイルのフルパスを入力",
            placeholder="/Users/yourname/video.mp4",
            help="3GB以上の大容量動画はこちらを使用してください"
        )
        if local_file_path:
            if not os.path.exists(local_file_path):
                st.error(f"ファイルが見つかりません: {local_file_path}")
                local_file_path = None
            else:
                file_size_mb = os.path.getsize(local_file_path) / (1024 * 1024)
                base_filename = os.path.basename(local_file_path)
                st.info(f"ファイル: {base_filename} ({file_size_mb:.2f} MB)")

    has_input = uploaded_file is not None or local_file_path is not None

    if has_input:
        # 文字起こし実行ボタン
        transcribe_button = st.button("文字起こし開始", type="primary")

        if transcribe_button:
            with st.spinner("文字起こし処理中..."):
                temp_input = None
                temp_audio = None

                try:
                    # 入力ファイルを確定
                    if uploaded_file is not None:
                        ext = os.path.splitext(uploaded_file.name)[1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_input = tmp_file.name
                        source_path = temp_input
                    else:
                        source_path = local_file_path

                    progress_text = st.empty()

                    # 動画の場合は音声を抽出
                    if is_video_file(base_filename):
                        temp_audio = extract_audio_from_video(source_path, progress_text)
                        audio_path = temp_audio
                        progress_text.text("音声抽出完了")
                    else:
                        audio_path = source_path

                    # モデルロード
                    load_start = time.time()
                    progress_text.text("モデルをロード中...")
                    model = load_whisper_model(model_option)
                    load_end = time.time()
                    progress_text.text(f"モデルロード完了（{load_end - load_start:.2f}秒）")

                    # 文字起こし
                    progress_text.text("文字起こし処理中...")
                    transcribe_start = time.time()

                    options = {}
                    if language_option:
                        options["language"] = language_option

                    result = model.transcribe(audio_path, **options)

                    transcribe_end = time.time()
                    progress_text.empty()

                    transcribe_time = transcribe_end - transcribe_start
                    total_time = transcribe_end - load_start

                    # 結果表示
                    st.markdown("### 文字起こし結果")
                    st.success(f"処理完了（文字起こし: {transcribe_time:.2f}秒、合計: {total_time:.2f}秒）")

                    st.markdown("#### テキスト")
                    st.text_area("", value=result["text"], height=200)

                    st.download_button(
                        label="テキストをダウンロード",
                        data=result["text"],
                        file_name=f"{os.path.splitext(base_filename)[0]}_transcript.txt",
                        mime="text/plain"
                    )

                    with st.expander("詳細（タイムスタンプ付き）"):
                        table_data = []
                        timestamp_text = ""

                        for segment in result["segments"]:
                            seg_start = segment["start"]
                            seg_end = segment["end"]
                            text = segment["text"]

                            start_formatted = str(datetime.utcfromtimestamp(seg_start).strftime('%H:%M:%S.%f'))[:-3]
                            end_formatted = str(datetime.utcfromtimestamp(seg_end).strftime('%H:%M:%S.%f'))[:-3]

                            table_data.append({
                                "開始": start_formatted,
                                "終了": end_formatted,
                                "テキスト": text
                            })
                            timestamp_text += f"[{start_formatted} --> {end_formatted}] {text}\n"

                        st.table(table_data)

                        st.download_button(
                            label="タイムスタンプ付きテキストをダウンロード",
                            data=timestamp_text,
                            file_name=f"{os.path.splitext(base_filename)[0]}_transcript_timestamps.txt",
                            mime="text/plain"
                        )

                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")

                finally:
                    if temp_input and os.path.exists(temp_input):
                        os.unlink(temp_input)
                    if temp_audio and os.path.exists(temp_audio):
                        os.unlink(temp_audio)

    else:
        st.info("👆 音声・動画ファイルをアップロードするか、ファイルパスを入力してください")

        with st.expander("使い方"):
            st.markdown("""
            1. サイドバーでモデルサイズと言語を選択
            2. 入力方法を選択:
               - **ファイルアップロード**: 200MB以下の音声・動画ファイル
               - **ローカルファイルパス**: 3GBなど大容量の動画ファイル（例: `/Users/yourname/video.mp4`）
            3. 「文字起こし開始」ボタンをクリック
            4. 結果を確認し、必要に応じてダウンロード

            **対応フォーマット:**
            - 音声: MP3, WAV, M4A, OGG, FLAC
            - 動画: MP4, MKV, AVI, MOV, WMV, WEBM, M4V（音声を自動抽出して文字起こし）

            **モデルサイズについて:**
            - tiny: 最小・最速（低精度）
            - base: バランス型（推奨）
            - small: 中程度の精度
            - medium: 高精度
            - large: 最高精度（処理時間が長い）
            """)

if __name__ == "__main__":
    main()