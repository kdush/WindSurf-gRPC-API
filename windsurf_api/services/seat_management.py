"""SeatManagementService — 145 RPC methods

用户管理、团队、计费、订阅、Pro 试用、推荐码、SSO、Internal 方法等。
逆向自 exa.seat_management_pb.SeatManagementService
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata, UserStatus, RegisterResult


SERVICE = "exa.seat_management_pb.SeatManagementService"
REGISTER_SERVER = "https://register.windsurf.com"


class SeatManagementService:
    """SeatManagementService 完整封装"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self, key: str = None) -> dict:
        return {"metadata": metadata(key or self.api_key)}

    def register_user(self, firebase_id_token: str = "") -> RegisterResult:
        """注册新用户 → 获取 API Key"""
        reg_transport = ConnectTransport(REGISTER_SERVER, timeout=self.t.timeout)
        r = reg_transport.call(SERVICE, "RegisterUser", {
            "firebaseIdToken": firebase_id_token,
        })
        if r.ok: return RegisterResult.from_response(r.data)
        return RegisterResult()

    def register_user_raw(self, firebase_id_token: str = "") -> RpcResponse:
        reg_transport = ConnectTransport(REGISTER_SERVER, timeout=self.t.timeout)
        return reg_transport.call(SERVICE, "RegisterUser", {
            "firebaseIdToken": firebase_id_token,
        })

    def get_user_status(self, key: str = None) -> UserStatus:
        """获取用户状态 + 额度"""
        try:
            r = self._call("GetUserStatus", self._meta(key))
            if r.ok and isinstance(getattr(r, 'data', None), dict):
                return UserStatus.from_response(r.data)
        except Exception: pass
        try:
            raw = r.data if isinstance(r.data, dict) else {"error": str(r.data)}
        except Exception: raw = {}
        return UserStatus(raw=raw)

    def get_user_status_raw(self, key: str = None) -> RpcResponse:
        return self._call("GetUserStatus", self._meta(key))

    # ── 预审批 ──

    def accept_preapproval(self, *, preapprovalId: str = "", **kw) -> RpcResponse:
        """接受预审批邀请 (加入团队)

        Args:
            preapprovalId: 预审批 ID
        """
        return self._call("AcceptPreapproval", {**self._meta(), "preapprovalId": preapprovalId, **kw})

    def get_preapproval_for_user(self, **kw) -> RpcResponse:
        """获取当前用户的预审批"""
        return self._call("GetPreapprovalForUser", {**self._meta(), **kw})

    def get_preapproval_metadata(self, *, preapprovalId: str = "", **kw) -> RpcResponse:
        """获取预审批元数据

        Args:
            preapprovalId: 预审批 ID
        """
        return self._call("GetPreapprovalMetadata", {**self._meta(), "preapprovalId": preapprovalId, **kw})

    def get_preapprovals(self, **kw) -> RpcResponse:
        """获取所有预审批列表"""
        return self._call("GetPreapprovals", {**self._meta(), **kw})

    def grant_preapproval(self, *, email: str = "", teamId: str = "", **kw) -> RpcResponse:
        """授予预审批 (邀请用户加入团队)

        Args:
            email: 被邀请人邮箱
            teamId: 团队 ID
        """
        return self._call("GrantPreapproval", {**self._meta(), "email": email, "teamId": teamId, **kw})

    def reject_preapproval(self, *, preapprovalId: str = "", **kw) -> RpcResponse:
        """拒绝预审批邀请

        Args:
            preapprovalId: 预审批 ID
        """
        return self._call("RejectPreapproval", {**self._meta(), "preapprovalId": preapprovalId, **kw})

    def revoke_preapproval(self, *, preapprovalId: str = "", **kw) -> RpcResponse:
        """撤销已授予的预审批

        Args:
            preapprovalId: 预审批 ID
        """
        return self._call("RevokePreapproval", {**self._meta(), "preapprovalId": preapprovalId, **kw})

    # ── 额度 / Internal ──

    def add_extra_flex_credits_internal(self, *, secret: str = "", email: str = "",
                                        credits: int = 0, **kw) -> RpcResponse:
        """[Internal] 为用户添加额外弹性额度

        Args:
            secret: Internal 密钥
            email: 目标用户邮箱
            credits: 添加额度数量
        """
        return self._call("AddExtraFlexCreditsInternal", {
            **self._meta(), "secret": secret, "email": email, "credits": credits, **kw})

    def add_flex_credits_to_multi_tenant_team(self, *, teamId: str = "", credits: int = 0, **kw) -> RpcResponse:
        """为多租户团队添加弹性额度

        Args:
            teamId: 团队 ID
            credits: 额度数量
        """
        return self._call("AddFlexCreditsToMultiTenantTeam", {
            **self._meta(), "teamId": teamId, "credits": credits, **kw})

    def adjust_overage_balance_internal(self, *, secret: str = "", email: str = "",
                                        amount: int = 0, **kw) -> RpcResponse:
        """[Internal] 调整超额余额

        Args:
            secret: Internal 密钥
            email: 用户邮箱
            amount: 调整金额
        """
        return self._call("AdjustOverageBalanceInternal", {
            **self._meta(), "secret": secret, "email": email, "amount": amount, **kw})

    def get_overage_balance_internal(self, *, secret: str = "", email: str = "", **kw) -> RpcResponse:
        """[Internal] 获取超额余额

        Args:
            secret: Internal 密钥
            email: 用户邮箱
        """
        return self._call("GetOverageBalanceInternal", {
            **self._meta(), "secret": secret, "email": email, **kw})

    def get_quota_usage_internal(self, *, secret: str = "", email: str = "", **kw) -> RpcResponse:
        """[Internal] 获取配额使用量

        Args:
            secret: Internal 密钥
            email: 用户邮箱
        """
        return self._call("GetQuotaUsageInternal", {
            **self._meta(), "secret": secret, "email": email, **kw})

    def reset_quota_usage_internal(self, *, secret: str = "", email: str = "", **kw) -> RpcResponse:
        """[Internal] 重置用户配额

        Args:
            secret: Internal 密钥
            email: 用户邮箱
        """
        return self._call("ResetQuotaUsageInternal", {
            **self._meta(), "secret": secret, "email": email, **kw})

    def update_plan_details_internal(self, *, secret: str = "", email: str = "",
                                     teamsTier: int = 0, hasPaidFeatures: bool = False, **kw) -> RpcResponse:
        """[Internal] 更新用户计划详情 (升级/降级)

        Args:
            secret: Internal 密钥
            email: 用户邮箱
            teamsTier: 计划等级 (0=Free, 1=Individual, 2=Pro, 3=Teams)
            hasPaidFeatures: 是否有付费功能
        """
        return self._call("UpdatePlanDetailsInternal", {
            **self._meta(), "secret": secret, "email": email,
            "teamsTier": teamsTier, "hasPaidFeatures": hasPaidFeatures, **kw})

    def export_user_data_internal(self, *, secret: str = "", email: str = "", **kw) -> RpcResponse:
        """[Internal] 导出用户数据

        Args:
            secret: Internal 密钥
            email: 用户邮箱
        """
        return self._call("ExportUserDataInternal", {
            **self._meta(), "secret": secret, "email": email, **kw})

    def initiate_account_ownership_verification_internal(self, *, secret: str = "",
                                                         email: str = "", **kw) -> RpcResponse:
        """[Internal] 发起账户所有权验证

        Args:
            secret: Internal 密钥
            email: 用户邮箱
        """
        return self._call("InitiateAccountOwnershipVerificationInternal", {
            **self._meta(), "secret": secret, "email": email, **kw})

    def verify_account_ownership_internal(self, *, secret: str = "", code: str = "", **kw) -> RpcResponse:
        """[Internal] 验证账户所有权

        Args:
            secret: Internal 密钥
            code: 验证码
        """
        return self._call("VerifyAccountOwnershipInternal", {
            **self._meta(), "secret": secret, "code": code, **kw})

    def invalidate_devin_caches(self, *, secret: str = "", **kw) -> RpcResponse:
        """[Internal] 使 Devin 缓存失效

        Args:
            secret: Internal 密钥
        """
        return self._call("InvalidateDevinCaches", {**self._meta(), "secret": secret, **kw})

    def bulk_delete_users_internal(self, *, secret: str = "", emails: list = None, **kw) -> RpcResponse:
        """[Internal] 批量删除用户

        Args:
            secret: Internal 密钥
            emails: 用户邮箱列表
        """
        return self._call("BulkDeleteUsersInternal", {
            **self._meta(), "secret": secret, "emails": emails or [], **kw})

    def bulk_delete_users_internal_from_big_query(self, *, secret: str = "", **kw) -> RpcResponse:
        """[Internal] 从 BigQuery 批量删除用户

        Args:
            secret: Internal 密钥
        """
        return self._call("BulkDeleteUsersInternalFromBigQuery", {**self._meta(), "secret": secret, **kw})

    def bulk_edit_user_approvals_internal(self, *, secret: str = "", approvals: list = None, **kw) -> RpcResponse:
        """[Internal] 批量编辑用户审批状态

        Args:
            secret: Internal 密钥
            approvals: 审批操作列表
        """
        return self._call("BulkEditUserApprovalsInternal", {
            **self._meta(), "secret": secret, "approvals": approvals or [], **kw})

    def verify_sso_login_internal(self, *, secret: str = "", token: str = "", **kw) -> RpcResponse:
        """[Internal] 验证 SSO 登录

        Args:
            secret: Internal 密钥
            token: SSO Token
        """
        return self._call("VerifySSOLoginInternal", {
            **self._meta(), "secret": secret, "token": token, **kw})

    # ── 团队管理 ──

    def add_team_add_on_feature(self, *, teamId: str = "", feature: str = "", **kw) -> RpcResponse:
        """为团队添加附加功能

        Args:
            teamId: 团队 ID
            feature: 功能名称
        """
        return self._call("AddTeamAddOnFeature", {
            **self._meta(), "teamId": teamId, "feature": feature, **kw})

    def add_team_domain(self, *, teamId: str = "", domain: str = "", **kw) -> RpcResponse:
        """为团队添加域名

        Args:
            teamId: 团队 ID
            domain: 域名 (如 "company.com")
        """
        return self._call("AddTeamDomain", {**self._meta(), "teamId": teamId, "domain": domain, **kw})

    def add_team_domain_internal(self, *, secret: str = "", teamId: str = "",
                                 domain: str = "", **kw) -> RpcResponse:
        """[Internal] 为团队添加域名

        Args:
            secret: Internal 密钥
            teamId: 团队 ID
            domain: 域名
        """
        return self._call("AddTeamDomainInternal", {
            **self._meta(), "secret": secret, "teamId": teamId, "domain": domain, **kw})

    def add_users_to_team(self, *, teamId: str = "", emails: list = None, **kw) -> RpcResponse:
        """将用户批量添加到团队

        Args:
            teamId: 团队 ID
            emails: 用户邮箱列表
        """
        return self._call("AddUsersToTeam", {**self._meta(), "teamId": teamId, "emails": emails or [], **kw})

    def create_enterprise(self, *, name: str = "", domain: str = "", **kw) -> RpcResponse:
        """创建企业

        Args:
            name: 企业名称
            domain: 企业域名
        """
        return self._call("CreateEnterprise", {**self._meta(), "name": name, "domain": domain, **kw})

    def create_multi_tenant_team(self, *, teamName: str = "", **kw) -> RpcResponse:
        """创建多租户团队

        Args:
            teamName: 团队名称
        """
        return self._call("CreateMultiTenantTeam", {**self._meta(), "teamName": teamName, **kw})

    def create_team_api_secret(self, *, teamId: str = "", name: str = "", **kw) -> RpcResponse:
        """创建团队 API Secret

        Args:
            teamId: 团队 ID
            name: Secret 名称
        """
        return self._call("CreateTeamApiSecret", {**self._meta(), "teamId": teamId, "name": name, **kw})

    def delete_multi_tenant_team(self, *, teamId: str = "", **kw) -> RpcResponse:
        """删除多租户团队

        Args:
            teamId: 团队 ID
        """
        return self._call("DeleteMultiTenantTeam", {**self._meta(), "teamId": teamId, **kw})

    def delete_team(self, *, teamId: str = "", **kw) -> RpcResponse:
        """删除团队

        Args:
            teamId: 团队 ID
        """
        return self._call("DeleteTeam", {**self._meta(), "teamId": teamId, **kw})

    def delete_team_api_secret(self, *, teamId: str = "", secretId: str = "", **kw) -> RpcResponse:
        """删除团队 API Secret

        Args:
            teamId: 团队 ID
            secretId: Secret ID
        """
        return self._call("DeleteTeamApiSecret", {**self._meta(), "teamId": teamId, "secretId": secretId, **kw})

    def delete_team_domain(self, *, teamId: str = "", domain: str = "", **kw) -> RpcResponse:
        """删除团队域名

        Args:
            teamId: 团队 ID
            domain: 域名
        """
        return self._call("DeleteTeamDomain", {**self._meta(), "teamId": teamId, "domain": domain, **kw})

    def delete_team_domain_internal(self, *, secret: str = "", teamId: str = "",
                                    domain: str = "", **kw) -> RpcResponse:
        """[Internal] 删除团队域名

        Args:
            secret: Internal 密钥
            teamId: 团队 ID
            domain: 域名
        """
        return self._call("DeleteTeamDomainInternal", {
            **self._meta(), "secret": secret, "teamId": teamId, "domain": domain, **kw})

    def get_all_team_api_secrets(self, *, teamId: str = "", **kw) -> RpcResponse:
        """获取团队所有 API Secret

        Args:
            teamId: 团队 ID
        """
        return self._call("GetAllTeamApiSecrets", {**self._meta(), "teamId": teamId, **kw})

    def get_cli_team_settings(self, **kw) -> RpcResponse:
        """获取 CLI 团队设置"""
        return self._call("GetCliTeamSettings", {**self._meta(), **kw})

    def get_multi_tenant_teams(self, **kw) -> RpcResponse:
        """获取所有多租户团队"""
        return self._call("GetMultiTenantTeams", {**self._meta(), **kw})

    def get_team_activity(self, *, teamId: str = "", **kw) -> RpcResponse:
        """获取团队活动记录

        Args:
            teamId: 团队 ID
        """
        return self._call("GetTeamActivity", {**self._meta(), "teamId": teamId, **kw})

    def get_team_billing(self, **kw) -> RpcResponse:
        """获取团队计费信息"""
        return self._call("GetTeamBilling", {**self._meta(), **kw})

    def get_team_config_record(self, *, teamId: str = "", **kw) -> RpcResponse:
        """获取团队配置记录

        Args:
            teamId: 团队 ID
        """
        return self._call("GetTeamConfigRecord", {**self._meta(), "teamId": teamId, **kw})

    def get_team_credit_balance(self, **kw) -> RpcResponse:
        """获取团队额度余额"""
        return self._call("GetTeamCreditBalance", {**self._meta(), **kw})

    def get_team_credit_entries(self, **kw) -> RpcResponse:
        """获取团队额度明细"""
        return self._call("GetTeamCreditEntries", {**self._meta(), **kw})

    def get_team_info(self, **kw) -> RpcResponse:
        """获取当前团队信息"""
        return self._call("GetTeamInfo", {**self._meta(), **kw})

    def get_team_metadata(self, *, teamId: str = "", **kw) -> RpcResponse:
        """获取团队元数据

        Args:
            teamId: 团队 ID
        """
        return self._call("GetTeamMetadata", {**self._meta(), "teamId": teamId, **kw})

    def get_team_org_id(self, **kw) -> RpcResponse:
        """获取团队组织 ID"""
        return self._call("GetTeamOrgId", {**self._meta(), **kw})

    def get_teams_features(self, **kw) -> RpcResponse:
        """获取团队功能列表"""
        return self._call("GetTeamsFeatures", {**self._meta(), **kw})

    def get_teams_features_internal(self, *, secret: str = "", teamId: str = "", **kw) -> RpcResponse:
        """[Internal] 获取团队功能列表

        Args:
            secret: Internal 密钥
            teamId: 团队 ID
        """
        return self._call("GetTeamsFeaturesInternal", {
            **self._meta(), "secret": secret, "teamId": teamId, **kw})

    def grant_super_admin_access(self, *, userId: str = "", **kw) -> RpcResponse:
        """授予超级管理员权限

        Args:
            userId: 目标用户 ID
        """
        return self._call("GrantSuperAdminAccess", {**self._meta(), "userId": userId, **kw})

    def grant_team_admin_access(self, *, userId: str = "", teamId: str = "", **kw) -> RpcResponse:
        """授予团队管理员权限

        Args:
            userId: 目标用户 ID
            teamId: 团队 ID
        """
        return self._call("GrantTeamAdminAccess", {**self._meta(), "userId": userId, "teamId": teamId, **kw})

    def join_team_with_sso_login(self, *, token: str = "", teamId: str = "", **kw) -> RpcResponse:
        """通过 SSO 登录加入团队

        Args:
            token: SSO Token
            teamId: 团队 ID
        """
        return self._call("JoinTeamWithSSOLogin", {**self._meta(), "token": token, "teamId": teamId, **kw})

    def list_team_domains(self, *, teamId: str = "", **kw) -> RpcResponse:
        """列出团队域名

        Args:
            teamId: 团队 ID
        """
        return self._call("ListTeamDomains", {**self._meta(), "teamId": teamId, **kw})

    def list_team_domains_internal(self, *, secret: str = "", teamId: str = "", **kw) -> RpcResponse:
        """[Internal] 列出团队域名

        Args:
            secret: Internal 密钥
            teamId: 团队 ID
        """
        return self._call("ListTeamDomainsInternal", {
            **self._meta(), "secret": secret, "teamId": teamId, **kw})

    def refresh_team_invite_id(self, *, teamId: str = "", **kw) -> RpcResponse:
        """刷新团队邀请 ID

        Args:
            teamId: 团队 ID
        """
        return self._call("RefreshTeamInviteId", {**self._meta(), "teamId": teamId, **kw})

    def remove_user_from_team(self, *, userId: str = "", teamId: str = "", **kw) -> RpcResponse:
        """将用户从团队中移除

        Args:
            userId: 用户 ID
            teamId: 团队 ID
        """
        return self._call("RemoveUserFromTeam", {**self._meta(), "userId": userId, "teamId": teamId, **kw})

    def remove_users_from_team_internal(self, *, secret: str = "", teamId: str = "",
                                        emails: list = None, **kw) -> RpcResponse:
        """[Internal] 批量移除团队成员

        Args:
            secret: Internal 密钥
            teamId: 团队 ID
            emails: 用户邮箱列表
        """
        return self._call("RemoveUsersFromTeamInternal", {
            **self._meta(), "secret": secret, "teamId": teamId, "emails": emails or [], **kw})

    def request_team_access(self, *, teamId: str = "", **kw) -> RpcResponse:
        """申请加入团队

        Args:
            teamId: 团队 ID
        """
        return self._call("RequestTeamAccess", {**self._meta(), "teamId": teamId, **kw})

    def set_team_license(self, *, teamId: str = "", license: str = "", **kw) -> RpcResponse:
        """设置团队许可证

        Args:
            teamId: 团队 ID
            license: 许可证内容
        """
        return self._call("SetTeamLicense", {**self._meta(), "teamId": teamId, "license": license, **kw})

    def set_teams_features(self, *, features: dict = None, **kw) -> RpcResponse:
        """设置团队功能

        Args:
            features: 功能配置字典
        """
        return self._call("SetTeamsFeatures", {**self._meta(), "features": features or {}, **kw})

    def update_team_api_secret(self, *, teamId: str = "", secretId: str = "",
                               name: str = "", **kw) -> RpcResponse:
        """更新团队 API Secret

        Args:
            teamId: 团队 ID
            secretId: Secret ID
            name: 新名称
        """
        return self._call("UpdateTeamApiSecret", {
            **self._meta(), "teamId": teamId, "secretId": secretId, "name": name, **kw})

    def update_team_config(self, *, config: dict = None, **kw) -> RpcResponse:
        """更新团队配置

        Args:
            config: 配置字典
        """
        return self._call("UpdateTeamConfig", {**self._meta(), "config": config or {}, **kw})

    def update_team_config_external(self, *, teamId: str = "", config: dict = None, **kw) -> RpcResponse:
        """外部更新团队配置

        Args:
            teamId: 团队 ID
            config: 配置字典
        """
        return self._call("UpdateTeamConfigExternal", {
            **self._meta(), "teamId": teamId, "config": config or {}, **kw})

    def update_team_name_internal(self, *, secret: str = "", teamId: str = "",
                                  name: str = "", **kw) -> RpcResponse:
        """[Internal] 更新团队名称

        Args:
            secret: Internal 密钥
            teamId: 团队 ID
            name: 新名称
        """
        return self._call("UpdateTeamNameInternal", {
            **self._meta(), "secret": secret, "teamId": teamId, "name": name, **kw})

    def update_teams_features_internal(self, *, secret: str = "", teamId: str = "",
                                       features: dict = None, **kw) -> RpcResponse:
        """[Internal] 更新团队功能

        Args:
            secret: Internal 密钥
            teamId: 团队 ID
            features: 功能配置字典
        """
        return self._call("UpdateTeamsFeaturesInternal", {
            **self._meta(), "secret": secret, "teamId": teamId, "features": features or {}, **kw})

    def verify_team_domain(self, *, teamId: str = "", domain: str = "", **kw) -> RpcResponse:
        """验证团队域名所有权

        Args:
            teamId: 团队 ID
            domain: 域名
        """
        return self._call("VerifyTeamDomain", {**self._meta(), "teamId": teamId, "domain": domain, **kw})

    # ── 用户角色 ──

    def add_user_role(self, *, userId: str = "", roleId: str = "", **kw) -> RpcResponse:
        """为用户添加角色

        Args:
            userId: 用户 ID
            roleId: 角色 ID
        """
        return self._call("AddUserRole", {**self._meta(), "userId": userId, "roleId": roleId, **kw})

    def bulk_edit_user_approvals(self, *, approvals: list = None, **kw) -> RpcResponse:
        """批量编辑用户审批

        Args:
            approvals: 审批操作列表
        """
        return self._call("BulkEditUserApprovals", {**self._meta(), "approvals": approvals or [], **kw})

    def bulk_update_user_roles(self, *, updates: list = None, **kw) -> RpcResponse:
        """批量更新用户角色

        Args:
            updates: 角色更新列表 [{userId, roleId}, ...]
        """
        return self._call("BulkUpdateUserRoles", {**self._meta(), "updates": updates or [], **kw})

    def create_role(self, *, name: str = "", permissions: list = None, **kw) -> RpcResponse:
        """创建角色

        Args:
            name: 角色名称
            permissions: 权限列表
        """
        return self._call("CreateRole", {**self._meta(), "name": name, "permissions": permissions or [], **kw})

    def delete_role(self, *, roleId: str = "", **kw) -> RpcResponse:
        """删除角色

        Args:
            roleId: 角色 ID
        """
        return self._call("DeleteRole", {**self._meta(), "roleId": roleId, **kw})

    def get_groups(self, **kw) -> RpcResponse:
        """获取所有用户群组"""
        return self._call("GetGroups", {**self._meta(), **kw})

    def get_roles(self, **kw) -> RpcResponse:
        """获取所有角色"""
        return self._call("GetRoles", {**self._meta(), **kw})

    def get_roles_for_user(self, *, userId: str = "", **kw) -> RpcResponse:
        """获取用户的角色列表

        Args:
            userId: 用户 ID
        """
        return self._call("GetRolesForUser", {**self._meta(), "userId": userId, **kw})

    def get_users(self, *, teamId: str = "", page: int = 0, limit: int = 0, **kw) -> RpcResponse:
        """获取用户列表

        Args:
            teamId: 团队 ID (可选, 过滤)
            page: 页码
            limit: 每页数量
        """
        return self._call("GetUsers", {**self._meta(), "teamId": teamId, "page": page, "limit": limit, **kw})

    def remove_user_role(self, *, userId: str = "", roleId: str = "", **kw) -> RpcResponse:
        """移除用户角色

        Args:
            userId: 用户 ID
            roleId: 角色 ID
        """
        return self._call("RemoveUserRole", {**self._meta(), "userId": userId, "roleId": roleId, **kw})

    def update_role(self, *, roleId: str = "", name: str = "", permissions: list = None, **kw) -> RpcResponse:
        """更新角色

        Args:
            roleId: 角色 ID
            name: 新名称
            permissions: 新权限列表
        """
        return self._call("UpdateRole", {
            **self._meta(), "roleId": roleId, "name": name, "permissions": permissions or [], **kw})

    def update_user_roles(self, *, userId: str = "", roleIds: list = None, **kw) -> RpcResponse:
        """更新用户的角色列表

        Args:
            userId: 用户 ID
            roleIds: 新角色 ID 列表
        """
        return self._call("UpdateUserRoles", {**self._meta(), "userId": userId, "roleIds": roleIds or [], **kw})

    def update_user_team_status(self, *, userId: str = "", status: str = "", **kw) -> RpcResponse:
        """更新用户团队状态

        Args:
            userId: 用户 ID
            status: 新状态
        """
        return self._call("UpdateUserTeamStatus", {**self._meta(), "userId": userId, "status": status, **kw})

    # ── 计划 / 订阅 / 计费 ──

    def cancel_plan(self, *, reason: str = "", **kw) -> RpcResponse:
        """取消当前计划

        Args:
            reason: 取消原因
        """
        return self._call("CancelPlan", {**self._meta(), "reason": reason, **kw})

    def check_pro_trial_eligibility(self, **kw) -> RpcResponse:
        """检查是否有 Pro 试用资格"""
        return self._call("CheckProTrialEligibility", {**self._meta(), **kw})

    def get_customer_portal(self, **kw) -> RpcResponse:
        """获取 Stripe 客户门户 URL"""
        return self._call("GetCustomerPortal", {**self._meta(), **kw})

    def get_plan_status(self, **kw) -> RpcResponse:
        """获取计划状态详情"""
        return self._call("GetPlanStatus", {**self._meta(), **kw})

    def get_stripe_subscription_state(self, **kw) -> RpcResponse:
        """获取 Stripe 订阅状态"""
        return self._call("GetStripeSubscriptionState", {**self._meta(), **kw})

    def get_usage_config(self, **kw) -> RpcResponse:
        """获取用量配置"""
        return self._call("GetUsageConfig", {**self._meta(), **kw})

    def get_user_subscription(self, **kw) -> RpcResponse:
        """获取用户订阅详情"""
        return self._call("GetUserSubscription", {**self._meta(), **kw})

    def initiate_top_up(self, *, amount: int = 0, **kw) -> RpcResponse:
        """发起额度充值

        Args:
            amount: 充值金额
        """
        return self._call("InitiateTopUp", {**self._meta(), "amount": amount, **kw})

    def purchase_cascade_credits(self, *, amount: int = 0, **kw) -> RpcResponse:
        """购买 Cascade 额度

        Args:
            amount: 购买数量
        """
        return self._call("PurchaseCascadeCredits", {**self._meta(), "amount": amount, **kw})

    def subscribe_to_plan(self, *, planId: str = "", **kw) -> RpcResponse:
        """订阅计划

        Args:
            planId: 计划 ID
        """
        return self._call("SubscribeToPlan", {**self._meta(), "planId": planId, **kw})

    def update_billing(self, *, billingEmail: str = "", **kw) -> RpcResponse:
        """更新计费信息

        Args:
            billingEmail: 计费邮箱
        """
        return self._call("UpdateBilling", {**self._meta(), "billingEmail": billingEmail, **kw})

    def update_credit_top_up_settings(self, *, enabled: bool = False,
                                      threshold: int = 0, amount: int = 0, **kw) -> RpcResponse:
        """更新额度自动充值设置

        Args:
            enabled: 是否启用自动充值
            threshold: 触发阈值
            amount: 每次充值金额
        """
        return self._call("UpdateCreditTopUpSettings", {
            **self._meta(), "enabled": enabled, "threshold": threshold, "amount": amount, **kw})

    def update_plan(self, *, planId: str = "", **kw) -> RpcResponse:
        """更新计划

        Args:
            planId: 新计划 ID
        """
        return self._call("UpdatePlan", {**self._meta(), "planId": planId, **kw})

    def update_seats(self, *, seats: int = 0, **kw) -> RpcResponse:
        """更新席位数

        Args:
            seats: 新席位数量
        """
        return self._call("UpdateSeats", {**self._meta(), "seats": seats, **kw})

    def usage_config(self, **kw) -> RpcResponse:
        """获取用量配置 (别名)"""
        return self._call("UsageConfig", {**self._meta(), **kw})

    # ── 用户账户 ──

    def check_email_for_sso(self, *, email: str = "", **kw) -> RpcResponse:
        """检查邮箱是否需要 SSO 登录

        Args:
            email: 用户邮箱
        """
        return self._call("CheckEmailForSSO", {**self._meta(), "email": email, **kw})

    def check_user_login_method(self, *, email: str = "", **kw) -> RpcResponse:
        """检查用户登录方式 (邮箱/SSO/OAuth)

        Args:
            email: 用户邮箱
        """
        return self._call("CheckUserLoginMethod", {**self._meta(), "email": email, **kw})

    def connect_github_account(self, *, token: str = "", **kw) -> RpcResponse:
        """关联 GitHub 账号

        Args:
            token: GitHub OAuth Token
        """
        return self._call("ConnectGithubAccount", {**self._meta(), "token": token, **kw})

    def connect_netlify_account(self, *, token: str = "", **kw) -> RpcResponse:
        """关联 Netlify 账号

        Args:
            token: Netlify OAuth Token
        """
        return self._call("ConnectNetlifyAccount", {**self._meta(), "token": token, **kw})

    def create_fb_user(self, *, firebaseIdToken: str = "", **kw) -> RpcResponse:
        """创建 Firebase 用户

        Args:
            firebaseIdToken: Firebase ID Token
        """
        return self._call("CreateFbUser", {**self._meta(), "firebaseIdToken": firebaseIdToken, **kw})

    def create_pkce_authorization_code(self, *, clientId: str = "", codeChallenge: str = "", **kw) -> RpcResponse:
        """创建 PKCE 授权码

        Args:
            clientId: OAuth Client ID
            codeChallenge: PKCE Code Challenge
        """
        return self._call("CreatePKCEAuthorizationCode", {
            **self._meta(), "clientId": clientId, "codeChallenge": codeChallenge, **kw})

    def delete_api_key(self, *, apiKeyId: str = "", **kw) -> RpcResponse:
        """删除 API Key

        Args:
            apiKeyId: 要删除的 API Key ID
        """
        return self._call("DeleteApiKey", {**self._meta(), "apiKeyId": apiKeyId, **kw})

    def delete_profile_picture(self, **kw) -> RpcResponse:
        """删除头像"""
        return self._call("DeleteProfilePicture", {**self._meta(), **kw})

    def delete_user(self, **kw) -> RpcResponse:
        """删除当前用户账号"""
        return self._call("DeleteUser", {**self._meta(), **kw})

    def delete_user_api_provider_key(self, *, provider: str = "", **kw) -> RpcResponse:
        """删除用户 API Provider Key

        Args:
            provider: 提供商名称
        """
        return self._call("DeleteUserApiProviderKey", {**self._meta(), "provider": provider, **kw})

    def disable_self_hosted_acu_billing(self, **kw) -> RpcResponse:
        """关闭自托管 ACU 计费"""
        return self._call("DisableSelfHostedAcuBilling", {**self._meta(), **kw})

    def disconnect_netlify_account(self, **kw) -> RpcResponse:
        """断开 Netlify 账号关联"""
        return self._call("DisconnectNetlifyAccount", {**self._meta(), **kw})

    def exchange_devin_code(self, *, code: str = "", **kw) -> RpcResponse:
        """兑换 Devin 授权码

        Args:
            code: Devin 授权码
        """
        return self._call("ExchangeDevinCode", {**self._meta(), "code": code, **kw})

    def exchange_pkce_authorization_code(self, *, code: str = "", codeVerifier: str = "", **kw) -> RpcResponse:
        """兑换 PKCE 授权码获取 Token

        Args:
            code: 授权码
            codeVerifier: PKCE Code Verifier
        """
        return self._call("ExchangePKCEAuthorizationCode", {
            **self._meta(), "code": code, "codeVerifier": codeVerifier, **kw})

    def get_api_key_summary(self, **kw) -> RpcResponse:
        """获取 API Key 摘要信息"""
        return self._call("GetApiKeySummary", {**self._meta(), **kw})

    def get_cascade_analytics(self, **kw) -> RpcResponse:
        """获取 Cascade 使用分析"""
        return self._call("GetCascadeAnalytics", {**self._meta(), **kw})

    def get_current_user(self, **kw) -> RpcResponse:
        """获取当前用户信息"""
        return self._call("GetCurrentUser", {**self._meta(), **kw})

    def get_github_access_token(self, **kw) -> RpcResponse:
        """获取已关联的 GitHub Access Token"""
        return self._call("GetGitHubAccessToken", {**self._meta(), **kw})

    def get_github_account_status(self, **kw) -> RpcResponse:
        """获取 GitHub 账号关联状态"""
        return self._call("GetGitHubAccountStatus", {**self._meta(), **kw})

    def get_license(self, **kw) -> RpcResponse:
        """获取许可证信息"""
        return self._call("GetLicense", {**self._meta(), **kw})

    def get_mucs_info(self, **kw) -> RpcResponse:
        """获取 MUCS (Multi-User Concurrent Sessions) 信息"""
        return self._call("GetMucsInfo", {**self._meta(), **kw})

    def get_netlify_account_status(self, **kw) -> RpcResponse:
        """获取 Netlify 账号关联状态"""
        return self._call("GetNetlifyAccountStatus", {**self._meta(), **kw})

    def get_one_time_auth_token(self, **kw) -> RpcResponse:
        """获取一次性认证 Token"""
        return self._call("GetOneTimeAuthToken", {**self._meta(), **kw})

    def get_primary_api_key_for_devs_only(self, **kw) -> RpcResponse:
        """[Dev] 获取主 API Key (仅开发用)"""
        return self._call("GetPrimaryApiKeyForDevsOnly", {**self._meta(), **kw})

    def get_profile_data(self, **kw) -> RpcResponse:
        """获取个人资料"""
        return self._call("GetProfileData", {**self._meta(), **kw})

    def get_profile_picture_presigned_upload_url(self, *, contentType: str = "", **kw) -> RpcResponse:
        """获取头像上传预签名 URL

        Args:
            contentType: 图片 MIME 类型 (如 "image/png")
        """
        return self._call("GetProfilePicturePresignedUploadUrl", {
            **self._meta(), "contentType": contentType, **kw})

    def get_self_devin_session_token(self, **kw) -> RpcResponse:
        """获取 Devin Session Token"""
        return self._call("GetSelfDevinSessionToken", {**self._meta(), **kw})

    def get_self_hosted_acu_config(self, **kw) -> RpcResponse:
        """获取自托管 ACU 配置"""
        return self._call("GetSelfHostedAcuConfig", {**self._meta(), **kw})

    def get_set_user_api_provider_keys(self, **kw) -> RpcResponse:
        """获取/设置用户 API Provider Keys"""
        return self._call("GetSetUserApiProviderKeys", {**self._meta(), **kw})

    def get_user_notifications(self, **kw) -> RpcResponse:
        """获取用户通知列表"""
        return self._call("GetUserNotifications", {**self._meta(), **kw})

    def get_wrapped2024(self, **kw) -> RpcResponse:
        """获取 2024 年度总结"""
        return self._call("GetWrapped2024", {**self._meta(), **kw})

    def is_valid_referral_code(self, *, referralCode: str = "", **kw) -> RpcResponse:
        """验证推荐码是否有效

        Args:
            referralCode: 推荐码
        """
        return self._call("IsValidReferralCode", {**self._meta(), "referralCode": referralCode, **kw})

    def log_out_user(self, **kw) -> RpcResponse:
        """登出用户"""
        return self._call("LogOutUser", {**self._meta(), **kw})

    def migrate_api_key(self, **kw) -> RpcResponse:
        """迁移 API Key (旧版升级)"""
        return self._call("MigrateApiKey", {**self._meta(), **kw})

    def process_referral_code(self, *, referralCode: str = "", **kw) -> RpcResponse:
        """处理推荐码 (兑换)

        Args:
            referralCode: 推荐码
        """
        return self._call("ProcessReferralCode", {**self._meta(), "referralCode": referralCode, **kw})

    def profile_picture_upload_complete(self, **kw) -> RpcResponse:
        """通知头像上传完成"""
        return self._call("ProfilePictureUploadComplete", {**self._meta(), **kw})

    def send_email_verification(self, **kw) -> RpcResponse:
        """发送邮箱验证邮件"""
        return self._call("SendEmailVerification", {**self._meta(), **kw})

    def set_self_hosted_acu_config(self, *, config: dict = None, **kw) -> RpcResponse:
        """设置自托管 ACU 配置

        Args:
            config: ACU 配置字典
        """
        return self._call("SetSelfHostedAcuConfig", {**self._meta(), "config": config or {}, **kw})

    def set_user_api_provider_key(self, *, provider: str = "", apiKey: str = "", **kw) -> RpcResponse:
        """设置用户 API Provider Key

        Args:
            provider: 提供商名称
            apiKey: API Key
        """
        return self._call("SetUserApiProviderKey", {**self._meta(), "provider": provider, "apiKey": apiKey, **kw})

    def update_cli_access(self, *, enabled: bool = False, **kw) -> RpcResponse:
        """更新 CLI 访问权限

        Args:
            enabled: 是否启用
        """
        return self._call("UpdateCliAccess", {**self._meta(), "enabled": enabled, **kw})

    def update_code_snippet_telemetry(self, *, enabled: bool = False, **kw) -> RpcResponse:
        """更新代码片段遥测设置

        Args:
            enabled: 是否启用
        """
        return self._call("UpdateCodeSnippetTelemetry", {**self._meta(), "enabled": enabled, **kw})

    def update_codeium_access(self, *, enabled: bool = False, **kw) -> RpcResponse:
        """更新 Codeium 访问权限

        Args:
            enabled: 是否启用
        """
        return self._call("UpdateCodeiumAccess", {**self._meta(), "enabled": enabled, **kw})

    def update_inbound_source(self, *, source: str = "", **kw) -> RpcResponse:
        """更新来源渠道

        Args:
            source: 渠道标识
        """
        return self._call("UpdateInboundSource", {**self._meta(), "source": source, **kw})

    def update_name(self, *, name: str = "", **kw) -> RpcResponse:
        """更新用户名

        Args:
            name: 新用户名
        """
        return self._call("UpdateName", {**self._meta(), "name": name, **kw})

    def update_occupation(self, *, occupation: str = "", **kw) -> RpcResponse:
        """更新职业信息

        Args:
            occupation: 职业
        """
        return self._call("UpdateOccupation", {**self._meta(), "occupation": occupation, **kw})

    def update_profile(self, *, name: str = "", occupation: str = "", **kw) -> RpcResponse:
        """更新个人资料

        Args:
            name: 显示名称
            occupation: 职业
        """
        return self._call("UpdateProfile", {**self._meta(), "name": name, "occupation": occupation, **kw})

    def windsurf_post_auth(self, *, firebaseIdToken: str = "", **kw) -> RpcResponse:
        """Windsurf 登录后回调

        Args:
            firebaseIdToken: Firebase ID Token
        """
        return self._call("WindsurfPostAuth", {**self._meta(), "firebaseIdToken": firebaseIdToken, **kw})

    # ── SSO ──

    def get_sso_provider(self, *, teamId: str = "", **kw) -> RpcResponse:
        """获取 SSO 提供商配置

        Args:
            teamId: 团队 ID
        """
        return self._call("GetSSOProvider", {**self._meta(), "teamId": teamId, **kw})

    def save_sso_provider(self, *, teamId: str = "", provider: dict = None, **kw) -> RpcResponse:
        """保存 SSO 提供商配置

        Args:
            teamId: 团队 ID
            provider: SSO 配置 (含 entityId, ssoUrl, certificate 等)
        """
        return self._call("SaveSSOProvider", {**self._meta(), "teamId": teamId, "provider": provider or {}, **kw})

    def show_sso_add_on(self, **kw) -> RpcResponse:
        """检查 SSO 附加功能是否可用"""
        return self._call("ShowSSOAddOn", {**self._meta(), **kw})

    def user_sso_login_redirect(self, *, email: str = "", **kw) -> RpcResponse:
        """获取 SSO 登录重定向 URL

        Args:
            email: 用户邮箱
        """
        return self._call("UserSSOLoginRedirect", {**self._meta(), "email": email, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)
