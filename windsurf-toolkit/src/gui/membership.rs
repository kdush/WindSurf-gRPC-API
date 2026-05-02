//! Windsurf 会员等级映射 (TEAMS_TIER_*)
//!
//! 完整覆盖从 LS 二进制扫描出的 20 种 TEAMS_TIER 枚举值,以及 4 种 BILLING_STRATEGY,
//! 提供中文名、徽标颜色、图标 URI、SVG 字节、说明等元数据,确保会员标识在 UI 上一致且准确.

use eframe::egui::Color32;
use crate::gui::theme::*;
use crate::gui::icons;

/// 会员等级元数据
pub struct TierInfo {
    /// 中文名 (短)
    pub label: &'static str,
    /// 徽标颜色
    pub color: Color32,
    /// 徽标背景 (浅色)
    pub bg: Color32,
    /// SVG 图标 URI (用于 egui Image 缓存键)
    pub icon_uri: &'static str,
    /// SVG 图标字节
    pub icon_bytes: &'static [u8],
    /// 中文说明
    pub description: &'static str,
}

impl TierInfo {
    /// 默认未识别 (UNSPECIFIED) 的灰色徽标
    pub fn unknown() -> &'static TierInfo {
        TIER_UNKNOWN
    }
}

static TIER_UNKNOWN: &TierInfo = &TierInfo {
    label: "未知",
    color: TEXT_MUTED,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_unknown.svg",
    icon_bytes: icons::ICON_USER,
    description: "未识别的会员等级",
};

/// 把 TEAMS_TIER_* 枚举值映射为完整的 TierInfo
/// 输入既可以是带前缀的 `TEAMS_TIER_DEVIN_FREE`, 也可以是去前缀的 `DEVIN_FREE`
pub fn lookup_tier(raw: &str) -> &'static TierInfo {
    let cleaned = raw.trim().trim_start_matches("TEAMS_TIER_").to_uppercase();
    match cleaned.as_str() {
        // ── Devin 系列 (智能体专用) ──
        "DEVIN_FREE" => TIER_DEVIN_FREE,
        "DEVIN_PRO" => TIER_DEVIN_PRO,
        "DEVIN_MAX" => TIER_DEVIN_MAX,
        "DEVIN_TEAMS" => TIER_DEVIN_TEAMS,
        "DEVIN_TEAMS_V2" => TIER_DEVIN_TEAMS_V2,
        "DEVIN_ENTERPRISE" => TIER_DEVIN_ENTERPRISE,
        "DEVIN_TRIAL" => TIER_DEVIN_TRIAL,

        // ── 个人套餐 ──
        "PRO" => TIER_PRO,
        "PRO_ULTIMATE" => TIER_PRO_ULTIMATE,
        "MAX" => TIER_MAX,
        "TRIAL" => TIER_TRIAL,
        "WAITLIST_PRO" => TIER_WAITLIST_PRO,

        // ── 团队套餐 ──
        "TEAMS" => TIER_TEAMS,
        "TEAMS_ULTIMATE" => TIER_TEAMS_ULTIMATE,
        "HYBRID" => TIER_HYBRID,

        // ── 企业套餐 ──
        "ENTERPRISE_SAAS" => TIER_ENTERPRISE_SAAS,
        "ENTERPRISE_SAAS_POOLED" => TIER_ENTERPRISE_SAAS_POOLED,
        "ENTERPRISE_SELF_HOSTED" => TIER_ENTERPRISE_SELF_HOSTED,
        "ENTERPRISE_SELF_SERVE" => TIER_ENTERPRISE_SELF_SERVE,

        // 兜底
        "UNSPECIFIED" | "" => TierInfo::unknown(),
        _ => TierInfo::unknown(),
    }
}

/// 把 BILLING_STRATEGY_* 转中文 (4 种真实值)
pub fn lookup_billing(raw: &str) -> &'static str {
    let cleaned = raw.trim().trim_start_matches("BILLING_STRATEGY_").to_uppercase();
    match cleaned.as_str() {
        "ACU" => "ACU 计费 (Agent 算力单元)",
        "CREDITS" => "Credits 计费 (按月度积分)",
        "QUOTA" => "Quota 计费 (按月度配额)",
        "UNSPECIFIED" | "" => "未指定",
        _ => "其他",
    }
}

// ═══════════════════════════════════════
// 静态 TierInfo 实例 (按等级颜色梯度)
// ═══════════════════════════════════════

// ── Devin 系列 (智能体, 紫色系) ──
static TIER_DEVIN_FREE: &TierInfo = &TierInfo {
    label: "Devin Free",
    color: TEXT_SECONDARY,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_devin_free.svg",
    icon_bytes: icons::ICON_BOT,
    description: "Devin 智能体免费版 (基础体验)",
};
static TIER_DEVIN_PRO: &TierInfo = &TierInfo {
    label: "Devin Pro",
    color: ACCENT_PURPLE,
    bg: ACCENT_PURPLE_LIGHT,
    icon_uri: "bytes://tier_devin_pro.svg",
    icon_bytes: icons::ICON_BOT,
    description: "Devin 智能体专业版 (个人开发者)",
};
static TIER_DEVIN_MAX: &TierInfo = &TierInfo {
    label: "Devin Max",
    color: ACCENT_PURPLE,
    bg: ACCENT_PURPLE_LIGHT,
    icon_uri: "bytes://tier_devin_max.svg",
    icon_bytes: icons::ICON_CROWN,
    description: "Devin 智能体最高个人套餐",
};
static TIER_DEVIN_TEAMS: &TierInfo = &TierInfo {
    label: "Devin Teams",
    color: ACCENT_CYAN,
    bg: ACCENT_CYAN_LIGHT,
    icon_uri: "bytes://tier_devin_teams.svg",
    icon_bytes: icons::ICON_TEAM,
    description: "Devin 智能体团队版",
};
static TIER_DEVIN_TEAMS_V2: &TierInfo = &TierInfo {
    label: "Devin Teams V2",
    color: ACCENT_CYAN,
    bg: ACCENT_CYAN_LIGHT,
    icon_uri: "bytes://tier_devin_teams_v2.svg",
    icon_bytes: icons::ICON_TEAM,
    description: "Devin 智能体团队版 V2 (新版本)",
};
static TIER_DEVIN_ENTERPRISE: &TierInfo = &TierInfo {
    label: "Devin Enterprise",
    color: ACCENT,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_devin_ent.svg",
    icon_bytes: icons::ICON_BUILDING,
    description: "Devin 智能体企业版",
};
static TIER_DEVIN_TRIAL: &TierInfo = &TierInfo {
    label: "Devin 试用",
    color: ACCENT_YELLOW,
    bg: ACCENT_YELLOW_LIGHT,
    icon_uri: "bytes://tier_devin_trial.svg",
    icon_bytes: icons::ICON_HOURGLASS,
    description: "Devin 智能体限时试用",
};

// ── 个人套餐 ──
static TIER_PRO: &TierInfo = &TierInfo {
    label: "Pro",
    color: ACCENT_PURPLE,
    bg: ACCENT_PURPLE_LIGHT,
    icon_uri: "bytes://tier_pro.svg",
    icon_bytes: icons::ICON_ZAP,
    description: "Pro 个人专业版",
};
static TIER_PRO_ULTIMATE: &TierInfo = &TierInfo {
    label: "Pro Ultimate",
    color: ACCENT_PURPLE,
    bg: ACCENT_PURPLE_LIGHT,
    icon_uri: "bytes://tier_pro_ult.svg",
    icon_bytes: icons::ICON_CROWN,
    description: "Pro 终极版 (个人最高套餐)",
};
static TIER_MAX: &TierInfo = &TierInfo {
    label: "Max",
    color: ACCENT_GREEN,
    bg: ACCENT_GREEN_LIGHT,
    icon_uri: "bytes://tier_max.svg",
    icon_bytes: icons::ICON_CROWN,
    description: "Max 套餐 (个人加强版)",
};
static TIER_TRIAL: &TierInfo = &TierInfo {
    label: "试用版",
    color: ACCENT_YELLOW,
    bg: ACCENT_YELLOW_LIGHT,
    icon_uri: "bytes://tier_trial.svg",
    icon_bytes: icons::ICON_HOURGLASS,
    description: "限时试用 (功能受限)",
};
static TIER_WAITLIST_PRO: &TierInfo = &TierInfo {
    label: "Pro 候补",
    color: TEXT_SECONDARY,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_waitlist.svg",
    icon_bytes: icons::ICON_HOURGLASS,
    description: "Pro 候补名单 (等待激活)",
};

// ── 团队套餐 ──
static TIER_TEAMS: &TierInfo = &TierInfo {
    label: "Teams",
    color: ACCENT_CYAN,
    bg: ACCENT_CYAN_LIGHT,
    icon_uri: "bytes://tier_teams.svg",
    icon_bytes: icons::ICON_TEAM,
    description: "Teams 团队版",
};
static TIER_TEAMS_ULTIMATE: &TierInfo = &TierInfo {
    label: "Teams Ultimate",
    color: ACCENT_CYAN,
    bg: ACCENT_CYAN_LIGHT,
    icon_uri: "bytes://tier_teams_ult.svg",
    icon_bytes: icons::ICON_CROWN,
    description: "Teams 终极版 (团队最高套餐)",
};
static TIER_HYBRID: &TierInfo = &TierInfo {
    label: "Hybrid",
    color: ACCENT_CYAN,
    bg: ACCENT_CYAN_LIGHT,
    icon_uri: "bytes://tier_hybrid.svg",
    icon_bytes: icons::ICON_TEAM,
    description: "混合套餐 (个人 + 团队功能)",
};

// ── 企业套餐 ──
static TIER_ENTERPRISE_SAAS: &TierInfo = &TierInfo {
    label: "Enterprise SaaS",
    color: ACCENT,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_ent_saas.svg",
    icon_bytes: icons::ICON_BUILDING,
    description: "企业 SaaS (云端托管)",
};
static TIER_ENTERPRISE_SAAS_POOLED: &TierInfo = &TierInfo {
    label: "Enterprise SaaS Pool",
    color: ACCENT,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_ent_pool.svg",
    icon_bytes: icons::ICON_BUILDING,
    description: "企业 SaaS 共享池版",
};
static TIER_ENTERPRISE_SELF_HOSTED: &TierInfo = &TierInfo {
    label: "Enterprise 私有部署",
    color: ACCENT,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_ent_host.svg",
    icon_bytes: icons::ICON_BUILDING,
    description: "企业私有部署 (本地服务器)",
};
static TIER_ENTERPRISE_SELF_SERVE: &TierInfo = &TierInfo {
    label: "Enterprise 自助",
    color: ACCENT,
    bg: BG_SUBTLE,
    icon_uri: "bytes://tier_ent_serve.svg",
    icon_bytes: icons::ICON_BUILDING,
    description: "企业自助版 (DIY 配置)",
};
