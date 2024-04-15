from ovmsclient import make_grpc_client
from numpy import ndarray
from ..abstract.client import Client, Connection


class OpenVinoClient(Client):
    def __init__(self, model: str, connection: Connection):
        self.client = make_grpc_client(
            f"{connection['ip']}:{connection['grpc_port']}"
        )
        self.model_name = model
        self.metadata = self.client.get_model_metadata(model)

    def predict(self, *inputs: ndarray, timeout: int = None):
        inputs_meta = self.metadata["inputs"]
        inputs_dict = {}

        for i, (k, _) in enumerate(inputs_meta.items()):
            inputs_dict[k] = inputs[i]

        response = self.client.predict(
            inputs=inputs_dict, model_name=self.model_name, timeout=timeout
        )

        if isinstance(response, ndarray):
            for k, _ in inputs_meta.items():
                return {k: response}

        return response
