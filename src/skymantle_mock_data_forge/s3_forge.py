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

        self._config = config
        self._s3_objects: list[S3ObjectConfig] = self._override_data(config["s3_objects"])
        self._keys: list[str] = [s3_object["key"] for s3_object in self._s3_objects]

    def _get_bucket_name(self):
        resource_config = self._config["bucket"]
        return self._get_destination_identifier(resource_config)

    def get_data(self, *, query: ForgeQuery, return_source: bool):
        data = [copy.deepcopy(s3_object) for s3_object in self._s3_objects]

        if query is not None:
            data = self._get_data_query(query, data)

        if not return_source:
            data = [{"key": item["key"], "data": item["data"]} for item in data]

        return data

    def add_key(self, key: str) -> None:
        self._keys.append(key)

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

        for s3_object in self._s3_objects:
            data_types = list(set(data_type_map.keys()).intersection(set(s3_object["data"].keys())))

            if len(data_types) != 1:
                raise Exception(f"Can only have one of the following per s3 config: {list(data_type_map.keys())}")

            data_type = data_types[0]
            data_func = data_type_map[data_type]
            data = data_func(s3_object["data"][data_type])

            s3.put_object(self._get_bucket_name(), s3_object["key"], data, session=self._aws_session)

    def cleanup_data(self) -> None:
        s3.delete_objects_simplified(self._get_bucket_name(), self._keys, session=self._aws_session)
