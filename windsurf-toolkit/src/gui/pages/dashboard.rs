use eframe::egui::{self, CornerRadius, RichText, Vec2, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::icons;
use crate::gui::app::AppState;

pub fn render(ui: &mut Ui, state: &AppState) {
    page_header(ui, "总览", "Windsurf Toolkit 系统概览 · 实时状态与协议服务");

    // ── 核心指标 · 4 列 (用 ui.columns 避免溢出) ──
    let healthy = state.keys.iter().filter(|k| k.healthy).count();
    let health_pct = if state.keys.is_empty() { "无数据".to_string() }
        else { format!("{:.0}% 可用", healthy as f32 / state.keys.len() as f32 * 100.0) };

    ui.columns(4, |cols| {
        hero_stat_card(&mut cols[0], "bytes://stat_key.svg", icons::ICON_KEY,
            "密钥总数", &format!("{}", state.keys.len()),
            &format!("{} 个有效", healthy), ACCENT);
        hero_stat_card(&mut cols[1], "bytes://stat_heart.svg", icons::ICON_HEART,
            "健康密钥", &format!("{}", healthy),
            &health_pct, ACCENT_GREEN);
        hero_stat_card(&mut cols[2], "bytes://stat_chart.svg", icons::ICON_CHART,
            "总请求", &format!("{}", state.total_requests),
            if state.proxy_running { "代理运行中" } else { "代理未启动" }, ACCENT_PURPLE);
        hero_stat_card(&mut cols[3], "bytes://stat_layers.svg", icons::ICON_MODELS,
            "可用模型", &format!("{}", state.models.len()),
            "Cascade 路由就绪", ACCENT_CYAN);
    });

    ui.add_space(SECTION_SPACING);

    // ── 服务状态 · 3 列 ──
    ui.columns(3, |cols| {
        service_card(&mut cols[0], "bytes://svc_proxy.svg", icons::ICON_BOLT,
            "代理服务", state.proxy_running,
            if state.proxy_running { "运行中" } else { "已停止" },
            &if state.proxy_running { format!("http://{}:{}", state.proxy_host, state.proxy_port) } else { "在「代理服务」页面启动".to_string() },
            ACCENT);
        service_card(&mut cols[1], "bytes://svc_ls.svg", icons::ICON_TERMINAL,
            "Language Server", state.ls_connected,
            if state.ls_connected { "已连接" } else { "未连接" },
            &if state.ls_port > 0 { format!("端口 {}", state.ls_port) } else { "请打开 Windsurf IDE".to_string() },
            ACCENT_CYAN);
        service_card(&mut cols[2], "bytes://svc_inject.svg", icons::ICON_ZAP,
            "Pro 注入", state.inject_running,
            if state.inject_running { "守护中" } else { "未启动" },
            &state.inject_status,
            ACCENT_PURPLE);
    });

    ui.add_space(SECTION_SPACING);

    // ── 2 列布局: 密钥 + 活动 ──
    ui.columns(2, |cols| {
        // 左: 密钥池
        card_with_desc(&mut cols[0], "密钥池状态", "已添加的 Windsurf API Key", |ui| {
            if state.keys.is_empty() {
                empty_state(ui, "暂无密钥", "请在「密钥管理」页面添加");
            } else {
                for key in state.keys.iter().take(6) {
                    ui.horizontal(|ui| {
                        if key.healthy {
                            pill(ui, "正常", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
                        } else {
                            pill(ui, "异常", ACCENT_RED_LIGHT, ACCENT_RED);
                        }
                        ui.label(RichText::new(&key.preview).color(TEXT_PRIMARY).size(12.0).monospace());
                        ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                            ui.label(RichText::new(format!("调用 {}", key.calls)).color(TEXT_MUTED).size(11.0));
                        });
                    });
                    ui.add_space(6.0);
                }
                if state.keys.len() > 6 {
                    ui.add_space(4.0);
                    ui.label(RichText::new(format!("… 还有 {} 个密钥", state.keys.len() - 6))
                        .color(TEXT_MUTED).size(11.0));
                }
            }
        });

        // 右: 活动日志
        card_with_desc(&mut cols[1], "活动日志", "最近的系统事件", |ui| {
            if state.log_messages.is_empty() {
                empty_state(ui, "暂无日志", "启动代理或使用功能后显示");
            } else {
                let start = if state.log_messages.len() > 8 { state.log_messages.len() - 8 } else { 0 };
                for msg in state.log_messages[start..].iter().rev() {
                    ui.horizontal(|ui| {
                        ui.label(RichText::new("●").color(ACCENT).size(7.0));
                        ui.label(RichText::new(msg).color(TEXT_SECONDARY).size(12.0));
                    });
                    ui.add_space(4.0);
                }
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 模型概览 (可滚动 + 刷新按钮) ──
    card(ui, "", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new(format!("可用模型 · {}", state.models.len()))
                .color(TEXT_PRIMARY).size(15.0).strong());
            ui.add_space(6.0);
            pill(ui, &format!("{}", state.models.len()), ACCENT_LIGHT, ACCENT);
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                let has_key = state.keys.iter().any(|k| k.healthy);
                ui.add_enabled_ui(has_key, |ui| {
                    if secondary_button(ui, "从 API 刷新").clicked() {
                        state.refresh_models_async();
                    }
                });
            });
        });
        ui.add_space(8.0);
        ui.label(RichText::new(if state.keys.iter().any(|k| k.healthy) {
            "Cascade / ApiServer 提供的模型 · 可点击「从 API 刷新」获取最新列表"
        } else {
            "本地静态列表 · 添加有效密钥后可拉取真实模型清单"
        }).color(TEXT_LABEL).size(12.0));
        ui.add_space(12.0);

        // 用 wrap_layout 强制每个 pill 不被字符级换行
        let row_w = ui.available_width();
        let pill_h = 26.0;
        let gap = 6.0;
        ui.allocate_ui_with_layout(
            Vec2::new(row_w, 0.0),
            egui::Layout::left_to_right(egui::Align::TOP).with_main_wrap(true),
            |ui| {
                ui.spacing_mut().item_spacing = Vec2::new(gap, gap);
                for model in &state.models {
                    let text = RichText::new(&model.name).color(TEXT_PRIMARY).size(11.5).monospace();
                    let label = egui::Label::new(text);
                    let galley = ui.painter().layout_no_wrap(
                        model.name.clone(),
                        egui::FontId::monospace(11.5),
                        TEXT_PRIMARY,
                    );
                    let pill_w = galley.size().x + 22.0;
                    ui.allocate_ui(Vec2::new(pill_w, pill_h), |ui| {
                        egui::Frame::new()
                            .fill(BG_SUBTLE)
                            .corner_radius(CornerRadius::same(6))
                            .inner_margin(egui::Margin::symmetric(10, 5))
                            .show(ui, |ui| {
                                ui.add(label);
                            });
                    });
                }
            },
        );
    });

    ui.add_space(SECTION_SPACING);

    // ── 协议服务 · 3列网格 (用 ui.columns 嵌套) ──
    card_with_desc(ui, "协议服务概览", "13 gRPC 服务 · 540+ RPC 方法", |ui| {
        let services: [(&str, &str, &str, eframe::egui::Color32); 11] = [
            ("SeatManagement",    "145", "用户/Plan/团队/SSO/计费",    ACCENT),
            ("ApiServer",         "170", "模型/聊天/容量/OIDC",        ACCENT_PURPLE),
            ("LanguageServer",    "172", "LS/Pro 注入/Cascade/MCP",    ACCENT_CYAN),
            ("ExtensionServer",   "49",  "扩展/终端/KV/文件/搜索",     ACCENT_GREEN),
            ("CascadePlugins",    "2",   "MCP 插件/OAuth",             ACCENT_ORANGE),
            ("Analytics",         "2",   "用户/产品分析",              ACCENT_YELLOW),
            ("BrowserPreview",    "3",   "浏览器预览",                 ACCENT),
            ("FileSystemProvider","3",   "远程文件系统",               ACCENT_PURPLE),
            ("Auth",              "1",   "JWT Token",                  ACCENT_CYAN),
            ("Dev",               "1",   "内部调试",                   ACCENT_GREEN),
            ("ChatClient",        "1",   "Cascade 聊天流",             ACCENT_ORANGE),
        ];

        let mut i = 0;
        while i < services.len() {
            let chunk_end = (i + 3).min(services.len());
            ui.columns(3, |cols| {
                for (col_idx, j) in (i..chunk_end).enumerate() {
                    let (name, count, desc, color) = services[j];
                    egui::Frame::new()
                        .fill(BG_SUBTLE)
                        .corner_radius(CornerRadius::same(8))
                        .inner_margin(egui::Margin::same(12))
                        .show(&mut cols[col_idx], |ui| {
                            ui.set_min_height(60.0);
                            ui.horizontal(|ui| {
                                ui.label(RichText::new("●").color(color).size(10.0));
                                ui.label(RichText::new(name).color(TEXT_PRIMARY).size(12.5).strong().monospace());
                                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                    pill(ui, count, color.gamma_multiply(0.12), color);
                                });
                            });
                            ui.add_space(4.0);
                            ui.label(RichText::new(desc).color(TEXT_LABEL).size(11.5));
                        });
                }
            });
            ui.add_space(10.0);
            i += 3;
        }
    });
}

fn empty_state(ui: &mut Ui, title: &str, hint: &str) {
    ui.vertical_centered(|ui| {
        ui.add_space(20.0);
        ui.label(RichText::new(title).color(TEXT_SECONDARY).size(13.0).strong());
        ui.label(RichText::new(hint).color(TEXT_MUTED).size(12.0));
        ui.add_space(20.0);
    });
}
