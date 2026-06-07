# my-dlp ⬇️

**my-dlp** is a modern, premium Desktop Application built on top of `yt-dlp` to download media from YouTube, Spotify, SoundCloud, TikTok, and hundreds of other websites. It features a sleek, beautiful User Interface, integrated Spotify search, and an interactive synchronized lyrics (Karaoke) player.

---

## ✨ Features

* **Multi-Platform Support:** Download videos and audio from YouTube, Spotify, SoundCloud, TikTok, and more.
* **Full Playlist Downloads:** Support for downloading entire playlists (both video and audio) seamlessly.
* **Integrated Spotify Search:** Look up tracks, artists, or entire Spotify playlists directly inside the app without needing external links.
* **Synchronized Lyrics (Karaoke):** Automatically fetch the most accurate synchronized lyrics (`.lrc`) from the internet (via LRCLIB or syncedlyrics) and play your audio files with a live Karaoke-style display.
* **Modern & Responsive UI:** Built with `customtkinter`, featuring a beautiful Glassmorphism-inspired dark mode, smooth hover effects, and a spacious layout.
* **Multi-Language Support (i18n):** Easily switch the UI between English and Arabic.
* **Metadata & Thumbnails:** Automatically embed thumbnails and high-quality metadata directly into your downloaded audio and video files.

---

## 📸 Screenshots
*(You can add screenshots of your application here)*

---

## 🛠️ Requirements & Installation

### Prerequisites
1. **Python 3.10+**
2. **FFmpeg**: Required for merging video and audio in high qualities, and for metadata embedding. Make sure it is installed and added to your system's PATH, or provide the exact path to `ffmpeg.exe` in the application settings.
3. **VLC Media Player**: The Lyrics Player uses `python-vlc`, which requires the VLC application to be installed on your computer.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/0xjoyo/my-dlp.git
   cd my-dlp
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python main.py
   ```

---

## 🚀 How to Use

### 1. Downloading Media (Downloader Tab)
* Navigate to the **Downloader** tab.
* Paste any video or playlist link (YouTube, Spotify, etc.).
* Click **Fetch Info** to retrieve metadata and available qualities.
* Select your preferred format (Video/Audio) and quality.
* Click **Download Now**. The file will be saved in your chosen downloads folder.

### 2. Searching Spotify (Spotify Tab)
* Navigate to the **Settings** tab and enter your `Spotify Client ID` and `Spotify Client Secret` (You can get these for free from [Spotify Developer Dashboard](https://developer.spotify.com/)).
* Go to the **Spotify Search** tab.
* Search for any song, artist, or paste a Spotify link.
* Click **Download Audio** to automatically fetch the best match from YouTube and download it in high-quality audio.

### 3. Playing Synchronized Lyrics (Karaoke)
* Go to the **Synced Lyrics** tab.
* Click **Choose Audio File** and select any local audio file.
* The application will automatically search the internet for the exact synced `.lrc` lyrics.
* Press **Play** and enjoy the real-time Karaoke experience!

### 4. Settings
Configure the application behavior from the Settings tab:
* Change the default download directory.
* Set the default download quality for video and audio.
* Add a custom `ffmpeg.exe` path.
* Switch between **English** and **Arabic** interface.
* Toggle Light/Dark appearance modes.

---

## 📦 Building to `.exe` (Windows)
To package the application into a standalone `.exe` without needing to install Python:
1. Ensure `pyinstaller` is installed (`pip install pyinstaller`).
2. Run the included build script:
   ```bash
   python build.py
   ```
3. You will find the compiled application inside the `dist/my-dlp/` directory.

---

## 🤝 Contributing
Contributions are always welcome! Feel free to open an issue or submit a Pull Request.

## 📄 License
This project is open-source and available under the MIT License.
