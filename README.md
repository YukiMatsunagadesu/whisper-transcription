# Whisper 文字起こしツール

OpenAIの[Whisper](https://github.com/openai/whisper)を使用して、音声・動画ファイルをテキストに文字起こしするツールです。
WebアプリとCLIの2つのインターフェースを提供します。

## 機能

- 音声ファイル（MP3, WAV, M4A, OGG, FLAC）の文字起こし
- 動画ファイル（MP4, MKV, AVI, MOV, WMV, WEBM, M4V など）の文字起こし（FFmpegで音声を自動抽出）
- 大容量ファイル（3GB以上）にも対応（CLIおよびWebアプリのローカルパス入力経由）
- タイムスタンプ付き出力
- 日本語・英語など多言語対応（自動検出も可能）

## 必要環境

- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html)

### FFmpegのインストール（Mac）

```bash
brew install ffmpeg
```

## セットアップ

```bash
git clone https://github.com/YukiMatsunagadesu/whisper-transcription.git
cd whisper-transcription

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## 使い方

### Webアプリ

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開きます。

**入力方法：**
- **ファイルアップロード**：500MB以下の音声・動画ファイルをブラウザからアップロード
- **ローカルファイルパス**：3GBなど大容量ファイルはフルパスを直接入力（例: `/Users/yourname/video.mp4`）

### CLI

```bash
python transcribe.py --file video.mp4 --language ja
```

**オプション：**

| オプション | 説明 | デフォルト |
|---|---|---|
| `--file` | 音声または動画ファイルのパス（必須） | - |
| `--model` | モデルサイズ: `tiny` / `base` / `small` / `medium` / `large` | `base` |
| `--language` | 言語コード（例: `ja`, `en`）。省略すると自動検出 | 自動検出 |
| `--output` | 出力テキストファイルのパス。省略すると標準出力 | 標準出力 |

**使用例：**

```bash
# 日本語動画を文字起こしして結果をファイルに保存
python transcribe.py --file lecture.mp4 --language ja --output result.txt

# 英語音声をlargeモデルで高精度に文字起こし
python transcribe.py --file interview.mp3 --model large --language en
```

## モデルサイズについて

| モデル | 精度 | 速度 | メモリ |
|---|---|---|---|
| tiny | 低 | 最速 | ~1GB |
| base | 普通 | 速い | ~1GB |
| small | 中 | 中 | ~2GB |
| medium | 高 | 遅い | ~5GB |
| large | 最高 | 最遅 | ~10GB |

GPUが利用可能な場合は自動的に使用されます。

## ファイル構成

```
whisper-transcription/
├── app.py              # Streamlit Webアプリ
├── transcribe.py       # CLIツール
├── utils.py            # 共通ユーティリティ（音声抽出、フォーマット等）
├── requirements.txt    # 依存パッケージ
└── .streamlit/
    └── config.toml     # Streamlit設定（アップロード上限など）
```
