import base64
import copy
import csv
import io
import json

from boto3 import Session
from skymantle_boto_buddy import s3

from skymantle_mock_data_forge.base_forge import BaseForge
from skymantle_mock_data_forge.models import (
    DataForgeConfigOverride,
    ForgeQuery,
    S3ForgeConfig,
    S3ObjectConfig,
)


class S3Forge(BaseForge):
    def __init__(
        self,
        forge_id: str,
        config: S3ForgeConfig,
        session: Session = None,
        overrides: list[DataForgeConfigOverride] | None = None,
    ) -> None:
        super().__init__(forge_id, overrides, session)

        resource_config = config["bucket"]
        self.bucket_name: str = self._get_destination_identifier(resource_config)

        self.s3_objects: list[S3ObjectConfig] = self._override_data(config["s3_objects"])
        self.keys: list[str] = [s3_object["key"] for s3_object in self.s3_objects]

    def get_data(self, query: ForgeQuery = None):
        data = [copy.deepcopy(s3_object) for s3_object in self.s3_objects]

        if query is None:
            return data

        return self._get_data_query(query, data)

    def add_key(self, key: str) -> None:
        self.keys.append(key)

    def load_data(self) -> None:
        def create_csv(data: list[list[str | int]]):
            with io.StringIO() as string_io:
                csv.writer(string_io).writerows(data)
                return string_io.getvalue()

        def load_file(filename: str):
            with open(filename, "rb") as file:
                data = file.read()

            return data

        data_type_map = {
            "text": (lambda data: data),
            "json": (lambda data: json.dumps(data)),
            "base64": (lambda data: base64.b64decode(data)),
            "csv": create_csv,
            "file": load_file,
        }

        for s3_object in self.s3_objects:
            data_types = list(set(data_type_map.keys()).intersection(set(s3_object["data"].keys())))

            if len(data_types) != 1:
                raise Exception(f"Can only have one of the following per s3 config: {list(data_type_map.keys())}")

            data_type = data_types[0]
            data_func = data_type_map[data_type]
            data = data_func(s3_object["data"][data_type])

            s3.put_object(self.bucket_name, s3_object["key"], data, session=self.aws_session)

    def cleanup_data(self) -> None:
        s3.delete_objects_simplified(self.bucket_name, self.keys, session=self.aws_session)
