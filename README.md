# geminitts

このリポジトリは Google Gemini 2.5 Flash Preview Text-to-Speech (TTS) を利用した、シンプルな音声生成 UI を提供します。入力したテキストや SRT ファイルから音声を生成し、ストリーミング再生します。
## 必要条件
- Python 3.11 以上
- Gemini API の API キー（`GEMINI_API_KEY` 環境変数に設定）

## 使い方
1. 依存関係のインストール
   ```bash
   pip install -r requirements.txt
   ```
   PyAudio は不要です。`requirements.txt` からも削除されています。
   以前の手順で `pip install pyaudio` を実行していた場合はアンインストールしてかまいません。
2. API キーの設定
   ```bash
   export GEMINI_API_KEY=YOUR_API_KEY
   ```
3. アプリケーションの起動
   ```bash
   python app.py
   ```
4. ブラウザでアプリを起動したURL (例: `https://your-app.example.com`) を開き、テキストを入力して 'Generate Audio' をクリックします。音声は Web Audio API により即時再生されます。

より詳しい情報は Gemini API ドキュメントの
[Speech Generation](https://ai.google.dev/gemini-api/docs/speech-generation)
を参照してください。
