from __future__ import annotations

import os
import traceback

import gradio as gr

from v2v_studio.config import settings
from v2v_studio.seedance import SeedanceClient, SeedanceError

PROMPTS = {
    "文生视频 T2V": "一只银色未来感机器人在雨夜霓虹城市中奔跑，低机位跟拍，电影级灯光，镜头运动流畅，细节丰富。",
    "图生视频 I2V": "以图片1为主体生成视频。保持主体身份、外观和服装特征稳定，让主体自然行走并看向镜头，电影感运镜，动作自然。",
    "视频编辑 V2V": """这是视频编辑任务。

请严格保持视频中的人物动作、镜头运动、构图、时序和节奏。
仅执行我描述的修改，其他内容尽量保持不变。
不要添加字幕，不要增加无关人物。""",
    "参考视频生成 R2V": """严格参考视频1中的人物动作、动作顺序、节奏和镜头运动，重新生成一段新视频。
如果提供了图片1，请保持图片1中主体的身份、外观和服装特征。""",
}

MODE_VALUES = {
    "文生视频 T2V": "text",
    "图生视频 I2V": "image",
    "视频编辑 V2V": "edit",
    "参考视频生成 R2V": "reference",
}


def run_generation(
    api_key: str,
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
    mode = MODE_VALUES[mode_label]
    try:
        progress(0.05, desc="检查配置")
        client = SeedanceClient(api_key=api_key)

        progress(0.10, desc="创建 Seedance 任务")
        task_id = client.create_task(
            prompt=prompt,
            mode=mode,
            video_uri=video_uri or None,
            image_uri=image_uri or None,
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
            raise SeedanceError("任务已成功，但响应中未找到可下载的视频 URL。")

        output_path = client.download_video(video_url, task_id)
        progress(1.0, desc="完成")
        status_lines.append(f"完成：{output_path.name}")
        return str(output_path), "\n".join(status_lines), task_id

    except Exception as exc:
        message = str(exc) if isinstance(exc, SeedanceError) else f"{type(exc).__name__}: {exc}"
        return None, f"生成失败：\n{message}\n\n{traceback.format_exc(limit=2)}", ""


def update_mode(mode_label: str):
    editing = mode_label == "视频编辑 V2V"
    image_visible = mode_label in {"图生视频 I2V", "参考视频生成 R2V"}
    video_visible = mode_label in {"视频编辑 V2V", "参考视频生成 R2V"}
    return (
        gr.update(visible=video_visible),
        gr.update(visible=image_visible),
        gr.update(interactive=not editing, value="adaptive" if editing else "16:9"),
        gr.update(interactive=not editing, value=-1 if editing else 10),
        PROMPTS[mode_label],
    )


with gr.Blocks(title="V2V Studio") as demo:
    gr.Markdown(
        """
# V2V Studio

Seedance Studio：支持 **文生视频、图生视频、视频编辑、参考视频生成**。

> API Key 可直接在页面输入，仅在当前请求中使用；.env 仅作为可选默认方式。
"""
    )

    with gr.Row():
        with gr.Column(scale=1):
            api_key = gr.Textbox(
                label="ARK API Key",
                type="password",
                placeholder="输入你的火山方舟 API Key",
            )
            mode = gr.Radio(
                list(MODE_VALUES.keys()),
                value="文生视频 T2V",
                label="生成模式",
            )
            video_uri = gr.Textbox(
                label="原视频 URL / Asset URI",
                placeholder="https://example.com/source.mp4 或 asset://asset-xxxx",
                visible=False,
            )
            image_uri = gr.Textbox(
                label="图片 URL / Asset URI",
                placeholder="https://example.com/character.jpg 或 asset://asset-xxxx",
                visible=False,
            )
            prompt = gr.Textbox(
                label="提示词",
                value=PROMPTS["文生视频 T2V"],
                lines=12,
            )

            with gr.Row():
                ratio = gr.Dropdown(
                    ["16:9", "9:16", "1:1", "4:3", "3:4", "adaptive"],
                    value="16:9",
                    label="宽高比",
                )
                duration = gr.Number(
                    value=10,
                    precision=0,
                    label="时长（秒）",
                )

            with gr.Row():
                generate_audio = gr.Checkbox(value=True, label="生成音频")
                watermark = gr.Checkbox(value=False, label="水印")

            generate = gr.Button("开始生成", variant="primary")

        with gr.Column(scale=1):
            result_video = gr.Video(label="生成结果")
            task_id = gr.Textbox(label="Task ID", interactive=False)
            status = gr.Textbox(label="运行状态", lines=12, interactive=False)

    gr.Markdown(f"当前模型：{settings.model}  ·  Ark Endpoint：{settings.base_url}")

    mode.change(
        fn=update_mode,
        inputs=mode,
        outputs=[video_uri, image_uri, ratio, duration, prompt],
    )

    generate.click(
        fn=run_generation,
        inputs=[
            api_key,
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
    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", os.getenv("PORT", "7860")))
    inbrowser = os.getenv("GRADIO_INBROWSER", "true").lower() in {"1", "true", "yes"}

    demo.queue(default_concurrency_limit=2).launch(
        server_name=server_name,
        server_port=server_port,
        inbrowser=inbrowser,
        show_error=True,
    )
