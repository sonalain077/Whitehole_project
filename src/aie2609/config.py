"""Load only the project's API key from a local file, without executing its contents."""

import os
from pathlib import Path

from .errors import RunError


def load_local_api_key(path: Path = Path(".env")) -> None:
    """Existing nonempty environment values take priority; never search parent folders."""
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            content = stream.read(65537)
    except FileNotFoundError:
        return
    except (OSError, UnicodeError):
        raise RunError("Cannot read the local .env file as UTF-8.") from None
    if len(content) > 65536:
        raise RunError("Local .env file exceeds the size limit.")

    key = None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if name.strip() != "OPENAI_API_KEY":
            continue  # Other settings cannot change the model, endpoint or budget.
        if not separator or key is not None:
            raise RunError("Use exactly one OPENAI_API_KEY=value assignment in .env.")
        value = value.strip()
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise RunError("Invalid quoting for OPENAI_API_KEY in .env.")
            value = value[1:-1]
        if any(ord(char) < 33 or ord(char) > 126 or char in "\"'" for char in value):
            raise RunError("Invalid characters in the .env API key; use a single line.")
        key = value
    if key:
        os.environ["OPENAI_API_KEY"] = key
