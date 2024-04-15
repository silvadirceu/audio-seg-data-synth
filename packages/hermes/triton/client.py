from numpy import ndarray
from tritonclient.grpc import InferenceServerClient, InferInput, InferRequestedOutput
from ..abstract.client import Client, Connection

MAX_MESSAGE_LENGTH = 200 * 1024 * 1024


class TritonClient(Client):
    def __init__(
        self,
        model: str,
        connection: Connection,
    ) -> None:
        GRPC_ARGS = [
            ("grpc.max_send_message_length", MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
            ("grpc.keepalive_time_ms", 2**31 - 1),
            ("grpc.keepalive_timeout_ms", 20000),
            ("grpc.keepalive_permit_without_calls", False),
            ("grpc.http2.max_pings_without_data", 2),
            ("grpc.dns_enable_srv_queries", 1),
        ]
        self.model_name = model

        self.client = InferenceServerClient(
            url=f"{connection['ip']}:{connection['grpc_port']}",
            verbose=False,
            channel_args=GRPC_ARGS,
        )

        self.metadata = self.client.get_model_metadata(self.model_name, as_json=True)
        self.input_name, _, self.input_dtype = self.__get_name_dim(
            self.metadata, "inputs"
        )
        self.output_name, _, _ = self.__get_name_dim(self.metadata, "outputs")

        self.outputs: list[InferRequestedOutput] = []
        for name in self.output_name:
            self.outputs.append(InferRequestedOutput(name))

    def predict(self, *inputs: ndarray, timeout: int = None):
        self.inputs: list[InferInput] = []
        for name, data, dtype in zip(self.input_name, inputs, self.input_dtype):
            infer_input = InferInput(name, data.shape, dtype)
            infer_input.set_data_from_numpy(data)
            self.inputs.append(infer_input)

        results = self.client.infer(
            model_name=self.model_name,
            inputs=self.inputs,
            outputs=self.outputs,
            timeout=timeout,
        )

        output = {}
        for i, _ in enumerate(self.outputs):
            output[self.output_name[i]] = results.as_numpy(self.output_name[i])

        return output

    def __get_name_dim(self, metadata, key):
        key_list = []
        dim_list = []
        precision_list = []
        for d in metadata[key]:
            if "name" in d:
                key_list.append(d["name"])
            if "shape" in d:
                dim_list.append(d["shape"])
            if "datatype" in d:
                precision_list.append(d["datatype"])

        return key_list, dim_list, precision_list
