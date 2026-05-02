use eframe::egui::{self, Color32, RichText, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::{AppState, KeyInfo};

const AMBER_LIGHT: Color32 = Color32::from_rgb(254, 243, 199);

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "密钥管理", "添加、删除、验证 Windsurf API Key · 配置自动持久化");

    // ── 添加 Key ──
    card_with_desc(ui, "添加 API Key", "sk-ws-... 格式，支持手动输入或从 .txt 文件批量导入", |ui| {
        ui.horizontal(|ui| {
            let response = ui.add(
                egui::TextEdit::singleline(&mut state.new_key_input)
                    .desired_width(420.0)
                    .hint_text("粘贴 sk-ws-... API Key")
            );
            let add_clicked = primary_button(ui, "添加").clicked()
                || (response.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)));
            if add_clicked {
                let key = state.new_key_input.trim().to_string();
                if !key.is_empty() && !state.keys.iter().any(|k| k.full_key == key) {
                    let preview = make_preview(&key);
                    state.keys.push(KeyInfo {
                        full_key: key.clone(),
                        preview: preview.clone(),
                        healthy: true,
                        calls: 0,
                        errors: 0,
                        credits: None,
                        plan: String::new(),
                        status_json: None,
                        source: crate::gui::app::KeySource::Manual,
                        is_active: false,
                        last_detected_unix: None,
                    });
                    state.new_key_input.clear();
                    state.log(format!("Key 已添加: {}", preview));
                    state.mark_dirty();
                    // 自动校验新 Key
                    state.check_key_async(key);
                }
            }
            if secondary_button(ui, "从文件导入").clicked() {
                if let Some(path) = rfd::FileDialog::new()
                    .add_filter("Text", &["txt"])
                    .pick_file()
                {
                    if let Ok(content) = std::fs::read_to_string(&path) {
                        let mut count = 0;
                        for line in content.lines() {
                            let line = line.trim();
                            if !line.is_empty() && !line.starts_with('#') && !state.keys.iter().any(|k| k.full_key == line) {
                                state.keys.push(KeyInfo {
                                    full_key: line.to_string(),
                                    preview: make_preview(line),
                                    healthy: true,
                                    calls: 0,
                                    errors: 0,
                                    credits: None,
                                    plan: String::new(),
                                    status_json: None,
                                    source: crate::gui::app::KeySource::File,
                                    is_active: false,
                                    last_detected_unix: None,
                                });
                                count += 1;
                            }
                        }
                        state.log(format!("从文件导入 {} 个 Key", count));
                        if count > 0 { state.mark_dirty(); }
                    }
                }
            }
            if secondary_button(ui, "从 Windsurf 编辑器导入").clicked() {
                let _ = state.detect_and_import_keys();
            }
        });
        ui.add_space(6.0);
        info_banner(ui, "「从 Windsurf 编辑器导入」会自动扫描 %APPDATA%\\Windsurf\\ 与 ~\\.codeium\\ 目录，提取已登录账号的 sk-ws-... 密钥");
    });

    ui.add_space(SECTION_SPACING);

    // ── Key 列表 ──
    card(ui, "", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("Key 列表").color(TEXT_PRIMARY).size(15.0).strong());
            ui.add_space(8.0);
            pill(ui, &format!("{}", state.keys.len()), ACCENT_LIGHT, ACCENT);
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if primary_button(ui, "全部验证").clicked() {
                    let count = state.keys.len();
                    let keys: Vec<String> = state.keys.iter().map(|k| k.full_key.clone()).collect();
                    for k in keys {
                        state.check_key_async(k);
                    }
                    state.log(format!("开始验证 {} 个 Key...", count));
                }
            });
        });
        ui.add_space(14.0);

        if state.keys.is_empty() {
            ui.vertical_centered(|ui| {
                ui.add_space(24.0);
                ui.label(RichText::new("暂无 Key").color(TEXT_SECONDARY).size(13.0).strong());
                ui.label(RichText::new("在上方输入或从 .txt 文件导入").color(TEXT_MUTED).size(12.0));
                ui.add_space(24.0);
            });
            return;
        }

        let mut to_remove: Option<usize> = None;
        let mut to_validate: Option<String> = None;
        let mut to_copy: Option<String> = None;
        let mut reveal_idx = state.keys_reveal_idx;

        egui::ScrollArea::vertical().max_height(500.0).auto_shrink([false, false]).show(ui, |ui| {
            for (i, key) in state.keys.iter().enumerate() {
                egui::Frame::new()
                    .fill(BG_WHITE)
                    .corner_radius(eframe::egui::CornerRadius::same(8))
                    .stroke(eframe::egui::Stroke::new(1.0, BORDER_LIGHT))
                    .inner_margin(eframe::egui::Margin::symmetric(14, 12))
                    .show(ui, |ui| {
                        ui.horizontal(|ui| {
                            if key.healthy {
                                pill(ui, "正常", ACCENT_GREEN_LIGHT, ACCENT_GREEN);
                            } else {
                                pill(ui, "异常", ACCENT_RED_LIGHT, ACCENT_RED);
                            }
                            ui.add_space(8.0);

                            // 显示密钥 (展开时显示完整 + 可全选复制)
                            let revealed = reveal_idx == Some(i);
                            if revealed {
                                let mut text = key.full_key.clone();
                                ui.add(egui::TextEdit::singleline(&mut text)
                                    .desired_width(420.0)
                                    .font(egui::TextStyle::Monospace));
                            } else {
                                ui.label(RichText::new(&key.preview).color(TEXT_PRIMARY).monospace().size(13.0));
                            }

                            if let Some(credits) = key.credits {
                                ui.add_space(6.0);
                                pill(ui, &format!("{}cr", credits), AMBER_LIGHT, ACCENT_YELLOW);
                            }
                            if !key.plan.is_empty() {
                                ui.add_space(6.0);
                                pill(ui, &key.plan, ACCENT_PURPLE_LIGHT, ACCENT_PURPLE);
                            }

                            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                if danger_button(ui, "删除").clicked() {
                                    to_remove = Some(i);
                                }
                                ui.add_space(4.0);
                                if secondary_button(ui, "验证").clicked() {
                                    to_validate = Some(key.full_key.clone());
                                }
                                ui.add_space(4.0);
                                if secondary_button(ui, "复制").clicked() {
                                    to_copy = Some(key.full_key.clone());
                                }
                                ui.add_space(4.0);
                                let reveal_label = if revealed { "隐藏" } else { "查看" };
                                if secondary_button(ui, reveal_label).clicked() {
                                    reveal_idx = if revealed { None } else { Some(i) };
                                }
                                ui.add_space(12.0);
                                ui.label(RichText::new(format!("错 {}", key.errors)).color(if key.errors > 0 { ACCENT_RED } else { TEXT_MUTED }).size(11.0));
                                ui.label(RichText::new(format!("调用 {}", key.calls)).color(TEXT_MUTED).size(11.0));
                            });
                        });
                    });
                ui.add_space(8.0);
            }
        });

        // 后处理 (避免在 borrow state.keys 时 mut 借用)
        state.keys_reveal_idx = reveal_idx;
        if let Some(idx) = to_remove {
            let removed = state.keys.remove(idx);
            state.log(format!("已移除 Key: {}", removed.preview));
            state.mark_dirty();
        }
        if let Some(k) = to_validate {
            state.check_key_async(k.clone());
            state.log(format!("验证中: {}", make_preview(&k)));
        }
        if let Some(k) = to_copy {
            ui.ctx().copy_text(k.clone());
            state.log(format!("已复制完整 Key 到剪贴板: {}", make_preview(&k)));
        }
    });
}

fn make_preview(key: &str) -> String {
    if key.len() > 16 {
        format!("{}...{}", &key[..12], &key[key.len()-4..])
    } else {
        key.to_string()
    }
}
