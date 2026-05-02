use eframe::egui::{self, RichText, Vec2, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "团队管理", "Windsurf Teams 全功能管理 · SeatManagement 服务");

    // ── 团队信息查询 ──
    card(ui, "团队信息查询", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("团队 ID").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.team_id_input).desired_width(200.0).hint_text("可选，留空用当前"));
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("获取团队信息").clicked() {
                state.team_info_result = "GetTeamInfo → 返回: 团队名称、成员列表、管理员、Plan".to_string();
                state.log_messages.push("查询团队信息".to_string());
            }
            if ui.button("团队功能").clicked() {
                state.team_info_result = "GetTeamsFeatures → 返回: 已开通功能列表".to_string();
            }
            if ui.button("成员列表").clicked() {
                state.team_members_result = "ListTeamMembers → 返回: 成员邮箱、角色、状态".to_string();
            }
            if ui.button("团队 API Secrets").clicked() {
                state.team_info_result = "GetTeamAPISecrets → 返回: Team Secret Key 列表".to_string();
            }
            if ui.button("使用统计").clicked() {
                state.team_billing_result = "GetTeamUsageDetails → 返回: 按成员/模型使用明细".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 创建团队 ──
    card(ui, "创建 / 管理团队", |ui| {
        egui::Grid::new("team_create").num_columns(2).spacing(Vec2::new(12.0, 6.0)).show(ui, |ui| {
            ui.label(RichText::new("团队名称").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.team_name_input).desired_width(250.0).hint_text("输入团队名称"));
            ui.end_row();
            ui.label(RichText::new("管理邮箱").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.team_email_input).desired_width(250.0).hint_text("admin@company.com"));
            ui.end_row();
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("创建团队").clicked() && !state.team_name_input.is_empty() {
                state.team_info_result = format!("CreateMultiTenantTeam({}) → 需要 API Key", state.team_name_input);
                state.log_messages.push(format!("创建团队: {}", state.team_name_input));
            }
            if ui.button("更新名称").clicked() {
                state.team_info_result = "UpdateTeamName → 需要管理员权限".to_string();
            }
            if ui.button("删除团队").clicked() {
                state.team_info_result = "DeleteTeam → 危险操作！需要确认".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 预审批 / 邀请 ──
    card(ui, "预审批与邀请 (Preapproval)", |ui| {
        egui::Grid::new("team_invite").num_columns(2).spacing(Vec2::new(12.0, 6.0)).show(ui, |ui| {
            ui.label(RichText::new("邮箱").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.team_email_input).desired_width(250.0).hint_text("invitee@company.com"));
            ui.end_row();
            ui.label(RichText::new("角色").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.team_role_input).desired_width(250.0).hint_text("member / admin"));
            ui.end_row();
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("添加预审批").clicked() && !state.team_email_input.is_empty() {
                state.team_info_result = format!("AddPreapproval({}) → 需要 API Key", state.team_email_input);
            }
            if ui.button("批量添加").clicked() {
                state.team_info_result = "AddPreapprovals → 批量预审批邮箱列表".to_string();
            }
            if ui.button("查询预审批").clicked() {
                state.team_info_result = "GetPreapprovals → 返回: 待审批邮箱列表".to_string();
            }
            if ui.button("接受邀请").clicked() {
                state.team_info_result = "AcceptPreapproval → 接受团队邀请".to_string();
            }
            if ui.button("拒绝邀请").clicked() {
                state.team_info_result = "RejectPreapproval → 拒绝团队邀请".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 域名与 SSO ──
    card(ui, "团队域名 / SSO 配置", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("域名").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.team_domain_input).desired_width(200.0).hint_text("company.com"));
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("添加域名").clicked() && !state.team_domain_input.is_empty() {
                state.team_info_result = format!("AddTeamDomain({}) → 添加自动加入域名", state.team_domain_input);
            }
            if ui.button("查询域名").clicked() {
                state.team_info_result = "GetTeamDomains → 返回: 已配置域名列表".to_string();
            }
            if ui.button("验证域名").clicked() {
                state.team_info_result = "VerifyTeamDomain → 验证域名所有权".to_string();
            }
            if ui.button("SSO 配置").clicked() {
                state.team_info_result = "GetSSOConfig → 返回: SAML/OIDC SSO 配置".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 计费 / 订阅 ──
    card(ui, "团队计费与订阅", |ui| {
        ui.horizontal(|ui| {
            if ui.button("查询计费详情").clicked() {
                state.team_billing_result = "GetBillingDetails → 返回: 当前 Plan、到期时间、费用".to_string();
            }
            if ui.button("更新 Plan").clicked() {
                state.team_billing_result = "UpdatePlanDetails → 升级/降级团队 Plan".to_string();
            }
            if ui.button("查询额度").clicked() {
                state.team_billing_result = "GetFlexCredits → 返回: 剩余弹性额度".to_string();
            }
            if ui.button("查询发票").clicked() {
                state.team_billing_result = "GetInvoices → 返回: 发票列表".to_string();
            }
            if ui.button("付款方式").clicked() {
                state.team_billing_result = "GetPaymentMethods → 返回: 绑定的支付方式".to_string();
            }
        });
        if !state.team_billing_result.is_empty() {
            ui.add_space(4.0);
            ui.label(RichText::new(&state.team_billing_result).color(TEXT_SECONDARY).size(12.0).monospace());
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── Internal 管理操作 ──
    card(ui, "Internal 管理 (需要 Secret)", |ui| {
        ui.label(RichText::new("以下操作需要 Internal Secret，仅供管理员使用").color(ACCENT_RED).size(11.0));
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            ui.label(RichText::new("Secret").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.internal_secret).desired_width(300.0).password(true).hint_text("Internal Secret"));
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("升级 Plan (内部)").clicked() {
                state.team_info_result = "UpdatePlanDetailsInternal → 需要 Secret + Email".to_string();
            }
            if ui.button("添加额度").clicked() {
                state.team_info_result = "AddExtraFlexCreditsInternal → 需要 Secret".to_string();
            }
            if ui.button("重置配额").clicked() {
                state.team_info_result = "ResetQuotaUsageInternal → 需要 Secret".to_string();
            }
            if ui.button("设置特征 Flag").clicked() {
                state.team_info_result = "SetFeatureFlagsInternal → 需要 Secret".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 成员结果 ──
    if !state.team_members_result.is_empty() {
        card(ui, "成员查询结果", |ui| {
            ui.label(RichText::new(&state.team_members_result).color(TEXT_SECONDARY).size(12.0).monospace());
        });
        ui.add_space(SECTION_SPACING);
    }

    // ── 操作结果 ──
    if !state.team_info_result.is_empty() {
        card(ui, "操作结果", |ui| {
            ui.label(RichText::new(&state.team_info_result).color(TEXT_SECONDARY).size(12.0).monospace());
        });
    }
}

