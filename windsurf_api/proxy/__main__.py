"""反代命令行入口

用法:
    python -m windsurf_api.proxy --keys sk-ws-key1,sk-ws-key2 --port 8080
    python -m windsurf_api.proxy --key-file keys.txt --port 8080 --auth my-token
"""
import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(
        description="Windsurf → OpenAI 兼容反代服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个 Key
  python -m windsurf_api.proxy --keys sk-ws-xxx --port 8080

  # 多个 Key (逗号分隔)
  python -m windsurf_api.proxy --keys sk-ws-key1,sk-ws-key2,sk-ws-key3

  # 从文件加载 Key (每行一个)
  python -m windsurf_api.proxy --key-file keys.txt

  # 带认证 token (客户端需要 Authorization: Bearer xxx)
  python -m windsurf_api.proxy --keys sk-ws-xxx --auth my-secret-token

  # 然后用 OpenAI SDK:
  import openai
  client = openai.OpenAI(base_url="http://localhost:8080/v1", api_key="my-secret-token")
  resp = client.chat.completions.create(
      model="claude-sonnet-4-20250514",
      messages=[{"role": "user", "content": "Hello!"}],
      stream=True
  )
""",
    )

    parser.add_argument("--keys", "-k", type=str, default="",
                        help="API Key 列表 (逗号分隔)")
    parser.add_argument("--key-file", "-f", type=str, default="",
                        help="Key 文件路径 (每行一个 Key)")
    parser.add_argument("--port", "-p", type=int, default=8080,
                        help="监听端口 (默认 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="监听地址 (默认 0.0.0.0)")
    parser.add_argument("--auth", "-a", type=str, default="",
                        help="客户端认证 token (可选)")
    parser.add_argument("--server", "-s", type=str,
                        default="https://server.self-serve.windsurf.com",
                        help="Windsurf API 服务器地址")
    parser.add_argument("--cooldown", type=int, default=60,
                        help="Key 错误冷却秒数 (默认 60)")
    parser.add_argument("--max-errors", type=int, default=10,
                        help="Key 连续错误阈值 (默认 10)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="打印详细请求日志")

    args = parser.parse_args()

    # 收集 Keys
    keys = []
    if args.keys:
        keys.extend([k.strip() for k in args.keys.split(",") if k.strip()])
    if args.key_file:
        if os.path.exists(args.key_file):
            with open(args.key_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        keys.append(line)
        else:
            print(f"❌ Key 文件不存在: {args.key_file}", file=sys.stderr)
            sys.exit(1)

    # 环境变量补充
    env_keys = os.environ.get("WINDSURF_KEYS", "")
    if env_keys:
        keys.extend([k.strip() for k in env_keys.split(",") if k.strip()])

    if not keys:
        print("❌ 没有提供 API Key!", file=sys.stderr)
        print("   用 --keys sk-ws-xxx 或 --key-file keys.txt 或设置 WINDSURF_KEYS 环境变量",
              file=sys.stderr)
        sys.exit(1)

    # 去重
    keys = list(dict.fromkeys(keys))

    print(f"📦 加载了 {len(keys)} 个 API Key")

    # 启动
    from .server import ProxyServer

    server = ProxyServer(
        keys=keys,
        port=args.port,
        host=args.host,
        server_url=args.server,
        auth_token=args.auth,
        cooldown=args.cooldown,
        max_errors=args.max_errors,
        verbose=args.verbose,
    )
    server.start()


if __name__ == "__main__":
    main()
