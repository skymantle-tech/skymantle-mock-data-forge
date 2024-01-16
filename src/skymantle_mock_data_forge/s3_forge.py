import base64
import copy
import csv
import io
import json

from boto3 import Session
from skymantle_boto_buddy import cloudformation, s3, ssm

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

        # Get the S3 bucket name
        if config["bucket"].get("name"):
            self.bucket_name: str = config["bucket"]["name"]
        elif config["bucket"].get("ssm"):
            self.bucket_name: str = ssm.get_parameter(config["bucket"]["ssm"], session=self.aws_session)
        else:
            stack_name = config["bucket"]["stack"]["name"]
            output = config["bucket"]["stack"]["output"]

            outputs = cloudformation.get_stack_outputs(stack_name, session=self.aws_session)
            bucket_name = outputs.get(output)

            if bucket_name:
                self.bucket_name: str = bucket_name
            else:
                raise Exception(f"Unable to find a bucket_name for stack: {stack_name} and output: {output}")

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

        data_type_map = {
            "text": (lambda data: data),
            "json": (lambda data: json.dumps(data)),
            "base64": (lambda data: base64.b64decode(data)),
            "csv": create_csv,
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
