"""
"""
from .base import MovaiBaseModel
from pydantic import Field, BaseModel, field_validator
from typing import Dict, List, Tuple, Union
import hashlib
from movai_core_shared.logger import Log
import zlib
import base64
from typing_extensions import Annotated
from pydantic import field_validator, BaseModel, Field, ValidationInfo, model_validator
from sys import getsizeof


logger = Log.get_logger(__name__)
MegaByte = 1000000


def compress(value: bytes) -> str:
    """This function is responsible for compressing byte data using the zlib
    compression and encoding the compressed data to a Base64 string for easy
    storage and representation.

    Args:
        value (bytes): The data you want to compress. If the input is a string,
            it returns the string as-is without performing any compression.
            This check is mainly to ensure that you don't accidentally try to
            compress an already compressed string.

    Returns:
        str: A Base64 encoded string representation of the compressed byte data.
        If the input is already a string, it returns the input string directly.
    """
    compressed_data = zlib.compress(value)
    value = base64.b64encode(compressed_data).decode('utf-8')

    return value


def decompress(value: str) -> bytes:
    """
    This function tries to decode a Base64 encoded string (which ideally represents compressed
    data) and then decompress it. If the given value is not compressed or encoded, or any error
    occurs during decompression or decoding, it returns the input data as-is.

    Args:
        value (str): The string you want to decompress. If the input is a byte sequence,
                    it returns the bytes as-is without performing any decompression.

    Returns:
        bytes: The decompressed byte data. If the input string isn't a valid compressed Base64
                encoded string or if the input is already in byte format,
                it returns the input data directly.
    """
    data = value
    try:
        # check if compressed
        decoded_compressed_data = base64.b64decode(value)
        decompressed_data = zlib.decompress(decoded_compressed_data)
        data = decompressed_data
    except Exception:
        return base64.b64decode(value)
    return data


class FileValue(BaseModel):
    FileLabel: str = None
    Value: str
    Checksum: str = None

    @field_validator("Value", mode="before")
    @classmethod
    def _validate_value(cls, value, info: ValidationInfo):
        if isinstance(value, str):
            return value
        if getsizeof(value) > 15 * MegaByte:
            return compress(value)
        return base64.b64encode(value).decode("utf-8")


class Package(MovaiBaseModel):
    File: Dict[str, FileValue] = Field(default_factory=dict, validate_default=True)

    @classmethod
    def _original_keys(cls) -> List[str]:
        """keys that are originally defined part of the model

        Returns:
            List[str]: list including the original keys
        """
        return super()._original_keys() + ["File"]

    def is_checksum_valid(self, file_name: str, checksum: str) -> bool:
        """ Check checksum """
        return checksum == self.File[file_name].Checksum

    def add_file(self, file_name, value: bytes):
        """ Add a file to the package

        Args:
            file_name (str): file name
            value (bytes): value of the file
        """
        self.File[file_name] = FileValue(Value=value, Checksum=compute_md5_checksum(value), FileLabel=file_name)

    def file_exists(self, file_name: str,  path_to: str) -> str:
        """ Check existing file against computed checksum """
        try:
            csum = compute_md5_checksum(path_to)
            if self.is_checksum_valid(file_name, csum):
                return csum
        except FileNotFoundError:
            logger.warning(f"File {path_to} not found")
            pass
        return None

    def get_value(self, file_name) -> bytes:
        return decompress(self.File[file_name].Value)

    def dump_file(self, file_name: str, path_to: str) -> Tuple[bool, str, str]:
        """ Dump a file to storage """
        csum = self.file_exists(file_name, path_to)

        if csum is None:
            with open(path_to, 'wb') as fd:
                contents = decompress(self.File[file_name].Value)
                fd.write(contents)
            # check checksum again
            csum = self.file_exists(file_name, path_to)
            if csum is None:
                raise RuntimeError("File checksum mismatch")
        return (True, path_to, csum)

    @staticmethod
    def dump(package: str, file_name: str, path_to: str) -> Tuple[bool, str, str]:
        """ Dump a file to storage """
        try:
            return Package(package).dump_file(file_name, path_to)
        except KeyError:  # Scope does not exist
            return (False, path_to, None)
    '''
    def model_dump(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = True,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
    ):
        dic = super().model_dump(by_alias=by_alias, exclude_none=exclude_none)
        for f in dic["Package"][self.name]["File"]:
            value = dic["Package"][self.name]["File"][f]["Value"]
            dic["Package"][self.name]["File"][f]["Value"] = compress(value)

        return dic
    '''


def compute_md5_checksum(file_path: str) -> str:
    """
    Compute the MD5 checksum of the file specified by file_path.

    Args:
        file_path: Path to the file to compute the MD5 checksum for.

    Returns:
        str: The MD5 checksum as a hex string.
    """
    # Create a new MD5 hash object.
    hasher = hashlib.md5()

    # Open the file in binary read mode.
    with open(file_path, 'rb') as file:
        # Read the file in chunks (here, we read 4096 bytes at a time).
        # This approach ensures that the whole file is not loaded into memory at once.
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)

    # Return the hex digest of the hash.
    return hasher.hexdigest()
