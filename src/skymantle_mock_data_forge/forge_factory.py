from boto3 import Session

from skymantle_mock_data_forge.dynamodb_forge import DynamoDbForge
from skymantle_mock_data_forge.models import DataForgeConfig, DataForgeConfigOverride
from skymantle_mock_data_forge.s3_forge import S3Forge


class ForgeFactory:
    def __init__(
        self,
        config: list[DataForgeConfig],
        session: Session = None,
        overrides: list[DataForgeConfigOverride] | None = None,
    ) -> None:
        forges = {"dynamodb": DynamoDbForge, "s3": S3Forge}

        self.data_managers: dict[str, DynamoDbForge] = {}

        for data_loader_config in config:
            forge_id = data_loader_config["forge_id"]

            forge_types = list(set(forges.keys()).intersection(set(data_loader_config.keys())))

            if len(forge_types) != 1:
                raise Exception(f"Can only have one of the following per config: {list(forges.keys())}")

            forge_type = forge_types[0]

            forge_overrides = None
            if overrides is not None:
                forge_overrides = [override for override in overrides if override.get("forge_id") is None]
                forge_overrides.extend([override for override in overrides if override.get("forge_id") == forge_id])

            self.data_managers[forge_id] = forges[forge_type](
                forge_id, data_loader_config[forge_type], session, forge_overrides
            )

    def add_key(self, forge_id: str, key: dict[str, str]) -> None:
        data_manager = self.data_managers.get(forge_id)

        if data_manager:
            data_manager.add_key(key)
        else:
            raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")

    def get_data(self, forge_id: str | None = None, query=None) -> None:
        forge_ids = self._get_forge_ids(forge_id)

        data = []
        for forge_id in forge_ids:
            data_manager = self.data_managers.get(forge_id)

            if data_manager:
                data.extend(data_manager.get_data(query))
            else:
                raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")

        return data

    def load_data(self, forge_id: str | None = None) -> None:
        forge_ids = self._get_forge_ids(forge_id)

        for forge_id in forge_ids:
            data_manager = self.data_managers.get(forge_id)

            if data_manager:
                data_manager.load_data()
            else:
                raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")

    def cleanup_data(self, forge_id: str | None = None) -> None:
        forge_ids = self._get_forge_ids(forge_id)

        for forge_id in forge_ids:
            data_manager = self.data_managers.get(forge_id)

            if data_manager:
                data_manager.cleanup_data()
            else:
                raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")

    def _get_forge_ids(self, forge_id: str | None) -> list[str]:
        forge_ids: list[str] = []
        if forge_id is None:
            forge_ids.extend(self.data_managers.keys())
        else:
            forge_ids.append(forge_id)

        return forge_ids
