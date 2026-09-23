from __future__ import annotations

import traceback

import gradio as gr

from v2v_studio.config import settings
from v2v_studio.seedance import SeedanceClient, SeedanceError

DEFAULT_EDIT_PROMPT = """这是视频编辑任务。

请严格保持视频中的人物动作、镜头运动、构图、时序和节奏。
仅执行我描述的修改，其他内容尽量保持不变。
不要添加字幕，不要增加无关人物。"""

DEFAULT_REFERENCE_PROMPT = """严格参考视频1中的人物动作、动作顺序、节奏和镜头运动，重新生成一段新视频。
如果提供了图片1，请保持图片1中主体的身份、外观和服装特征。"""


def run_generation(
    mode_label: str,
    video_uri: str,
    image_uri: str,
    prompt: str,
    ratio: str,
    duration: int,
    generate_audio: bool,
    watermark: bool,
    progress=gr.Progress(track_tqdm=False),
):
    mode = "edit" if mode_label.startswith("视频编辑") else "reference"

    try:
        progress(0.05, desc="检查配置")
        client = SeedanceClient()

        progress(0.10, desc="创建 Seedance 任务")
        task_id = client.create_task(
            prompt=prompt,
            video_uri=video_uri,
            image_uri=image_uri or None,
            mode=mode,
            ratio=ratio,
            duration=int(duration),
            generate_audio=generate_audio,
            watermark=watermark,
        )

        status_lines = [f"任务已创建：{task_id}"]

        def on_status(status, _data):
            status_lines.append(f"状态：{status}")
            progress(0.35, desc=f"Seedance: {status}")

        result = client.wait_for_task(task_id, on_status=on_status)
        client.dump_response(result, task_id)

        progress(0.85, desc="获取生成视频")
        video_url = client.find_video_url(result)
        if not video_url:
            raise SeedanceError(
                "任务已成功，但响应中未找到可下载的视频 URL。完整响应已保存到 data/ 目录。"
            )

        output_path = client.download_video(video_url, task_id)
        progress(1.0, desc="完成")
        status_lines.append(f"完成：{output_path.name}")
        return str(output_path), "\n".join(status_lines), task_id

    except Exception as exc:
        if isinstance(exc, SeedanceError):
            message = str(exc)
        else:
            message = f"{type(exc).__name__}: {exc}"
        return None, f"生成失败：\n{message}\n\n{traceback.format_exc(limit=2)}", ""


def update_mode(mode_label: str):
    editing = mode_label.startswith("视频编辑")
    return (
        gr.update(interactive=not editing, value="adaptive" if editing else "16:9"),
        gr.update(interactive=not editing, value=-1 if editing else 10),
        DEFAULT_EDIT_PROMPT if editing else DEFAULT_REFERENCE_PROMPT,
    )


with gr.Blocks(title="V2V Studio") as demo:
    gr.Markdown(
        """
# V2V Studio

本地 Gradio 界面的 Seedance V2V 工具。第一版直接使用 **公开 HTTPS URL** 或 **Ark asset:// URI** 作为素材输入。

> API Key 只从项目目录下的 `.env` 读取，不会显示在页面，也不会提交到 GitHub。
"""
    )

    with gr.Row():
        with gr.Column(scale=1):
            mode = gr.Radio(
                ["视频编辑（保持原视频时长/比例）", "参考视频生成（动作/运镜参考）"],
                value="视频编辑（保持原视频时长/比例）",
                label="生成模式",
            )
            video_uri = gr.Textbox(
                label="原视频 URL / Asset URI",
                placeholder="https://example.com/source.mp4 或 asset://asset-xxxx",
            )
            image_uri = gr.Textbox(
                label="参考图片 URL / Asset URI（可选）",
                placeholder="https://example.com/character.jpg 或 asset://asset-xxxx",
            )
            prompt = gr.Textbox(
                label="提示词",
                value=DEFAULT_EDIT_PROMPT,
                lines=12,
            )

            with gr.Row():
                ratio = gr.Dropdown(
                    ["adaptive", "16:9", "9:16", "1:1", "4:3", "3:4"],
                    value="adaptive",
                    label="宽高比",
                    interactive=False,
                )
                duration = gr.Number(
                    value=-1,
                    precision=0,
                    label="时长（秒）",
                    interactive=False,
                )

            with gr.Row():
                generate_audio = gr.Checkbox(value=True, label="生成音频")
                watermark = gr.Checkbox(value=False, label="水印")

            generate = gr.Button("开始生成", variant="primary")

        with gr.Column(scale=1):
            result_video = gr.Video(label="生成结果")
            task_id = gr.Textbox(label="Task ID", interactive=False)
            status = gr.Textbox(label="运行状态", lines=12, interactive=False)

    gr.Markdown(
        f"当前模型：`{settings.model}`  ·  Ark Endpoint：`{settings.base_url}`"
    )

    mode.change(
        fn=update_mode,
        inputs=mode,
        outputs=[ratio, duration, prompt],
    )

    generate.click(
        fn=run_generation,
        inputs=[
            mode,
            video_uri,
            image_uri,
            prompt,
            ratio,
            duration,
            generate_audio,
            watermark,
        ],
        outputs=[result_video, status, task_id],
    )


if __name__ == "__main__":
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    demo.queue(default_concurrency_limit=2).launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        show_error=True,
    )
