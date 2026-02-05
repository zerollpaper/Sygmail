import argparse
import sys
from typing import List, Optional

from .client import Sygmail

CLI_DEFAULT_CONTENTS = "[sygmail notification]"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sygmail", description="Send Gmail notifications.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send", help="Send a notification email")
    send_parser.add_argument("--env", default=".env", help="Path to .env file")
    send_parser.add_argument("--from", dest="from_addr", help="From address")
    send_parser.add_argument("--to", help="To address")
    send_parser.add_argument("--subject", help="Email subject")
    send_parser.add_argument("--contents", help="Email contents")
    send_parser.add_argument(
        "--attachments",
        nargs="*",
        default=None,
        help="Attachment file paths",
    )
    send_parser.add_argument(
        "--attachments-path",
        dest="attachments_path",
        help="Path to auto-attach files",
    )

    config_parser = subparsers.add_parser("config", help="Manage .env configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)

    config_set_parser = config_subparsers.add_parser("set", help="Set config values")
    config_set_parser.add_argument("--env", default=".env", help="Path to .env file")
    config_set_parser.add_argument("--from", dest="from_addr", help="From address")
    config_set_parser.add_argument("--app-password", help="Gmail app password")
    config_set_parser.add_argument("--to", help="To address")
    config_set_parser.add_argument("--subject", help="Email subject")
    config_set_parser.add_argument("--contents", help="Email contents")
    config_set_parser.add_argument(
        "--attachments-path",
        dest="attachments_path",
        help="Path to auto-attach files",
    )

    config_reset_parser = config_subparsers.add_parser(
        "reset",
        help="Reset subject/contents to defaults",
    )
    config_reset_parser.add_argument("--env", default=".env", help="Path to .env file")

    config_show_parser = config_subparsers.add_parser(
        "show",
        help="Show current config values",
    )
    config_show_parser.add_argument("--env", default=".env", help="Path to .env file")
    config_show_parser.add_argument(
        "--raw",
        action="store_true",
        help="Show secrets without masking",
    )

    return parser


def run_send(args: argparse.Namespace) -> int:
    syg = Sygmail(env_path=args.env)

    contents = args.contents
    if contents is None:
        contents = CLI_DEFAULT_CONTENTS

    attachments = _normalize_attachments_arg(args.attachments)

    syg.send(
        from_addr=args.from_addr,
        to=args.to,
        subject=args.subject,
        contents=contents,
        attachments=attachments,
        attachments_path=args.attachments_path,
    )
    return 0


def _normalize_attachments_arg(raw: Optional[List[str]]) -> Optional[List[str]]:
    if raw is None:
        return None
    if len(raw) == 0:
        return []
    return raw


def _mask_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def run_config_set(args: argparse.Namespace) -> int:
    syg = Sygmail(env_path=args.env)
    syg.configure(
        from_addr=args.from_addr,
        app_password=args.app_password,
        to=args.to,
        subject=args.subject,
        contents=args.contents,
        attachments_path=args.attachments_path,
        persist=True,
    )
    return 0


def run_config_reset(args: argparse.Namespace) -> int:
    syg = Sygmail(env_path=args.env)
    syg.reset_subject_contents(persist=True)
    return 0


def run_config_show(args: argparse.Namespace) -> int:
    syg = Sygmail(env_path=args.env)
    config = syg.config

    app_password = config.app_password
    if not args.raw:
        app_password = _mask_secret(app_password)

    print(f"SYGMAIL_FROM={config.from_addr or ''}")
    print(f"SYGMAIL_APP_PASSWORD={app_password or ''}")
    print(f"SYGMAIL_TO={config.to or ''}")
    print(f"SYGMAIL_SUBJECT={config.subject or ''}")
    print(f"SYGMAIL_CONTENTS={config.contents or ''}")
    print(f"SYGMAIL_ATTACHMENTS_PATH={config.attachments_path or ''}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "send":
        return run_send(args)
    if args.command == "config":
        if args.config_command == "set":
            return run_config_set(args)
        if args.config_command == "reset":
            return run_config_reset(args)
        if args.config_command == "show":
            return run_config_show(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
