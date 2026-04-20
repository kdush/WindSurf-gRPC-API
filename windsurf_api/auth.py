"""Firebase 认证

Windsurf 使用 Firebase Authentication:
  - 支持 Google / GitHub / Microsoft OAuth
  - 注册/登录后拿到 Firebase ID Token
  - 用 ID Token 调用 RegisterUser 拿到 API Key

协议细节 (逆向自 extension.js):
  - Firebase API Key: AIzaSyDsOl-1XpT5err0Tcnx8FFod1H8gVGIycY
  - signInWithIdp: 用 OAuth token 登录
  - token endpoint: 用 refresh_token 换新 id_token
"""
from dataclasses import dataclass
from typing import Optional
from .transport import http_post, RpcResponse

FIREBASE_API_KEY = "AIzaSyDsOl-1XpT5err0Tcnx8FFod1H8gVGIycY"
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1"
FIREBASE_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"

GOOGLE_CLIENT_ID = "957777847521-egrk5uakal87pjkqctk89fe7b7qtd1dq.apps.googleusercontent.com"
REDIRECT_URI = "https://windsurf.com/login"

PROVIDERS = {
    "google":    {"providerId": "google.com",    "tokenField": "id_token"},
    "github":    {"providerId": "github.com",    "tokenField": "access_token"},
    "microsoft": {"providerId": "microsoft.com", "tokenField": "id_token"},
}


@dataclass
class FirebaseUser:
    """Firebase 认证结果"""
    id_token: str
    refresh_token: str
    email: str
    local_id: str = ""
    display_name: str = ""
    provider: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.id_token)


def _firebase_call(endpoint: str, payload: dict) -> RpcResponse:
    """调用 Firebase REST API"""
    url = f"{FIREBASE_AUTH_URL}/{endpoint}?key={FIREBASE_API_KEY}"
    return http_post(url, payload, headers={
        "Referer": "https://windsurf.com/",
        "Origin": "https://windsurf.com",
    })


def oauth_login(provider: str, token: str) -> FirebaseUser:
    """用第三方 OAuth token 登录 Firebase

    Args:
        provider: "google" | "github" | "microsoft"
        token: OAuth access_token 或 id_token

    Returns:
        FirebaseUser (检查 .ok 判断是否成功)

    Raises:
        ValueError: 不支持的 provider
    """
    if provider not in PROVIDERS:
        raise ValueError(f"不支持的 provider: {provider}. 可用: {list(PROVIDERS.keys())}")

    cfg = PROVIDERS[provider]
    post_body = f"{cfg['tokenField']}={token}&providerId={cfg['providerId']}"

    r = _firebase_call("accounts:signInWithIdp", {
        "postBody": post_body,
        "requestUri": REDIRECT_URI,
        "returnIdpCredential": True,
        "returnSecureToken": True,
    })

    if not r.ok:
        return FirebaseUser(id_token="", refresh_token="", email="",
                           display_name=str(r.data)[:200], provider=provider)

    d = r.data if isinstance(r.data, dict) else {}
    return FirebaseUser(
        id_token=d.get("idToken", ""),
        refresh_token=d.get("refreshToken", ""),
        email=d.get("email", ""),
        local_id=d.get("localId", ""),
        display_name=d.get("displayName", ""),
        provider=provider,
    )


def email_signup(email: str, password: str) -> FirebaseUser:
    """邮箱密码注册"""
    r = _firebase_call("accounts:signUp", {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    })
    if not r.ok:
        return FirebaseUser(id_token="", refresh_token="", email=email,
                           display_name=str(r.data)[:200])
    d = r.data if isinstance(r.data, dict) else {}
    return FirebaseUser(
        id_token=d.get("idToken", ""),
        refresh_token=d.get("refreshToken", ""),
        email=d.get("email", email),
        local_id=d.get("localId", ""),
        provider="email",
    )


def email_login(email: str, password: str) -> FirebaseUser:
    """邮箱密码登录"""
    r = _firebase_call("accounts:signInWithPassword", {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    })
    if not r.ok:
        return FirebaseUser(id_token="", refresh_token="", email=email,
                           display_name=str(r.data)[:200])
    d = r.data if isinstance(r.data, dict) else {}
    return FirebaseUser(
        id_token=d.get("idToken", ""),
        refresh_token=d.get("refreshToken", ""),
        email=d.get("email", email),
        local_id=d.get("localId", ""),
        provider="email",
    )


def refresh_token(refresh_tok: str) -> Optional[FirebaseUser]:
    """用 refresh_token 换新的 id_token"""
    url = f"{FIREBASE_TOKEN_URL}?key={FIREBASE_API_KEY}"
    r = http_post(url, f"grant_type=refresh_token&refresh_token={refresh_tok}", headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://windsurf.com/",
    })
    if not r.ok:
        return None
    d = r.data if isinstance(r.data, dict) else {}
    return FirebaseUser(
        id_token=d.get("id_token", ""),
        refresh_token=d.get("refresh_token", ""),
        email="",
        local_id=d.get("user_id", ""),
        provider="refresh",
    )


def check_providers() -> dict:
    """检测 Firebase 支持哪些 OAuth providers"""
    results = {}
    for name, cfg in PROVIDERS.items():
        body = f"{cfg['tokenField']}=test_token&providerId={cfg['providerId']}"
        r = _firebase_call("accounts:signInWithIdp", {
            "postBody": body,
            "requestUri": REDIRECT_URI,
            "returnIdpCredential": True,
            "returnSecureToken": True,
        })
        err = str(r.data) if r.data else ""
        if "OPERATION_NOT_ALLOWED" in err:
            results[name] = "disabled"
        elif "INVALID_IDP_RESPONSE" in err or "INVALID_CREDENTIAL" in err:
            results[name] = "enabled"
        elif "BLOCKING_FUNCTION" in err:
            results[name] = "blocked_by_cloud_function"
        else:
            results[name] = err[:100]
    return results
