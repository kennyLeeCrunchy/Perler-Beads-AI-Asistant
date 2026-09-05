from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError


@dataclass(frozen=True)
class DashScopeRequest:
    url: str
    headers: dict[str, str]
    body: str


GENERAL_BEAD_SYSTEM_PROMPT = """你是用于生成豆画、拼豆图纸素材的 AI 生图助手。

你的目标是帮助用户生成广义上适合转为豆画/拼豆图纸的图片。图片应主体清晰、颜色分区明确、轮廓易识别，方便后续进行颜色量化、编号和转图纸处理。

生成规则：
1. 根据用户描述生成图片主体，主体需要清晰、完整、易识别。
2. 图片应适合转成拼豆/豆画图纸，颜色分区清楚，避免过度复杂的细节。
3. 尽量使用明确的色块和稳定的轮廓，不要生成大量细碎纹理。
4. 构图应简洁，主体不要过小，主体和背景需要有较好区分。
5. 避免生成文字、水印、签名、复杂边框。
6. 避免生成过多光效、烟雾、半透明碎片、复杂发丝等不利于转图纸的元素。
7. 如果用户没有明确要求复杂背景，应优先保持背景简洁。
8. 图片整体应便于后续转为有限颜色数量的拼豆图纸。"""


TRANSPARENT_IRREGULAR_SYSTEM_PROMPT = """你是“转图纸前置插画素材”的 AI 生图助手。

当前任务只是第一步：先生成一张干净的原始插画素材。后续系统会再自动抠图、透明化、量化颜色并转换成制作图纸。

重要：用户输入里的“贴纸、挂饰、图纸、拼豆、豆画”等词只表示后续用途，不是画面内容，也不是视觉风格。你不要画贴纸纸张、挂链、挂孔、制作图纸、网格、像素点、珠子或成品照片。

用户选择了“透明底/不规则图形”模式。透明底由系统后处理生成，不依赖你输出 alpha 通道。

必须严格遵守：
1. 背景必须是纯白背景 #FFFFFF，不能有任何纹理、阴影、灰底、棋盘格或透明预览格。
2. 只生成一个主体，主体完整、居中、正面或轻微侧面，轮廓闭合，四周保留安全边距。
3. 主体是平滑的扁平卡通角色插画，不是贴纸纸张，不是实物照片，不是 3D 渲染，不是已经做好的手工成品。
4. 主体内部使用清晰的大色块和干净描边，颜色分区明确，避免细碎纹理和渐变噪声。
5. 不要生成像素画、马赛克、点阵、颗粒化、半调网点、珠子纹理、珠子排列或拼豆成品效果。
6. 不要生成挂链、金属环、挂孔、绳子、底座、地面、墙面、投影、光斑、彩纸碎片、装饰背景或边框。
7. 不要生成文字、水印、签名。
8. 避免复杂发丝、烟雾、半透明光效、碎片飞散等难以抠图的边缘。
9. 主体边缘必须和纯白背景有清晰边界，方便系统生成 mask。
10. 如果用户说“挂饰”或“贴纸”，只提取其中的角色/物体内容，输出单个干净卡通主体，不要画真实挂饰、吊链、挂孔、贴纸纸张或成品照片。"""


TRANSPARENT_FINAL_IMAGE_CONSTRAINTS = """最终画面输出指令（优先级最高）：
- 只画用户想要的单个角色/物体本身。
- 输出平滑扁平卡通角色插画，clean flat vector cartoon character。
- 背景必须是纯白 #FFFFFF。
- 不要画贴纸纸张、透明棋盘格、网格、挂链、挂孔、金属环、纸屑、阴影、地面、墙面、像素点、颗粒、珠子、拼豆成品、制作图纸。
- 不要把“贴纸/挂饰/拼豆/图纸”这些用途词表现成画面元素。
- 画面应该像一个干净的角色设计稿，用于后续系统抠图，不是最终产品效果图。"""


def build_bead_prompt(prompt: str, transparent_irregular: bool = False) -> str:
    system_prompt = TRANSPARENT_IRREGULAR_SYSTEM_PROMPT if transparent_irregular else GENERAL_BEAD_SYSTEM_PROMPT
    if transparent_irregular:
        return (
            f"{system_prompt}\n\n"
            f"用户原始需求（只提取主体内容，不把用途词画成画面元素）：{prompt.strip()}\n\n"
            f"{TRANSPARENT_FINAL_IMAGE_CONSTRAINTS}"
        )
    return f"{system_prompt}\n\n用户需求：{prompt.strip()}"


class DashScopeClient:
    def __init__(self, api_key: str | None, base_url: str = "https://dashscope.aliyuncs.com/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def build_generation_request(
        self,
        prompt: str,
        model: str = "wan2.6-t2i",
        size: str = "1280*1280",
    ) -> DashScopeRequest:
        body = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "prompt_extend": False,
                "watermark": False,
                "n": 1,
                "negative_prompt": (
                    "checkerboard background, transparent preview grid, gray grid, grid lines, "
                    "bead texture, perler bead photo, lego studs, 3d render, physical object, "
                    "product photo, pixel art, mosaic, halftone dots, dotted texture, grainy texture, "
                    "bead pattern, dot matrix, perler bead pattern, beadwork, craft photo, handmade product, "
                    "keychain, chain, metal ring, hanging hole, rope, hook, confetti, paper scraps, sparkle, "
                    "shadow, drop shadow, floor, wall, textured background, complex background, watermark, text, logo"
                ),
                "size": size,
            },
        }
        return DashScopeRequest(
            url=f"{self.base_url}/services/aigc/image-generation/generation",
            headers={
                "Authorization": f"Bearer {self.api_key or ''}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
            body=json.dumps(body, ensure_ascii=False),
        )

    def create_generation_task(self, prompt: str, model: str, size: str) -> str:
        self._require_key()
        spec = self.build_generation_request(prompt=prompt, model=model, size=size)
        payload = self._request_json(spec.url, method="POST", headers=spec.headers, body=spec.body)
        task_id = payload.get("output", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"DashScope did not return a task_id: {payload}")
        return task_id

    def poll_task(self, task_id: str, timeout_seconds: int = 180, interval_seconds: int = 3) -> dict:
        self._require_key()
        deadline = time.time() + timeout_seconds
        url = f"{self.base_url}/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        while time.time() < deadline:
            payload = self._request_json(url, method="GET", headers=headers)
            status = payload.get("output", {}).get("task_status")
            if status == "SUCCEEDED":
                return payload
            if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                raise RuntimeError(f"DashScope task ended with {status}: {payload}")
            time.sleep(interval_seconds)
        raise TimeoutError(f"DashScope task timed out after {timeout_seconds} seconds")

    def generate_image_url(self, prompt: str, model: str, size: str) -> str:
        task_id = self.create_generation_task(prompt=prompt, model=model, size=size)
        payload = self.poll_task(task_id)
        return self.extract_first_image_url(payload)

    def extract_first_image_url(self, payload: dict) -> str:
        output = payload.get("output", {})
        results = output.get("results") or output.get("images") or []
        for result in results:
            if isinstance(result, dict):
                url = result.get("url") or result.get("image_url") or result.get("orig_url")
                if url:
                    return url
            if isinstance(result, str):
                return result

        for choice in output.get("choices") or []:
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            for content in message.get("content") or []:
                if isinstance(content, dict):
                    url = content.get("image") or content.get("url") or content.get("image_url")
                    if url:
                        return url
        raise RuntimeError(f"No image URL found in DashScope payload: {payload}")

    def download_image(self, image_url: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(image_url, headers={"User-Agent": "pindou-app/0.2"})
        with urllib.request.urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())
        return destination

    def _request_json(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        body: str | None = None,
    ) -> dict:
        data = body.encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DashScope HTTP {exc.code}: {detail}") from exc

    def _require_key(self) -> None:
        if not self.api_key or self.api_key.strip() in {"", "sk-your-key-here"}:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured")
        try:
            self.api_key.encode("latin-1")
        except UnicodeEncodeError as exc:
            raise RuntimeError(
                "DASHSCOPE_API_KEY must be the real DashScope key, not the Chinese placeholder text"
            ) from exc
