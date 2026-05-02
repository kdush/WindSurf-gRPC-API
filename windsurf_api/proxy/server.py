"""多协议兼容反代服务器 (OpenAI / Anthropic / Gemini)

将 Windsurf 的 AI 模型接口包装成三种主流 API 格式。
零依赖 — 仅使用 Python 标准库 (http.server + threading)。

支持:
  OpenAI 兼容:
    - POST /v1/chat/completions — 聊天补全 (streaming + non-streaming)
    - GET  /v1/models          — 列出可用模型

  Anthropic 兼容:
    - POST /v1/messages         — Messages API (streaming + non-streaming)

  Gemini 兼容:
    - POST /v1beta/models/{model}:generateContent       — 生成内容
    - POST /v1beta/models/{model}:streamGenerateContent  — 流式生成

  通用:
    - GET  /v1/status          — Key 池状态
    - GET  /health             — 健康检查

用法::

    server = ProxyServer(keys=["sk-ws-key1", "sk-ws-key2"], port=8080)
    server.start()  # 阻塞运行

    # 或作为后台线程:
    server.start_background()
"""
import json
import time
import uuid
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from .streaming import StreamingTransport
from .key_pool import KeyPool
from .model_map import MODEL_MAP, resolve_model, list_models

API_SERVER = "https://server.self-serve.windsurf.com"
API_SERVICE = "exa.api_server_pb.ApiServerService"


def _make_metadata(api_key: str) -> dict:
    """构建 Windsurf 请求 metadata"""
    return {
        "apiKey": api_key,
        "ideName": "windsurf",
        "ideVersion": "1.7.3",
        "extensionVersion": "2.30.4",
        "locale": "en",
    }


def _timestamp():
    return int(time.time())


def _chat_id():
    return f"chatcmpl-{uuid.uuid4().hex[:24]}"


def _msg_id():
    return f"msg_{uuid.uuid4().hex[:24]}"


class _ProxyHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    server: "ProxyHTTPServer"

    def log_message(self, format, *args):
        # 安静模式 — 不打印每个请求日志 (可通过 verbose 开启)
        if self.server.proxy_config.get("verbose"):
            BaseHTTPRequestHandler.log_message(self, format, *args)

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _send_sse_chunk(self, data: dict):
        line = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        self.wfile.write(line.encode())
        self.wfile.flush()

    def _send_sse_done(self):
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _send_sse_event(self, event: str, data: dict):
        """发送带 event 类型的 SSE (Anthropic 格式)"""
        line = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        self.wfile.write(line.encode())
        self.wfile.flush()

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _verify_auth(self) -> bool:
        """验证请求的 Bearer token (可选)"""
        required = self.server.proxy_config.get("auth_token")
        if not required:
            return True
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:] == required
        return False

    def _verify_auth_anthropic(self) -> bool:
        """Anthropic 认证: x-api-key 或 Authorization: Bearer"""
        required = self.server.proxy_config.get("auth_token")
        if not required:
            return True
        # x-api-key 优先
        api_key = self.headers.get("x-api-key", "")
        if api_key == required:
            return True
        # 回退到 Bearer
        return self._verify_auth()

    def _verify_auth_gemini(self) -> bool:
        """Gemini 认证: ?key=xxx 或 Authorization: Bearer"""
        required = self.server.proxy_config.get("auth_token")
        if not required:
            return True
        # URL 查询参数 ?key=xxx
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if qs.get("key", [""])[0] == required:
            return True
        # 回退到 Bearer
        return self._verify_auth()

    # ── CORS ──

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, x-api-key, anthropic-version")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    # ── Routes ──

    def do_GET(self):
        if self.path == "/v1/models":
            self._handle_models()
        elif self.path == "/v1/status":
            self._handle_status()
        elif self.path in ("/health", "/v1/health"):
            self._send_json(200, {"status": "ok", "keys": self.server.key_pool.available_count})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        # 解析路径 (去掉查询参数)
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # ── OpenAI ──
        if path == "/v1/chat/completions":
            if not self._verify_auth():
                self._send_json(401, {"error": {"message": "Unauthorized", "type": "auth_error"}})
                return
            self._handle_chat_completions()

        # ── Anthropic ──
        elif path == "/v1/messages":
            if not self._verify_auth_anthropic():
                self._send_json(401, {
                    "type": "error",
                    "error": {"type": "authentication_error", "message": "Invalid API key"}
                })
                return
            self._handle_anthropic_messages()

        # ── Gemini ──
        elif path.startswith("/v1beta/models/"):
            if not self._verify_auth_gemini():
                self._send_json(401, {
                    "error": {"code": 401, "message": "API key not valid.", "status": "PERMISSION_DENIED"}
                })
                return
            self._handle_gemini_dispatch(path)

        else:
            self._send_json(404, {"error": {"message": "not found", "type": "invalid_request"}})

    # ── /v1/models ──

    def _handle_models(self):
        models = list_models()
        self._send_json(200, {"object": "list", "data": models})

    # ── /v1/status ──

    def _handle_status(self):
        self._send_json(200, {
            "keys": self.server.key_pool.status(),
            "total": self.server.key_pool.size,
            "available": self.server.key_pool.available_count,
        })

    # ── /v1/chat/completions ──

    def _handle_chat_completions(self):
        body = self._read_body()

        # 解析参数
        messages = body.get("messages", [])
        model_raw = body.get("model", "")
        stream = body.get("stream", False)
        temperature = body.get("temperature", 0.7)
        max_tokens = body.get("max_tokens", 4096)

        if not messages:
            self._send_json(400, {
                "error": {"message": "messages is required", "type": "invalid_request_error"}
            })
            return

        # 解析模型
        model_uid = resolve_model(model_raw)

        # 获取 Key
        key = self.server.key_pool.next()
        if not key:
            self._send_json(503, {
                "error": {"message": "No available API keys", "type": "server_error"}
            })
            return

        # 构建 Windsurf 请求
        payload = {
            "metadata": _make_metadata(key),
            "messages": messages,
            "modelUid": model_uid,
            "temperature": temperature,
            "maxTokens": max_tokens,
        }

        if stream:
            self._handle_streaming(payload, model_uid, key)
        else:
            self._handle_non_streaming(payload, model_uid, key)

    def _handle_non_streaming(self, payload: dict, model: str, key: str):
        """非流式 — 一次性返回完整结果"""
        transport = self.server.transport
        try:
            result = transport.call(API_SERVICE, "GetChatCompletions", payload)
            if not result.get("ok"):
                status = result.get("status", 500)
                error_data = result.get("data", {})
                # 检查是否是 Key 问题
                if status in (401, 403):
                    self.server.key_pool.report_error(key, "auth_error", permanent=True)
                elif status == 429:
                    self.server.key_pool.report_error(key, "rate_limited")
                else:
                    self.server.key_pool.report_error(key, f"status_{status}")

                self._send_json(status, {
                    "error": {"message": str(error_data), "type": "api_error"}
                })
                return

            self.server.key_pool.report_success(key)

            # 提取内容
            data = result.get("data", {})
            content = self._extract_content(data)

            response = {
                "id": _chat_id(),
                "object": "chat.completion",
                "created": _timestamp(),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": data.get("promptTokens", 0),
                    "completion_tokens": data.get("completionTokens", 0),
                    "total_tokens": data.get("totalTokens", 0),
                },
            }
            self._send_json(200, response)

        except Exception as e:
            self.server.key_pool.report_error(key, str(e))
            self._send_json(500, {
                "error": {"message": f"Internal error: {e}", "type": "server_error"}
            })

    def _handle_streaming(self, payload: dict, model: str, key: str):
        """流式 — SSE 逐块返回"""
        transport = self.server.transport
        chat_id = _chat_id()

        try:
            self._send_sse_start()

            # 发送开始的 role chunk
            self._send_sse_chunk({
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": _timestamp(),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None,
                }],
            })

            full_content = ""
            got_response = False

            for chunk in transport.stream(API_SERVICE,
                                          "GetStreamingExternalChatCompletions",
                                          payload):
                got_response = True

                # 处理错误
                if "error" in chunk:
                    status = chunk.get("status", 500)
                    if status in (401, 403):
                        self.server.key_pool.report_error(key, "auth_error", permanent=True)
                    elif status == 429:
                        self.server.key_pool.report_error(key, "rate_limited")
                    # 在 SSE 中发送错误
                    self._send_sse_chunk({
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": _timestamp(),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": f"\n[Error: {chunk['error']}]"},
                            "finish_reason": "stop",
                        }],
                    })
                    break

                # 提取 delta 内容
                delta = self._extract_stream_delta(chunk)
                if delta:
                    full_content += delta
                    self._send_sse_chunk({
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": _timestamp(),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": delta},
                            "finish_reason": None,
                        }],
                    })

            # 发送 finish
            self._send_sse_chunk({
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": _timestamp(),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }],
            })
            self._send_sse_done()

            if got_response:
                self.server.key_pool.report_success(key)

        except Exception as e:
            self.server.key_pool.report_error(key, str(e))
            try:
                self._send_sse_chunk({
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": _timestamp(),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": f"\n[Stream Error: {e}]"},
                        "finish_reason": "stop",
                    }],
                })
                self._send_sse_done()
            except Exception:
                pass

    # ── 内容提取 ──

    @staticmethod
    def _extract_content(data: dict) -> str:
        """从 Windsurf 非流式响应中提取文本内容"""
        # 常见响应格式
        if "content" in data:
            return data["content"]
        if "message" in data:
            msg = data["message"]
            if isinstance(msg, dict):
                return msg.get("content", "")
            return str(msg)
        if "result" in data:
            r = data["result"]
            if isinstance(r, dict):
                return r.get("content", r.get("text", str(r)))
            return str(r)
        if "choices" in data:
            choices = data["choices"]
            if choices and isinstance(choices, list):
                return choices[0].get("message", {}).get("content", "")
        # 整个 data 转 str
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _extract_stream_delta(chunk: dict) -> str:
        """从 Windsurf 流式响应块中提取增量文本"""
        # Connect streaming 格式: {"result": {"content": "..."}}
        if "result" in chunk:
            r = chunk["result"]
            if isinstance(r, dict):
                return r.get("content", r.get("text", r.get("delta", "")))
            return str(r)
        if "content" in chunk:
            return chunk["content"]
        if "delta" in chunk:
            d = chunk["delta"]
            if isinstance(d, dict):
                return d.get("content", "")
            return str(d)
        if "text" in chunk:
            return chunk["text"]
        return ""

    # ══════════════════════════════════════════
    #  Anthropic Messages API — /v1/messages
    # ══════════════════════════════════════════

    @staticmethod
    def _anthropic_to_messages(body: dict) -> list:
        """将 Anthropic 请求格式转为内部 messages 列表"""
        messages = []
        # system 字段 → system message
        system = body.get("system", "")
        if system:
            messages.append({"role": "system", "content": system})
        for msg in body.get("messages", []):
            content = msg.get("content", "")
            if isinstance(content, list):
                # content block 数组 → 拼接 text
                texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                content = "\n".join(texts)
            messages.append({"role": msg.get("role", "user"), "content": content})
        return messages

    def _handle_anthropic_messages(self):
        """POST /v1/messages — Anthropic Messages API"""
        body = self._read_body()

        messages = body.get("messages", [])
        if not messages:
            self._send_json(400, {
                "type": "error",
                "error": {"type": "invalid_request_error",
                          "message": "messages: at least 1 message is required"}
            })
            return

        model_uid = resolve_model(body.get("model", ""))
        max_tokens = body.get("max_tokens", 4096)
        temperature = body.get("temperature", 0.7)
        stream = body.get("stream", False)

        key = self.server.key_pool.next()
        if not key:
            self._send_json(503, {
                "type": "error",
                "error": {"type": "overloaded_error", "message": "No available API keys"}
            })
            return

        internal_messages = self._anthropic_to_messages(body)

        payload = {
            "metadata": _make_metadata(key),
            "messages": internal_messages,
            "modelUid": model_uid,
            "temperature": temperature,
            "maxTokens": max_tokens,
        }

        if stream:
            self._handle_anthropic_streaming(payload, model_uid, key)
        else:
            self._handle_anthropic_non_streaming(payload, model_uid, key)

    def _handle_anthropic_non_streaming(self, payload: dict, model: str, key: str):
        """Anthropic 非流式响应"""
        transport = self.server.transport
        try:
            result = transport.call(API_SERVICE, "GetChatCompletions", payload)
            if not result.get("ok"):
                status = result.get("status", 500)
                self._report_key_error(key, status)
                self._send_anthropic_error(status, str(result.get("data", "")))
                return

            self.server.key_pool.report_success(key)
            data = result.get("data", {})
            content = self._extract_content(data)

            self._send_json(200, {
                "id": _msg_id(),
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": content}],
                "model": model,
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": data.get("promptTokens", 0),
                    "output_tokens": data.get("completionTokens", 0),
                },
            })

        except Exception as e:
            self.server.key_pool.report_error(key, str(e))
            self._send_anthropic_error(500, f"Internal error: {e}")

    def _handle_anthropic_streaming(self, payload: dict, model: str, key: str):
        """Anthropic 流式 SSE — event: message_start / content_block_delta / ..."""
        transport = self.server.transport
        msg_id = _msg_id()

        try:
            self._send_sse_start()

            # event: message_start
            self._send_sse_event("message_start", {
                "type": "message_start",
                "message": {
                    "id": msg_id, "type": "message", "role": "assistant",
                    "content": [], "model": model,
                    "stop_reason": None, "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                },
            })

            # event: content_block_start
            self._send_sse_event("content_block_start", {
                "type": "content_block_start", "index": 0,
                "content_block": {"type": "text", "text": ""},
            })

            # event: ping
            self._send_sse_event("ping", {"type": "ping"})

            got_response = False
            for chunk in transport.stream(API_SERVICE,
                                          "GetStreamingExternalChatCompletions",
                                          payload):
                got_response = True

                if "error" in chunk:
                    status = chunk.get("status", 500)
                    self._report_key_error(key, status)
                    break

                delta = self._extract_stream_delta(chunk)
                if delta:
                    self._send_sse_event("content_block_delta", {
                        "type": "content_block_delta", "index": 0,
                        "delta": {"type": "text_delta", "text": delta},
                    })

            # event: content_block_stop
            self._send_sse_event("content_block_stop", {
                "type": "content_block_stop", "index": 0,
            })

            # event: message_delta
            self._send_sse_event("message_delta", {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": 0},
            })

            # event: message_stop
            self._send_sse_event("message_stop", {"type": "message_stop"})

            if got_response:
                self.server.key_pool.report_success(key)

        except Exception as e:
            self.server.key_pool.report_error(key, str(e))
            try:
                self._send_sse_event("error", {
                    "type": "error",
                    "error": {"type": "api_error", "message": str(e)},
                })
            except Exception:
                pass

    def _send_anthropic_error(self, status: int, message: str):
        """发送 Anthropic 格式的错误响应"""
        type_map = {
            401: "authentication_error", 403: "permission_error",
            404: "not_found_error", 429: "rate_limit_error",
        }
        error_type = type_map.get(status, "api_error" if status >= 500 else "invalid_request_error")
        self._send_json(status, {
            "type": "error",
            "error": {"type": error_type, "message": message},
        })

    # ══════════════════════════════════════════
    #  Gemini API — /v1beta/models/{model}:*
    # ══════════════════════════════════════════

    @staticmethod
    def _gemini_to_messages(body: dict) -> list:
        """将 Gemini 请求格式转为内部 messages 列表"""
        messages = []
        # systemInstruction → system message
        sys_inst = body.get("systemInstruction", {})
        if sys_inst:
            parts = sys_inst.get("parts", [])
            text = "\n".join(p.get("text", "") for p in parts if p.get("text"))
            if text:
                messages.append({"role": "system", "content": text})
        for content in body.get("contents", []):
            role_raw = content.get("role", "user")
            role = "assistant" if role_raw == "model" else role_raw
            parts = content.get("parts", [])
            text = "\n".join(p.get("text", "") for p in parts if p.get("text"))
            messages.append({"role": role, "content": text})
        return messages

    def _handle_gemini_dispatch(self, path: str):
        """根据路径后缀分发 generateContent / streamGenerateContent"""
        # /v1beta/models/gemini-2.5-pro:generateContent
        suffix = path[len("/v1beta/models/"):]  # e.g. "gemini-2.5-pro:generateContent"

        if ":streamGenerateContent" in suffix:
            model_name = suffix.split(":streamGenerateContent")[0]
            self._handle_gemini_stream(model_name)
        elif ":generateContent" in suffix:
            model_name = suffix.split(":generateContent")[0]
            self._handle_gemini_generate(model_name)
        else:
            self._send_json(404, {
                "error": {"code": 404, "message": "Method not found", "status": "NOT_FOUND"}
            })

    def _handle_gemini_generate(self, model_name: str):
        """POST /v1beta/models/{model}:generateContent — 非流式"""
        body = self._read_body()
        contents = body.get("contents", [])
        if not contents:
            self._send_gemini_error(400, "Request must contain at least one content.")
            return

        model_uid = resolve_model(model_name)
        gen_config = body.get("generationConfig", {})
        temperature = gen_config.get("temperature", 0.7)
        max_tokens = gen_config.get("maxOutputTokens", 4096)

        key = self.server.key_pool.next()
        if not key:
            self._send_gemini_error(503, "No available API keys")
            return

        messages = self._gemini_to_messages(body)
        payload = {
            "metadata": _make_metadata(key),
            "messages": messages,
            "modelUid": model_uid,
            "temperature": temperature,
            "maxTokens": max_tokens,
        }

        transport = self.server.transport
        try:
            result = transport.call(API_SERVICE, "GetChatCompletions", payload)
            if not result.get("ok"):
                status = result.get("status", 500)
                self._report_key_error(key, status)
                self._send_gemini_error(status, str(result.get("data", "")))
                return

            self.server.key_pool.report_success(key)
            data = result.get("data", {})
            content = self._extract_content(data)

            self._send_json(200, {
                "candidates": [{
                    "content": {
                        "role": "model",
                        "parts": [{"text": content}],
                    },
                    "finishReason": "STOP",
                    "index": 0,
                }],
                "usageMetadata": {
                    "promptTokenCount": data.get("promptTokens", 0),
                    "candidatesTokenCount": data.get("completionTokens", 0),
                    "totalTokenCount": data.get("totalTokens", 0),
                },
                "modelVersion": model_uid,
            })

        except Exception as e:
            self.server.key_pool.report_error(key, str(e))
            self._send_gemini_error(500, f"Internal error: {e}")

    def _handle_gemini_stream(self, model_name: str):
        """POST /v1beta/models/{model}:streamGenerateContent — 流式"""
        body = self._read_body()
        contents = body.get("contents", [])
        if not contents:
            self._send_gemini_error(400, "Request must contain at least one content.")
            return

        model_uid = resolve_model(model_name)
        gen_config = body.get("generationConfig", {})
        temperature = gen_config.get("temperature", 0.7)
        max_tokens = gen_config.get("maxOutputTokens", 4096)

        key = self.server.key_pool.next()
        if not key:
            self._send_gemini_error(503, "No available API keys")
            return

        messages = self._gemini_to_messages(body)
        payload = {
            "metadata": _make_metadata(key),
            "messages": messages,
            "modelUid": model_uid,
            "temperature": temperature,
            "maxTokens": max_tokens,
        }

        transport = self.server.transport
        try:
            self._send_sse_start()

            got_response = False
            for chunk in transport.stream(API_SERVICE,
                                          "GetStreamingExternalChatCompletions",
                                          payload):
                got_response = True

                if "error" in chunk:
                    status = chunk.get("status", 500)
                    self._report_key_error(key, status)
                    break

                delta = self._extract_stream_delta(chunk)
                if delta:
                    self._send_sse_chunk({
                        "candidates": [{
                            "content": {"role": "model", "parts": [{"text": delta}]},
                            "index": 0,
                        }],
                        "usageMetadata": {
                            "promptTokenCount": 0,
                            "candidatesTokenCount": 0,
                            "totalTokenCount": 0,
                        },
                    })

            # 结束 chunk
            self._send_sse_chunk({
                "candidates": [{
                    "content": {"role": "model", "parts": [{"text": ""}]},
                    "finishReason": "STOP",
                    "index": 0,
                }],
                "usageMetadata": {
                    "promptTokenCount": 0,
                    "candidatesTokenCount": 0,
                    "totalTokenCount": 0,
                },
                "modelVersion": model_uid,
            })

            if got_response:
                self.server.key_pool.report_success(key)

        except Exception as e:
            self.server.key_pool.report_error(key, str(e))

    def _send_gemini_error(self, status: int, message: str):
        """发送 Gemini 格式的错误响应"""
        code_map = {
            400: "INVALID_ARGUMENT", 401: "PERMISSION_DENIED",
            403: "PERMISSION_DENIED", 404: "NOT_FOUND",
            429: "RESOURCE_EXHAUSTED", 503: "UNAVAILABLE",
        }
        self._send_json(status, {
            "error": {
                "code": status,
                "message": message,
                "status": code_map.get(status, "INTERNAL"),
            }
        })

    # ── 通用辅助 ──

    def _report_key_error(self, key: str, status: int):
        """根据 HTTP 状态码报告 Key 错误"""
        if status in (401, 403):
            self.server.key_pool.report_error(key, "auth_error", permanent=True)
        elif status == 429:
            self.server.key_pool.report_error(key, "rate_limited")
        else:
            self.server.key_pool.report_error(key, f"status_{status}")


class ProxyHTTPServer(HTTPServer):
    """扩展的 HTTPServer — 携带 proxy 配置"""

    def __init__(self, addr, handler, *, transport: StreamingTransport,
                 key_pool: KeyPool, config: dict = None):
        super().__init__(addr, handler)
        self.transport = transport
        self.key_pool = key_pool
        self.proxy_config = config or {}


class ProxyServer:
    """反代服务器主类

    用法::

        server = ProxyServer(
            keys=["sk-ws-key1", "sk-ws-key2"],
            port=8080,
            auth_token="my-secret",  # 可选: 客户端需要带 Bearer token
        )
        server.start()  # 阻塞
    """

    def __init__(self, keys: list, *, port: int = 8080, host: str = "0.0.0.0",
                 server_url: str = API_SERVER, auth_token: str = "",
                 cooldown: int = 60, max_errors: int = 10, verbose: bool = False):
        """
        Args:
            keys: Windsurf API Key 列表
            port: 监听端口
            host: 监听地址
            server_url: Windsurf API 服务器
            auth_token: 可选认证 token (客户端需 Bearer token)
            cooldown: Key 冷却秒数
            max_errors: 连续错误阈值
            verbose: 是否打印请求日志
        """
        self.host = host
        self.port = port
        self.key_pool = KeyPool(keys, cooldown=cooldown, max_errors=max_errors)
        self.transport = StreamingTransport(server_url)
        self.config = {
            "auth_token": auth_token,
            "verbose": verbose,
        }
        self._httpd: Optional[ProxyHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """启动服务器 (阻塞)"""
        self._httpd = ProxyHTTPServer(
            (self.host, self.port), _ProxyHandler,
            transport=self.transport, key_pool=self.key_pool, config=self.config,
        )
        print(f"🚀 Windsurf Multi-Protocol Proxy on http://{self.host}:{self.port}")
        print(f"   Keys: {self.key_pool.size} loaded, {self.key_pool.available_count} available")
        print(f"   OpenAI 兼容:")
        print(f"     POST /v1/chat/completions")
        print(f"     GET  /v1/models")
        print(f"   Anthropic 兼容:")
        print(f"     POST /v1/messages")
        print(f"   Gemini 兼容:")
        print(f"     POST /v1beta/models/{{model}}:generateContent")
        print(f"     POST /v1beta/models/{{model}}:streamGenerateContent")
        print(f"   通用:")
        print(f"     GET  /v1/status")
        print(f"     GET  /health")
        print()
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹ Proxy stopped.")
            self._httpd.shutdown()

    def start_background(self) -> threading.Thread:
        """后台启动服务器 (非阻塞)"""
        self._httpd = ProxyHTTPServer(
            (self.host, self.port), _ProxyHandler,
            transport=self.transport, key_pool=self.key_pool, config=self.config,
        )
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        print(f"🚀 Windsurf Multi-Protocol Proxy (background) on http://{self.host}:{self.port}")
        return self._thread

    def stop(self):
        """停止服务器"""
        if self._httpd:
            self._httpd.shutdown()


def run_proxy(keys: list, port: int = 8080, **kwargs):
    """快速启动反代的便捷函数"""
    server = ProxyServer(keys=keys, port=port, **kwargs)
    server.start()
