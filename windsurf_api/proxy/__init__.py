"""windsurf_api.proxy — OpenAI 兼容反代服务器

把 Windsurf 的 AI 模型接口包装成 OpenAI API 格式:
  - GET  /v1/models
  - POST /v1/chat/completions (streaming + non-streaming)

用法::

    # 启动反代
    python -m windsurf_api.proxy --keys sk-ws-key1,sk-ws-key2 --port 8080

    # 然后用 OpenAI SDK 调用
    import openai
    client = openai.OpenAI(base_url="http://localhost:8080/v1", api_key="any")
    resp = client.chat.completions.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "Hello"}],
    )
"""
from .server import ProxyServer, run_proxy
from .key_pool import KeyPool
from .streaming import StreamingTransport
from .model_map import MODEL_MAP, resolve_model

__all__ = ["ProxyServer", "run_proxy", "KeyPool", "StreamingTransport", "MODEL_MAP", "resolve_model"]
