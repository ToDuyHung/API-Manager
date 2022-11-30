from typing import List
import regex as re
from TMTChatbot.Common.storage.base_storage import BaseStorage

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.default_intents import *
from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Schema.objects.graph.graph_data import Weather


class WeatherService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(WeatherService, self).__init__(config=config)
        self.session = None
        self.api_url = f"{self.config.weather_url}/process"
        self.storage = storage

    def _pre_process(self, input_data: Conversation) -> BaseDataModel:
        weather_conv = input_data.data.weather
        location = weather_conv.get_attr(LOCATION)
        location = location if location else []
        location = [re.sub(r"Tỉnh|Thành phố", "", loc) for loc in location]
        date = weather_conv.get_attr(DATE)
        date = date if date else []
        return BaseDataModel(data={
            LOCATION: location,
            DATE: date,
            STORAGE_ID: input_data.storage_id,
            CLASS: Weather.class_name()})

    @staticmethod
    def update_weather_infor(conversation: Conversation):
        message = conversation.current_state.message
        nodes = conversation.data.get_previous_node(node_class=Weather.class_name())
        weather_node = [node for node in nodes if isinstance(node, Weather)]
        if not weather_node:
            node_data = {STORAGE_ID: conversation.storage_id}
            weather_node = Weather(**node_data)
        else:
            weather_node = weather_node[0]

        mentioned_time = [ent.text for ent in message.entities if ent.label == DATE.upper()]
        if len(mentioned_time) > 0 or weather_node.get_attr(DATE):
            if len(mentioned_time) > 0:
                weather_node.drop_attr(DATE)
                weather_node.set_attr(DATE, ",".join(mentioned_time))
            conversation.current_state.update_intents([BOT_USER_HAS_TIME_WEATHER])

        mentioned_location = [ent.text for ent in message.entities if ent.label == ADDRESS.upper()]
        if len(mentioned_location) > 0 or weather_node.get_attr(LOCATION):
            if len(mentioned_location) > 0:
                weather_node.drop_attr(LOCATION)
                weather_node.set_attr(LOCATION, ",".join(mentioned_location))
            conversation.current_state.update_intents([BOT_USER_HAS_LOCATION])

        conversation.data.add_nodes([weather_node])

    def _post_process(self, data: BaseDataModel) -> List[Weather]:
        if data is not None:
            result = [Weather.from_json(w) for w in data.data]
        else:
            result = []
        return result

    def __call__(self, input_data: Conversation, key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        if input_data is not None and self.api_possible():
            data = self._pre_process(input_data)
            result: BaseDataModel = self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                                      num_retry=num_retry, call_prop=call_prop)
            output = self._post_process(result)

            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return output
