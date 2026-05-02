use eframe::egui::{self, RichText, Vec2, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "代理服务", "OpenAI 兼容反向代理 · SSE 流式 · 多 Key 轮换");

    // ── 状态栏 ──
    card(ui, "", |ui| {
        ui.horizontal(|ui| {
            if state.proxy_running {
                pill(ui, "● 运行中", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
                ui.add_space(12.0);
                ui.label(RichText::new(format!("http://{}:{}", state.proxy_host, state.proxy_port)).color(ACCENT).size(14.0).monospace().strong());
            } else {
                pill(ui, "○ 已停止", BG_SUBTLE, TEXT_MUTED);
                ui.add_space(12.0);
                ui.label(RichText::new(format!("将监听 http://{}:{}", state.proxy_host, state.proxy_port)).color(TEXT_MUTED).size(13.0));
            }
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if state.proxy_running {
                    if danger_button(ui, "停止服务").clicked() {
                        state.stop_proxy_real();
                    }
                } else if primary_button(ui, "启动服务").clicked() {
                    state.start_proxy_real();
                }
            });
        });
        if !state.proxy_running && state.keys.is_empty() {
            ui.add_space(8.0);
            warning_banner(ui, "需要先在「密钥管理」中添加至少一个 API Key");
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── 服务器配置 ──
    card_with_desc(ui, "服务器配置", "监听地址、端口与后端 Windsurf 服务器", |ui| {
        egui::Grid::new("proxy_config").num_columns(2).spacing(Vec2::new(16.0, 10.0)).show(ui, |ui| {
            ui.label(RichText::new("监听地址").color(TEXT_LABEL).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.proxy_host).desired_width(220.0));
            ui.end_row();

            ui.label(RichText::new("监听端口").color(TEXT_LABEL).size(12.0));
            ui.add(egui::DragValue::new(&mut state.proxy_port).range(1..=65535));
            ui.end_row();

            ui.label(RichText::new("Auth Token").color(TEXT_LABEL).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.auth_token).desired_width(320.0).password(true).hint_text("可选"));
            ui.end_row();

            ui.label(RichText::new("Windsurf 服务器").color(TEXT_LABEL).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.server_url).desired_width(420.0));
            ui.end_row();

            ui.label(RichText::new("冷却秒数").color(TEXT_LABEL).size(12.0));
            ui.add(egui::DragValue::new(&mut state.cooldown_secs).range(1..=3600).suffix(" 秒"));
            ui.end_row();

            ui.label(RichText::new("最大连续错误").color(TEXT_LABEL).size(12.0));
            ui.add(egui::DragValue::new(&mut state.max_errors).range(1..=100));
            ui.end_row();
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── API 端点 ──
    card_with_desc(ui, "API 端点", "代理服务提供的 OpenAI 兼容 HTTP 接口", |ui| {
        let endpoints = [
            ("GET",  "/health",               "健康检查",          ACCENT_GREEN),
            ("GET",  "/v1/models",            "模型列表",          ACCENT_GREEN),
            ("POST", "/v1/chat/completions",  "聊天补全 (SSE 流式)", ACCENT),
            ("GET",  "/v1/status",            "Key 池状态",        ACCENT_GREEN),
            ("GET",  "/dashboard",            "Web 管理面板",      ACCENT_GREEN),
        ];

        egui::Grid::new("endpoints").num_columns(3).spacing(Vec2::new(16.0, 10.0)).show(ui, |ui| {
            for (method, path, desc, color) in &endpoints {
                pill(ui, method, color.linear_multiply(0.15), *color);
                ui.label(RichText::new(*path).color(TEXT_PRIMARY).size(12.5).monospace().strong());
                ui.label(RichText::new(*desc).color(TEXT_SECONDARY).size(12.0));
                ui.end_row();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 日志 ──
    card(ui, "", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("运行日志").color(TEXT_PRIMARY).size(14.5).strong());
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if ui.small_button("清空日志").clicked() {
                    state.log_messages.clear();
                }
            });
        });
        ui.add_space(10.0);

        sub_card(ui, |ui| {
            egui::ScrollArea::vertical().max_height(180.0).stick_to_bottom(true).auto_shrink([false, false]).show(ui, |ui| {
                if state.log_messages.is_empty() {
                    ui.label(RichText::new("等待日志...").color(TEXT_MUTED).size(12.0));
                }
                for msg in &state.log_messages {
                    ui.label(RichText::new(msg).color(TEXT_SECONDARY).size(11.5).monospace());
                }
            });
        });
    });
}
