"""Base class for all skills. Provides schema definition and input validation."""

from typing import Any


class BaseSkill:
    """Base class for all skills managed by SkillManager.

    Subclasses should override `parameters` with a list of parameter
    schema dicts ({"name": str, "type": str, "description": str, ...}).
    """

    parameters: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def get_schema(self) -> list[dict[str, Any]]:
        """Return the expected parameters schema for this skill."""
        return self.parameters

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize arguments against the skill's parameter schema.

        Raises ValueError on missing required params or unresolvable type errors.
        Returns a sanitized dict with only known parameters.
        """
        schema = self.get_schema()
        if not schema:
            return args

        validated: dict[str, Any] = {}

        for param in schema:
            pname = param["name"]
            ptype = param.get("type", "string")
            has_default = "default" in param

            if pname not in args:
                if not has_default:
                    raise ValueError(f"Missing required parameter: {pname}")
                validated[pname] = param["default"]
                continue

            raw = args[pname]

            # Type coercion with safety — never silently corrupt data
            try:
                if ptype == "string":
                    validated[pname] = str(raw)
                elif ptype == "integer":
                    validated[pname] = int(float(raw)) if isinstance(raw, str) else int(raw)
                elif ptype == "number":
                    validated[pname] = float(raw)
                elif ptype == "boolean":
                    if isinstance(raw, str):
                        validated[pname] = raw.lower() in ("true", "1", "yes")
                    else:
                        validated[pname] = bool(raw)
                elif ptype == "list":
                    if isinstance(raw, str):
                        import json as _json
                        validated[pname] = _json.loads(raw)
                    else:
                        validated[pname] = list(raw)
                elif ptype == "object":
                    if isinstance(raw, str):
                        import json as _json
                        validated[pname] = _json.loads(raw)
                    else:
                        validated[pname] = dict(raw)
                else:
                    validated[pname] = raw
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Parameter '{pname}': cannot coerce {raw!r} to {ptype}: {exc}"
                ) from exc

        return validated

    def run(self, *args, **kwargs):
        raise NotImplementedError
