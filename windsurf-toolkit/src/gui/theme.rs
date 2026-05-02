use eframe::egui::{self, Color32, CornerRadius, FontData, FontDefinitions, FontFamily, Stroke, Vec2, Margin, Shadow, FontId};

// ═══════════════════════════════════════
//  现代化调色板 — Indigo + Slate
// ═══════════════════════════════════════

// 背景层次
pub const BG_WHITE: Color32 = Color32::from_rgb(255, 255, 255);
pub const BG_PANEL: Color32 = Color32::from_rgb(250, 251, 252);   // 主内容区 — 极浅灰
pub const BG_CARD: Color32 = Color32::from_rgb(255, 255, 255);    // 卡片
pub const BG_SIDEBAR: Color32 = Color32::from_rgb(252, 252, 253); // 侧栏 — 几乎白
pub const BG_HOVER: Color32 = Color32::from_rgb(244, 245, 247);   // 悬停
pub const BG_INPUT: Color32 = Color32::from_rgb(249, 250, 251);   // 输入框
pub const BG_SUBTLE: Color32 = Color32::from_rgb(246, 247, 249);  // 次级背景

// 文本层次
pub const TEXT_PRIMARY: Color32 = Color32::from_rgb(15, 23, 42);      // slate-900
pub const TEXT_SECONDARY: Color32 = Color32::from_rgb(71, 85, 105);   // slate-600 — 更深 更易读
pub const TEXT_MUTED: Color32 = Color32::from_rgb(148, 163, 184);     // slate-400
pub const TEXT_LABEL: Color32 = Color32::from_rgb(100, 116, 139);     // slate-500

// 主色 — Indigo (比 Blue 更现代)
pub const ACCENT: Color32 = Color32::from_rgb(99, 102, 241);          // indigo-500
pub const ACCENT_HOVER: Color32 = Color32::from_rgb(79, 70, 229);     // indigo-600
pub const ACCENT_LIGHT: Color32 = Color32::from_rgb(238, 242, 255);   // indigo-50
pub const ACCENT_SOFT: Color32 = Color32::from_rgb(224, 231, 255);    // indigo-100

// 状态色 — 柔和现代
pub const ACCENT_GREEN: Color32 = Color32::from_rgb(16, 185, 129);    // emerald-500
pub const ACCENT_GREEN_LIGHT: Color32 = Color32::from_rgb(209, 250, 229); // emerald-100
pub const ACCENT_RED: Color32 = Color32::from_rgb(239, 68, 68);       // red-500
pub const ACCENT_RED_LIGHT: Color32 = Color32::from_rgb(254, 226, 226); // red-100
pub const ACCENT_YELLOW: Color32 = Color32::from_rgb(245, 158, 11);   // amber-500
pub const ACCENT_YELLOW_LIGHT: Color32 = Color32::from_rgb(254, 243, 199); // amber-100
pub const ACCENT_PURPLE: Color32 = Color32::from_rgb(139, 92, 246);   // violet-500
pub const ACCENT_PURPLE_LIGHT: Color32 = Color32::from_rgb(237, 233, 254);
pub const ACCENT_ORANGE: Color32 = Color32::from_rgb(249, 115, 22);
pub const ACCENT_CYAN: Color32 = Color32::from_rgb(6, 182, 212);      // cyan-500
pub const ACCENT_CYAN_LIGHT: Color32 = Color32::from_rgb(207, 250, 254); // cyan-100

// 边框 — 非常浅
pub const BORDER: Color32 = Color32::from_rgb(229, 231, 235);         // gray-200
pub const BORDER_LIGHT: Color32 = Color32::from_rgb(243, 244, 246);   // gray-100
pub const BORDER_FOCUS: Color32 = Color32::from_rgb(165, 180, 252);   // indigo-300
pub const DIVIDER: Color32 = Color32::from_rgb(229, 231, 235);

// ═══════════════════════════════════════
//  尺寸常量
// ═══════════════════════════════════════
pub const SIDEBAR_WIDTH: f32 = 224.0;
pub const CARD_ROUNDING: u8 = 10;
pub const CARD_PADDING: i8 = 18;
pub const BTN_ROUNDING: u8 = 6;
pub const ITEM_SPACING: f32 = 14.0;
pub const SECTION_SPACING: f32 = 12.0;
pub const ICON_SIZE: Vec2 = Vec2::new(16.0, 16.0);
pub const ICON_SIZE_SMALL: Vec2 = Vec2::new(14.0, 14.0);
pub const LOGO_SIZE: Vec2 = Vec2::new(26.0, 26.0);

/// 加载中文字体
pub fn setup_fonts(ctx: &egui::Context) {
    let mut fonts = FontDefinitions::default();

    let font_paths = [
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\msyh.ttf",
        "C:\\Windows\\Fonts\\simhei.ttf",
        "C:\\Windows\\Fonts\\simsun.ttc",
    ];

    for path in &font_paths {
        if let Ok(data) = std::fs::read(path) {
            fonts.font_data.insert(
                "chinese".to_owned(),
                std::sync::Arc::new(FontData::from_owned(data)),
            );
            fonts.families
                .get_mut(&FontFamily::Proportional)
                .unwrap()
                .insert(0, "chinese".to_owned());
            fonts.families
                .get_mut(&FontFamily::Monospace)
                .unwrap()
                .push("chinese".to_owned());
            break;
        }
    }

    ctx.set_fonts(fonts);
}

/// 配置现代化全局样式
pub fn apply_theme(ctx: &egui::Context) {
    let mut style = (*ctx.style()).clone();

    // ── 基础 ──
    style.visuals.dark_mode = false;
    style.visuals.override_text_color = Some(TEXT_PRIMARY);
    style.visuals.window_fill = BG_WHITE;
    style.visuals.panel_fill = BG_PANEL;
    style.visuals.faint_bg_color = BG_HOVER;
    style.visuals.extreme_bg_color = BG_INPUT;

    // ── 文本字号层次 ──
    use egui::{TextStyle, FontFamily::Proportional, FontFamily::Monospace};
    style.text_styles.insert(TextStyle::Heading, FontId::new(20.0, Proportional));
    style.text_styles.insert(TextStyle::Body, FontId::new(13.0, Proportional));
    style.text_styles.insert(TextStyle::Monospace, FontId::new(12.0, Monospace));
    style.text_styles.insert(TextStyle::Button, FontId::new(13.0, Proportional));
    style.text_styles.insert(TextStyle::Small, FontId::new(11.0, Proportional));

    // ── 控件 · noninteractive (labels) ──
    style.visuals.widgets.noninteractive.bg_fill = BG_CARD;
    style.visuals.widgets.noninteractive.weak_bg_fill = BG_CARD;
    style.visuals.widgets.noninteractive.fg_stroke = Stroke::new(1.0, TEXT_PRIMARY);
    style.visuals.widgets.noninteractive.bg_stroke = Stroke::new(1.0, BORDER_LIGHT);
    style.visuals.widgets.noninteractive.corner_radius = CornerRadius::same(BTN_ROUNDING);

    // ── 控件 · inactive (按钮/输入框默认态) ──
    style.visuals.widgets.inactive.bg_fill = BG_WHITE;
    style.visuals.widgets.inactive.weak_bg_fill = BG_WHITE;
    style.visuals.widgets.inactive.fg_stroke = Stroke::new(1.0, TEXT_PRIMARY);
    style.visuals.widgets.inactive.bg_stroke = Stroke::new(1.0, BORDER);
    style.visuals.widgets.inactive.corner_radius = CornerRadius::same(BTN_ROUNDING);
    style.visuals.widgets.inactive.expansion = 0.0;

    // ── 控件 · hovered ──
    style.visuals.widgets.hovered.bg_fill = BG_HOVER;
    style.visuals.widgets.hovered.weak_bg_fill = BG_HOVER;
    style.visuals.widgets.hovered.fg_stroke = Stroke::new(1.0, TEXT_PRIMARY);
    style.visuals.widgets.hovered.bg_stroke = Stroke::new(1.0, ACCENT);
    style.visuals.widgets.hovered.corner_radius = CornerRadius::same(BTN_ROUNDING);
    style.visuals.widgets.hovered.expansion = 0.0;

    // ── 控件 · active (点击中) ──
    style.visuals.widgets.active.bg_fill = ACCENT_LIGHT;
    style.visuals.widgets.active.weak_bg_fill = ACCENT_LIGHT;
    style.visuals.widgets.active.fg_stroke = Stroke::new(1.0, ACCENT_HOVER);
    style.visuals.widgets.active.bg_stroke = Stroke::new(1.0, ACCENT);
    style.visuals.widgets.active.corner_radius = CornerRadius::same(BTN_ROUNDING);
    style.visuals.widgets.active.expansion = 0.0;

    // ── 控件 · open (下拉打开) ──
    style.visuals.widgets.open.bg_fill = BG_HOVER;
    style.visuals.widgets.open.weak_bg_fill = BG_HOVER;
    style.visuals.widgets.open.fg_stroke = Stroke::new(1.0, TEXT_PRIMARY);
    style.visuals.widgets.open.bg_stroke = Stroke::new(1.0, BORDER_FOCUS);
    style.visuals.widgets.open.corner_radius = CornerRadius::same(BTN_ROUNDING);

    // ── 选中 ──
    style.visuals.selection.bg_fill = ACCENT_SOFT;
    style.visuals.selection.stroke = Stroke::new(1.0, ACCENT);

    // ── 间距 ──
    style.spacing.item_spacing = Vec2::new(8.0, 8.0);
    style.spacing.button_padding = Vec2::new(12.0, 6.0);
    style.spacing.interact_size = Vec2::new(40.0, 30.0);
    style.spacing.window_margin = Margin::same(0);
    style.spacing.menu_margin = Margin::same(8);
    style.spacing.indent = 18.0;

    // ── 分隔线 ──
    style.visuals.window_corner_radius = CornerRadius::same(12);
    style.visuals.window_stroke = Stroke::new(1.0, BORDER_LIGHT);
    style.visuals.window_shadow = Shadow {
        offset: [0, 4],
        blur: 16,
        spread: 0,
        color: Color32::from_black_alpha(16),
    };
    style.visuals.popup_shadow = Shadow {
        offset: [0, 2],
        blur: 10,
        spread: 0,
        color: Color32::from_black_alpha(12),
    };

    ctx.set_style(style);
}
