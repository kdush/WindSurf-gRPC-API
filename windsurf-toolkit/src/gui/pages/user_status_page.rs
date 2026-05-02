use eframe::egui::{self, RichText, Ui, Vec2, CornerRadius, Stroke};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;
use crate::gui::icons;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "用户状态", "查询 Windsurf 用户信息、Plan、额度 · 调用真实 gRPC API");

    // 自动用第一个有效密钥填充
    if state.user_status_key.is_empty() {
        if let Some(k) = state.keys.iter().find(|k| k.healthy) {
            state.user_status_key = k.full_key.clone();
        }
    }

    // ── API Key 输入 ──
    card_with_desc(ui, "Windsurf API Key", "已自动填充第一个健康密钥 · 也可粘贴其他 sk-ws-... 密钥", |ui| {
        ui.horizontal(|ui| {
            ui.add(
                egui::TextEdit::singleline(&mut state.user_status_key)
                    .desired_width(ui.available_width() - 240.0)
                    .hint_text("粘贴 sk-ws-... API Key")
                    .font(egui::TextStyle::Monospace)
            );
            if secondary_button(ui, "使用首个密钥").clicked() {
                if let Some(k) = state.keys.iter().find(|k| k.healthy) {
                    state.user_status_key = k.full_key.clone();
                }
            }
            if secondary_button(ui, "清空结果").clicked() {
                state.api_result_label.clear();
                state.api_result_text.clear();
                state.user_status_result.clear();
                state.parsed_user_loaded = false;
            }
        });
        if state.keys.is_empty() {
            ui.add_space(8.0);
            info_banner(ui, "暂无密钥 · 请先在「密钥管理」添加 API Key");
        }
    });

    ui.add_space(SECTION_SPACING);

    let has_key = !state.user_status_key.is_empty();
    let key = state.user_status_key.clone();

    // ── 一键加载 / 结构化用户信息 ──
    card_with_desc(ui, "账户信息", "调用 GetUserStatus 获取真实用户数据 (姓名、邮箱、Plan、额度、Team)", |ui| {
        ui.horizontal(|ui| {
            ui.add_enabled_ui(has_key, |ui| {
                if primary_button(ui, "加载/刷新").clicked() {
                    state.call_api_async("用户状态".into(),
                        "exa.seat_management_pb.SeatManagementService".into(),
                        "GetUserStatus".into(), key.clone());
                }
            });
            if state.parsed_user_loaded {
                ui.add_space(8.0);
                pill(ui, "已加载", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
            }
        });

        if state.parsed_user_loaded {
            ui.add_space(14.0);
            // 4 列结构化展示
            ui.columns(4, |cols| {
                user_field(&mut cols[0], "姓名", &if state.parsed_user_name.is_empty() { "-".to_string() } else { state.parsed_user_name.clone() });
                user_field(&mut cols[1], "邮箱", &if state.parsed_user_email.is_empty() { "-".to_string() } else { state.parsed_user_email.clone() });
                user_field(&mut cols[2], "Plan", &if state.parsed_user_plan.is_empty() { "-".to_string() } else { state.parsed_user_plan.clone() });
                user_field(&mut cols[3], "Tier", &short_tier(&state.parsed_user_tier));
            });
            ui.add_space(8.0);
            ui.columns(4, |cols| {
                user_field(&mut cols[0], "提示词额度", &format!("{}/月", state.parsed_credits_prompt));
                user_field(&mut cols[1], "流量额度", &format!("{}/月", state.parsed_credits_flow));
                user_field(&mut cols[2], "Billing", &short_billing(&state.parsed_user_billing));
                user_field(&mut cols[3], "User ID", &short_id(&state.parsed_user_id));
            });
            if !state.parsed_user_team.is_empty() {
                ui.add_space(8.0);
                team_field(ui, "Team ID", &state.parsed_user_team);
            }
        } else {
            ui.add_space(8.0);
            ui.label(RichText::new("点击「加载/刷新」按钮调用 GetUserStatus 获取真实用户数据")
                .color(TEXT_MUTED).size(12.0));
        }
    });

    ui.add_space(SECTION_SPACING);

    let api = "exa.api_server_pb.ApiServerService";
    let seat = "exa.seat_management_pb.SeatManagementService";

    // ── 三大分类 · 每类 1 张卡片 ──
    card_with_desc(ui, "账户与配额", "查询账号档案、订阅 Plan、月度额度等基础信息 · 点击卡片弹出中文解读", |ui| {
        api_grid(ui, &[
            ApiBtn { icon_bytes: icons::ICON_USER, icon_uri: "bytes://api_user.svg",
                title: "账号档案", desc: "查询姓名、邮箱、Plan、Team、月度配额",
                method: "GetUserStatus", service: seat, accent: ACCENT },
            ApiBtn { icon_bytes: icons::ICON_CHAT, icon_uri: "bytes://api_chat.svg",
                title: "聊天容量", desc: "服务器是否还有容量接收新对话",
                method: "CheckChatCapacity", service: api, accent: ACCENT_GREEN },
            ApiBtn { icon_bytes: icons::ICON_GAUGE, icon_uri: "bytes://api_rate.svg",
                title: "消息限速", desc: "剩余可发送消息数 + 速率限制 (-1=无限)",
                method: "CheckUserMessageRateLimit", service: api, accent: ACCENT_YELLOW },
            ApiBtn { icon_bytes: icons::ICON_USERS, icon_uri: "bytes://api_users.svg",
                title: "并发会话", desc: "多用户并发会话状态 (MUCS)",
                method: "GetMucsInfo", service: seat, accent: ACCENT_CYAN },
        ], has_key, &mut |service, method, label| {
            state.show_result_modal = true;
            state.result_modal_pending = true;
            state.result_modal_label = label.clone();
            state.result_modal_show_raw = false;
            state.api_result_label.clear();
            state.api_result_text.clear();
            state.call_api_async(label, service, method, key.clone());
        });
    });

    ui.add_space(SECTION_SPACING);

    card_with_desc(ui, "模型列表", "Windsurf 平台支持的 AI 模型,按用途分类查询 · 点击卡片弹出中文解读", |ui| {
        api_grid(ui, &[
            ApiBtn { icon_bytes: icons::ICON_PROVIDER, icon_uri: "bytes://api_provider.svg",
                title: "厂商列表", desc: "OpenAI / Anthropic / Google / xAI / Qwen 等",
                method: "GetModelProviders", service: api, accent: ACCENT },
            ApiBtn { icon_bytes: icons::ICON_WAVE, icon_uri: "bytes://api_cascade.svg",
                title: "Cascade 模型", desc: "Cascade Agent 可用模型 (含价格倍率)",
                method: "GetCascadeModelConfigs", service: api, accent: ACCENT_CYAN },
            ApiBtn { icon_bytes: icons::ICON_CODE, icon_uri: "bytes://api_cli.svg",
                title: "CLI 模型", desc: "命令行工具可用的模型列表",
                method: "GetCliModelConfigs", service: api, accent: ACCENT_PURPLE },
            ApiBtn { icon_bytes: icons::ICON_BOLT, icon_uri: "bytes://api_cmd.svg",
                title: "快速命令模型", desc: "代码内联补全/快速编辑模型",
                method: "GetCommandModelConfigs", service: api, accent: ACCENT_YELLOW },
        ], has_key, &mut |service, method, label| {
            state.show_result_modal = true;
            state.result_modal_pending = true;
            state.result_modal_label = label.clone();
            state.result_modal_show_raw = false;
            state.api_result_label.clear();
            state.api_result_text.clear();
            state.call_api_async(label, service, method, key.clone());
        });
    });

    // ── 弹窗 (modal) ──
    if state.show_result_modal {
        render_result_modal(ui.ctx(), state);
    }
}

/// 公共入口 (供其他页面复用)
pub fn render_result_modal_pub(ctx: &egui::Context, state: &mut AppState) {
    render_result_modal(ctx, state);
}

/// 中央弹窗展示 API 调用结果 — 加载/中文解读/原始 JSON 切换
fn render_result_modal(ctx: &egui::Context, state: &mut AppState) {
    let mut open = state.show_result_modal;
    let title = if state.result_modal_label.is_empty() {
        "API 调用结果".to_string()
    } else {
        format!("{} · API 结果", state.result_modal_label)
    };

    egui::Window::new(title)
        .open(&mut open)
        .collapsible(false)
        .resizable(true)
        .default_size([720.0, 540.0])
        .min_width(560.0)
        .anchor(egui::Align2::CENTER_CENTER, [0.0, 0.0])
        .show(ctx, |ui| {
            if state.result_modal_pending {
                // 加载状态
                ui.add_space(40.0);
                ui.vertical_centered(|ui| {
                    ui.spinner();
                    ui.add_space(12.0);
                    ui.label(RichText::new("正在调用 Windsurf gRPC API...")
                        .color(TEXT_PRIMARY).size(14.0).strong());
                    ui.add_space(4.0);
                    ui.label(RichText::new("请稍候,响应到达后将自动展示中文解读")
                        .color(TEXT_MUTED).size(12.0));
                });
                ui.add_space(40.0);
                // 重绘以等待响应
                ctx.request_repaint();
                return;
            }

            // 顶部状态条
            ui.horizontal(|ui| {
                if state.api_result_ok {
                    pill(ui, "✓ 调用成功", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
                } else {
                    pill(ui, "✗ 调用失败", ACCENT_RED_LIGHT, ACCENT_RED);
                }
                if !state.api_result_label.is_empty() {
                    ui.add_space(8.0);
                    ui.label(RichText::new(&state.api_result_label).color(TEXT_LABEL).size(12.0).monospace());
                }
            });
            ui.add_space(12.0);

            // 中文智能解读 (主内容)
            let interpretation = interpret_api_result(
                &state.result_modal_label,
                &state.api_result_text,
                state.api_result_ok,
            );
            let display_text = if interpretation.is_empty() {
                "ℹ 此响应类型暂无专属中文解读 · 请展开下方查看原始 JSON".to_string()
            } else {
                interpretation
            };

            egui::Frame::new()
                .fill(if state.api_result_ok { ACCENT_GREEN_LIGHT } else { ACCENT_RED_LIGHT })
                .corner_radius(CornerRadius::same(10))
                .stroke(Stroke::new(1.0,
                    if state.api_result_ok { ACCENT_GREEN.gamma_multiply(0.4) }
                    else { ACCENT_RED.gamma_multiply(0.4) }))
                .inner_margin(egui::Margin::same(16))
                .show(ui, |ui| {
                    ui.set_min_width(ui.available_width() - 4.0);
                    ui.horizontal(|ui| {
                        let tint = if state.api_result_ok { ACCENT_GREEN } else { ACCENT_RED };
                        inline_icon(ui, "bytes://lightbulb_modal.svg", icons::ICON_LIGHTBULB, tint, 16.0);
                        ui.add_space(6.0);
                        ui.label(RichText::new("中文解读")
                            .color(tint)
                            .size(14.0).strong());
                    });
                    ui.add_space(10.0);
                    egui::ScrollArea::vertical().max_height(280.0).auto_shrink([false, true]).show(ui, |ui| {
                        ui.label(RichText::new(&display_text).color(TEXT_PRIMARY).size(13.5));
                    });
                });

            ui.add_space(12.0);

            // 原始 JSON 折叠区
            ui.horizontal(|ui| {
                let label = if state.result_modal_show_raw { "▼ 隐藏原始 JSON" } else { "▶ 查看原始 JSON" };
                if secondary_button(ui, label).clicked() {
                    state.result_modal_show_raw = !state.result_modal_show_raw;
                }
                ui.add_space(8.0);
                if secondary_button(ui, "复制 JSON").clicked() {
                    ui.ctx().copy_text(state.api_result_text.clone());
                }
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    if primary_button(ui, "关闭").clicked() {
                        state.show_result_modal = false;
                    }
                });
            });

            if state.result_modal_show_raw {
                ui.add_space(8.0);
                egui::Frame::new()
                    .fill(BG_SUBTLE)
                    .corner_radius(CornerRadius::same(8))
                    .inner_margin(egui::Margin::same(12))
                    .show(ui, |ui| {
                        ui.set_min_width(ui.available_width() - 4.0);
                        egui::ScrollArea::vertical().max_height(220.0).auto_shrink([false, true]).show(ui, |ui| {
                            ui.label(RichText::new(&state.api_result_text)
                                .color(TEXT_PRIMARY).size(11.0).monospace());
                        });
                    });
            }
        });

    // 用户点了 X 关闭弹窗
    if !open {
        state.show_result_modal = false;
    }
}

/// API 按钮元数据 (使用 SVG 图标)
struct ApiBtn<'a> {
    icon_bytes: &'static [u8],
    icon_uri: &'static str,
    title: &'a str,
    desc: &'a str,
    method: &'a str,
    service: &'a str,
    accent: eframe::egui::Color32,
}

/// 网格布局 — 每行 2 个大按钮
fn api_grid<'a>(ui: &mut Ui, btns: &[ApiBtn<'a>], enabled: bool, on_click: &mut dyn FnMut(String, String, String)) {
    let cols = 2;
    let chunks: Vec<_> = btns.chunks(cols).collect();
    for chunk in chunks {
        ui.columns(cols, |columns| {
            for (i, btn) in chunk.iter().enumerate() {
                if api_card_btn(&mut columns[i], btn, enabled) {
                    on_click(btn.service.to_string(), btn.method.to_string(), btn.title.to_string());
                }
            }
        });
        ui.add_space(8.0);
    }
}

/// 大号 API 卡片按钮 — SVG 图标徽标 + 中文标题 + 方法名标签 + 描述
fn api_card_btn(ui: &mut Ui, btn: &ApiBtn, enabled: bool) -> bool {
    let resp = ui.add_enabled_ui(enabled, |ui| {
        let (bg, border) = if enabled { (BG_CARD, BORDER_LIGHT) } else { (BG_INPUT, BORDER_LIGHT) };
        let muted_accent = if enabled { btn.accent } else { TEXT_MUTED };
        egui::Frame::new()
            .fill(bg)
            .corner_radius(CornerRadius::same(10))
            .stroke(Stroke::new(1.0, border))
            .inner_margin(egui::Margin::symmetric(14, 12))
            .show(ui, |ui| {
                ui.set_min_width(ui.available_width() - 4.0);
                ui.set_min_height(78.0);
                ui.horizontal(|ui| {
                    // 彩色 SVG 图标徽标
                    egui::Frame::new()
                        .fill(muted_accent.gamma_multiply(0.12))
                        .corner_radius(CornerRadius::same(8))
                        .inner_margin(egui::Margin::same(8))
                        .show(ui, |ui| {
                            ui.add(egui::Image::from_bytes(btn.icon_uri, btn.icon_bytes)
                                .fit_to_exact_size(Vec2::new(20.0, 20.0))
                                .tint(muted_accent));
                        });
                    ui.add_space(10.0);
                    ui.vertical(|ui| {
                        ui.horizontal(|ui| {
                            ui.label(RichText::new(btn.title)
                                .color(if enabled { TEXT_PRIMARY } else { TEXT_MUTED })
                                .size(14.0).strong());
                            ui.add_space(6.0);
                            // 方法名小标签
                            egui::Frame::new()
                                .fill(if enabled { ACCENT_PURPLE_LIGHT } else { BG_SUBTLE })
                                .corner_radius(CornerRadius::same(4))
                                .inner_margin(egui::Margin::symmetric(6, 2))
                                .show(ui, |ui| {
                                    ui.label(RichText::new(btn.method)
                                        .color(if enabled { ACCENT } else { TEXT_MUTED })
                                        .size(10.0).monospace());
                                });
                        });
                        ui.add_space(4.0);
                        ui.label(RichText::new(btn.desc)
                            .color(if enabled { TEXT_LABEL } else { TEXT_MUTED })
                            .size(11.5));
                    });
                });
            })
            .response
    }).inner;
    let clicked = resp.interact(eframe::egui::Sense::click()).clicked();
    if resp.hovered() && enabled {
        ui.ctx().set_cursor_icon(eframe::egui::CursorIcon::PointingHand);
    }
    clicked && enabled
}

/// 智能解读卡片 (中文)
fn interpretation_card(ui: &mut Ui, text: &str, ok: bool) {
    let (tint, accent) = if ok {
        (ACCENT_GREEN_LIGHT, ACCENT_GREEN)
    } else {
        (ACCENT_RED_LIGHT, ACCENT_RED)
    };
    egui::Frame::new()
        .fill(tint)
        .corner_radius(CornerRadius::same(10))
        .stroke(Stroke::new(1.0, accent.gamma_multiply(0.4)))
        .inner_margin(egui::Margin::same(14))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            ui.horizontal(|ui| {
                inline_icon(ui, "bytes://lightbulb_inline.svg", icons::ICON_LIGHTBULB, accent, 14.0);
                ui.add_space(4.0);
                ui.label(RichText::new("智能解读").color(accent).size(13.0).strong());
            });
            ui.add_space(8.0);
            ui.label(RichText::new(text).color(TEXT_PRIMARY).size(13.0));
        });
}

/// 把 API 响应解析为中文自然语言
fn interpret_api_result(label: &str, body: &str, ok: bool) -> String {
    if !ok {
        // 错误响应 — 简单解释
        if body.contains("invalid token") || body.contains("permission_denied") {
            return "❌ 密钥无效或已过期 · 请检查 API Key 是否正确".to_string();
        }
        if body.contains("404") || body.contains("not found") {
            return "❌ 端点不存在 · 此 API 在当前环境不可用".to_string();
        }
        if body.contains("400") {
            return "❌ 请求参数错误 · 此 API 需要额外参数才能调用".to_string();
        }
        return format!("❌ 调用失败 · 详见下方原始响应");
    }

    let json: serde_json::Value = match serde_json::from_str(body) {
        Ok(v) => v,
        Err(_) => return String::new(),
    };

    // 根据 label 关键字判断响应类型
    if label.contains("账号档案") || label.contains("用户状态") {
        let name = json.pointer("/userStatus/name").and_then(|v| v.as_str()).unwrap_or("-");
        let email = json.pointer("/userStatus/email").and_then(|v| v.as_str()).unwrap_or("-");
        let plan = json.pointer("/planInfo/planName").and_then(|v| v.as_str()).unwrap_or("-");
        let teams_tier_raw = json.pointer("/planInfo/teamsTier").and_then(|v| v.as_str()).unwrap_or("");
        let billing_raw = json.pointer("/planInfo/billingStrategy").and_then(|v| v.as_str()).unwrap_or("");
        let prompt = json.pointer("/planInfo/monthlyPromptCredits").and_then(|v| v.as_i64()).unwrap_or(0);
        let flow = json.pointer("/planInfo/monthlyFlowCredits").and_then(|v| v.as_i64()).unwrap_or(0);
        let team = json.pointer("/userStatus/teamId").and_then(|v| v.as_str()).unwrap_or("-");
        let user_id = json.pointer("/userInfo/userId").and_then(|v| v.as_str()).unwrap_or("-");
        let is_devin = json.pointer("/planInfo/isDevin").and_then(|v| v.as_bool()).unwrap_or(false);

        let tier_meta = crate::gui::membership::lookup_tier(teams_tier_raw);
        let billing_label = crate::gui::membership::lookup_billing(billing_raw);

        return format!(
            "账号档案加载成功\n\n\
             用户姓名: {}\n\
             邮箱地址: {}\n\
             User ID: {}\n\
             ─────────────────\n\
             订阅 Plan: {}\n\
             会员等级: {} ({})\n\
             计费策略: {}\n\
             Devin 智能体: {}\n\
             ─────────────────\n\
             月度总配额: {} credits\n\
             • Prompt 配额: {} credits/月\n\
             • Flow 配额: {} credits/月\n\
             ─────────────────\n\
             Team ID: {}",
            name, email, user_id,
            plan, tier_meta.label, tier_meta.description,
            billing_label,
            if is_devin { "已启用" } else { "未启用" },
            prompt + flow, prompt, flow,
            team
        );
    }

    if label.contains("聊天容量") || label.contains("ChatCapacity") {
        let has = json.get("hasCapacity").and_then(|v| v.as_bool()).unwrap_or(false);
        return if has {
            "✓ 服务器有容量 · 可以正常发起对话".to_string()
        } else {
            "⚠ 服务器容量已满 · 请稍后再试".to_string()
        };
    }

    if label.contains("消息限速") || label.contains("RateLimit") {
        let has = json.get("hasCapacity").and_then(|v| v.as_bool()).unwrap_or(false);
        let remaining = json.get("messagesRemaining").and_then(|v| v.as_i64()).unwrap_or(0);
        let max = json.get("maxMessages").and_then(|v| v.as_i64()).unwrap_or(0);
        let status = if has { "✓ 未触发限速" } else { "⚠ 已触发限速" };
        let detail = if remaining < 0 || max < 0 {
            "无消息数限制 (Free Plan 默认无限制)".to_string()
        } else {
            format!("剩余 {} 条消息 / 上限 {} 条", remaining, max)
        };
        return format!("{} · {}", status, detail);
    }

    if label.contains("厂商列表") || label.contains("Provider") {
        if let Some(arr) = json.get("modelProviders").and_then(|v| v.as_array()) {
            let names: Vec<String> = arr.iter()
                .filter_map(|p| p.get("displayName").and_then(|v| v.as_str()).map(String::from))
                .collect();
            return format!("✓ 共 {} 家模型厂商\n\n🏢 {}", names.len(), names.join(" · "));
        }
    }

    if label.contains("Cascade 模型") || label.contains("CLI 模型") || label.contains("快速命令模型") {
        if let Some(arr) = json.get("clientModelConfigs").and_then(|v| v.as_array()) {
            let mut lines = Vec::new();
            let mut enabled_count = 0;
            for cfg in arr.iter().take(20) {
                let name = cfg.get("label").and_then(|v| v.as_str()).unwrap_or("?");
                let mult = cfg.get("creditMultiplier").and_then(|v| v.as_f64()).unwrap_or(1.0);
                let disabled = cfg.get("disabled").and_then(|v| v.as_bool()).unwrap_or(false);
                if !disabled { enabled_count += 1; }
                let status = if disabled { "🔒" } else { "✓" };
                lines.push(format!("  {} {} ({}x)", status, name, mult));
            }
            let total = arr.len();
            let mut msg = format!("✓ 共 {} 个模型 · 已启用 {}\n\n", total, enabled_count);
            msg.push_str(&lines.join("\n"));
            if total > 20 {
                msg.push_str(&format!("\n  ... 还有 {} 个", total - 20));
            }
            return msg;
        }
    }

    if label.contains("MUCS") || label.contains("并发会话") {
        if json.as_object().map_or(true, |o| o.is_empty()) {
            return "ℹ 当前账号无并发会话信息 (Free Plan 通常返回空对象)".to_string();
        }
    }

    // ── LS / Pro 注入相关解读 ──
    if label.contains("LS 探测") || label.contains("自动检测 LS") {
        let connected = json.get("connected").and_then(|v| v.as_bool()).unwrap_or(false);
        if connected {
            let port = json.get("port").and_then(|v| v.as_u64()).unwrap_or(0);
            let status_code = json.get("ls_status_code").and_then(|v| v.as_u64()).unwrap_or(0);
            let csrf_status = json.get("csrf_status").and_then(|v| v.as_str()).unwrap_or("");
            let note = json.get("note").and_then(|v| v.as_str()).unwrap_or("");
            return format!(
                "✓ Windsurf Language Server 已连接\n\n\
                 📡 端口: {}\n\
                 🔐 CSRF: {}\n\
                 📊 LS 响应: HTTP {}\n\n\
                 💡 {}",
                port, csrf_status, status_code, note
            );
        } else {
            let reason = json.get("reason").and_then(|v| v.as_str()).unwrap_or("未知原因");
            let scanned = json.get("scanned_ports").and_then(|v| v.as_str()).unwrap_or("");
            if !scanned.is_empty() {
                return format!("⚠ 未检测到 LS\n\n扫描端口: {}\n原因: {}\n\n请确认 Windsurf 已启动且 LS 正常运行", scanned, reason);
            }
            return format!("⚠ 未检测到 Windsurf LS\n\n{}\n\n请先启动 Windsurf 编辑器", reason);
        }
    }

    if label.contains("LS 心跳") || label.contains("Heartbeat") {
        return "✓ LS 心跳响应正常 · LanguageServer 在线运行".to_string();
    }

    if label.contains("一键注入 Pro") || label.contains("注入 Pro 实验") {
        return "✓ Pro 实验注入成功!\n\n🚀 已启用以下 Cascade 高级特性:\n\
                  • 禁用额度限制 (调用不计入月度配额)\n\
                  • Plan 配置覆盖 (高级 Plan 默认配置)\n\
                  • MCP 外部工具支持\n\
                  • Web App 一键部署\n\
                  • 代理 Web 服务器\n\
                  • 自动记忆功能\n\
                  • 浏览器工具控制".to_string();
    }

    if label.contains("查询当前实验") || label.contains("查询实验") || label.contains("GetUserSettings") || label.contains("GetBaseExperiments") {
        // GetUserSettings 返回 {"userSettings": {...}}
        let settings = json.get("userSettings").unwrap_or(&json);
        let mut lines = vec!["✓ LS 当前用户设置:".to_string(), "".to_string()];
        if let Some(obj) = settings.as_object() {
            // 优先展示与实验/Cascade 相关的字段
            let priority_keys = ["lastSelectedCascadeModel", "cascadePlannerMode",
                "lastModelDefaultOverrideVersionId", "cascadeAllowedCommands",
                "cascadeAutoAcceptCommands", "cascadeReasoningMode",
                "experimentOverrides", "userExperiments"];
            for k in &priority_keys {
                if let Some(v) = obj.get(*k) {
                    let v_str = v.to_string();
                    let truncated = if v_str.len() > 200 {
                        format!("{}... (省略 {} 字符)", &v_str[..200], v_str.len() - 200)
                    } else { v_str };
                    lines.push(format!("  {} = {}", k, truncated));
                }
            }
            lines.push("".to_string());
            lines.push(format!("📋 共 {} 个设置项 · 详见原始 JSON", obj.len()));
        }
        return lines.join("\n");
    }

    if label.contains("清除") {
        return "✓ 实验已清除 · LS 已恢复默认状态".to_string();
    }

    if label.contains("LS 状态") || (label.contains("查看 LS") && json.is_object()) {
        // GetDebugDiagnostics 返回 {"languageServerDiagnostics":{"logs":[...]}}
        let diag = json.get("languageServerDiagnostics").unwrap_or(&json);
        let mut lines = vec!["✓ Windsurf Language Server 诊断信息:".to_string(), "".to_string()];

        // 显示 LS 启动日志的关键行 (版本、端口、配置)
        if let Some(logs) = diag.get("logs").and_then(|v| v.as_array()) {
            lines.push(format!("📋 LS 启动日志 (共 {} 行,展示关键行):", logs.len()));
            lines.push(String::new());
            let mut shown = 0;
            for log in logs {
                if let Some(s) = log.as_str() {
                    let lower = s.to_lowercase();
                    // 只展示有信息量的关键行
                    if lower.contains("version") || lower.contains("port") || lower.contains("listening")
                        || lower.contains("startup") || lower.contains("started")
                        || lower.contains("gomaxprocs") || lower.contains("config")
                        || lower.contains("metadata") || lower.contains("server") {
                        let trimmed = s.trim_end_matches('\n').trim();
                        if trimmed.len() > 200 {
                            lines.push(format!("  {}...", &trimmed[..200]));
                        } else {
                            lines.push(format!("  {}", trimmed));
                        }
                        shown += 1;
                        if shown >= 25 { break; }
                    }
                }
            }
            if shown == 0 {
                lines.push("  (没有匹配的关键行,详见原始 JSON)".to_string());
            }
        } else if let Some(obj) = json.as_object() {
            // 兜底: 直接展示对象字段
            for (k, v) in obj.iter().take(15) {
                let v_str = v.to_string();
                let truncated = if v_str.len() > 150 {
                    format!("{}...", &v_str[..150])
                } else { v_str };
                lines.push(format!("  {} = {}", k, truncated));
            }
        }
        return lines.join("\n");
    }

    String::new()
}

/// 单字段展示 (label 上 / value 下)
fn user_field(ui: &mut Ui, label: &str, value: &str) {
    egui::Frame::new()
        .fill(BG_SUBTLE)
        .corner_radius(CornerRadius::same(8))
        .stroke(Stroke::new(1.0, BORDER_LIGHT))
        .inner_margin(egui::Margin::symmetric(12, 10))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            ui.label(RichText::new(label).color(TEXT_LABEL).size(11.0));
            ui.add_space(2.0);
            ui.label(RichText::new(value).color(TEXT_PRIMARY).size(13.5).strong());
        });
}

/// 全宽字段 (用于长字符串如 Team ID)
fn team_field(ui: &mut Ui, label: &str, value: &str) {
    egui::Frame::new()
        .fill(BG_SUBTLE)
        .corner_radius(CornerRadius::same(8))
        .stroke(Stroke::new(1.0, BORDER_LIGHT))
        .inner_margin(egui::Margin::symmetric(12, 10))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            ui.label(RichText::new(label).color(TEXT_LABEL).size(11.0));
            ui.add_space(2.0);
            ui.label(RichText::new(value).color(TEXT_PRIMARY).size(12.5).monospace());
        });
}

fn short_tier(t: &str) -> String {
    if t.is_empty() { return "-".to_string(); }
    t.replace("TEAMS_TIER_", "").replace("_", " ")
}

fn short_billing(b: &str) -> String {
    if b.is_empty() { return "-".to_string(); }
    b.replace("BILLING_STRATEGY_", "").replace("_", " ")
}

fn short_id(id: &str) -> String {
    if id.is_empty() { return "-".to_string(); }
    if id.len() > 16 {
        format!("{}...{}", &id[..8], &id[id.len()-4..])
    } else { id.to_string() }
}

