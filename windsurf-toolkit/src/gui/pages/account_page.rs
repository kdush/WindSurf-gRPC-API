use eframe::egui::{self, RichText, Vec2, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "账号工具", "注册 / 登录 / 获取 API Key · SeatManagement + Auth 服务");

    // ── 邮箱登录 ──
    card(ui, "邮箱登录 / 注册", |ui| {
        egui::Grid::new("email_login").num_columns(2).spacing(Vec2::new(12.0, 8.0)).show(ui, |ui| {
            ui.label(RichText::new("邮箱").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.login_email).desired_width(300.0).hint_text("user@example.com"));
            ui.end_row();
            ui.label(RichText::new("密码").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.login_password).desired_width(300.0).password(true).hint_text("密码"));
            ui.end_row();
        });
        ui.add_space(8.0);
        ui.horizontal(|ui| {
            if ui.button("登录").clicked() && !state.login_email.is_empty() {
                state.login_status = "FirebaseAuth.EmailLogin → 登录中...".to_string();
                state.log_messages.push(format!("邮箱登录: {}", state.login_email));
            }
            if ui.button("注册").clicked() && !state.login_email.is_empty() {
                state.login_status = "FirebaseAuth.EmailSignup → 注册中...".to_string();
                state.log_messages.push(format!("邮箱注册: {}", state.login_email));
            }
            if ui.button("发送验证邮件").clicked() && !state.login_email.is_empty() {
                state.login_status = "SendVerificationEmail → 发送验证邮件...".to_string();
            }
            if ui.button("重置密码").clicked() && !state.login_email.is_empty() {
                state.login_status = "SendPasswordReset → 发送重置密码邮件...".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── OAuth 登录 ──
    card(ui, "OAuth 第三方登录", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("GitHub Token").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.login_github_token).desired_width(300.0).hint_text("ghp_..."));
        });
        ui.add_space(8.0);
        ui.horizontal(|ui| {
            if ui.button("GitHub 登录").clicked() && !state.login_github_token.is_empty() {
                state.login_status = "OAuthLogin(github) → 使用 GitHub Token 登录".to_string();
            }
            if ui.button("Google 登录").clicked() {
                state.login_status = "OAuthLogin(google) → 需要 Google ID Token".to_string();
            }
            if ui.button("Microsoft 登录").clicked() {
                state.login_status = "OAuthLogin(microsoft) → 需要 Microsoft ID Token".to_string();
            }
        });
        ui.add_space(4.0);
        ui.label(RichText::new("OAuth 登录通过 Firebase Custom Token 交换 Windsurf API Key").color(TEXT_MUTED).size(11.0));
    });

    ui.add_space(SECTION_SPACING);

    // ── SSO / OIDC ──
    card(ui, "SSO / OIDC 企业登录", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("企业邮箱").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.sso_email).desired_width(250.0).hint_text("user@company.com"));
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("检查 SSO 配置").clicked() && !state.sso_email.is_empty() {
                state.login_status = format!("CheckSSOForEmail({}) → 检查企业 SSO", state.sso_email);
            }
            if ui.button("OIDC 登录").clicked() {
                state.login_status = "OIDCLogin → 通过企业 OIDC 提供商登录".to_string();
            }
            if ui.button("SAML 登录").clicked() {
                state.login_status = "SAMLLogin → 通过 SAML SSO 登录".to_string();
            }
        });
        ui.add_space(4.0);
        ui.label(RichText::new("企业 SSO 支持 SAML 2.0 和 OIDC 协议 (需要团队管理员配置)").color(TEXT_MUTED).size(11.0));
    });

    ui.add_space(SECTION_SPACING);

    // ── 注册获取 Key ──
    card(ui, "注册 Windsurf 获取 API Key", |ui| {
        ui.label(RichText::new("登录 Firebase 后，调用 RegisterUser 注册 Windsurf 账号并获取 API Key").color(TEXT_SECONDARY).size(12.0));
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("注册并获取 API Key").clicked() {
                state.login_status = "RegisterUser → 需要先完成 Firebase 登录".to_string();
            }
            if ui.button("刷新 Token").clicked() {
                state.login_status = "RefreshToken → 刷新 Firebase ID Token".to_string();
            }
            if ui.button("获取 JWT").clicked() {
                state.login_status = "GetAuthToken → 获取 Windsurf JWT Token".to_string();
            }
        });
        if !state.registered_keys.is_empty() {
            ui.add_space(8.0);
            ui.label(RichText::new("已获取的 Key:").color(TEXT_PRIMARY).size(12.0).strong());
            for key in &state.registered_keys {
                ui.label(RichText::new(key).color(ACCENT).size(12.0).monospace());
            }
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── 账号关联 ──
    card(ui, "第三方账号关联", |ui| {
        ui.horizontal(|ui| {
            if ui.button("关联 GitHub").clicked() {
                state.login_status = "ConnectGitHubAccount → 需要 GitHub Token".to_string();
            }
            if ui.button("关联 Netlify").clicked() {
                state.login_status = "ConnectNetlifyAccount → 需要 Netlify Token".to_string();
            }
            if ui.button("查询 GitHub").clicked() {
                state.login_status = "GetGitHubAccountStatus → 查询关联状态".to_string();
            }
            if ui.button("查询 Netlify").clicked() {
                state.login_status = "GetNetlifyAccountStatus → 查询关联状态".to_string();
            }
        });
        ui.add_space(4.0);
        ui.horizontal(|ui| {
            if ui.button("解除 GitHub").clicked() {
                state.login_status = "DisconnectGitHubAccount → 解除关联".to_string();
            }
            if ui.button("解除 Netlify").clicked() {
                state.login_status = "DisconnectNetlifyAccount → 解除关联".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 认证流程参考 ──
    card(ui, "认证流程参考", |ui| {
        let steps = [
            "1. Firebase Auth: Email/GitHub/Google/Microsoft → Firebase ID Token",
            "2. RegisterUser: Firebase ID Token → Windsurf API Key (sk-ws-...)",
            "3. API 调用: 所有 gRPC 请求携带 API Key 作为 Authorization Header",
            "4. JWT Token: Auth 服务提供短期 JWT Token 用于特定操作",
            "5. SSO/OIDC: 企业用户通过公司 IDP 获取 Token → 自动关联 Windsurf 账号",
        ];
        for step in &steps {
            ui.label(RichText::new(*step).color(TEXT_SECONDARY).size(12.0));
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── 状态 ──
    if !state.login_status.is_empty() {
        card(ui, "操作结果", |ui| {
            ui.label(RichText::new(&state.login_status).color(TEXT_SECONDARY).size(12.0).monospace());
        });
    }
}

