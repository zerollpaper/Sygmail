import os
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import yagmail

DEFAULT_SUBJECT = "Process Completed"
DEFAULT_CONTENTS_TEMPLATE = "{script_name} has finished running."

ENV_KEYS = {
    "from_addr": "SYGMAIL_FROM",
    "app_password": "SYGMAIL_APP_PASSWORD",
    "to": "SYGMAIL_TO",
    "subject": "SYGMAIL_SUBJECT",
    "contents": "SYGMAIL_CONTENTS",
    "attachments_path": "SYGMAIL_ATTACHMENTS_PATH",
}


@dataclass
class SygmailConfig:
    from_addr: Optional[str] = None
    app_password: Optional[str] = None
    to: Optional[str] = None
    subject: Optional[str] = None
    contents: Optional[str] = None
    attachments_path: Optional[str] = None

    @classmethod
    def load(cls, env_path: str = ".env") -> "SygmailConfig":
        file_values = _read_env_file(env_path)
        values = {**file_values}
        for field, key in ENV_KEYS.items():
            env_value = os.environ.get(key)
            if env_value is None:
                env_value = os.environ.get(key.lower())
            if env_value is not None:
                values[field] = env_value
        return cls(
            from_addr=values.get("from_addr"),
            app_password=values.get("app_password"),
            to=values.get("to"),
            subject=values.get("subject"),
            contents=values.get("contents"),
            attachments_path=values.get("attachments_path"),
        )

    def save(self, env_path: str = ".env") -> None:
        data = {
            ENV_KEYS["from_addr"]: self.from_addr or "",
            ENV_KEYS["app_password"]: self.app_password or "",
            ENV_KEYS["to"]: self.to or "",
            ENV_KEYS["subject"]: self.subject or DEFAULT_SUBJECT,
            ENV_KEYS["contents"]: self.contents or DEFAULT_CONTENTS_TEMPLATE,
        }
        if self.attachments_path is not None:
            data[ENV_KEYS["attachments_path"]] = self.attachments_path
        _write_env_file(env_path, data)

    def reset_subject_contents(self) -> None:
        self.subject = DEFAULT_SUBJECT
        self.contents = DEFAULT_CONTENTS_TEMPLATE


class Sygmail:
    def __init__(self, config: Optional[SygmailConfig] = None, env_path: str = ".env") -> None:
        self.env_path = env_path
        self.config = config or SygmailConfig.load(env_path)

    def configure(
        self,
        *,
        from_addr: Optional[str] = None,
        from_: Optional[str] = None,
        app_password: Optional[str] = None,
        to: Optional[str] = None,
        subject: Optional[str] = None,
        contents: Optional[str] = None,
        attachments_path: Optional[str] = None,
        persist: bool = True,
    ) -> None:
        if from_addr is None and from_ is not None:
            from_addr = from_
        if from_addr is not None:
            self.config.from_addr = from_addr
        if app_password is not None:
            self.config.app_password = app_password
        if to is not None:
            self.config.to = to
        if subject is not None:
            self.config.subject = subject
        if contents is not None:
            self.config.contents = contents
        if attachments_path is not None:
            self.config.attachments_path = attachments_path
        if persist:
            self.config.save(self.env_path)

    def reset_subject_contents(self, persist: bool = True) -> None:
        self.config.reset_subject_contents()
        if persist:
            self.config.save(self.env_path)

    def send(
        self,
        *,
        from_addr: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        subject: Optional[str] = None,
        contents: Optional[str] = None,
        attachments: Optional[Iterable[str]] = None,
        attachments_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        resolved_from = from_addr or from_ or self.config.from_addr
        app_password = self.config.app_password
        target = to or self.config.to or resolved_from

        if not resolved_from or not app_password or not target:
            raise ValueError("from_addr and app_password are required")

        script_name = _get_script_name()
        subject_value = subject or self.config.subject or DEFAULT_SUBJECT
        contents_value = contents or self.config.contents or DEFAULT_CONTENTS_TEMPLATE
        contents_value = _render_contents(contents_value, script_name)

        attachments_list = _normalize_attachments(attachments)
        path_value = attachments_path or self.config.attachments_path
        if attachments is None and path_value:
            attachments_list.extend(_collect_attachments(path_value))

        yag = yagmail.SMTP(resolved_from, app_password)
        yag.send(
            to=target,
            subject=subject_value,
            contents=contents_value,
            attachments=attachments_list if attachments_list else None,
            **kwargs,
        )


def _get_script_name() -> str:
    raw = sys.argv[0] if sys.argv and sys.argv[0] else "script"
    return os.path.basename(raw)


def _render_contents(contents: str, script_name: str) -> str:
    if "{script_name}" in contents:
        try:
            return contents.format(script_name=script_name)
        except Exception:
            return contents
    return contents


def _normalize_attachments(attachments: Optional[Iterable[str]]) -> List[str]:
    if not attachments:
        return []
    if isinstance(attachments, (str, bytes, os.PathLike)):
        existing, missing = _filter_existing_paths([str(attachments)])
        _warn_missing_attachments(missing)
        return existing
    existing, missing = _filter_existing_paths([str(item) for item in attachments])
    _warn_missing_attachments(missing)
    return existing


def _collect_attachments(attachments_path: str) -> List[str]:
    path = Path(attachments_path)
    if not path.exists():
        _warn_missing_attachments([str(path)])
        return []
    if path.is_file():
        existing, missing = _filter_existing_paths([str(path)])
        _warn_missing_attachments(missing)
        return existing
    existing, missing = _filter_existing_paths([str(child) for child in path.iterdir() if child.is_file()])
    _warn_missing_attachments(missing)
    return existing


def _filter_existing_paths(paths: Iterable[str]) -> tuple[List[str], List[str]]:
    existing: List[str] = []
    missing: List[str] = []
    for value in paths:
        try:
            if Path(value).is_file():
                existing.append(value)
            else:
                missing.append(value)
        except OSError:
            missing.append(value)
    return existing, missing


def _warn_missing_attachments(paths: Iterable[str]) -> None:
    missing = [path for path in paths if path]
    if not missing:
        return
    joined = ", ".join(missing)
    warnings.warn(f"missing attachments ignored: {joined}", stacklevel=3)


def _read_env_file(env_path: str) -> dict:
    path = Path(env_path)
    if not path.exists():
        return {}

    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if not key:
            continue
        normalized_key = _normalize_env_key(key)
        if normalized_key in ENV_KEYS.values():
            field = _env_key_to_field(normalized_key)
            if field:
                values[field] = value
    return values


def _write_env_file(env_path: str, data: dict) -> None:
    path = Path(env_path)
    lines = [f"{key}={value}" for key, value in data.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _normalize_env_key(key: str) -> str:
    return key.upper()


def _env_key_to_field(env_key: str) -> Optional[str]:
    for field, key in ENV_KEYS.items():
        if key == env_key:
            return field
    return None
