"""SeatManagementService — 142 RPC methods

用户管理、团队、计费、订阅、Pro 试用、推荐码、SSO、Internal 方法等。
逆向自 exa.seat_management_pb.SeatManagementService
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata, UserStatus, RegisterResult


SERVICE = "exa.seat_management_pb.SeatManagementService"

# 注册服务器 (RegisterUser 专用)
REGISTER_SERVER = "https://register.windsurf.com"


class SeatManagementService:
    """SeatManagementService 完整封装

    Args:
        transport: ConnectTransport 实例 (指向 API server)
        api_key: 默认 API key
    """

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self, key: str = None) -> dict:
        return {"metadata": metadata(key or self.api_key)}

    # ═══════════════════════════════════════════════════
    #  注册 & 认证
    # ═══════════════════════════════════════════════════

    def register_user(self, firebase_id_token: str = "") -> RegisterResult:
        """注册新用户 → 获取 API Key (需用 register server)"""
        reg_transport = ConnectTransport(REGISTER_SERVER, timeout=self.t.timeout)
        r = reg_transport.call(SERVICE, "RegisterUser", {
            "firebaseIdToken": firebase_id_token,
        })
        if r.ok:
            return RegisterResult.from_response(r.data)
        return RegisterResult()

    def register_user_raw(self, firebase_id_token: str = "") -> RpcResponse:
        """注册 (返回原始响应)"""
        reg_transport = ConnectTransport(REGISTER_SERVER, timeout=self.t.timeout)
        return reg_transport.call(SERVICE, "RegisterUser", {
            "firebaseIdToken": firebase_id_token,
        })

    def windsurf_post_auth(self, **kw) -> RpcResponse:
        """注册后回调"""
        return self._call("WindsurfPostAuth", {**self._meta(), **kw})

    def check_user_login_method(self, email: str = "") -> RpcResponse:
        """检查用户登录方式"""
        return self._call("CheckUserLoginMethod", {"email": email})

    def log_out_user(self) -> RpcResponse:
        return self._call("LogOutUser", self._meta())

    def migrate_api_key(self) -> RpcResponse:
        return self._call("MigrateApiKey", self._meta())

    def get_one_time_auth_token(self) -> RpcResponse:
        return self._call("GetOneTimeAuthToken", self._meta())

    def create_pkce_authorization_code(self) -> RpcResponse:
        return self._call("CreatePKCEAuthorizationCode", self._meta())

    def exchange_pkce_authorization_code(self, code: str = "") -> RpcResponse:
        return self._call("ExchangePKCEAuthorizationCode",
                          {**self._meta(), "code": code})

    def create_fb_user(self, **kw) -> RpcResponse:
        return self._call("CreateFbUser", kw)

    # ═══════════════════════════════════════════════════
    #  用户状态 & Profile
    # ═══════════════════════════════════════════════════

    def get_user_status(self, key: str = None) -> UserStatus:
        """获取用户状态 + 额度 (解析)"""
        try:
            r = self._call("GetUserStatus", self._meta(key))
            if r.ok and isinstance(getattr(r, 'data', None), dict):
                return UserStatus.from_response(r.data)
        except Exception:
            pass
        try:
            raw = r.data if isinstance(r.data, dict) else {"error": str(r.data)}
        except Exception:
            raw = {}
        return UserStatus(raw=raw)

    def get_user_status_raw(self, key: str = None) -> RpcResponse:
        """获取用户状态 (原始)"""
        return self._call("GetUserStatus", self._meta(key))

    def get_current_user(self) -> RpcResponse:
        return self._call("GetCurrentUser", self._meta())

    def get_plan_status(self) -> RpcResponse:
        return self._call("GetPlanStatus", self._meta())

    def get_profile_data(self) -> RpcResponse:
        return self._call("GetProfileData", self._meta())

    def update_profile(self, **fields) -> RpcResponse:
        return self._call("UpdateProfile", {**self._meta(), **fields})

    def update_name(self, name: str = "") -> RpcResponse:
        return self._call("UpdateName", {**self._meta(), "name": name})

    def update_occupation(self, occupation: str = "") -> RpcResponse:
        return self._call("UpdateOccupation", {**self._meta(), "occupation": occupation})

    def update_inbound_source(self, source: str = "") -> RpcResponse:
        return self._call("UpdateInboundSource", {**self._meta(), "inboundSource": source})

    def delete_user(self) -> RpcResponse:
        return self._call("DeleteUser", self._meta())

    def delete_profile_picture(self) -> RpcResponse:
        return self._call("DeleteProfilePicture", self._meta())

    def get_profile_picture_upload_url(self) -> RpcResponse:
        return self._call("GetProfilePicturePresignedUploadUrl", self._meta())

    def profile_picture_upload_complete(self) -> RpcResponse:
        return self._call("ProfilePictureUploadComplete", self._meta())

    def send_email_verification(self) -> RpcResponse:
        return self._call("SendEmailVerification", self._meta())

    def get_wrapped(self) -> RpcResponse:
        return self._call("GetWrapped", self._meta())

    def get_user_notifications(self) -> RpcResponse:
        return self._call("GetUserNotifications", self._meta())

    # ═══════════════════════════════════════════════════
    #  计划 & 订阅
    # ═══════════════════════════════════════════════════

    def get_user_subscription(self) -> RpcResponse:
        return self._call("GetUserSubscription", self._meta())

    def subscribe_to_plan(self, plan_id: str = "", **kw) -> RpcResponse:
        return self._call("SubscribeToPlan", {**self._meta(), "planId": plan_id, **kw})

    def update_plan(self, **kw) -> RpcResponse:
        return self._call("UpdatePlan", {**self._meta(), **kw})

    def cancel_plan(self, reason: str = "") -> RpcResponse:
        return self._call("CancelPlan", {**self._meta(), "reason": reason})

    def update_billing(self, **kw) -> RpcResponse:
        return self._call("UpdateBilling", {**self._meta(), **kw})

    def update_seats(self, count: int = 1) -> RpcResponse:
        return self._call("UpdateSeats", {**self._meta(), "seats": count})

    def get_customer_portal(self) -> RpcResponse:
        return self._call("GetCustomerPortal", self._meta())

    def initiate_top_up(self, **kw) -> RpcResponse:
        return self._call("InitiateTopUp", {**self._meta(), **kw})

    def purchase_cascade_credits(self, **kw) -> RpcResponse:
        return self._call("PurchaseCascadeCredits", {**self._meta(), **kw})

    def update_credit_top_up_settings(self, **kw) -> RpcResponse:
        return self._call("UpdateCreditTopUpSettings", {**self._meta(), **kw})

    def get_usage_config(self) -> RpcResponse:
        return self._call("GetUsageConfig", self._meta())

    # ═══════════════════════════════════════════════════
    #  Pro Trial
    # ═══════════════════════════════════════════════════

    def check_pro_trial_eligibility(self) -> RpcResponse:
        return self._call("CheckProTrialEligibility", self._meta())

    # ═══════════════════════════════════════════════════
    #  推荐码
    # ═══════════════════════════════════════════════════

    def process_referral_code(self, code: str = "") -> RpcResponse:
        return self._call("ProcessReferralCode", {**self._meta(), "referralCode": code})

    def is_valid_referral_code(self, code: str = "") -> RpcResponse:
        return self._call("IsValidReferralCode", {"referralCode": code})

    # ═══════════════════════════════════════════════════
    #  GitHub / Netlify 连接
    # ═══════════════════════════════════════════════════

    def get_github_account_status(self) -> RpcResponse:
        return self._call("GetGitHubAccountStatus", self._meta())

    def get_github_access_token(self) -> RpcResponse:
        return self._call("GetGitHubAccessToken", self._meta())

    def connect_github_account(self, code: str = "") -> RpcResponse:
        return self._call("ConnectGithubAccount", {**self._meta(), "code": code})

    def get_netlify_account_status(self) -> RpcResponse:
        return self._call("GetNetlifyAccountStatus", self._meta())

    def connect_netlify_account(self, code: str = "") -> RpcResponse:
        return self._call("ConnectNetlifyAccount", {**self._meta(), "code": code})

    def disconnect_netlify_account(self) -> RpcResponse:
        return self._call("DisconnectNetlifyAccount", self._meta())

    # ═══════════════════════════════════════════════════
    #  团队
    # ═══════════════════════════════════════════════════

    def create_multi_tenant_team(self, name: str = "", **kw) -> RpcResponse:
        return self._call("CreateMultiTenantTeam", {**self._meta(), "teamName": name, **kw})

    def delete_multi_tenant_team(self, team_id: str = "") -> RpcResponse:
        return self._call("DeleteMultiTenantTeam", {**self._meta(), "teamId": team_id})

    def get_multi_tenant_teams(self) -> RpcResponse:
        return self._call("GetMultiTenantTeams", self._meta())

    def get_team_info(self) -> RpcResponse:
        return self._call("GetTeamInfo", self._meta())

    def get_team_metadata(self) -> RpcResponse:
        return self._call("GetTeamMetadata", self._meta())

    def get_team_billing(self) -> RpcResponse:
        return self._call("GetTeamBilling", self._meta())

    def get_team_credit_entries(self) -> RpcResponse:
        return self._call("GetTeamCreditEntries", self._meta())

    def get_team_activity(self) -> RpcResponse:
        return self._call("GetTeamActivity", self._meta())

    def get_users(self) -> RpcResponse:
        return self._call("GetUsers", self._meta())

    def add_users_to_team(self, emails: list = None) -> RpcResponse:
        return self._call("AddUsersToTeam", {**self._meta(), "emails": emails or []})

    def remove_user_from_team(self, user_id: str = "") -> RpcResponse:
        return self._call("RemoveUserFromTeam", {**self._meta(), "userId": user_id})

    def request_team_access(self) -> RpcResponse:
        return self._call("RequestTeamAccess", self._meta())

    def refresh_team_invite_id(self) -> RpcResponse:
        return self._call("RefreshTeamInviteId", self._meta())

    def update_user_team_status(self, user_id: str = "", status: str = "") -> RpcResponse:
        return self._call("UpdateUserTeamStatus",
                          {**self._meta(), "userId": user_id, "status": status})

    def get_team_org_id(self) -> RpcResponse:
        return self._call("GetTeamOrgId", self._meta())

    # ═══════════════════════════════════════════════════
    #  团队配置
    # ═══════════════════════════════════════════════════

    def get_teams_features(self) -> RpcResponse:
        return self._call("GetTeamsFeatures", self._meta())

    def set_teams_features(self, **features) -> RpcResponse:
        return self._call("SetTeamsFeatures", {**self._meta(), **features})

    def update_team_config(self, **config) -> RpcResponse:
        return self._call("UpdateTeamConfig", {**self._meta(), **config})

    def update_team_config_external(self, **config) -> RpcResponse:
        return self._call("UpdateTeamConfigExternal", {**self._meta(), **config})

    def get_team_config(self) -> RpcResponse:
        return self._call("GetTeamConfigRecord", self._meta())

    def update_codeium_access(self, **kw) -> RpcResponse:
        return self._call("UpdateCodeiumAccess", {**self._meta(), **kw})

    def update_cli_access(self, **kw) -> RpcResponse:
        return self._call("UpdateCliAccess", {**self._meta(), **kw})

    def update_code_snippet_telemetry(self, **kw) -> RpcResponse:
        return self._call("UpdateCodeSnippetTelemetry", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  角色 & 权限
    # ═══════════════════════════════════════════════════

    def get_roles(self) -> RpcResponse:
        return self._call("GetRoles", self._meta())

    def get_roles_for_user(self, user_id: str = "") -> RpcResponse:
        return self._call("GetRolesForUser", {**self._meta(), "userId": user_id})

    def create_role(self, **kw) -> RpcResponse:
        return self._call("CreateRole", {**self._meta(), **kw})

    def update_role(self, **kw) -> RpcResponse:
        return self._call("UpdateRole", {**self._meta(), **kw})

    def delete_role(self, role_id: str = "") -> RpcResponse:
        return self._call("DeleteRole", {**self._meta(), "roleId": role_id})

    def add_user_role(self, user_id: str = "", role_id: str = "") -> RpcResponse:
        return self._call("AddUserRole", {**self._meta(), "userId": user_id, "roleId": role_id})

    def remove_user_role(self, user_id: str = "", role_id: str = "") -> RpcResponse:
        return self._call("RemoveUserRole",
                          {**self._meta(), "userId": user_id, "roleId": role_id})

    def update_user_roles(self, **kw) -> RpcResponse:
        return self._call("UpdateUserRoles", {**self._meta(), **kw})

    def bulk_update_user_roles(self, **kw) -> RpcResponse:
        return self._call("BulkUpdateUserRoles", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Preapproval
    # ═══════════════════════════════════════════════════

    def grant_preapproval(self, email: str = "") -> RpcResponse:
        return self._call("GrantPreapproval", {**self._meta(), "email": email})

    def accept_preapproval(self) -> RpcResponse:
        return self._call("AcceptPreapproval", self._meta())

    def reject_preapproval(self) -> RpcResponse:
        return self._call("RejectPreapproval", self._meta())

    def revoke_preapproval(self, email: str = "") -> RpcResponse:
        return self._call("RevokePreapproval", {**self._meta(), "email": email})

    def get_preapproval_for_user(self) -> RpcResponse:
        return self._call("GetPreapprovalForUser", self._meta())

    def get_preapprovals(self) -> RpcResponse:
        return self._call("GetPreapprovals", self._meta())

    def get_preapproval_metadata(self) -> RpcResponse:
        return self._call("GetPreapprovalMetadata", self._meta())

    def bulk_edit_user_approvals(self, **kw) -> RpcResponse:
        return self._call("BulkEditUserApprovals", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  SSO
    # ═══════════════════════════════════════════════════

    def check_email_for_sso(self, email: str = "") -> RpcResponse:
        return self._call("CheckEmailForSSO", {"email": email})

    def get_sso_provider(self) -> RpcResponse:
        return self._call("GetSSOProvider", self._meta())

    def save_sso_provider(self, **kw) -> RpcResponse:
        return self._call("SaveSSOProvider", {**self._meta(), **kw})

    def user_sso_login_redirect(self, **kw) -> RpcResponse:
        return self._call("UserSSOLoginRedirect", kw)

    def join_team_with_sso_login(self, **kw) -> RpcResponse:
        return self._call("JoinTeamWithSSOLogin", kw)

    def show_sso_add_on(self) -> RpcResponse:
        return self._call("ShowSSOAddOn", self._meta())

    # ═══════════════════════════════════════════════════
    #  域名
    # ═══════════════════════════════════════════════════

    def list_team_domains(self) -> RpcResponse:
        return self._call("ListTeamDomains", self._meta())

    def delete_team_domain(self, domain: str = "") -> RpcResponse:
        return self._call("DeleteTeamDomain", {**self._meta(), "domain": domain})

    def verify_team_domain(self, domain: str = "") -> RpcResponse:
        return self._call("VerifyTeamDomain", {**self._meta(), "domain": domain})

    # ═══════════════════════════════════════════════════
    #  API Key / Provider Key
    # ═══════════════════════════════════════════════════

    def get_api_key_summary(self) -> RpcResponse:
        return self._call("GetApiKeySummary", self._meta())

    def set_user_api_provider_key(self, provider: str = "", key: str = "") -> RpcResponse:
        return self._call("SetUserApiProviderKey",
                          {**self._meta(), "provider": provider, "apiKey": key})

    def delete_user_api_provider_key(self, provider: str = "") -> RpcResponse:
        return self._call("DeleteUserApiProviderKey",
                          {**self._meta(), "provider": provider})

    def get_set_user_api_provider_keys(self) -> RpcResponse:
        return self._call("GetSetUserApiProviderKeys", self._meta())

    def get_all_team_api_secrets(self) -> RpcResponse:
        return self._call("GetAllTeamApiSecrets", self._meta())

    def create_team_api_secret(self, **kw) -> RpcResponse:
        return self._call("CreateTeamApiSecret", {**self._meta(), **kw})

    def update_team_api_secret(self, **kw) -> RpcResponse:
        return self._call("UpdateTeamApiSecret", {**self._meta(), **kw})

    def delete_team_api_secret(self, secret_id: str = "") -> RpcResponse:
        return self._call("DeleteTeamApiSecret", {**self._meta(), "secretId": secret_id})

    # ═══════════════════════════════════════════════════
    #  License
    # ═══════════════════════════════════════════════════

    def get_license(self) -> RpcResponse:
        return self._call("GetLicense", self._meta())

    def set_team_license(self, **kw) -> RpcResponse:
        return self._call("SetTeamLicense", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Analytics
    # ═══════════════════════════════════════════════════

    def get_cascade_analytics(self) -> RpcResponse:
        return self._call("GetCascadeAnalytics", self._meta())

    # ═══════════════════════════════════════════════════
    #  Admin 方法
    # ═══════════════════════════════════════════════════

    def grant_super_admin_access(self) -> RpcResponse:
        return self._call("GrantSuperAdminAccess", self._meta())

    def grant_team_admin_access(self) -> RpcResponse:
        return self._call("GrantTeamAdminAccess", self._meta())

    # ═══════════════════════════════════════════════════
    #  Internal 方法 (需要服务端 secret)
    # ═══════════════════════════════════════════════════

    def update_plan_details_internal(self, secret: str = "", email: str = "", **kw) -> RpcResponse:
        return self._call("UpdatePlanDetailsInternal",
                          {"secret": secret, "email": email, **kw})

    def add_extra_flex_credits_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("AddExtraFlexCreditsInternal", {"secret": secret, **kw})

    def reset_quota_usage_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("ResetQuotaUsageInternal", {"secret": secret, **kw})

    def export_user_data_internal(self, secret: str = "", email: str = "") -> RpcResponse:
        return self._call("ExportUserDataInternal",
                          {"secret": secret, "email": email})

    def get_quota_usage_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("GetQuotaUsageInternal", {"secret": secret, **kw})

    def update_teams_features_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("UpdateTeamsFeaturesInternal", {"secret": secret, **kw})

    def get_teams_features_internal(self, secret: str = "") -> RpcResponse:
        return self._call("GetTeamsFeaturesInternal", {"secret": secret})

    def add_team_domain_internal(self, secret: str = "", domain: str = "") -> RpcResponse:
        return self._call("AddTeamDomainInternal",
                          {"secret": secret, "domain": domain})

    def delete_team_domain_internal(self, secret: str = "", domain: str = "") -> RpcResponse:
        return self._call("DeleteTeamDomainInternal",
                          {"secret": secret, "domain": domain})

    def list_team_domains_internal(self, secret: str = "") -> RpcResponse:
        return self._call("ListTeamDomainsInternal", {"secret": secret})

    def update_team_name_internal(self, secret: str = "", name: str = "") -> RpcResponse:
        return self._call("UpdateTeamNameInternal",
                          {"secret": secret, "teamName": name})

    def remove_users_from_team_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("RemoveUsersFromTeamInternal", {"secret": secret, **kw})

    def bulk_delete_users_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("BulkDeleteUsersInternal", {"secret": secret, **kw})

    def add_flex_credits_to_team(self, secret: str = "", **kw) -> RpcResponse:
        payload = {**self._meta(), **kw}
        if secret:
            payload["secret"] = secret
        return self._call("AddFlexCreditsToMultiTenantTeam", payload)

    # ═══════════════════════════════════════════════════
    #  补充方法 (逆向发现)
    # ═══════════════════════════════════════════════════

    def add_team_add_on_feature(self, **kw) -> RpcResponse:
        return self._call("AddTeamAddOnFeature", {**self._meta(), **kw})

    def add_team_domain(self, domain: str = "") -> RpcResponse:
        return self._call("AddTeamDomain", {**self._meta(), "domain": domain})

    def adjust_overage_balance_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("AdjustOverageBalanceInternal", {"secret": secret, **kw})

    def bulk_delete_users_internal_bq(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("BulkDeleteUsersInternalFromBigQuery", {"secret": secret, **kw})

    def bulk_edit_user_approvals_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("BulkEditUserApprovalsInternal", {"secret": secret, **kw})

    def create_enterprise(self, **kw) -> RpcResponse:
        return self._call("CreateEnterprise", {**self._meta(), **kw})

    def delete_api_key(self, **kw) -> RpcResponse:
        return self._call("DeleteApiKey", {**self._meta(), **kw})

    def delete_team(self, team_id: str = "") -> RpcResponse:
        return self._call("DeleteTeam", {**self._meta(), "teamId": team_id})

    def exchange_devin_code(self, code: str = "") -> RpcResponse:
        return self._call("ExchangeDevinCode", {**self._meta(), "code": code})

    def get_cli_team_settings(self) -> RpcResponse:
        return self._call("GetCliTeamSettings", self._meta())

    def get_groups(self) -> RpcResponse:
        return self._call("GetGroups", self._meta())

    def get_mucs_info(self) -> RpcResponse:
        return self._call("GetMucsInfo", self._meta())

    def get_overage_balance_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("GetOverageBalanceInternal", {"secret": secret, **kw})

    def get_primary_api_key_for_devs(self) -> RpcResponse:
        return self._call("GetPrimaryApiKeyForDevsOnly", self._meta())

    def get_self_devin_session_token(self) -> RpcResponse:
        return self._call("GetSelfDevinSessionToken", self._meta())

    def get_stripe_subscription_state(self) -> RpcResponse:
        return self._call("GetStripeSubscriptionState", self._meta())

    def get_team_credit_balance(self) -> RpcResponse:
        return self._call("GetTeamCreditBalance", self._meta())

    def initiate_account_verification_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("InitiateAccountOwnershipVerificationInternal", {"secret": secret, **kw})

    def verify_account_ownership_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("VerifyAccountOwnershipInternal", {"secret": secret, **kw})

    def verify_sso_login_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("VerifySSOLoginInternal", {"secret": secret, **kw})

    def invalidate_devin_caches(self, **kw) -> RpcResponse:
        return self._call("InvalidateDevinCaches", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  通用调用 (任意方法名)
    # ═══════════════════════════════════════════════════

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        """调用任意 SeatManagement 方法"""
        return self._call(method, payload, **kw)
