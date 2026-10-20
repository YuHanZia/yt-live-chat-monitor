# YouTube Live Chat Monitor｜YT 直播留言監控

[繁體中文](#繁體中文) ｜ [English](#english) ｜ [日本語](#日本語)

## 繁體中文

Windows 桌面直播留言監控工具，可追蹤指定 YouTube 頻道，並將符合監控名單的留言通知到 Discord。

- 自動偵測頻道直播，直播網址更換時會重新連線。
- 監控名單支援名稱與頻道 ID。
- Discord 通知只顯示發送者名稱與留言內容。
- 可過濾純 Emoji 留言。
- 設定與名單保存在本機，不會包含在此儲存庫中。

## English

A Windows desktop app that monitors YouTube live chat and sends messages from your watchlist to Discord.

- Detects channel livestreams and reconnects when the live URL changes.
- Watchlist entries can use channel names or channel IDs.
- Discord notifications show only the sender name and message.
- Optionally filters emoji-only messages.
- Your settings and watchlist stay on your PC and are not included in this repository.

## 日本語

YouTube のライブチャットを監視し、指定したユーザーのコメントを Discord に通知する Windows デスクトップアプリです。

- チャンネルの配信を自動検出し、配信 URL が変わると再接続します。
- 監視リストにはチャンネル名またはチャンネル ID を登録できます。
- Discord 通知には投稿者名とコメントのみを表示します。
- 絵文字だけのコメントを除外できます。
- 設定と監視リストは PC 内に保存され、このリポジトリには含まれません。

## 功能

- 追蹤 YouTube 頻道的直播，直播網址更換時會重新偵測。
- 管理留言監控名單，支援名稱與頻道 ID。
- 將符合名單的留言以 Discord 卡片通知，卡片只顯示發送者名稱與留言內容。
- 過濾純 Emoji 留言。
- 保存通知設定與監控名單。

## Windows 執行檔

到 GitHub 專案的 **Releases** 下載最新的 `yt-live-chat-monitor-windows-x64.zip`，解壓縮後執行 `YT直播留言監控.exe`。

第一次執行請在介面填入 YouTube 頻道 ID 與 Discord Webhook，並設定監控名單。個人設定和名單不包含在 GitHub 版本中。

程式會把正式版資料保存在：

```text
%LOCALAPPDATA%\YT直播留言監控\data\
```

## 從原始碼執行

需要 Windows 與 Python 3.12。

```powershell
python -m pip install -r requirements.txt
python gui_app.py
```

## 建置 Windows 版本

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean YT直播留言監控.spec
```

輸出位於 `dist\YT直播留言監控\`。

## 隱私

`data/`、建置產物和環境設定已列入 `.gitignore`。請勿將 Discord Webhook、個人設定或留言名單加入版本控制。
