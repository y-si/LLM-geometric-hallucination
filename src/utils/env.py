"""Explicit .env loading.

The repo's convention has been to assume the shell exported credentials before
invoking a script (`set -a && source .env`), which fails silently in any context
where that chaining doesn't happen — the script then gets api_key=None and the
provider SDK raises a confusing error about a *different* missing variable
(OPENAI_API_KEY when you meant TOGETHER_API_KEY).

Loading is explicit rather than an import side effect: research scripts should say
out loud where their credentials came from.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent


def load_env_file(path=None, override=False, required=()):
    """Load KEY=VALUE lines from a .env file into os.environ.

    Args:
        path: .env location. Defaults to the repo root's .env.
        override: If False (default), existing environment variables win, so an
            explicitly exported value beats the file.
        required: Variable names that must be non-empty afterward. Raises
            RuntimeError listing every missing one.

    Returns:
        Names of the variables this call set (never their values).
    """
    env_path = Path(path) if path else BASE_DIR / ".env"
    loaded = []

    if env_path.exists():
        with open(env_path) as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                if key.startswith("export "):
                    key = key[len("export "):].strip()
                value = value.strip().strip("\"'")
                if not value:
                    continue
                if override or not os.environ.get(key):
                    os.environ[key] = value
                    loaded.append(key)

    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            f"Missing required credential(s): {', '.join(missing)}.\n"
            f"Looked for {env_path}"
            f"{' (exists)' if env_path.exists() else ' (DOES NOT EXIST)'}.\n"
            "Add a line like NAME=value to that file, or export it in your shell."
        )

    return loaded
