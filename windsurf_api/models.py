"""Protobuf 消息类型定义 — 逆向自 extension.js typeName 和 LS binary

所有 gRPC 请求/响应的标准 metadata 构造 + 枚举类型定义。
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from enum import IntEnum


# ═══════════════════════════════════════════════════════
#  枚举 (逆向自 LS binary + extension.js)
# ═══════════════════════════════════════════════════════

class TeamsTier(IntEnum):
    """团队层级"""
    UNSPECIFIED = 0
    TEAMS = 1
    PRO = 2
    ENTERPRISE_SAAS = 3
    PRO_ULTIMATE = 8
    TRIAL = 9


class BillingStrategy(IntEnum):
    """计费策略"""
    UNSPECIFIED = 0
    CREDITS = 1
    QUOTA = 2


class ExperimentKey(IntEnum):
    """实验 Key ID (Feature Flag)"""
    CASCADE_ENFORCE_QUOTA = 204
    CASCADE_ENABLE_AUTOMATED_MEMORIES = 224
    CASCADE_ENABLE_MCP_TOOLS = 245
    CASCADE_PLAN_BASED_CONFIG_OVERRIDE = 266
    CASCADE_ENABLE_PROXY_WEB_SERVER = 290
    CASCADE_WEB_APP_DEPLOYMENTS_ENABLED = 300
    CASCADE_WINDSURF_BROWSER_TOOLS_ENABLED = 328


# ═══════════════════════════════════════════════════════
#  请求 metadata
# ═══════════════════════════════════════════════════════

IDE_VERSION = "2.0.61"


@dataclass
class RequestMetadata:
    """标准请求 metadata — 几乎所有 API 调用都需要"""
    api_key: str = ""
    ide_name: str = "windsurf"
    ide_version: str = IDE_VERSION
    extension_version: str = IDE_VERSION
    locale: str = "en"

    def to_dict(self) -> dict:
        d = {
            "apiKey": self.api_key,
            "ideName": self.ide_name,
            "ideVersion": self.ide_version,
            "extensionVersion": self.extension_version,
        }
        if self.locale:
            d["locale"] = self.locale
        return d


def metadata(api_key: str) -> dict:
    """快速构造 metadata dict"""
    return RequestMetadata(api_key=api_key).to_dict()


# ═══════════════════════════════════════════════════════
#  响应数据类
# ═══════════════════════════════════════════════════════

@dataclass
class UserStatus:
    """GetUserStatus 解析结果"""
    email: str = ""
    user_id: str = ""
    name: str = ""
    plan_name: str = ""
    teams_tier: int = 0
    billing_strategy: int = 0
    monthly_prompt_credits: int = 0
    monthly_flow_credits: int = 0
    available_prompt_credits: int = 0
    available_flow_credits: int = 0
    daily_quota_pct: float = 100.0
    weekly_quota_pct: float = 100.0
    plan_start: str = ""
    plan_end: str = ""
    has_paid_features: bool = False
    referral_code: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def total_credits(self) -> int:
        return self.available_prompt_credits + self.available_flow_credits

    @property
    def is_pro(self) -> bool:
        return self.teams_tier == TeamsTier.PRO or self.plan_name == "Pro"

    @classmethod
    def from_response(cls, data: dict) -> "UserStatus":
        us = data.get("userStatus", {})
        ps = us.get("planStatus", {})
        pi = ps.get("planInfo", {})
        ri = ps.get("referralInfo", {})
        return cls(
            email=us.get("email", ""),
            user_id=us.get("userId", ""),
            name=us.get("name", ""),
            plan_name=pi.get("planName", ""),
            teams_tier=pi.get("teamsTier", 0),
            billing_strategy=pi.get("billingStrategy", 0),
            monthly_prompt_credits=int(pi.get("monthlyPromptCredits", 0)),
            monthly_flow_credits=int(pi.get("monthlyFlowCredits", 0)),
            available_prompt_credits=int(ps.get("availablePromptCredits", 0)),
            available_flow_credits=int(ps.get("availableFlowCredits", 0)),
            daily_quota_pct=ps.get("dailyQuotaRemainingPercent", 100) or 100,
            weekly_quota_pct=ps.get("weeklyQuotaRemainingPercent", 100) or 100,
            plan_start=ps.get("planStart", ""),
            plan_end=ps.get("planEnd", ""),
            has_paid_features=pi.get("hasPaidFeatures", False),
            referral_code=ri.get("referralCode", ""),
            raw=data,
        )


@dataclass
class ModelProvider:
    """模型提供商"""
    name: str = ""
    display_name: str = ""
    models: list = field(default_factory=list)

    @classmethod
    def from_response(cls, data: dict) -> "ModelProvider":
        return cls(
            name=data.get("name", ""),
            display_name=data.get("displayName", ""),
            models=data.get("models", []),
        )


@dataclass
class RegisterResult:
    """注册结果"""
    api_key: str = ""
    user: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(self.api_key)

    @classmethod
    def from_response(cls, data: dict) -> "RegisterResult":
        return cls(
            api_key=data.get("apiKey", ""),
            user=data,
        )
