use eframe::egui::{self, RichText, Vec2, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;
use crate::gui::icons;
use crate::gui::membership;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "额度监控", "实时监控 Key 额度使用情况 · 自动健康检查");

    // ── 控制栏 ──
    let mut check_all = false;
    card(ui, "", |ui| {
        ui.horizontal(|ui| {
            if state.monitor_running {
                pill(ui, "● 监控中", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
            } else {
                pill(ui, "○ 已停止", BG_SUBTLE, TEXT_MUTED);
            }
            ui.add_space(16.0);
            ui.label(RichText::new("检查间隔").color(TEXT_LABEL).size(12.0));
            ui.add(egui::DragValue::new(&mut state.monitor_interval).range(10..=3600).suffix(" 秒"));

            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                let enabled = !state.keys.is_empty();
                ui.add_enabled_ui(enabled, |ui| {
                    if primary_button(ui, "立即检查").clicked() {
                        check_all = true;
                    }
                });
                ui.add_space(4.0);
                if state.monitor_running {
                    if danger_button(ui, "停止").clicked() {
                        state.monitor_running = false;
                    }
                } else if secondary_button(ui, "开始监控").clicked() {
                    state.monitor_running = true;
                    state.log_messages.push("额度监控已启动".to_string());
                    check_all = true; // 启动监控时立即检查一次
                }
            });
        });
    });

    if check_all {
        let keys: Vec<String> = state.keys.iter().map(|k| k.full_key.clone()).collect();
        state.log(format!("立即检查 · 正在并发校验 {} 个密钥...", keys.len()));
        for k in keys {
            state.check_key_async(k);
        }
    }

    ui.add_space(SECTION_SPACING);

    // ── 汇总统计 ──
    let total = state.keys.len();
    let healthy = state.keys.iter().filter(|k| k.healthy).count();
    let total_credits: i64 = state.keys.iter().filter_map(|k| k.credits).sum();
    let plans_loaded = state.keys.iter().filter(|k| !k.plan.is_empty()).count();

    ui.columns(4, |cols| {
        stat_card(&mut cols[0], "总密钥", &format!("{}", total), TEXT_PRIMARY);
        stat_card(&mut cols[1], "健康", &format!("{}/{}", healthy, total), ACCENT_GREEN);
        stat_card(&mut cols[2], "已加载 Plan", &format!("{}/{}", plans_loaded, total), ACCENT);
        stat_card(&mut cols[3], "月度总额度", &format!("{} cr", total_credits), ACCENT_YELLOW);
    });

    ui.add_space(SECTION_SPACING);

    // ── 额度详情 (每个 Key 一张富信息卡片) ──
    card_with_desc(ui, "额度详情", "每个 Key 的完整账户信息 · 数据来自 GetUserStatus (Plan / Tier / 配额 / 功能开关 / 团队配置)", |ui| {
        if state.keys.is_empty() {
            ui.vertical_centered(|ui| {
                ui.add_space(16.0);
                ui.label(RichText::new("暂无 Key").color(TEXT_SECONDARY).size(13.0).strong());
                ui.label(RichText::new("请先在「密钥管理」中添加").color(TEXT_MUTED).size(12.0));
                ui.add_space(16.0);
            });
            return;
        }

        // 密钥池同步状态栏
        ui.horizontal(|ui| {
            if state.auto_sync_keys {
                pill(ui, "● 实时同步中", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
            } else {
                pill(ui, "○ 同步已暂停", BG_SUBTLE, TEXT_MUTED);
            }
            ui.add_space(8.0);
            ui.label(RichText::new(format!("每 {} 秒自动扫描 Windsurf 当前 Key", state.key_sync_interval_secs))
                .color(TEXT_MUTED).size(11.5));
            ui.with_layout(eframe::egui::Layout::right_to_left(eframe::egui::Align::Center), |ui| {
                if state.auto_sync_keys {
                    if secondary_button(ui, "暂停同步").clicked() {
                        state.auto_sync_keys = false;
                    }
                } else {
                    if secondary_button(ui, "启用同步").clicked() {
                        state.auto_sync_keys = true;
                        state.last_key_sync_unix = 0;
                    }
                }
            });
        });
        ui.add_space(8.0);

        // 取每个 Key 的快照, 避免 borrow checker 冲突
        let keys_snapshot: Vec<_> = state.keys.iter()
            .map(|k| (k.full_key.clone(), k.preview.clone(), k.healthy, k.plan.clone(),
                      k.credits, k.status_json.clone(), k.is_active, k.source.clone()))
            .collect();

        let mut to_check: Option<String> = None;
        for (full_key, preview, healthy, plan, credits, status_json, is_active, source) in keys_snapshot {
            render_key_detail_card(ui, &full_key, &preview, healthy, &plan, credits,
                status_json.as_ref(), is_active, &source, &mut to_check);
            ui.add_space(8.0);
        }
        if let Some(k) = to_check {
            state.check_key_async(k);
        }
    });
}

/// 单个 Key 的详细信息卡片 (展示 GetUserStatus 的所有关键字段)
fn render_key_detail_card(
    ui: &mut Ui,
    full_key: &str,
    preview: &str,
    healthy: bool,
    plan: &str,
    credits: Option<i64>,
    status_json: Option<&serde_json::Value>,
    is_active: bool,
    source: &crate::gui::app::KeySource,
    to_check: &mut Option<String>,
) {
    // active key 的卡片边框用 ACCENT 高亮
    let (card_bg, card_stroke) = if is_active {
        (ACCENT_LIGHT, eframe::egui::Stroke::new(2.0, ACCENT))
    } else {
        (BG_CARD, eframe::egui::Stroke::new(1.0, BORDER_LIGHT))
    };
    egui::Frame::new()
        .fill(card_bg)
        .corner_radius(eframe::egui::CornerRadius::same(CARD_ROUNDING))
        .stroke(card_stroke)
        .inner_margin(eframe::egui::Margin::same(20))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);

            // ─── 顶部 Header: Key + 状态 + 活跃徽标 + 会员等级 + 来源 + 刷新 ───
            let header_tier = status_json
                .and_then(|j| j.pointer("/planInfo/teamsTier")
                    .or_else(|| j.pointer("/userStatus/teamsTier")))
                .and_then(|v| v.as_str())
                .map(membership::lookup_tier);

            ui.horizontal(|ui| {
                ui.label(RichText::new(preview).color(TEXT_PRIMARY).monospace().size(14.0).strong());
                ui.add_space(10.0);
                if healthy {
                    pill(ui, "有效", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
                } else {
                    pill(ui, "无效", ACCENT_RED_LIGHT, ACCENT_RED);
                }
                ui.add_space(6.0);
                // 🔥 当前正在使用的 Key (从 Windsurf LS 实时检测到)
                if is_active {
                    egui::Frame::new()
                        .fill(ACCENT)
                        .corner_radius(eframe::egui::CornerRadius::same(10))
                        .inner_margin(eframe::egui::Margin::symmetric(8, 4))
                        .show(ui, |ui| {
                            ui.horizontal(|ui| {
                                inline_icon(ui, "bytes://active_dot.svg", icons::ICON_PLAY,
                                    eframe::egui::Color32::WHITE, 10.0);
                                ui.add_space(3.0);
                                ui.label(RichText::new("Windsurf 正在使用")
                                    .color(eframe::egui::Color32::WHITE).size(10.5).strong());
                            });
                        });
                    ui.add_space(4.0);
                }
                // 来源徽标
                source_pill(ui, source);
                ui.add_space(6.0);
                // 会员等级徽标
                if let Some(t) = header_tier {
                    tier_pill(ui, t);
                }
                ui.with_layout(eframe::egui::Layout::right_to_left(eframe::egui::Align::Center), |ui| {
                    if icon_button(ui, "刷新", "bytes://btn_refresh.svg", icons::ICON_REFRESH_ARROW).clicked() {
                        *to_check = Some(full_key.to_string());
                    }
                });
            });

            ui.add_space(12.0);

            // 如果未加载 GetUserStatus, 提示
            let Some(j) = status_json else {
                egui::Frame::new()
                    .fill(BG_SUBTLE)
                    .corner_radius(eframe::egui::CornerRadius::same(8))
                    .inner_margin(eframe::egui::Margin::same(14))
                    .show(ui, |ui| {
                        ui.set_min_width(ui.available_width() - 4.0);
                        ui.horizontal(|ui| {
                            inline_icon(ui, "bytes://hourglass_load.svg", icons::ICON_HOURGLASS, TEXT_SECONDARY, 16.0);
                            ui.add_space(4.0);
                            ui.label(RichText::new("尚未获取详细信息")
                                .color(TEXT_SECONDARY).size(13.0).strong());
                        });
                        ui.label(RichText::new("点击右上角「刷新」按钮调用 GetUserStatus 加载完整账户信息")
                            .color(TEXT_MUTED).size(11.5));
                    });
                return;
            };

            // ─── 提取字段 (兼容两种路径: 顶级 planInfo 或 userStatus.planStatus.planInfo) ───
            let pi = j.pointer("/planInfo")
                .or_else(|| j.pointer("/userStatus/planStatus/planInfo"))
                .cloned().unwrap_or(serde_json::Value::Null);
            let us = j.pointer("/userStatus").cloned().unwrap_or(serde_json::Value::Null);
            let ps = j.pointer("/userStatus/planStatus")
                .or_else(|| j.pointer("/planStatus"))
                .cloned().unwrap_or(serde_json::Value::Null);

            // 用户基本信息 (userStatus 根级)
            let user_name = us.get("name").and_then(|v| v.as_str()).unwrap_or("-");
            let user_email = us.get("email").and_then(|v| v.as_str()).unwrap_or("-");
            let team_id = us.get("teamId").and_then(|v| v.as_str()).unwrap_or("-");
            let team_status = us.get("teamStatus").and_then(|v| v.as_str()).unwrap_or("-");
            let user_id = j.pointer("/userInfo/userId").and_then(|v| v.as_str()).unwrap_or("-");

            // Plan / Tier / 计费
            let teams_tier = pi.get("teamsTier").and_then(|v| v.as_str()).unwrap_or("-");
            let billing_strategy = pi.get("billingStrategy").and_then(|v| v.as_str()).unwrap_or("-");

            // 月度总额 (monthlyXxx)
            let monthly_prompt = pi.get("monthlyPromptCredits").and_then(|v| v.as_i64());
            let monthly_flow = pi.get("monthlyFlowCredits").and_then(|v| v.as_i64());
            let monthly_total = monthly_prompt.zip(monthly_flow).map(|(p, f)| p + f)
                .or(monthly_prompt).or(monthly_flow);

            // 剩余额度 (availableXxx) + 日/周百分比 + 重置时间
            let avail_prompt = ps.get("availablePromptCredits").and_then(|v| v.as_i64());
            let avail_flow = ps.get("availableFlowCredits").and_then(|v| v.as_i64());
            let avail_total = avail_prompt.zip(avail_flow).map(|(p, f)| p + f)
                .or(avail_prompt).or(avail_flow);
            let daily_pct = ps.get("dailyQuotaRemainingPercent").and_then(|v| v.as_i64());
            let weekly_pct = ps.get("weeklyQuotaRemainingPercent").and_then(|v| v.as_i64());
            let daily_reset = ps.get("dailyQuotaResetAtUnix").and_then(|v| v.as_str()).and_then(|s| s.parse::<i64>().ok());
            let weekly_reset = ps.get("weeklyQuotaResetAtUnix").and_then(|v| v.as_str()).and_then(|s| s.parse::<i64>().ok());

            // 容量
            let max_chat_tokens = pi.get("maxNumChatInputTokens").and_then(|v| v.as_str()).map(String::from);
            let max_local_index = pi.get("maxLocalIndexSize").and_then(|v| v.as_str()).map(String::from);
            let max_pinned = pi.get("maxNumPinnedContextItems").and_then(|v| v.as_str()).map(String::from);
            let max_custom_chars = pi.get("maxCustomChatInstructionCharacters").and_then(|v| v.as_str()).map(String::from);

            // Cascade 功能
            let is_devin = pi.get("isDevin").and_then(|v| v.as_bool()).unwrap_or(false);
            let has_autocomplete = pi.get("hasAutocompleteFastMode").and_then(|v| v.as_bool()).unwrap_or(false);
            let has_tab_jump = pi.get("hasTabToJump").and_then(|v| v.as_bool()).unwrap_or(false);
            let web_search = pi.get("cascadeWebSearchEnabled").and_then(|v| v.as_bool()).unwrap_or(false);
            let auto_run = pi.get("cascadeCanAutoRunCommands").and_then(|v| v.as_bool()).unwrap_or(false);
            let bg_cascade = pi.get("canAllowCascadeInBackground").and_then(|v| v.as_bool()).unwrap_or(false);
            let browser = pi.get("browserEnabled").and_then(|v| v.as_bool()).unwrap_or(false);
            let allowed_models = pi.get("cascadeAllowedModelsConfig")
                .and_then(|v| v.as_array()).map(|a| a.len()).unwrap_or(0);

            // 团队配置
            let tc = pi.get("defaultTeamConfig").cloned().unwrap_or(serde_json::Value::Null);
            let allow_mcp = tc.get("allowMcpServers").and_then(|v| v.as_bool()).unwrap_or(false);
            let allow_app_deploy = tc.get("allowAppDeployments").and_then(|v| v.as_bool()).unwrap_or(false);
            let arena_mode = tc.get("allowArenaMode").and_then(|v| v.as_bool()).unwrap_or(false);
            let max_unclaimed = tc.get("maxUnclaimedSites").and_then(|v| v.as_i64());
            let max_new_sites = tc.get("maxNewSitesPerDay").and_then(|v| v.as_i64());
            let auto_exec_level = tc.get("maxCascadeAutoExecutionLevel").and_then(|v| v.as_str()).unwrap_or("-").to_string();
            let disable_lifeguard = tc.get("disableLifeguard").and_then(|v| v.as_bool()).unwrap_or(false);
            let allow_codemap = tc.get("allowCodemapSharing").and_then(|v| v.as_str()).unwrap_or("-").to_string();

            // Devin 信息 (如果 isDevin)
            let di = pi.get("devinInfo").cloned().unwrap_or(serde_json::Value::Null);
            let devin_can_cascade = di.get("canUseCascade").and_then(|v| v.as_bool()).unwrap_or(false);
            let devin_can_cli = di.get("canUseCli").and_then(|v| v.as_bool()).unwrap_or(false);
            let devin_is_admin = di.get("isAdmin").and_then(|v| v.as_bool()).unwrap_or(false);
            let devin_org_id = di.get("orgId").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let devin_host = di.get("webappHost").and_then(|v| v.as_str()).unwrap_or("").to_string();
            let devin_review = di.get("devinReviewEnabled").and_then(|v| v.as_bool()).unwrap_or(false);

            // ─── 大数据展示行: 剩余额度 / 月度总额 / Cascade 模型 / 日额度 % ───
            let remaining_credits = avail_total.or(credits);
            ui.columns(4, |cols| {
                big_stat(&mut cols[0], icons::ICON_WALLET, "bytes://stat_wallet.svg", "剩余额度",
                    &remaining_credits.map_or("—".to_string(), fmt_int_i64),
                    &monthly_total.map_or(" credits".to_string(), |t| format!(" / {} 总额", fmt_int_i64(t))),
                    ACCENT_YELLOW);
                big_stat(&mut cols[1], icons::ICON_CHAT, "bytes://stat_prompt.svg", "Prompt 剩余",
                    &avail_prompt.or(monthly_prompt).map_or("—".to_string(), fmt_int_i64),
                    &monthly_prompt.map_or("".to_string(), |t| format!(" / {}", fmt_int_i64(t))),
                    ACCENT);
                big_stat(&mut cols[2], icons::ICON_BOLT, "bytes://stat_flow.svg", "Flow 剩余",
                    &avail_flow.or(monthly_flow).map_or("—".to_string(), fmt_int_i64),
                    &monthly_flow.map_or("".to_string(), |t| format!(" / {}", fmt_int_i64(t))),
                    ACCENT_PURPLE);
                big_stat(&mut cols[3], icons::ICON_BRAIN, "bytes://stat_brain.svg", "可用模型",
                    &format!("{}", allowed_models),
                    "个 (Cascade)",
                    if allowed_models > 0 { ACCENT_GREEN } else { TEXT_MUTED });
            });

            ui.add_space(14.0);

            // ─── 块 1: 账户基本信息 (真实姓名 + 邮箱 + Plan) ───
            section_header(ui, icons::ICON_USER, "bytes://sec_account.svg", "账户信息", ACCENT);
            ui.add_space(6.0);
            ui.columns(3, |cols| {
                kv_box(&mut cols[0], "账户姓名",
                    if user_name == "-" { "—" } else { user_name },
                    if user_name == "-" { TEXT_MUTED } else { TEXT_PRIMARY });
                kv_box(&mut cols[1], "注册邮箱",
                    if user_email == "-" { "—" } else { user_email },
                    if user_email == "-" { TEXT_MUTED } else { TEXT_PRIMARY });
                let tier_meta = membership::lookup_tier(teams_tier);
                kv_box(&mut cols[2], "会员等级", tier_meta.label, tier_meta.color);
            });
            ui.add_space(6.0);
            ui.columns(3, |cols| {
                kv_box(&mut cols[0], "套餐名", if plan.is_empty() { "—" } else { plan }, ACCENT);
                kv_box(&mut cols[1], "计费策略", membership::lookup_billing(billing_strategy), TEXT_PRIMARY);
                kv_box(&mut cols[2], "团队状态", &short_team_status(team_status),
                    if team_status == "USER_TEAM_STATUS_APPROVED" { ACCENT_GREEN } else { TEXT_PRIMARY });
            });
            ui.add_space(6.0);
            ui.columns(3, |cols| {
                kv_box(&mut cols[0], "User ID", &short_id(user_id), TEXT_SECONDARY);
                kv_box(&mut cols[1], "Team ID", &short_id(team_id), TEXT_SECONDARY);
                kv_box(&mut cols[2], "Lifeguard 守卫",
                    if disable_lifeguard { "已禁用" } else { "启用中" },
                    if disable_lifeguard { TEXT_MUTED } else { ACCENT_GREEN });
            });

            ui.add_space(14.0);

            // ─── 块 2: 额度重置 (日/周配额 + 重置时间) ───
            if daily_pct.is_some() || weekly_pct.is_some() || daily_reset.is_some() {
                section_header(ui, icons::ICON_HOURGLASS, "bytes://sec_quota.svg", "额度重置与限额", ACCENT_YELLOW);
                ui.add_space(6.0);
                ui.columns(4, |cols| {
                    kv_box(&mut cols[0], "日额度剩余",
                        &daily_pct.map_or("—".to_string(), |p| format!("{}%", p)),
                        if daily_pct.unwrap_or(0) >= 80 { ACCENT_GREEN }
                        else if daily_pct.unwrap_or(0) >= 30 { ACCENT_YELLOW }
                        else { ACCENT_RED });
                    kv_box(&mut cols[1], "周额度剩余",
                        &weekly_pct.map_or("—".to_string(), |p| format!("{}%", p)),
                        if weekly_pct.unwrap_or(0) >= 80 { ACCENT_GREEN }
                        else if weekly_pct.unwrap_or(0) >= 30 { ACCENT_YELLOW }
                        else { ACCENT_RED });
                    kv_box(&mut cols[2], "日额度重置时间",
                        &daily_reset.map_or("—".to_string(), fmt_unix_time), TEXT_PRIMARY);
                    kv_box(&mut cols[3], "周额度重置时间",
                        &weekly_reset.map_or("—".to_string(), fmt_unix_time), TEXT_PRIMARY);
                });
                ui.add_space(14.0);
            }

            // ─── 块 2.5: Devin 智能体 (如果 isDevin) ───
            if is_devin {
                section_header(ui, icons::ICON_BOT, "bytes://sec_devin.svg", "Devin 智能体集成", ACCENT_PURPLE);
                ui.add_space(6.0);
                ui.columns(3, |cols| {
                    kv_box(&mut cols[0], "Cascade 可用",
                        if devin_can_cascade { "已启用" } else { "未启用" },
                        if devin_can_cascade { ACCENT_GREEN } else { TEXT_MUTED });
                    kv_box(&mut cols[1], "CLI 可用",
                        if devin_can_cli { "已启用" } else { "未启用" },
                        if devin_can_cli { ACCENT_GREEN } else { TEXT_MUTED });
                    kv_box(&mut cols[2], "管理员权限",
                        if devin_is_admin { "已授予" } else { "无" },
                        if devin_is_admin { ACCENT_PURPLE } else { TEXT_MUTED });
                });
                ui.add_space(6.0);
                let devin_org_short = short_id(&devin_org_id);
                ui.columns(3, |cols| {
                    kv_box(&mut cols[0], "组织 ID",
                        if devin_org_id.is_empty() { "—" } else { &devin_org_short },
                        TEXT_SECONDARY);
                    kv_box(&mut cols[1], "Webapp 域名",
                        if devin_host.is_empty() { "—" } else { &devin_host },
                        TEXT_PRIMARY);
                    kv_box(&mut cols[2], "Devin Review",
                        if devin_review { "已启用" } else { "未启用" },
                        if devin_review { ACCENT_GREEN } else { TEXT_MUTED });
                });
                ui.add_space(14.0);
            }

            // ─── 块 2: Cascade 功能开关 ───
            section_header(ui, icons::ICON_ROCKET, "bytes://sec_cascade.svg", "Cascade 功能开关", ACCENT_PURPLE);
            ui.add_space(6.0);
            ui.horizontal_wrapped(|ui| {
                feature_pill(ui, "代码补全 Fast 模式", has_autocomplete);
                feature_pill(ui, "Tab 跳转", has_tab_jump);
                feature_pill(ui, "Web 联网搜索", web_search);
                feature_pill(ui, "自动执行命令", auto_run);
                feature_pill(ui, "后台运行 Cascade", bg_cascade);
                feature_pill(ui, "浏览器集成", browser);
                feature_pill(ui, "MCP 外部工具", allow_mcp);
                feature_pill(ui, "App 一键部署", allow_app_deploy);
                feature_pill(ui, "Arena 对战模式", arena_mode);
            });

            ui.add_space(14.0);

            // ─── 块 3: 容量上限 ───
            section_header(ui, icons::ICON_CHART, "bytes://sec_limit.svg", "容量上限", ACCENT_CYAN);
            ui.add_space(6.0);
            ui.columns(4, |cols| {
                kv_box(&mut cols[0], "Chat 输入 Token",
                    &fmt_int_str(max_chat_tokens.as_deref()), TEXT_PRIMARY);
                kv_box(&mut cols[1], "本地索引文件",
                    &fmt_int_str(max_local_index.as_deref()), TEXT_PRIMARY);
                kv_box(&mut cols[2], "Pin 上下文",
                    &fmt_int_str(max_pinned.as_deref()), TEXT_PRIMARY);
                kv_box(&mut cols[3], "自定义指令字符",
                    &fmt_int_str(max_custom_chars.as_deref()), TEXT_PRIMARY);
            });
            ui.add_space(6.0);
            ui.columns(4, |cols| {
                kv_box(&mut cols[0], "未领取站点",
                    &max_unclaimed.map_or("—".to_string(), |c| c.to_string()), TEXT_PRIMARY);
                kv_box(&mut cols[1], "每日新增站点",
                    &max_new_sites.map_or("—".to_string(), |c| c.to_string()), TEXT_PRIMARY);
                kv_box(&mut cols[2], "命令自动执行",
                    &short_exec(&auto_exec_level), TEXT_PRIMARY);
                kv_box(&mut cols[3], "Codemap 共享",
                    &allow_codemap, TEXT_PRIMARY);
            });
        });
}

/// 把团队状态枚举转成中文
fn short_team_status(s: &str) -> String {
    match s {
        "USER_TEAM_STATUS_APPROVED" => "已批准".to_string(),
        "USER_TEAM_STATUS_PENDING" => "待审批".to_string(),
        "USER_TEAM_STATUS_REJECTED" => "已拒绝".to_string(),
        "USER_TEAM_STATUS_REMOVED" => "已移除".to_string(),
        "-" | "" => "—".to_string(),
        other => other.replace("USER_TEAM_STATUS_", "").replace("_", " "),
    }
}

/// Unix 时间戳 → 可读本地时间 "MM/DD HH:MM"
fn fmt_unix_time(ts: i64) -> String {
    use chrono::{DateTime, Local, TimeZone};
    match Local.timestamp_opt(ts, 0) {
        chrono::LocalResult::Single(dt) => {
            let dt: DateTime<Local> = dt;
            let now = Local::now();
            let duration = dt.signed_duration_since(now);
            let secs = duration.num_seconds();
            let rel = if secs > 86400 {
                format!(" ({}天后)", secs / 86400)
            } else if secs > 3600 {
                format!(" ({}小时后)", secs / 3600)
            } else if secs > 60 {
                format!(" ({}分钟后)", secs / 60)
            } else if secs > 0 {
                " (即将)".to_string()
            } else {
                " (已过)".to_string()
            };
            format!("{}{}", dt.format("%m/%d %H:%M"), rel)
        }
        _ => "—".to_string(),
    }
}

/// 节标题 (SVG 图标 + 大字)
fn section_header(ui: &mut Ui, icon_bytes: &'static [u8], icon_uri: &'static str,
                  title: &str, color: eframe::egui::Color32) {
    ui.horizontal(|ui| {
        inline_icon(ui, icon_uri, icon_bytes, color, 16.0);
        ui.add_space(6.0);
        ui.label(RichText::new(title).color(TEXT_PRIMARY).size(13.5).strong());
    });
}

/// 大数据卡 (顶部 4 个核心数字 · SVG 图标 + 大数字 + 单位)
fn big_stat(
    ui: &mut Ui,
    icon_bytes: &'static [u8],
    icon_uri: &'static str,
    label: &str,
    value: &str,
    unit: &str,
    color: eframe::egui::Color32,
) {
    egui::Frame::new()
        .fill(BG_SUBTLE)
        .corner_radius(eframe::egui::CornerRadius::same(10))
        .inner_margin(eframe::egui::Margin::same(14))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            // 顶部: 图标 + 标签
            ui.horizontal(|ui| {
                inline_icon(ui, icon_uri, icon_bytes, color, 14.0);
                ui.add_space(5.0);
                ui.label(RichText::new(label).color(TEXT_SECONDARY).size(11.5));
            });
            ui.add_space(4.0);
            // 大数字 + 单位
            ui.horizontal(|ui| {
                ui.label(RichText::new(value).color(color).size(22.0).strong());
                ui.add_space(4.0);
                ui.with_layout(eframe::egui::Layout::bottom_up(eframe::egui::Align::Min), |ui| {
                    ui.add_space(4.0);
                    ui.label(RichText::new(unit).color(TEXT_MUTED).size(10.5));
                });
            });
        });
}

/// 字段盒 (浅灰背景的小卡, label + value 上下排列)
fn kv_box(ui: &mut Ui, label: &str, value: &str, value_color: eframe::egui::Color32) {
    egui::Frame::new()
        .fill(BG_SUBTLE)
        .corner_radius(eframe::egui::CornerRadius::same(8))
        .inner_margin(eframe::egui::Margin::symmetric(12, 9))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            ui.label(RichText::new(label).color(TEXT_MUTED).size(11.0));
            ui.add_space(3.0);
            ui.label(RichText::new(value).color(value_color).size(13.0).strong());
        });
}

/// 功能开关徽标 (SVG check/x 图标 + 文字)
fn feature_pill(ui: &mut Ui, name: &str, enabled: bool) {
    let (icon_bytes, icon_uri, fg, bg) = if enabled {
        (icons::ICON_CHECK, "bytes://feat_on.svg", ACCENT_GREEN, ACCENT_GREEN_LIGHT)
    } else {
        (icons::ICON_X, "bytes://feat_off.svg", TEXT_MUTED, BG_SUBTLE)
    };
    egui::Frame::new()
        .fill(bg)
        .corner_radius(eframe::egui::CornerRadius::same(12))
        .inner_margin(eframe::egui::Margin::symmetric(10, 5))
        .show(ui, |ui| {
            ui.horizontal(|ui| {
                inline_icon(ui, icon_uri, icon_bytes, fg, 12.0);
                ui.add_space(4.0);
                ui.label(RichText::new(name).color(fg).size(11.5).strong());
            });
        });
}

/// Key 来源徽标 (显示 Key 从哪里导入的)
fn source_pill(ui: &mut Ui, source: &crate::gui::app::KeySource) {
    use crate::gui::app::KeySource;
    let (icon_bytes, uri, label, color, bg) = match source {
        KeySource::Windsurf => (icons::ICON_SEARCH, "bytes://src_ws.svg",
            "Windsurf 自动同步", ACCENT_CYAN, ACCENT_CYAN_LIGHT),
        KeySource::Manual => (icons::ICON_PLUS, "bytes://src_manual.svg",
            "手动添加", TEXT_SECONDARY, BG_SUBTLE),
        KeySource::File => (icons::ICON_CODE, "bytes://src_file.svg",
            "文件导入", ACCENT_PURPLE, ACCENT_PURPLE_LIGHT),
    };
    egui::Frame::new()
        .fill(bg)
        .corner_radius(eframe::egui::CornerRadius::same(10))
        .inner_margin(eframe::egui::Margin::symmetric(7, 3))
        .show(ui, |ui| {
            ui.horizontal(|ui| {
                inline_icon(ui, uri, icon_bytes, color, 10.0);
                ui.add_space(3.0);
                ui.label(RichText::new(label).color(color).size(10.5).strong());
            });
        });
}

/// 会员等级徽标 (彩色背景 + SVG 图标 + 中文名)
fn tier_pill(ui: &mut Ui, tier: &membership::TierInfo) {
    egui::Frame::new()
        .fill(tier.bg)
        .corner_radius(eframe::egui::CornerRadius::same(12))
        .inner_margin(eframe::egui::Margin::symmetric(10, 5))
        .show(ui, |ui| {
            ui.horizontal(|ui| {
                inline_icon(ui, tier.icon_uri, tier.icon_bytes, tier.color, 13.0);
                ui.add_space(5.0);
                ui.label(RichText::new(tier.label).color(tier.color).size(11.5).strong());
            });
        });
}

/// 带 SVG 图标的次级按钮 (用于「刷新」等动作)
fn icon_button(
    ui: &mut Ui,
    label: &str,
    icon_uri: &'static str,
    icon_bytes: &'static [u8],
) -> eframe::egui::Response {
    let resp = egui::Frame::new()
        .fill(BG_SUBTLE)
        .corner_radius(eframe::egui::CornerRadius::same(6))
        .stroke(eframe::egui::Stroke::new(1.0, BORDER_LIGHT))
        .inner_margin(eframe::egui::Margin::symmetric(12, 6))
        .show(ui, |ui| {
            ui.horizontal(|ui| {
                inline_icon(ui, icon_uri, icon_bytes, ACCENT, 13.0);
                ui.add_space(4.0);
                ui.label(RichText::new(label).color(TEXT_PRIMARY).size(12.0).strong());
            });
        }).response;
    resp.interact(eframe::egui::Sense::click()).on_hover_cursor(eframe::egui::CursorIcon::PointingHand)
}

/// 把可能为 string 的整数加千分位逗号
fn fmt_int_str(s: Option<&str>) -> String {
    let s = match s { Some(v) => v, None => return "—".to_string() };
    if let Ok(n) = s.parse::<i64>() {
        fmt_int_i64(n)
    } else {
        s.to_string()
    }
}

/// i64 转千分位字符串
fn fmt_int_i64(n: i64) -> String {
    let neg = n < 0;
    let digits: Vec<char> = n.abs().to_string().chars().collect();
    let mut out = String::new();
    for (i, c) in digits.iter().rev().enumerate() {
        if i > 0 && i % 3 == 0 { out.insert(0, ','); }
        out.insert(0, *c);
    }
    if neg { out.insert(0, '-'); }
    out
}

fn short_exec(s: &str) -> String {
    let cleaned = s.replace("CASCADE_COMMANDS_AUTO_EXECUTION_", "");
    match cleaned.as_str() {
        "EAGER" => "积极 (无确认直接执行)".to_string(),
        "PROMPT" => "确认 (每次询问)".to_string(),
        "DISABLED" => "禁用 (手动执行)".to_string(),
        "CONSERVATIVE" => "保守".to_string(),
        _ => cleaned.replace("_", " "),
    }
}

fn short_id(s: &str) -> String {
    if s.starts_with("user-") && s.len() > 18 {
        format!("{}…{}", &s[..14], &s[s.len()-4..])
    } else if s.len() > 24 {
        format!("{}…{}", &s[..12], &s[s.len()-6..])
    } else {
        s.to_string()
    }
}

/// 数据统计卡片
fn stat_card(ui: &mut Ui, label: &str, value: &str, value_color: eframe::egui::Color32) {
    egui::Frame::new()
        .fill(BG_CARD)
        .corner_radius(eframe::egui::CornerRadius::same(CARD_ROUNDING))
        .stroke(eframe::egui::Stroke::new(1.0, BORDER_LIGHT))
        .inner_margin(eframe::egui::Margin::symmetric(14, 12))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            ui.label(RichText::new(label).color(TEXT_LABEL).size(11.0));
            ui.add_space(4.0);
            ui.label(RichText::new(value).color(value_color).size(20.0).strong());
        });
}
