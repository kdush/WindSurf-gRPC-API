"""流式传输层 — 支持 SSE / chunked transfer 读取

Windsurf 的流式接口返回 Connect-protocol streaming 格式:
  - Content-Type: application/connect+json
  - 每行一个 JSON envelope: {"result": {...}} 或 end-of-stream 标记

本模块用 http.client 底层连接实现逐块读取。
"""
import http.client
import json
import ssl
import urllib.parse
from typing import Generator, Any

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

CONNECT_HEADERS = {
    "Content-Type": "application/json",
    "Connect-Protocol-Version": "1",
    "Connect-Accept-Encoding": "identity",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


class StreamingTransport:
    """支持流式响应的 Connect-protocol 传输

    用法::

        st = StreamingTransport("https://server.self-serve.windsurf.com")
        for chunk in st.stream("exa.api_server_pb.ApiServerService",
                               "GetStreamingExternalChatCompletions", payload):
            print(chunk)
    """

    def __init__(self, base_url: str, timeout: int = 60, extra_headers: dict = None):
        parsed = urllib.parse.urlparse(base_url)
        self.scheme = parsed.scheme
        self.host = parsed.hostname
        self.port = parsed.port or (443 if self.scheme == "https" else 80)
        self.path_prefix = parsed.path.rstrip("/")
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    def _conn(self) -> http.client.HTTPConnection:
        if self.scheme == "https":
            return http.client.HTTPSConnection(
                self.host, self.port, timeout=self.timeout, context=_ssl_ctx)
        return http.client.HTTPConnection(self.host, self.port, timeout=self.timeout)

    def stream(self, service: str, method: str, payload: dict = None,
               *, headers: dict = None, timeout: int = None) -> Generator[dict, None, None]:
        """发起流式 RPC 调用，逐条 yield 响应 JSON

        Args:
            service: gRPC 服务名
            method: 方法名
            payload: 请求 JSON 体
            headers: 额外 headers
            timeout: 超时

        Yields:
            dict — 每个流式响应片段 (通常包含 delta/content)
        """
        path = f"{self.path_prefix}/{service}/{method}"
        body = json.dumps(payload or {}).encode()

        h = {**CONNECT_HEADERS, **self.extra_headers}
        if headers:
            h.update(headers)

        conn = self._conn()
        if timeout:
            conn.timeout = timeout

        try:
            conn.request("POST", path, body=body, headers=h)
            resp = conn.getresponse()

            if resp.status != 200:
                error_body = resp.read().decode(errors="replace")
                try:
                    yield {"error": json.loads(error_body), "status": resp.status}
                except Exception:
                    yield {"error": error_body[:500], "status": resp.status}
                return

            # 读取流式响应 — Connect streaming 每行一个 JSON
            buffer = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk

                # 按换行分割 (Connect streaming 用 \n 分隔 JSON 对象)
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        yield obj
                    except json.JSONDecodeError:
                        # 可能是 SSE 格式: "data: {...}"
                        if line.startswith(b"data: "):
                            data_str = line[6:]
                            if data_str == b"[DONE]":
                                return
                            try:
                                yield json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

            # 处理 buffer 中剩余数据
            if buffer.strip():
                try:
                    yield json.loads(buffer)
                except json.JSONDecodeError:
                    pass
        finally:
            conn.close()

    def call(self, service: str, method: str, payload: dict = None,
             *, headers: dict = None, timeout: int = None) -> dict:
        """非流式调用 — 一次性返回完整响应

        Returns:
            dict — 完整响应 JSON
        """
        path = f"{self.path_prefix}/{service}/{method}"
        body = json.dumps(payload or {}).encode()

        h = {**CONNECT_HEADERS, **self.extra_headers}
        if headers:
            h.update(headers)

        conn = self._conn()
        if timeout:
            conn.timeout = timeout

        try:
            conn.request("POST", path, body=body, headers=h)
            resp = conn.getresponse()
            raw = resp.read().decode(errors="replace")
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {"raw": raw[:1000]}
            return {"ok": resp.status == 200, "status": resp.status, "data": data}
        finally:
            conn.close()


class LocalStreamingTransport(StreamingTransport):
    """本地 LS 流式传输 — 带 CSRF token"""

    def __init__(self, port: int, csrf_token: str = "", timeout: int = 60):
        super().__init__(f"http://127.0.0.1:{port}", timeout=timeout)
        if csrf_token:
            self.extra_headers["X-Csrf-Token"] = csrf_token
