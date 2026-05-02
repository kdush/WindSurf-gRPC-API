"""模型映射 — Windsurf 模型 UID ↔ OpenAI 兼容模型名

Windsurf 内部用 modelUid 标识模型，外部需要映射为标准名称。
映射表来源于逆向 GetModelProviders / GetCascadeModelConfigs 响应。
"""

# Windsurf modelUid → 标准显示名
# 格式: {windsurf_uid: (provider, openai_compatible_name, display_name)}
MODEL_MAP = {
    # ── Anthropic ──
    "claude-sonnet-4-20250514": ("anthropic", "claude-sonnet-4-20250514", "Claude Sonnet 4"),
    "claude-3-5-sonnet": ("anthropic", "claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
    "claude-3-5-haiku": ("anthropic", "claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
    "claude-3-7-sonnet": ("anthropic", "claude-3-7-sonnet-20250219", "Claude 3.7 Sonnet"),

    # ── OpenAI ──
    "gpt-4o": ("openai", "gpt-4o", "GPT-4o"),
    "gpt-4o-mini": ("openai", "gpt-4o-mini", "GPT-4o Mini"),
    "gpt-4.1": ("openai", "gpt-4.1", "GPT-4.1"),
    "o3": ("openai", "o3", "o3"),
    "o3-mini": ("openai", "o3-mini", "o3-mini"),
    "o4-mini": ("openai", "o4-mini", "o4-mini"),

    # ── Google ──
    "gemini-2.5-pro": ("google", "gemini-2.5-pro", "Gemini 2.5 Pro"),
    "gemini-2.0-flash": ("google", "gemini-2.0-flash", "Gemini 2.0 Flash"),
    "gemini-2.5-flash": ("google", "gemini-2.5-flash", "Gemini 2.5 Flash"),

    # ── xAI ──
    "grok-3": ("xai", "grok-3", "Grok 3"),
    "grok-3-mini": ("xai", "grok-3-mini", "Grok 3 Mini"),

    # ── DeepSeek ──
    "deepseek-v3": ("deepseek", "deepseek-chat", "DeepSeek V3"),
    "deepseek-r1": ("deepseek", "deepseek-reasoner", "DeepSeek R1"),
}

# 反向映射: openai 兼容名 → windsurf uid
REVERSE_MAP = {}
for uid, (provider, compat_name, display) in MODEL_MAP.items():
    REVERSE_MAP[compat_name] = uid
    REVERSE_MAP[uid] = uid
    REVERSE_MAP[display.lower()] = uid


def resolve_model(model_name: str) -> str:
    """将用户传入的模型名解析为 Windsurf modelUid

    支持:
      - 精确匹配 Windsurf UID
      - 匹配 OpenAI 兼容名
      - 模糊匹配 (大小写不敏感)

    Args:
        model_name: 用户传入的模型名

    Returns:
        Windsurf modelUid (找不到则原样返回)
    """
    if not model_name:
        return "claude-sonnet-4-20250514"

    # 精确匹配
    if model_name in MODEL_MAP:
        return model_name

    # 反向映射
    if model_name in REVERSE_MAP:
        return REVERSE_MAP[model_name]

    # 大小写不敏感
    lower = model_name.lower()
    if lower in REVERSE_MAP:
        return REVERSE_MAP[lower]

    # 模糊前缀匹配
    for uid in MODEL_MAP:
        if uid.startswith(lower) or lower.startswith(uid):
            return uid

    # 找不到 — 原样传给 Windsurf (可能是新模型)
    return model_name


def list_models() -> list:
    """列出所有已知模型 (OpenAI /v1/models 格式)

    Returns:
        list of dict — OpenAI models response 格式
    """
    models = []
    for uid, (provider, compat_name, display) in MODEL_MAP.items():
        models.append({
            "id": uid,
            "object": "model",
            "created": 1700000000,
            "owned_by": provider,
            "permission": [],
            "root": uid,
            "parent": None,
        })
    return models
