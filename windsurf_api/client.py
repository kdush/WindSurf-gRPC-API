"""WindsurfClient — 高层封装

整合 transport + auth + 13 services 的统一入口。

用法::

    from windsurf_api import WindsurfClient

    # 方式 1: API Key 直接使用
    ws = WindsurfClient(api_key="sk-ws-...")
    status = ws.get_user_status()
    models = ws.get_models()

    # 方式 2: OAuth 登录
    ws = WindsurfClient()
    ws.login_github("github_access_token")
    status = ws.get_user_status()

    # 方式 3: 访问底层服务
    ws.seat.get_plan_status()
    ws.api_server.get_cascade_model_configs()
    ws.ls.inject_pro_experiments()
    ws.plugins.get_mcp_client_infos()
"""
from .transport import ConnectTransport
from .auth import oauth_login, email_login, email_signup, refresh_token, FirebaseUser
from .models import UserStatus, ModelProvider, RegisterResult, metadata
from .services.seat_management import SeatManagementService
from .services.api_server import ApiServerService
from .services.language_server import LanguageServerService
from .services.extension_server import ExtensionServerService
from .services.plugins import CascadePluginsService
from .services.analytics import AnalyticsService, UserAnalyticsService, ProductAnalyticsService
from .services.misc import (
    BrowserPreviewService, FileSystemProviderService,
    DevService, AuthService, ChatClientServerService,
)


API_SERVER = "https://server.self-serve.windsurf.com"
EU_SERVER = "https://eu.windsurf.com/_route/api_server"
REGISTER_SERVER = "https://register.windsurf.com"


class WindsurfClient:
    """Windsurf 协议客户端

    Args:
        api_key: Windsurf API key (sk-ws-...)
        server: API 服务器 URL
        timeout: 默认超时秒数
    """

    def __init__(self, api_key: str = "", server: str = API_SERVER, timeout: int = 15):
        self.api_key = api_key
        self.server = server
        self.timeout = timeout
        self.firebase_user: FirebaseUser = None

        # 传输层
        self._transport = ConnectTransport(server, timeout=timeout)

        # 服务实例 (13 gRPC services)
        self.seat = SeatManagementService(self._transport, api_key)
        self.api_server = ApiServerService(self._transport, api_key)
        self.plugins = CascadePluginsService(self._transport, api_key)
        self.ls = LanguageServerService(api_key=api_key)
        self.extension = ExtensionServerService(self._transport, api_key)
        self.analytics = AnalyticsService(self._transport, api_key)
        self.user_analytics = UserAnalyticsService(self._transport, api_key)
        self.product_analytics = ProductAnalyticsService(self._transport, api_key)
        self.browser_preview = BrowserPreviewService(self._transport, api_key)
        self.filesystem = FileSystemProviderService(self._transport, api_key)
        self.dev = DevService(self._transport, api_key)
        self.auth_service = AuthService(self._transport, api_key)
        self.chat_client = ChatClientServerService(self._transport, api_key)

    def _update_key(self, key: str):
        """更新所有服务的 api_key"""
        self.api_key = key
        for svc in [self.seat, self.api_server, self.plugins, self.ls,
                    self.extension, self.analytics, self.user_analytics,
                    self.product_analytics, self.browser_preview,
                    self.filesystem, self.dev, self.auth_service, self.chat_client]:
            svc.api_key = key

    # ═══════════════════════════════════════════════════
    #  认证
    # ═══════════════════════════════════════════════════

    def login_github(self, access_token: str) -> FirebaseUser:
        """GitHub OAuth 登录"""
        self.firebase_user = oauth_login("github", access_token)
        return self.firebase_user

    def login_google(self, id_token: str) -> FirebaseUser:
        """Google OAuth 登录"""
        self.firebase_user = oauth_login("google", id_token)
        return self.firebase_user

    def login_microsoft(self, id_token: str) -> FirebaseUser:
        """Microsoft OAuth 登录"""
        self.firebase_user = oauth_login("microsoft", id_token)
        return self.firebase_user

    def login_email(self, email: str, password: str) -> FirebaseUser:
        """邮箱密码登录"""
        self.firebase_user = email_login(email, password)
        return self.firebase_user

    def signup_email(self, email: str, password: str) -> FirebaseUser:
        """邮箱密码注册"""
        self.firebase_user = email_signup(email, password)
        return self.firebase_user

    def refresh(self, refresh_tok: str = None) -> FirebaseUser:
        """刷新 token"""
        tok = refresh_tok or (self.firebase_user.refresh_token if self.firebase_user else "")
        if not tok:
            return None
        self.firebase_user = refresh_token(tok)
        return self.firebase_user

    # ═══════════════════════════════════════════════════
    #  注册 → 获取 API Key
    # ═══════════════════════════════════════════════════

    def register(self, firebase_id_token: str = None) -> RegisterResult:
        """注册 Windsurf 账号，获取 API Key

        如果已登录 Firebase，自动使用 id_token。
        """
        token = firebase_id_token
        if not token and self.firebase_user:
            token = self.firebase_user.id_token
        if not token:
            return RegisterResult()

        result = self.seat.register_user(token)
        if result.ok:
            self._update_key(result.api_key)
        return result

    # ═══════════════════════════════════════════════════
    #  用户状态
    # ═══════════════════════════════════════════════════

    def get_user_status(self, key: str = None) -> UserStatus:
        """获取用户状态 + 额度"""
        return self.seat.get_user_status(key)

    def get_plan_status(self):
        return self.seat.get_plan_status()

    def check_login_method(self, email: str):
        return self.seat.check_user_login_method(email)

    # ═══════════════════════════════════════════════════
    #  模型
    # ═══════════════════════════════════════════════════

    def get_models(self) -> list:
        """获取所有模型提供商"""
        return self.api_server.get_model_providers()

    def get_model_configs(self):
        """获取 Cascade 模型配置"""
        return self.api_server.get_cascade_model_configs()

    def get_model_statuses(self):
        return self.api_server.get_model_statuses()

    # ═══════════════════════════════════════════════════
    #  聊天容量
    # ═══════════════════════════════════════════════════

    def check_capacity(self, model_uid: str = ""):
        return self.api_server.check_chat_capacity(model_uid)

    def check_rate_limit(self, model_uid: str = ""):
        return self.api_server.check_user_message_rate_limit(model_uid)

    # ═══════════════════════════════════════════════════
    #  MCP 插件
    # ═══════════════════════════════════════════════════

    def get_mcp_secrets(self):
        """获取 MCP OAuth 凭据"""
        return self.plugins.get_mcp_client_infos()

    def get_plugins(self):
        return self.plugins.get_available_cascade_plugins()

    # ═══════════════════════════════════════════════════
    #  Pro Trial
    # ═══════════════════════════════════════════════════

    def check_pro_trial(self):
        return self.seat.check_pro_trial_eligibility()

    # ═══════════════════════════════════════════════════
    #  推荐
    # ═══════════════════════════════════════════════════

    def process_referral(self, code: str):
        return self.seat.process_referral_code(code)

    def check_referral(self, code: str):
        return self.seat.is_valid_referral_code(code)

    # ═══════════════════════════════════════════════════
    #  GitHub / Netlify
    # ═══════════════════════════════════════════════════

    def github_status(self):
        return self.seat.get_github_account_status()

    def netlify_status(self):
        return self.seat.get_netlify_account_status()

    # ═══════════════════════════════════════════════════
    #  团队
    # ═══════════════════════════════════════════════════

    def get_team_info(self):
        return self.seat.get_team_info()

    def get_team_features(self):
        return self.seat.get_teams_features()

    def create_team(self, name: str):
        return self.seat.create_multi_tenant_team(name)

    # ═══════════════════════════════════════════════════
    #  LS 实验
    # ═══════════════════════════════════════════════════

    def inject_experiments(self, disable: list = None, enable: list = None):
        """向 LS 注入实验 flags"""
        if not self.ls.port:
            self.ls.auto_connect()
        return self.ls.set_base_experiments(disable, enable)

    def inject_pro(self):
        """一键注入 Pro 实验"""
        if not self.ls.port:
            self.ls.auto_connect()
        return self.ls.inject_pro_experiments()

    # ═══════════════════════════════════════════════════
    #  Internal 方法 (需 secret)
    # ═══════════════════════════════════════════════════

    def upgrade_plan_internal(self, secret: str, email: str, **kw):
        return self.seat.update_plan_details_internal(secret, email, **kw)

    def add_credits_internal(self, secret: str, **kw):
        return self.seat.add_extra_flex_credits_internal(secret, **kw)

    def reset_quota_internal(self, secret: str, **kw):
        return self.seat.reset_quota_usage_internal(secret, **kw)

    # ═══════════════════════════════════════════════════
    #  通用调用
    # ═══════════════════════════════════════════════════

    def call(self, service: str, method: str, payload: dict = None, **kw):
        """调用任意 gRPC 方法"""
        return self._transport.call(service, method, payload or {}, **kw)

    def __repr__(self):
        key_preview = f"{self.api_key[:20]}..." if self.api_key else "(no key)"
        return f"WindsurfClient({key_preview}, server={self.server})"
