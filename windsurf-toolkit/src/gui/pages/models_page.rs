use eframe::egui::{self, CornerRadius, RichText, Stroke, Ui, Vec2, Color32, FontId};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "模型列表",
        &format!("当前模型 · 共 {} 款 · 添加密钥后可从 Windsurf API 拉取真实清单", state.models.len()));

    // ── 顶部刷新工具栏 ──
    card(ui, "", |ui| {
        ui.horizontal(|ui| {
            let has_key = state.keys.iter().any(|k| k.healthy);
            if has_key {
                pill(ui, &format!("{} 个有效密钥", state.keys.iter().filter(|k| k.healthy).count()),
                    ACCENT_GREEN_LIGHT, ACCENT_GREEN);
            } else {
                pill(ui, "未配置有效密钥", BG_SUBTLE, TEXT_MUTED);
            }
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                ui.add_enabled_ui(has_key, |ui| {
                    if primary_button(ui, "从 API 刷新").clicked() {
                        state.refresh_models_async();
                    }
                });
            });
        });
    });

    ui.add_space(SECTION_SPACING);

    let provider_labels: [(&str, &str, Color32); 6] = [
        ("anthropic", "Anthropic", Color32::from_rgb(217, 119, 87)),
        ("openai",    "OpenAI",    Color32::from_rgb(16, 163, 127)),
        ("google",    "Google",    Color32::from_rgb(66, 133, 244)),
        ("xai",       "xAI",       Color32::from_rgb(99, 102, 241)),
        ("deepseek",  "DeepSeek",  Color32::from_rgb(6, 182, 212)),
        ("?",         "其他",      Color32::from_rgb(148, 163, 184)),
    ];

    let mut shown_providers = std::collections::HashSet::new();

    for (provider_id, provider_name, provider_color) in &provider_labels {
        let provider_models: Vec<_> = state.models.iter()
            .filter(|m| m.provider == *provider_id || (provider_id == &"?" && !["anthropic","openai","google","xai","deepseek"].contains(&m.provider.as_str())))
            .collect();
        if provider_models.is_empty() {
            continue;
        }
        shown_providers.insert(*provider_id);

        card(ui, "", |ui| {
            ui.horizontal(|ui| {
                egui::Frame::new()
                    .fill(provider_color.linear_multiply(0.15))
                    .corner_radius(CornerRadius::same(6))
                    .inner_margin(egui::Margin::same(6))
                    .show(ui, |ui| {
                        ui.label(RichText::new("◆").color(*provider_color).size(11.0));
                    });
                ui.add_space(2.0);
                ui.label(RichText::new(*provider_name).color(TEXT_PRIMARY).size(15.0).strong());
                pill(ui, &format!("{} 款", provider_models.len()), provider_color.linear_multiply(0.15), *provider_color);
            });
            ui.add_space(12.0);

            // 智能换行: 用 main_wrap=true 的 left_to_right 布局
            ui.allocate_ui_with_layout(
                Vec2::new(ui.available_width(), 0.0),
                egui::Layout::left_to_right(egui::Align::TOP).with_main_wrap(true),
                |ui| {
                    ui.spacing_mut().item_spacing = Vec2::new(8.0, 8.0);
                    for model in &provider_models {
                        let galley = ui.painter().layout_no_wrap(
                            model.name.clone(),
                            FontId::monospace(12.0),
                            TEXT_PRIMARY,
                        );
                        let w = galley.size().x + 26.0;
                        ui.allocate_ui(Vec2::new(w, 32.0), |ui| {
                            egui::Frame::new()
                                .fill(BG_SUBTLE)
                                .corner_radius(CornerRadius::same(8))
                                .stroke(Stroke::new(1.0, BORDER_LIGHT))
                                .inner_margin(egui::Margin::symmetric(12, 7))
                                .show(ui, |ui| {
                                    ui.label(RichText::new(&model.name).color(TEXT_PRIMARY).size(12.0).strong().monospace());
                                });
                        });
                    }
                },
            );
        });
        ui.add_space(SECTION_SPACING);
    }

    if state.models.is_empty() {
        card(ui, "", |ui| {
            ui.vertical_centered(|ui| {
                ui.add_space(40.0);
                ui.label(RichText::new("暂无模型").color(TEXT_SECONDARY).size(14.0).strong());
                ui.label(RichText::new("添加 API Key 后点击「从 API 刷新」拉取模型列表").color(TEXT_MUTED).size(12.0));
                ui.add_space(40.0);
            });
        });
    }
}
