"""Connect-protocol 传输层

Windsurf 使用 Connect-protocol — 一种 gRPC 兼容协议:
  - HTTP/1.1 (非 HTTP/2)
  - JSON 编码 (非 protobuf binary)
  - POST {base_url}/{service}/{method}
  - Header: Connect-Protocol-Version: 1
  - Header: Content-Type: application/json

本模块提供底层传输，所有 service 调用都通过这里。
"""
import json
import ssl
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Optional


# ── SSL (忽略证书，兼容代理/抓包) ──
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


@dataclass
class RpcResponse:
    """gRPC 响应"""
    ok: bool
    status: int
    data: Any
    headers: dict = field(default_factory=dict)

    def __bool__(self):
        return self.ok

    def __getitem__(self, key):
        if isinstance(self.data, dict):
            return self.data[key]
        raise KeyError(key)

    def get(self, key, default=None):
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        return default


class RpcError(Exception):
    """gRPC 调用错误"""
    def __init__(self, status: int, code: str, message: str, data: Any = None):
        self.status = status
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"[{status}] {code}: {message}")


class ConnectTransport:
    """Connect-protocol HTTP 传输层

    用法::

        t = ConnectTransport("https://server.self-serve.windsurf.com")
        resp = t.call("exa.seat_management_pb.SeatManagementService", "GetUserStatus", {...})
    """

    CONNECT_HEADERS = {
        "Content-Type": "application/json",
        "Connect-Protocol-Version": "1",
    }

    BROWSER_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://windsurf.com/",
        "Origin": "https://windsurf.com",
    }

    def __init__(self, base_url: str, timeout: int = 15, extra_headers: dict = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    def call(self, service: str, method: str, payload: dict = None, *,
             headers: dict = None, timeout: int = None, raise_on_error: bool = False) -> RpcResponse:
        """调用 gRPC 方法

        Args:
            service: 完整服务名 (e.g. "exa.seat_management_pb.SeatManagementService")
            method: 方法名 (e.g. "GetUserStatus")
            payload: JSON 请求体
            headers: 额外 headers
            timeout: 超时秒数
            raise_on_error: 非 200 时是否抛异常

        Returns:
            RpcResponse
        """
        url = f"{self.base_url}/{service}/{method}"
        body = json.dumps(payload or {}).encode()

        h = {**self.CONNECT_HEADERS, **self.BROWSER_HEADERS, **self.extra_headers}
        if headers:
            h.update(headers)

        req = urllib.request.Request(url, data=body, headers=h)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout or self.timeout, context=_ssl_ctx)
            raw = resp.read().decode()
            data = json.loads(raw) if raw else {}
            result = RpcResponse(ok=True, status=resp.status, data=data)
        except urllib.error.HTTPError as e:
            raw = e.read().decode() if e.fp else ""
            try:
                data = json.loads(raw)
            except Exception:
                data = {"raw": raw[:1000]}
            result = RpcResponse(ok=False, status=e.code, data=data)
            if raise_on_error:
                code = data.get("code", "unknown") if isinstance(data, dict) else "unknown"
                msg = data.get("message", raw[:200]) if isinstance(data, dict) else raw[:200]
                raise RpcError(e.code, code, msg, data)
        except Exception as e:
            result = RpcResponse(ok=False, status=0, data={"error": str(e)[:300]})
            if raise_on_error:
                raise RpcError(0, "transport_error", str(e))

        return result

    def call_binary(self, service: str, method: str, data: bytes, *,
                    timeout: int = None) -> RpcResponse:
        """发送 protobuf binary 请求"""
        url = f"{self.base_url}/{service}/{method}"
        h = {"Content-Type": "application/proto", "Connect-Protocol-Version": "1",
             **self.BROWSER_HEADERS, **self.extra_headers}

        req = urllib.request.Request(url, data=data, headers=h)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout or self.timeout, context=_ssl_ctx)
            return RpcResponse(ok=True, status=resp.status, data=resp.read())
        except urllib.error.HTTPError as e:
            raw = e.read().decode() if e.fp else ""
            return RpcResponse(ok=False, status=e.code, data=raw[:1000])
        except Exception as e:
            return RpcResponse(ok=False, status=0, data=str(e)[:300])


def http_get(url: str, headers: dict = None, timeout: int = 15) -> RpcResponse:
    """通用 HTTP GET"""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx)
        raw = resp.read().decode()
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        return RpcResponse(ok=True, status=resp.status, data=data)
    except urllib.error.HTTPError as e:
        return RpcResponse(ok=False, status=e.code, data=e.read().decode()[:1000] if e.fp else "")
    except Exception as e:
        return RpcResponse(ok=False, status=0, data=str(e)[:300])


def http_post(url: str, payload: Any, headers: dict = None, timeout: int = 15) -> RpcResponse:
    """通用 HTTP POST"""
    if isinstance(payload, dict):
        body = json.dumps(payload).encode()
        h = {"Content-Type": "application/json"}
    elif isinstance(payload, str):
        body = payload.encode()
        h = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        body = payload
        h = {}
    if headers:
        h.update(headers)

    req = urllib.request.Request(url, data=body, headers=h)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx)
        raw = resp.read().decode()
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        return RpcResponse(ok=True, status=resp.status, data=data)
    except urllib.error.HTTPError as e:
        return RpcResponse(ok=False, status=e.code, data=e.read().decode()[:1000] if e.fp else "")
    except Exception as e:
        return RpcResponse(ok=False, status=0, data=str(e)[:300])
