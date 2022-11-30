from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Common.config.config import Config


class DocQAService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(DocQAService, self).__init__(config=config)
        self.session = None
        self.api_url = f"{self.config.doc_qa_url}/process"
        self.storage = storage

    def _pre_process(self, input_data):
        return BaseDataModel(data=input_data)

    def _post_process(self, data: BaseDataModel) -> str:
        if data is not None:
            result = data.data.get("answer", "")
        else:
            result = ""
        return result
