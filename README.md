# sygmail

Lightweight wrapper for sending Gmail notifications with simple defaults and a .env config.

## Features

- Load settings from `.env` and environment variables
- Save settings from code (`persist=True`)
- Defaults for subject/contents with `{script_name}` placeholder
- Optional auto-attachments from a path

## Install

```
pip install sygmail
```

## Requirements

- Python 3.9+
- Dependency: `yagmail`

## Quick start

```python
from sygmail import Sygmail

syg = Sygmail()
syg.configure(
    from_addr="you@gmail.com",
    app_password="app-password",
    persist=True,
)
syg.send()
```

## .env keys

```
SYGMAIL_FROM=you@gmail.com
SYGMAIL_APP_PASSWORD=app-password
SYGMAIL_TO=to@example.com
SYGMAIL_SUBJECT=Process Completed
SYGMAIL_CONTENTS={script_name} has finished running.
SYGMAIL_ATTACHMENTS_PATH=./a/
```

## Defaults

- Subject: `Process Completed`
- Contents: `{script_name} has finished running.`

Reset back to defaults:

```python
syg.reset_subject_contents(persist=True)
```

## Attachments behavior

- If `attachments` is provided in `send()`, it is used as-is.
- If `attachments` is not provided, and `SYGMAIL_ATTACHMENTS_PATH` is set,
  files under that path are attached (files only, no folders).

Examples:

```python
syg.send(attachments=["./a/file.txt"])  # use only this
syg.send(attachments=[])               # explicitly no attachments
syg.send()                             # auto-attach from SYGMAIL_ATTACHMENTS_PATH if set
```

## CLI

Use `python -m sygmail` for now:

```
python -m sygmail send
```

Options:

```
python -m sygmail send \
    --env .env \
    --from you@gmail.com \
    --to to@example.com \
    --subject "Process Completed" \
    --contents "[sygmail notification]" \
    --attachments ./path/to/file \
    --attachments-path ./path/to/folder/
```

- If `--contents` is omitted, CLI uses `[sygmail notification]` without editing `.env`.

Common examples:

```
python -m sygmail send

python -m sygmail send --subject "Job Done" --contents "[sygmail notification]"

python -m sygmail send --attachments ./a/a.txt ./a/b.txt

python -m sygmail config set --from you@gmail.com --app-password "app-password"

python -m sygmail config show
```

Config commands:

```
python -m sygmail config set \
    --env .env \
    --from you@gmail.com \
    --app-password "app-password" \
    --to to@example.com \
    --subject "Process Completed" \
    --contents "{script_name} has finished running." \
    --attachments-path ./a/

python -m sygmail config reset --env .env

python -m sygmail config show --env .env

python -m sygmail config show --env .env --raw
```

## API

```python
Sygmail(env_path=".env")
Sygmail.configure(
    from_addr=None,
    from_=None,
    app_password=None,
    to=None,
    subject=None,
    contents=None,
    attachments_path=None,
    persist=True,
)
Sygmail.reset_subject_contents(persist=True)
Sygmail.send(
    from_addr=None,
    from_=None,
    to=None,
    subject=None,
    contents=None,
    attachments=None,
    attachments_path=None,
    **kwargs,
)
```

## Notes

- Use a Gmail app password (not your normal password).
- Settings are stored in `.env` in the current working directory by default.
- If `to` is omitted, the message is sent to the same address as `from_addr`.

## Security

- Do not commit `.env` to public repos.
- Treat app passwords like secrets.

## Operations

- Prefer `chmod 600 .env` on shared machines.
- Use `--env` to separate configs per project.
