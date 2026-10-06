"""Optional per-model, per-provider overrides for reasoning-model handling.

The runners key their reasoning handling (system prompt choice and the
request fields that turn thinking off) on Berget's exact model ids. Other
providers serve the same model under other ids, and the switch that turns
thinking off differs per provider. A JSON file named by EVAL_MODEL_PROFILES
overrides the built-in handling for the models it lists; with the env var
unset, behaviour is unchanged.

File format:

    {"profiles": [
      {"model": "moonshotai/kimi-k3",                  # required, exact id sent
       "api_base": "https://api.tensorx.ai/v1",        # optional, any provider if omitted
       "reasoning_model": true,                        # required
       "thinking_off": {"chat_template_kwargs": {"enable_thinking": false}},
       "note": "free text, ignored"}
    ]}

thinking_off holds top-level request-body fields (default {}: nothing extra).
An entry whose api_base matches the run's base URL beats one without
api_base. A matching profile fully replaces the built-in handling.
"""
import copy
import hashlib
import json
import os
from pathlib import Path

ENV_VAR = "EVAL_MODEL_PROFILES"

DEFAULT_THINKING_OFF = {"chat_template_kwargs": {"enable_thinking": False}}

# key -> (accepted type, required)
_FIELDS = {
    "model": (str, True),
    "api_base": (str, False),
    "reasoning_model": (bool, True),
    "thinking_off": (dict, False),
    "note": (str, False),
}

_cache = None  # (path, raw bytes, validated entries) once loaded


def _norm_base(api_base):
    return api_base.rstrip("/")


def _validate(path, data):
    if not isinstance(data, dict) or set(data) != {"profiles"}:
        raise ValueError(f"{path}: top level must be an object with only a 'profiles' key")
    entries = data["profiles"]
    if not isinstance(entries, list):
        raise ValueError(f"{path}: 'profiles' must be a list")
    seen = {}
    for i, entry in enumerate(entries):
        where = f"{path}: profiles[{i}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{where}: entry must be an object")
        unknown = sorted(set(entry) - set(_FIELDS))
        if unknown:
            raise ValueError(f"{where}: unknown key(s) {unknown}")
        for key, (typ, required) in _FIELDS.items():
            if key not in entry:
                if required:
                    raise ValueError(f"{where}: missing required key '{key}'")
                continue
            if not isinstance(entry[key], typ):
                raise ValueError(f"{where}: '{key}' must be {typ.__name__}")
        base = entry.get("api_base")
        key = (entry["model"], _norm_base(base) if base is not None else None)
        if key in seen:
            raise ValueError(
                f"{where}: duplicate of profiles[{seen[key]}] "
                f"(model={key[0]!r}, api_base={key[1]!r})"
            )
        seen[key] = i
    return entries


def load():
    """Read and validate the profile file once; [] when the env var is unset."""
    global _cache
    path = os.environ.get(ENV_VAR)
    if not path:
        return []
    if _cache is None or _cache[0] != path:
        raw = Path(path).read_bytes()
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"{path}: invalid JSON: {e}") from e
        _cache = (path, raw, _validate(path, data))
    return _cache[2]


def lookup(model, api_base):
    """The profile for model at api_base, or None. api_base match wins."""
    base = _norm_base(api_base)
    fallback = None
    for entry in load():
        if entry["model"] != model:
            continue
        if "api_base" not in entry:
            fallback = entry
        elif _norm_base(entry["api_base"]) == base:
            return entry
    return fallback


def is_reasoning_model(model, api_base, builtin):
    profile = lookup(model, api_base)
    if profile is not None:
        return profile["reasoning_model"]
    return model in builtin


def thinking_off_fields(model, api_base, builtin):
    """Top-level request-body fields that turn thinking off for model."""
    # Copies, so callers that mutate the request body cannot alter the profile.
    profile = lookup(model, api_base)
    if profile is not None:
        return copy.deepcopy(profile.get("thinking_off", {}))
    if model in builtin:
        return copy.deepcopy(DEFAULT_THINKING_OFF)
    return {}


def provenance():
    """run.json record of the profile file, or None when the env var is unset."""
    if not os.environ.get(ENV_VAR):
        return None
    entries = load()
    path, raw, _ = _cache
    return {
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "profiles": copy.deepcopy(entries),
    }
