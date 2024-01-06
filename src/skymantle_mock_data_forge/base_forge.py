import copy

from boto3 import Session

from skymantle_mock_data_forge.models import DataForgeConfigOverride, OverideType


class BaseForge:
    def __init__(
        self, forge_id: str, overrides: list[DataForgeConfigOverride] | None = None, session: Session = None
    ) -> None:
        self.forge_id: str = forge_id
        self.aws_session = session
        self.config_overrides = overrides

    def _override_data(self, items: list[dict]) -> list[dict]:
        data: list[dict] = [copy.deepcopy(item) for item in items]

        if not self.config_overrides:
            return data

        if not (
            isinstance(self.config_overrides, list) and all(isinstance(item, dict) for item in self.config_overrides)
        ):
            raise Exception("Overrides must be a list[DataForgeConfigOverride]")

        if not (isinstance(data, list) and all(isinstance(item, dict) for item in data)):
            raise Exception("The provided data must be a list of dictionaries")

        for config_override in self.config_overrides:
            key_paths = config_override.get("key_paths")

            if isinstance(key_paths, str):
                key_paths = [key_paths]

            elif not (isinstance(key_paths, list) and all(isinstance(item, str) for item in key_paths)):
                raise Exception("key_paths must be a str or list[str]")

            override_type = config_override.get("override_type")
            override = config_override.get("override")

            for key_path in key_paths:
                keys = key_path.split(".")

                for item in data:
                    self._replace_values(item, keys, override_type, override)

        return data

    def _replace_values(self, item: dict, keys: list[str], override_type: OverideType, override: any):
        temp_item = item

        for key in keys[:-1]:
            temp_item = temp_item.get(key)

            if not isinstance(temp_item, dict):
                raise Exception(f"The key:{key} does not exist or its value is not a dict")

        end_key = keys[-1]
        if end_key not in temp_item:
            raise Exception(f"The key:{end_key} does not exist.")

        match override_type:
            case OverideType.REPLACE_VALUE:
                temp_item[end_key] = override

            case OverideType.FORMAT_VALUE:
                value = temp_item[end_key]

                if not isinstance(value, str):
                    raise Exception(f"The value for key:{end_key} must be str for FORMAT_VALUE.")

                temp_item[end_key] = value.format(*override)

            case OverideType.CALL_FUNCTION:
                temp_item[end_key] = override(end_key, temp_item[end_key], copy.deepcopy(temp_item))

            case _:
                raise Exception(f"Unsupported override type - {override_type}")
