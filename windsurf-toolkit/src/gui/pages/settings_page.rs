use eframe::egui::{self, RichText, Vec2, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "设置", "应用程序与 Windsurf 服务器配置");

    // ── 代理设置 ──
    card_with_desc(ui, "代理服务设置", "修改后自动保存到 %APPDATA%/windsurf-toolkit/config.json", |ui| {
        let mut changed = false;
        egui::Grid::new("settings_proxy").num_columns(2).spacing(Vec2::new(12.0, 10.0)).show(ui, |ui| {
            ui.label(RichText::new("监听端口").color(TEXT_LABEL).size(12.0));
            changed |= ui.add(egui::DragValue::new(&mut state.proxy_port).range(1..=65535)).changed();
            ui.end_row();

            ui.label(RichText::new("监听地址").color(TEXT_LABEL).size(12.0));
            changed |= ui.add(egui::TextEdit::singleline(&mut state.proxy_host).desired_width(200.0)).changed();
            ui.end_row();

            ui.label(RichText::new("目标服务器").color(TEXT_LABEL).size(12.0));
            changed |= ui.add(egui::TextEdit::singleline(&mut state.server_url).desired_width(400.0)).changed();
            ui.end_row();

            ui.label(RichText::new("Auth Token").color(TEXT_LABEL).size(12.0));
            changed |= ui.add(egui::TextEdit::singleline(&mut state.auth_token).desired_width(300.0).password(true)).changed();
            ui.end_row();
        });
        if changed { state.mark_dirty(); }
    });

    ui.add_space(SECTION_SPACING);

    // ── 健康检查 ──
    card(ui, "健康检查与监控", |ui| {
        egui::Grid::new("settings_health").num_columns(2).spacing(Vec2::new(12.0, 10.0)).show(ui, |ui| {
            ui.label(RichText::new("冷却时间").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::DragValue::new(&mut state.cooldown_secs).range(1..=3600).suffix("s"));
            ui.end_row();

            ui.label(RichText::new("最大连续错误").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::DragValue::new(&mut state.max_errors).range(1..=100));
            ui.end_row();

            ui.label(RichText::new("监控间隔").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::DragValue::new(&mut state.monitor_interval).range(10..=3600).suffix("s"));
            ui.end_row();
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── LS 配置 ──
    card(ui, "Language Server 配置", |ui| {
        egui::Grid::new("settings_ls").num_columns(2).spacing(Vec2::new(12.0, 10.0)).show(ui, |ui| {
            ui.label(RichText::new("LS 端口").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::DragValue::new(&mut state.ls_port).range(0..=65535));
            ui.end_row();

            ui.label(RichText::new("CSRF Token").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.ls_csrf_token).desired_width(300.0).password(true).hint_text("自动读取"));
            ui.end_row();

            ui.label(RichText::new("注入间隔").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::DragValue::new(&mut state.inject_check_interval).range(5..=300).suffix("s"));
            ui.end_row();
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 数据管理 ──
    card(ui, "数据管理", |ui| {
        ui.horizontal(|ui| {
            if ui.button("导出 Key 列表").clicked() {
                if let Some(path) = rfd::FileDialog::new()
                    .add_filter("Text", &["txt"])
                    .set_file_name("windsurf_keys.txt")
                    .save_file()
                {
                    let content: String = state.keys.iter().map(|k| k.full_key.clone()).collect::<Vec<_>>().join("\n");
                    if std::fs::write(&path, content).is_ok() {
                        state.log_messages.push(format!("已导出 {} 个 Key 到 {:?}", state.keys.len(), path));
                    }
                }
            }
            if ui.button("清空所有 Key").clicked() {
                state.keys.clear();
                state.log_messages.push("已清空所有 Key".to_string());
            }
            if ui.button("清空日志").clicked() {
                state.log_messages.clear();
                state.inject_log.clear();
            }
            if ui.button("重置所有设置").clicked() {
                state.proxy_host = "0.0.0.0".to_string();
                state.proxy_port = 8080;
                state.server_url = "https://server.self-serve.windsurf.com".to_string();
                state.cooldown_secs = 60;
                state.max_errors = 10;
                state.monitor_interval = 300;
                state.log_messages.push("设置已重置为默认值".to_string());
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── Internal Secret ──
    card(ui, "Internal Secret (管理员)", |ui| {
        ui.label(RichText::new("用于团队管理页面的 Internal 操作").color(TEXT_MUTED).size(11.0));
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            ui.label(RichText::new("Secret").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.internal_secret).desired_width(400.0).password(true).hint_text("输入 Internal Secret"));
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 关于 ──
    card(ui, "关于", |ui| {
        ui.label(RichText::new("Windsurf Toolkit v1.0.0").color(TEXT_PRIMARY).size(14.0).strong());
        ui.add_space(4.0);
        ui.label(RichText::new("Windsurf IDE 全功能工具箱").color(TEXT_SECONDARY).size(13.0));
        ui.label(RichText::new("覆盖 13 个 gRPC 服务 · 540+ RPC 方法").color(TEXT_SECONDARY).size(12.0));
        ui.add_space(4.0);
        ui.label(RichText::new("Rust + egui · 单文件分发 · 零依赖 · 白色简约主题").color(TEXT_MUTED).size(12.0));
    });
}

