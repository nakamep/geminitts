# geminitts

このリポジトリは Google Gemini 2.5 Flash Preview Text-to-Speech (TTS) を利用してテキストから音声を生成し、ブラウザで再生するシンプルな UI を提供します。Gemini API のストリーミング機能を使うため、生成完了を待つ時間を最小限に抑えられます。

## 必要条件
- Python 3.11 以上
- `GEMINI_API_KEY` 環境変数に設定した Gemini API キー

## 使い方
1. 依存関係をインストール
   ```bash
   pip install -r requirements.txt
   ```
2. API キーを設定
   ```bash
   export GEMINI_API_KEY=YOUR_API_KEY
   ```
3. アプリケーションを起動
   ```bash
   python app.py
   ```
4. デプロイした URL (例: `https://your-app.example.com`) を開き、テキストを入力して「Generate Audio」をクリックします。音声がストリーミング再生されます。

詳しくは [Speech Generation](https://ai.google.dev/gemini-api/docs/speech-generation) を参照してください。

