use eframe::egui::{self, Color32, CornerRadius, RichText, Stroke, Ui, Vec2, Margin, Response};
use crate::gui::theme::*;

// ═══════════════════════════════════════
//  现代化可复用组件
// ═══════════════════════════════════════

/// 页面头部 — 大标题 + 副标题
pub fn page_header(ui: &mut Ui, title: &str, subtitle: &str) {
    ui.label(RichText::new(title).color(TEXT_PRIMARY).size(28.0).strong());
    ui.add_space(4.0);
    ui.label(RichText::new(subtitle).color(TEXT_LABEL).size(13.5));
    ui.add_space(24.0);
}

/// 现代卡片 — 白底 · 浅边框 · 柔和阴影感
pub fn card(ui: &mut Ui, title: &str, content: impl FnOnce(&mut Ui)) {
    card_with_desc(ui, title, "", content);
}

/// 卡片 + 描述
pub fn card_with_desc(ui: &mut Ui, title: &str, desc: &str, content: impl FnOnce(&mut Ui)) {
    egui::Frame::new()
        .fill(BG_CARD)
        .corner_radius(CornerRadius::same(CARD_ROUNDING))
        .stroke(Stroke::new(1.0, BORDER_LIGHT))
        .inner_margin(Margin::same(CARD_PADDING))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            if !title.is_empty() {
                ui.label(RichText::new(title).color(TEXT_PRIMARY).size(15.0).strong());
            }
            if !desc.is_empty() {
                ui.add_space(2.0);
                ui.label(RichText::new(desc).color(TEXT_LABEL).size(12.0));
            }
            if !title.is_empty() || !desc.is_empty() {
                ui.add_space(14.0);
            }
            content(ui);
        });
}

/// 无边框的子卡片 (用于嵌套) — 浅灰底
pub fn sub_card(ui: &mut Ui, content: impl FnOnce(&mut Ui)) {
    egui::Frame::new()
        .fill(BG_SUBTLE)
        .corner_radius(CornerRadius::same(8))
        .inner_margin(Margin::same(14))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            content(ui);
        });
}

/// 图标圆角方块 — 使用真实 SVG
pub fn icon_badge_svg(ui: &mut Ui, uri: &'static str, icon_bytes: &'static [u8], accent: Color32) {
    egui::Frame::new()
        .fill(accent.gamma_multiply(0.12))
        .corner_radius(CornerRadius::same(8))
        .inner_margin(Margin::same(8))
        .show(ui, |ui| {
            ui.add(egui::Image::from_bytes(uri, icon_bytes)
                .fit_to_exact_size(Vec2::new(18.0, 18.0))
                .tint(accent));
        });
}

/// 内联小图标 (用于和文字并排展示, 替代 emoji)
/// size: 14.0 默认
pub fn inline_icon(
    ui: &mut Ui,
    uri: &'static str,
    icon_bytes: &'static [u8],
    color: Color32,
    size: f32,
) {
    ui.add(egui::Image::from_bytes(uri, icon_bytes)
        .fit_to_exact_size(Vec2::new(size, size))
        .tint(color));
}

/// 大号指标卡片 — SVG 图标 + 大数字 + 标签 + 说明
pub fn hero_stat_card(
    ui: &mut Ui,
    uri: &'static str,
    icon_bytes: &'static [u8],
    label: &str,
    value: &str,
    hint: &str,
    accent: Color32,
) {
    egui::Frame::new()
        .fill(BG_CARD)
        .corner_radius(CornerRadius::same(CARD_ROUNDING))
        .stroke(Stroke::new(1.0, BORDER_LIGHT))
        .inner_margin(Margin::same(16))
        .show(ui, |ui| {
            ui.set_min_height(96.0);

            // 顶部: 图标 + 标签
            ui.horizontal(|ui| {
                icon_badge_svg(ui, uri, icon_bytes, accent);
                ui.add_space(4.0);
                ui.vertical(|ui| {
                    ui.add_space(6.0);
                    ui.label(RichText::new(label).color(TEXT_LABEL).size(12.5));
                });
            });

            ui.add_space(8.0);
            ui.label(RichText::new(value).color(TEXT_PRIMARY).size(28.0).strong());

            if !hint.is_empty() {
                ui.add_space(2.0);
                ui.label(RichText::new(hint).color(TEXT_MUTED).size(11.0));
            }
        });
}

/// 服务状态卡 — SVG 图标 + 标题 + 状态 + 详情
pub fn service_card(
    ui: &mut Ui,
    uri: &'static str,
    icon_bytes: &'static [u8],
    title: &str,
    active: bool,
    status_text: &str,
    detail: &str,
    accent: Color32,
) {
    let border_color = if active { accent.gamma_multiply(0.45) } else { BORDER_LIGHT };

    egui::Frame::new()
        .fill(BG_CARD)
        .corner_radius(CornerRadius::same(CARD_ROUNDING))
        .stroke(Stroke::new(1.0, border_color))
        .inner_margin(Margin::same(16))
        .show(ui, |ui| {
            ui.set_min_height(96.0);

            ui.horizontal(|ui| {
                icon_badge_svg(ui, uri, icon_bytes, accent);
                ui.add_space(4.0);
                ui.vertical(|ui| {
                    ui.add_space(6.0);
                    ui.label(RichText::new(title).color(TEXT_PRIMARY).size(13.5).strong());
                });
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    if active {
                        pill(ui, status_text, ACCENT_GREEN_LIGHT, ACCENT_GREEN);
                    } else {
                        pill(ui, status_text, BG_SUBTLE, TEXT_MUTED);
                    }
                });
            });

            ui.add_space(12.0);
            ui.label(RichText::new(detail).color(TEXT_LABEL).size(12.0).monospace());
        });
}

/// 主按钮 — 填色 Indigo 按钮
pub fn primary_button(ui: &mut Ui, text: &str) -> Response {
    let btn = egui::Button::new(RichText::new(text).color(Color32::WHITE).size(13.0).strong())
        .fill(ACCENT)
        .stroke(Stroke::new(1.0, ACCENT))
        .corner_radius(CornerRadius::same(BTN_ROUNDING))
        .min_size(Vec2::new(88.0, 34.0));
    ui.add(btn)
}

/// 危险按钮 — 红色填充浅底
pub fn danger_button(ui: &mut Ui, text: &str) -> Response {
    let btn = egui::Button::new(RichText::new(text).color(ACCENT_RED).size(13.0).strong())
        .fill(ACCENT_RED_LIGHT)
        .stroke(Stroke::new(0.0, Color32::TRANSPARENT))
        .corner_radius(CornerRadius::same(BTN_ROUNDING))
        .min_size(Vec2::new(72.0, 30.0));
    ui.add(btn)
}

/// 次级按钮 — 浅灰底 (与默认白底按钮区分)
pub fn secondary_button(ui: &mut Ui, text: &str) -> Response {
    let btn = egui::Button::new(RichText::new(text).color(TEXT_PRIMARY).size(13.0))
        .fill(BG_SUBTLE)
        .stroke(Stroke::new(0.0, Color32::TRANSPARENT))
        .corner_radius(CornerRadius::same(BTN_ROUNDING))
        .min_size(Vec2::new(72.0, 30.0));
    ui.add(btn)
}

/// 文字按钮 — 无底无边，仅文字有悬停色
pub fn ghost_button(ui: &mut Ui, text: &str) -> Response {
    let btn = egui::Button::new(RichText::new(text).color(TEXT_LABEL).size(12.5))
        .fill(Color32::TRANSPARENT)
        .stroke(Stroke::new(0.0, Color32::TRANSPARENT))
        .corner_radius(CornerRadius::same(BTN_ROUNDING))
        .min_size(Vec2::new(0.0, 28.0));
    ui.add(btn)
}

/// Pill 标签 (已开启/已停止/错误等)
pub fn pill(ui: &mut Ui, text: &str, bg: Color32, fg: Color32) {
    egui::Frame::new()
        .fill(bg)
        .corner_radius(CornerRadius::same(100))
        .inner_margin(Margin::symmetric(10, 4))
        .show(ui, |ui| {
            ui.label(RichText::new(text).color(fg).size(11.0).strong());
        });
}

/// 标签 (Key-Value 水平对)
pub fn kv(ui: &mut Ui, key: &str, value: &str) {
    ui.horizontal(|ui| {
        ui.label(RichText::new(key).color(TEXT_LABEL).size(12.0));
        ui.add_space(4.0);
        ui.label(RichText::new(value).color(TEXT_PRIMARY).size(12.0).monospace());
    });
}

/// 分区头 (在卡片中分组)
pub fn section_title(ui: &mut Ui, text: &str) {
    ui.add_space(4.0);
    ui.label(RichText::new(text).color(TEXT_LABEL).size(11.0).strong());
    ui.add_space(4.0);
}

/// 信息提示条 (蓝色背景)
pub fn info_banner(ui: &mut Ui, text: &str) {
    egui::Frame::new()
        .fill(ACCENT_LIGHT)
        .corner_radius(CornerRadius::same(8))
        .inner_margin(Margin::symmetric(12, 8))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            ui.horizontal(|ui| {
                ui.label(RichText::new("ⓘ").color(ACCENT).size(13.0).strong());
                ui.label(RichText::new(text).color(ACCENT_HOVER).size(12.0));
            });
        });
}

/// API 调用结果卡片 — 带状态标记 + JSON 等宽显示
pub fn result_card(ui: &mut Ui, label: &str, ok: bool, body: &str) {
    let (tint, border) = if ok {
        (ACCENT_GREEN_LIGHT, ACCENT_GREEN.gamma_multiply(0.4))
    } else {
        (ACCENT_RED_LIGHT, ACCENT_RED.gamma_multiply(0.4))
    };
    egui::Frame::new()
        .fill(BG_CARD)
        .corner_radius(CornerRadius::same(CARD_ROUNDING))
        .stroke(Stroke::new(1.0, border))
        .inner_margin(Margin::same(CARD_PADDING))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);

            // 头部带状态
            ui.horizontal(|ui| {
                egui::Frame::new()
                    .fill(tint)
                    .corner_radius(CornerRadius::same(6))
                    .inner_margin(Margin::same(6))
                    .show(ui, |ui| {
                        ui.label(RichText::new(if ok { "✓" } else { "✗" })
                            .color(if ok { ACCENT_GREEN } else { ACCENT_RED })
                            .size(14.0).strong());
                    });
                ui.add_space(4.0);
                ui.label(RichText::new(label).color(TEXT_PRIMARY).size(14.0).strong());
            });
            ui.add_space(10.0);

            // 正文 — 代码块风格
            egui::Frame::new()
                .fill(BG_SUBTLE)
                .corner_radius(CornerRadius::same(6))
                .inner_margin(Margin::same(12))
                .show(ui, |ui| {
                    ui.set_min_width(ui.available_width() - 4.0);
                    egui::ScrollArea::vertical().max_height(280.0).auto_shrink([false, true]).show(ui, |ui| {
                        ui.label(RichText::new(body).color(TEXT_PRIMARY).size(11.5).monospace());
                    });
                });
        });
}

/// 警告提示条 (琥珀色)
pub fn warning_banner(ui: &mut Ui, text: &str) {
    egui::Frame::new()
        .fill(Color32::from_rgb(255, 251, 235))
        .corner_radius(CornerRadius::same(8))
        .inner_margin(Margin::symmetric(12, 8))
        .show(ui, |ui| {
            ui.set_min_width(ui.available_width() - 4.0);
            ui.horizontal(|ui| {
                ui.label(RichText::new("⚠").color(ACCENT_YELLOW).size(13.0).strong());
                ui.label(RichText::new(text).color(Color32::from_rgb(146, 64, 14)).size(12.0));
            });
        });
}
