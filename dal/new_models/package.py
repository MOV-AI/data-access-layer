"""
"""
from .base import MovaiBaseModel
from pydantic import Field, BaseModel, StrictBytes, field_validator
from typing import Dict, List, Tuple, Optional
import hashlib
from movai_core_shared.logger import Log


logger = Log.get_logger(__name__)


class FileValue(BaseModel):
    FileLabel: str = None
    Value: bytes = None
    Checksum: str = None

    @classmethod
    @field_validator("Value", mode="before")
    def _validate_value(cls, value):
        if isinstance(value, str):
            return value.encode()
        return value


class Package(MovaiBaseModel):
    File: Dict[str, FileValue] = Field(default_factory=dict)

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

    def dump_file(self, file_name: str, path_to: str) -> Tuple[bool, str, str]:
        """ Dump a file to storage """
        csum = self.file_exists(file_name, path_to)

        if csum is None:
            with open(path_to, 'wb') as fd:
                contents = self.File[file_name].Value
                try:
                    fd.write(contents.encode())
                except AttributeError:
                    # bytes has no attribute encode
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
            dic["Package"][self.name]["File"][f]["Value"] = dic["Package"][self.name]["File"][f]["Value"].decode(errors='replace')

        return dic


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
