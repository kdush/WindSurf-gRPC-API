use eframe::egui::{self, RichText, Vec2, Ui};
use crate::gui::theme::*;
use crate::gui::widgets::*;
use crate::gui::app::AppState;

pub fn render(ui: &mut Ui, state: &mut AppState) {
    page_header(ui, "MCP 插件", "Cascade MCP 插件管理 · LanguageServer + CascadePlugins 服务");

    // ── Cascade 插件 (云端) ──
    card(ui, "Cascade 插件 (云端 API)", |ui| {
        ui.horizontal(|ui| {
            if ui.button("获取可用插件").clicked() {
                state.mcp_result = "GetAvailableCascadePlugins → 返回: 已安装的 Cascade 插件列表\n\n包括: 插件名称、描述、版本、状态".to_string();
                state.log_messages.push("查询 MCP 插件列表".to_string());
            }
            if ui.button("获取 MCP OAuth 凭据").clicked() {
                state.mcp_result = "GetMCPClientInfos → 返回: MCP 客户端 ID 和 Secret\n\n用途: 第三方工具接入 MCP 协议".to_string();
                state.log_messages.push("查询 MCP OAuth 凭据".to_string());
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── LS MCP 服务器管理 ──
    card(ui, "MCP 服务器管理 (Language Server)", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("Server ID").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.mcp_server_id).desired_width(250.0).hint_text("MCP 服务器 ID"));
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("获取服务器状态").clicked() {
                state.mcp_server_result = "GetMCPServerStates → 返回: 所有 MCP 服务器连接状态\n\n包括: 服务器名称、URL、连接状态、工具列表".to_string();
                state.log_messages.push("查询 MCP 服务器状态".to_string());
            }
            if ui.button("初始化服务器").clicked() {
                state.mcp_server_result = "InitializeMCPServer → 初始化指定 MCP 服务器连接".to_string();
            }
            if ui.button("停止服务器").clicked() {
                state.mcp_server_result = "StopMCPServer → 停止指定 MCP 服务器".to_string();
            }
            if ui.button("重启服务器").clicked() {
                state.mcp_server_result = "RestartMCPServer → 重启指定 MCP 服务器连接".to_string();
            }
        });
        if !state.mcp_server_result.is_empty() {
            ui.add_space(4.0);
            ui.label(RichText::new(&state.mcp_server_result).color(TEXT_SECONDARY).size(12.0).monospace());
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── MCP 工具管理 ──
    card(ui, "MCP 工具切换", |ui| {
        ui.horizontal(|ui| {
            ui.label(RichText::new("工具名称").color(TEXT_SECONDARY).size(12.0));
            ui.add(egui::TextEdit::singleline(&mut state.mcp_tool_name).desired_width(250.0).hint_text("tool_name"));
        });
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("启用工具").clicked() && !state.mcp_tool_name.is_empty() {
                state.mcp_plugin_result = format!("ToggleMCPTool({}, enabled=true) → 启用", state.mcp_tool_name);
            }
            if ui.button("禁用工具").clicked() && !state.mcp_tool_name.is_empty() {
                state.mcp_plugin_result = format!("ToggleMCPTool({}, enabled=false) → 禁用", state.mcp_tool_name);
            }
            if ui.button("列出所有工具").clicked() {
                state.mcp_plugin_result = "GetMCPServerStates → 列出所有可用 MCP 工具列表".to_string();
            }
        });
        if !state.mcp_plugin_result.is_empty() {
            ui.add_space(4.0);
            ui.label(RichText::new(&state.mcp_plugin_result).color(TEXT_SECONDARY).size(12.0).monospace());
        }
    });

    ui.add_space(SECTION_SPACING);

    // ── MCP 注册表 ──
    card(ui, "MCP 注册表 (Registry)", |ui| {
        ui.horizontal(|ui| {
            if ui.button("获取注册表服务器").clicked() {
                state.mcp_result = "GetMCPRegistryServers → 返回: 注册表中所有 MCP 服务器\n\n包括: 服务器元数据、安装状态".to_string();
            }
            if ui.button("安装注册表插件").clicked() && !state.mcp_server_id.is_empty() {
                state.mcp_result = format!("InstallMCPRegistryServer({}) → 从注册表安装", state.mcp_server_id);
            }
            if ui.button("卸载注册表插件").clicked() && !state.mcp_server_id.is_empty() {
                state.mcp_result = format!("UninstallMCPRegistryServer({}) → 从注册表卸载", state.mcp_server_id);
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── MCP 服务器配置 ──
    card(ui, "MCP 服务器配置 (JSON)", |ui| {
        ui.add(
            egui::TextEdit::multiline(&mut state.mcp_config_json)
                .desired_width(ui.available_width() - 8.0)
                .desired_rows(6)
                .hint_text("{\n  \"mcpServers\": {\n    \"server_name\": {\n      \"command\": \"npx\",\n      \"args\": [\"-y\", \"@modelcontextprotocol/server\"]\n    }\n  }\n}")
                .font(egui::TextStyle::Monospace)
        );
        ui.add_space(6.0);
        ui.horizontal(|ui| {
            if ui.button("保存 MCP 配置").clicked() {
                state.mcp_result = "SaveMCPServerConfig → 已保存 MCP 服务器配置".to_string();
                state.log_messages.push("保存 MCP 配置".to_string());
            }
            if ui.button("重载配置").clicked() {
                state.mcp_result = "ReloadMCPConfig → 重新加载 MCP 配置文件".to_string();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 协议方法参考 ──
    card(ui, "MCP 协议方法参考", |ui| {
        let methods = [
            ("GetAvailableCascadePlugins", "CascadePlugins", "列出所有可用的 Cascade 插件"),
            ("GetMCPClientInfos",          "CascadePlugins", "获取 MCP OAuth 客户端凭据"),
            ("GetMCPServerStates",         "LanguageServer", "获取 MCP 服务器连接状态 + 工具列表"),
            ("InitializeMCPServer",        "LanguageServer", "初始化 MCP 服务器连接"),
            ("StopMCPServer",              "LanguageServer", "停止 MCP 服务器"),
            ("RestartMCPServer",           "LanguageServer", "重启 MCP 服务器"),
            ("ToggleMCPTool",              "LanguageServer", "启用/禁用 MCP 工具"),
            ("GetMCPRegistryServers",      "LanguageServer", "获取注册表中的 MCP 服务器列表"),
            ("InstallMCPRegistryServer",   "LanguageServer", "从注册表安装 MCP 服务器"),
            ("UninstallMCPRegistryServer", "LanguageServer", "卸载注册表 MCP 服务器"),
            ("SaveMCPServerConfig",        "LanguageServer", "保存 MCP 服务器配置"),
        ];
        egui::Grid::new("mcp_methods").num_columns(3).spacing(Vec2::new(12.0, 4.0)).show(ui, |ui| {
            ui.label(RichText::new("方法").color(TEXT_MUTED).size(11.0).strong());
            ui.label(RichText::new("服务").color(TEXT_MUTED).size(11.0).strong());
            ui.label(RichText::new("说明").color(TEXT_MUTED).size(11.0).strong());
            ui.end_row();
            for (method, svc, desc) in &methods {
                ui.label(RichText::new(*method).color(ACCENT).size(11.0).monospace());
                ui.label(RichText::new(*svc).color(ACCENT_PURPLE).size(11.0));
                ui.label(RichText::new(*desc).color(TEXT_SECONDARY).size(11.0));
                ui.end_row();
            }
        });
    });

    ui.add_space(SECTION_SPACING);

    // ── 查询结果 ──
    if !state.mcp_result.is_empty() {
        card(ui, "查询结果", |ui| {
            ui.label(RichText::new(&state.mcp_result).color(TEXT_SECONDARY).size(12.0).monospace());
        });
    }
}

