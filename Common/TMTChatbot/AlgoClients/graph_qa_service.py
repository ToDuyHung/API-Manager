from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Node
from TMTChatbot.Schema.objects.graph.graph import SubGraph
from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService


class GraphQAService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(GraphQAService, self).__init__(config=config)
        self.session = None
        self.api_url = f"{self.config.graph_qa_url}/process"
        self.storage = storage

    def _pre_process(self, input_data: Conversation):
        graph_data = input_data.data.json
        graph_data["question"] = input_data.current_state.message.message
        return BaseDataModel(data=graph_data)

    def _post_process(self, data: BaseDataModel) -> str:
        if data is not None:
            result = data.data.get("answer", "")
        else:
            result = ""
        return result

    def custom_question(self, input_data: Conversation, question: str):
        graph_data = input_data.data.json
        graph_data["question"] = question
        data = BaseDataModel(data=graph_data)
        if self.api_possible():
            result: BaseDataModel = self.make_request(lambda: self._call_api(data))
            output = self._post_process(result)
            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return output

    def custom_node_question(self, node: Node, question: str, conversation: Conversation):
        subgraph = SubGraph(storage_id=conversation.storage_id, user=conversation.user, shop=conversation.shop,
                            nodes=[node])
        graph_data = subgraph.json
        graph_data["question"] = question
        data = BaseDataModel(data=graph_data)
        if self.api_possible():
            result: BaseDataModel = self.make_request(lambda: self._call_api(data))
            output = self._post_process(result)
            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return output
