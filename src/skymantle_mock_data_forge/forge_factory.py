from boto3 import Session

from skymantle_mock_data_forge.dynamodb_forge import DynamoDbForge
from skymantle_mock_data_forge.models import DataForgeConfig


class ForgeFactory:
    def __init__(self, config: list[DataForgeConfig], session: Session = None) -> None:
        forges = {"dynamodb": DynamoDbForge}

        self.data_managers: dict[str, DynamoDbForge] = {}

        for data_loader_config in config:
            forge_id = data_loader_config["forge_id"]

            forge_types = list(set(forges.keys()).intersection(set(data_loader_config.keys())))

            if len(forge_types) != 1:
                raise Exception(f"Can only have one of the following per config: {list(forges.keys())}")

            self.data_managers[forge_id] = forges[forge_types[0]](forge_id, data_loader_config["dynamodb"], session)

    def add_key(self, forge_id: str, key: dict[str, str]) -> None:
        data_manager = self.data_managers.get(forge_id)

        if data_manager:
            data_manager.add_key(key)
        else:
            raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")

    def get_data(self, forge_id: str) -> dict:
        data_manager = self.data_managers.get(forge_id)

        if data_manager:
            return data_manager.get_data()
        else:
            raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")

    def load_data(self, forge_id: str) -> None:
        data_manager = self.data_managers.get(forge_id)

        if data_manager:
            data_manager.load_data()
        else:
            raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")

    def cleanup_data(self, forge_id: str) -> None:
        data_manager = self.data_managers.get(forge_id)

        if data_manager:
            data_manager.cleanup_data()
        else:
            raise Exception(f"{forge_id} not initialized ({','.join(self.data_managers.keys())}).")
