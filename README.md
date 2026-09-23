# V2V Studio

A lightweight Seedance studio for text-to-video, image-to-video, video editing and reference-video generation with Volcengine Ark.

> Status: first MVP.

## Features

- Python + Gradio, no separate frontend required.
- Four generation modes: T2V, I2V, V2V editing and reference-video generation.
- Supports public HTTPS URLs and Ark `asset://...` references.
- Polls asynchronous generation tasks until completion.
- Downloads generated videos into `outputs/`.
- Lets you enter the Ark API key directly in the UI; `.env` is optional.
- All code, dependencies (virtualenv), local data and outputs can live under this single project directory.

## Requirements

- Python 3.10+
- A Volcengine Ark API key with access to Seedance 2.5

## Quick start

### Windows

```powershell
setup.bat
start.bat
# Enter ARK API Key in the page
```

### macOS / Linux

```bash
chmod +x setup.sh start.sh
./setup.sh
./start.sh
# Enter ARK API Key in the page
```

Open: http://127.0.0.1:7860


## GitHub Codespaces

This repository is ready for GitHub Codespaces.

1. Open the repository on GitHub.
2. Click **Code** -> **Codespaces** -> **Create codespace on main**.
3. Dependencies are installed automatically.
4. V2V Studio starts automatically on port `7860`.
5. GitHub will forward port `7860`; open the forwarded URL and enter your Ark API key in the page.

Codespaces uses:

- `.devcontainer/devcontainer.json`
- `.devcontainer/start-codespace.sh`

The API key can be entered in the page and is not stored in the repository.

## Configuration

Optional `.env` fallback:

```env
ARK_API_KEY=
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-seedance-2-5-260628
POLL_INTERVAL_SECONDS=10
TASK_TIMEOUT_SECONDS=3600
```

## Generation modes

### Text-to-video

Generate a video from prompt only. No source video is required.

### Image-to-video

Generate a video from an image plus prompt.

### Video editing

Use this when you want to replace, add, remove or modify something in an existing video.

Seedance 2.5 locks the editing task to:

- `ratio=adaptive`
- `duration=-1`

The app applies these values automatically.

### Reference-video generation

Use this when the source video is a motion / camera / timing reference but the output can use a different duration or aspect ratio.

## Input files

The first MVP accepts a public HTTPS URL or an Ark asset URI such as:

```text
asset://asset-xxxxxxxx
```

Local browser upload -> Ark Assets/TOS upload is planned for a later version. This avoids pretending that a path such as `C:\video.mp4` or `/Users/me/video.mp4` is reachable by Volcengine's servers.

## Project layout

```text
v2v-studio/
├── app.py
├── v2v_studio/
│   ├── __init__.py
│   ├── config.py
│   └── seedance.py
├── data/
├── outputs/
├── .env.example
├── .gitignore
├── requirements.txt
├── setup.bat
├── start.bat
├── setup.sh
└── start.sh
```

`data/` and `outputs/` are created automatically. Generated videos are ignored by Git.

## Security

Do **not** commit:

- `.env`
- API keys
- access keys / secret keys
- private video files

Only `.env.example` belongs in Git.

## License

No license has been selected yet.
