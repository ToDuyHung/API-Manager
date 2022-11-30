from TMTChatbot import (
    JoinCollMongoConnector,
    BaseServiceWithRAMCacheSingleton,
)

from config.config import Config
from data_model import ResponseStatus


class BaseController(BaseServiceWithRAMCacheSingleton):
    def __init__(self, config: Config):
        super(BaseController, self).__init__(config=config)
        self.storage = JoinCollMongoConnector(config=config)

    def process(self, func, response_model, return_response=True, return_json=False, args=tuple()):
        try:
            obj, status = func(*args)
        except Exception as e:
            self.logger.error(f"Exception {repr(e)} occur", exc_info=True)
            obj = None
            status = ResponseStatus.ERROR
        if return_response:
            if isinstance(obj, list):
                obj = [o.json if o and return_json else o for o in obj]
            elif obj and return_json:
                obj = obj.json
            return response_model(obj, status=status)
        return obj
