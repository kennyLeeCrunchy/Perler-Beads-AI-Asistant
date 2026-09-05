import json
import unittest

from app.core.dashscope_client import DashScopeClient, build_bead_prompt


class DashScopeClientTests(unittest.TestCase):
    def test_build_bead_prompt_uses_general_pattern_prompt_by_default(self):
        prompt = build_bead_prompt("cute cat", transparent_irregular=False)

        self.assertIn("cute cat", prompt)
        self.assertIn("适合转为豆画/拼豆图纸", prompt)
        self.assertNotIn("透明背景 PNG", prompt)
        self.assertNotIn("纯白背景 #FFFFFF", prompt)

    def test_build_bead_prompt_zero_trusts_transparency_generation(self):
        prompt = build_bead_prompt("cute cat", transparent_irregular=True)

        self.assertIn("cute cat", prompt)
        self.assertIn("纯白背景 #FFFFFF", prompt)
        self.assertIn("不能有任何纹理、阴影、灰底、棋盘格", prompt)
        self.assertIn("不是已经做好的手工成品", prompt)
        self.assertIn("透明底由系统后处理生成", prompt)
        self.assertNotIn("优先输出带 alpha 通道的透明背景 PNG", prompt)

    def test_build_generation_request_uses_dashscope_async_protocol(self):
        client = DashScopeClient(api_key="test-key", base_url="https://example.test/api/v1")

        request = client.build_generation_request(
            prompt="cute pixel cat",
            model="wan2.6-t2i",
            size="1280*1280",
        )

        self.assertEqual(request.url, "https://example.test/api/v1/services/aigc/image-generation/generation")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(request.headers["X-DashScope-Async"], "enable")
        self.assertEqual(request.headers["Content-Type"], "application/json")
        body = json.loads(request.body)
        self.assertEqual(body["model"], "wan2.6-t2i")
        self.assertEqual(body["input"]["messages"][0]["content"][0]["text"], "cute pixel cat")
        self.assertEqual(body["parameters"]["n"], 1)
        self.assertIs(body["parameters"]["watermark"], False)
        self.assertEqual(body["parameters"]["size"], "1280*1280")

    def test_extract_first_image_url_supports_common_task_payload_shapes(self):
        client = DashScopeClient(api_key="test-key")

        url = client.extract_first_image_url(
            {
                "output": {
                    "task_status": "SUCCEEDED",
                    "results": [{"url": "https://cdn.example/image.png"}],
                }
            }
        )

        self.assertEqual(url, "https://cdn.example/image.png")

    def test_extract_first_image_url_supports_choices_message_content_image(self):
        client = DashScopeClient(api_key="test-key")

        url = client.extract_first_image_url(
            {
                "output": {
                    "task_status": "SUCCEEDED",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": [
                                    {
                                        "image": "https://cdn.example/choices-image.png",
                                        "type": "image",
                                    }
                                ],
                            }
                        }
                    ],
                }
            }
        )

        self.assertEqual(url, "https://cdn.example/choices-image.png")

    def test_rejects_placeholder_or_non_ascii_api_key_before_http_headers(self):
        client = DashScopeClient(api_key="你的 DashScope Key")

        with self.assertRaisesRegex(RuntimeError, "DASHSCOPE_API_KEY"):
            client.create_generation_task(prompt="cute cat", model="wan2.6-t2i", size="1280*1280")


if __name__ == "__main__":
    unittest.main()
