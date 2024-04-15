from typing import TypedDict, Union
from numpy import ndarray


class Connection(TypedDict):
    ip: str
    grpc_port: Union[str, int]
    rest_port: Union[str, int]
    metrics_port: Union[str, int]
    timeout: int = 10


class Client:
    def predict(*inputs: ndarray, timeout: int = None) -> dict: ...
