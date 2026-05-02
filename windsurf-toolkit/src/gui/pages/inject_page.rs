use eframe::egui::{self, RichText, Vec2, Ui, CornerRadius, Stroke};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;
use crate::gui::icons;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "Pro 注入", "向本地 Windsurf Language Server 注入 Pro 实验以解锁 Cascade 高级特性");

    // ── LS 连接状态 (大卡片) ──
    card_with_desc(ui, "Language Server 连接", "本机运行的 Windsurf LS 进程信息 · 自动探测端口与 CSRF Token", |ui| {
        ui.horizontal(|ui| {
            // 连接状态圆点
            let (label_text, color) = if state.ls_connected {
                ("● 已连接", ACCENT_GREEN)
            } else {
                ("○ 未连接", TEXT_MUTED)
            };
            pill(ui, label_text, if state.ls_connected { ACCENT_GREEN_LIGHT } else { BG_SUBTLE }, color);
            ui.add_space(12.0);
            ui.label(RichText::new("端口").color(TEXT_LABEL).size(12.0));
            ui.add(egui::DragValue::new(&mut state.ls_port).range(0..=65535));
            ui.add_space(8.0);
            ui.label(RichText::new("CSRF").color(TEXT_LABEL).size(12.0));
            let masked = if state.ls_csrf_token.is_empty() { "(未读取)".to_string() } else { format!("✓ 已读取 ({}位)", state.ls_csrf_token.len()) };
            ui.label(RichText::new(&masked).color(if state.ls_csrf_token.is_empty() { TEXT_MUTED } else { ACCENT_GREEN }).size(12.0).monospace());
        });
        ui.add_space(10.0);
        ui.horizontal_wrapped(|ui| {
            ui.spacing_mut().item_spacing = Vec2::new(8.0, 8.0);
            if icon_text_button(ui, icons::ICON_SEARCH, "btn_detect", "自动检测 LS", true).clicked() {
                state.discover_ls_async();
                state.show_result_modal = true;
                state.result_modal_pending = true;
                state.result_modal_label = "自动检测 LS".to_string();
                state.result_modal_show_raw = false;
                state.api_result_label.clear();
                state.api_result_text.clear();
            }
            if icon_text_button(ui, icons::ICON_HEART, "btn_heartbeat", "发送心跳", false).clicked() {
                state.ls_heartbeat_async();
                open_modal(state, "LS 心跳");
            }
            if icon_text_button(ui, icons::ICON_X, "btn_disconnect", "断开", false).clicked() {
                state.ls_connected = false;
                state.ls_port = 0;
                state.ls_csrf_token.clear();
                state.ls_status = "已手动断开".to_string();
            }
        });
        if !state.ls_status.is_empty() {
            ui.add_space(6.0);
            ui.label(RichText::new(&state.ls_status).color(TEXT_LABEL).size(11.5));
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── 守护进程 ──
    card_with_desc(ui, "后台守护进程", "后台周期性检测 LS 状态并重新注入 · LS 重启后自动恢复", |ui| {
        ui.horizontal(|ui| {
            if state.inject_running {
                pill(ui, "● 守护运行中", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
            } else {
                pill(ui, "○ 未启动", BG_SUBTLE, TEXT_MUTED);
            }
            ui.add_space(16.0);
            ui.label(RichText::new("检查间隔").color(TEXT_LABEL).size(12.0));
            ui.add(egui::DragValue::new(&mut state.inject_check_interval).range(5..=300).suffix(" 秒"));
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if state.inject_running {
                    if danger_button(ui, "停止守护").clicked() {
                        state.stop_inject_real();
                        state.inject_log.push("守护进程已停止".to_string());
                    }
                } else if primary_button(ui, "启动守护").clicked() {
                    if state.start_inject_real() {
                        state.inject_log.push("守护进程已启动 · 等待 LS".to_string());
                    }
                }
            });
        });
        ui.add_space(6.0);
        ui.label(RichText::new(format!("状态: {}", state.inject_status)).color(TEXT_LABEL).size(12.0));
        if !state.inject_running && state.keys.is_empty() {
            ui.add_space(6.0);
            warning_banner(ui, "需要先在「密钥管理」中添加有效的 API Key");
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── 手动操作 (大卡片) ──
    card_with_desc(ui, "手动操作", "一次性调用 LS gRPC · 点击卡片弹出中文解读", |ui| {
        let ls_ready = state.ls_port > 0;
        if !ls_ready {
            info_banner(ui, "请先点击上方「自动检测 LS」连接本地 Language Server");
            ui.add_space(8.0);
        }

        let actions: [(&[u8], &str, &str, &str, &str, eframe::egui::Color32); 4] = [
            (icons::ICON_ZAP, "act_inject", "一键注入 Pro", "启用 6 个 Cascade 高级实验 · 禁用额度限制", "inject", ACCENT_PURPLE),
            (icons::ICON_SEARCH, "act_query", "查询当前实验", "读取 LS 当前已生效的 BaseExperiments", "query", ACCENT),
            (icons::ICON_BROOM, "act_clear", "清除所有实验", "发送空列表 · 恢复 LS 默认状态", "clear", ACCENT_ORANGE),
            (icons::ICON_EYE, "act_status", "查看 LS 状态", "GetDebugDiagnostics · LS 启动日志、版本、运行参数", "status", ACCENT_CYAN),
        ];
        let chunks: Vec<_> = actions.chunks(2).collect();
        for chunk in chunks {
            ui.columns(2, |cols| {
                for (i, (icon_bytes, icon_uri, title, desc, action, accent)) in chunk.iter().enumerate() {
                    if action_card(&mut cols[i], icon_bytes, icon_uri, title, desc, *accent, ls_ready) {
                        match *action {
                            "inject" => {
                                state.inject_pro_async();
                                state.inject_log.push("SetBaseExperiments · 注入 6 个 Cascade 实验".to_string());
                                open_modal(state, title);
                            }
                            "query" => {
                                state.query_experiments_async();
                                open_modal(state, title);
                            }
                            "clear" => {
                                state.clear_experiments_async();
                                state.inject_log.push("SetBaseExperiments · 发送空列表清除注入".to_string());
                                open_modal(state, title);
                            }
                            "status" => {
                                state.call_ls_async(title.to_string(), "GetDebugDiagnostics".to_string(), serde_json::json!({}));
                                open_modal(state, title);
                            }
                            _ => {}
                        }
                    }
                }
            });
            ui.add_space(8.0);
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── 注入的实验 Flag 详情 ──
    card_with_desc(ui, "注入的实验 Flag 明细", "「一键注入 Pro」会修改以下实验状态 · 使用数字 ExperimentKey ID", |ui| {
        let flags: [(&str, i32, bool, &str); 7] = [
            ("CASCADE_ENFORCE_QUOTA",                204, false, "禁用额度检查 · Cascade 调用不计入月度配额"),
            ("CASCADE_PLAN_BASED_CONFIG_OVERRIDE",   266, true,  "启用 Plan 配置覆盖 · 可使用高级 Plan 默认配置"),
            ("CASCADE_ENABLE_MCP_TOOLS",             245, true,  "启用 MCP 外部工具 (Model Context Protocol)"),
            ("CASCADE_WEB_APP_DEPLOYMENTS_ENABLED",  300, true,  "启用 Web App 一键部署功能"),
            ("CASCADE_ENABLE_PROXY_WEB_SERVER",      290, true,  "启用代理 Web 服务器 · 本地预览"),
            ("CASCADE_ENABLE_AUTOMATED_MEMORIES",    224, true,  "启用自动记忆 · Cascade 会从对话中提取项目信息"),
            ("CASCADE_WINDSURF_BROWSER_TOOLS_ENABLED", 328, true, "启用浏览器工具 · Cascade 可控制本地浏览器"),
        ];
        egui::Grid::new("flags_grid").num_columns(4).spacing(Vec2::new(14.0, 8.0)).show(ui, |ui| {
            ui.label(RichText::new("状态").color(TEXT_LABEL).size(11.0).strong());
            ui.label(RichText::new("ID").color(TEXT_LABEL).size(11.0).strong());
            ui.label(RichText::new("名称").color(TEXT_LABEL).size(11.0).strong());
            ui.label(RichText::new("作用").color(TEXT_LABEL).size(11.0).strong());
            ui.end_row();
            for (name, id, enable, desc) in &flags {
                if *enable {
                    pill(ui, "启用", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
                } else {
                    pill(ui, "禁用", ACCENT_RED_LIGHT, ACCENT_RED);
                }
                ui.label(RichText::new(format!("{}", id)).color(ACCENT_PURPLE).size(12.0).monospace().strong());
                ui.label(RichText::new(*name).color(ACCENT).size(11.5).monospace());
                ui.label(RichText::new(*desc).color(TEXT_SECONDARY).size(11.5));
                ui.end_row();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 注入日志 ──
    if !state.inject_log.is_empty() {
        card_with_desc(ui, "操作日志", "最近的注入操作记录", |ui| {
            egui::ScrollArea::vertical().max_height(140.0).stick_to_bottom(true).auto_shrink([false, true]).show(ui, |ui| {
                for msg in &state.inject_log {
                    ui.label(RichText::new(msg).color(TEXT_PRIMARY).size(11.5).monospace());
                }
            });
            ui.add_space(6.0);
            if secondary_button(ui, "清空日志").clicked() {
                state.inject_log.clear();
            }
        });
    }

    // ── 弹窗 ──
    if state.show_result_modal {
        super::user_status_page::render_result_modal_pub(ui.ctx(), state);
    }
}

/// 大号动作卡片 — SVG 图标 + 彩色徽标 + 中文标题 + 中文描述
fn action_card(
    ui: &mut Ui,
    icon_bytes: &'static [u8],
    icon_uri: &'static str,
    title: &str,
    desc: &str,
    accent: eframe::egui::Color32,
    enabled: bool,
) -> bool {
    let resp = ui.add_enabled_ui(enabled, |ui| {
        let bg = if enabled { BG_CARD } else { BG_INPUT };
        let muted_accent = if enabled { accent } else { TEXT_MUTED };
        egui::Frame::new()
            .fill(bg)
            .corner_radius(CornerRadius::same(10))
            .stroke(Stroke::new(1.0, BORDER_LIGHT))
            .inner_margin(egui::Margin::symmetric(14, 12))
            .show(ui, |ui| {
                ui.set_min_width(ui.available_width() - 4.0);
                ui.set_min_height(72.0);
                ui.horizontal(|ui| {
                    // 彩色图标徽标
                    egui::Frame::new()
                        .fill(muted_accent.gamma_multiply(0.12))
                        .corner_radius(CornerRadius::same(8))
                        .inner_margin(egui::Margin::same(8))
                        .show(ui, |ui| {
                            ui.add(egui::Image::from_bytes(icon_uri, icon_bytes)
                                .fit_to_exact_size(Vec2::new(20.0, 20.0))
                                .tint(muted_accent));
                        });
                    ui.add_space(10.0);
                    ui.vertical(|ui| {
                        ui.label(RichText::new(title)
                            .color(if enabled { TEXT_PRIMARY } else { TEXT_MUTED })
                            .size(14.0).strong());
                        ui.add_space(3.0);
                        ui.label(RichText::new(desc)
                            .color(if enabled { TEXT_LABEL } else { TEXT_MUTED })
                            .size(11.5));
                    });
                });
            }).response
    }).inner;
    let clicked = resp.interact(eframe::egui::Sense::click()).clicked();
    if resp.hovered() && enabled {
        ui.ctx().set_cursor_icon(eframe::egui::CursorIcon::PointingHand);
    }
    clicked && enabled
}

/// 带 SVG 图标前缀的按钮 (主按钮风格 = primary, 否则次级风格)
fn icon_text_button(
    ui: &mut Ui,
    icon_bytes: &'static [u8],
    uri_key: &'static str,
    label: &str,
    primary: bool,
) -> eframe::egui::Response {
    let (bg, fg, border) = if primary {
        (ACCENT, eframe::egui::Color32::WHITE, ACCENT)
    } else {
        (BG_SUBTLE, TEXT_PRIMARY, BORDER_LIGHT)
    };
    let resp = egui::Frame::new()
        .fill(bg)
        .corner_radius(CornerRadius::same(7))
        .stroke(Stroke::new(1.0, border))
        .inner_margin(egui::Margin::symmetric(14, 7))
        .show(ui, |ui| {
            ui.horizontal(|ui| {
                let uri = match uri_key {
                    "btn_detect" => "bytes://btn_detect.svg",
                    "btn_heartbeat" => "bytes://btn_heartbeat.svg",
                    "btn_disconnect" => "bytes://btn_disconnect.svg",
                    _ => "bytes://btn_default.svg",
                };
                ui.add(egui::Image::from_bytes(uri, icon_bytes)
                    .fit_to_exact_size(Vec2::new(13.0, 13.0))
                    .tint(fg));
                ui.add_space(5.0);
                ui.label(RichText::new(label).color(fg).size(13.0).strong());
            });
        }).response;
    resp.interact(eframe::egui::Sense::click())
        .on_hover_cursor(eframe::egui::CursorIcon::PointingHand)
}

/// 打开结果弹窗
fn open_modal(state: &mut AppState, label: &str) {
    state.show_result_modal = true;
    state.result_modal_pending = true;
    state.result_modal_label = label.to_string();
    state.result_modal_show_raw = false;
    state.api_result_label.clear();
    state.api_result_text.clear();
}

