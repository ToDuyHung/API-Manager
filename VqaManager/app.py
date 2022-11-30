import json

from common.common_keys import *
from config.config import Config
from controller.main_controller import Processor
from utils.utils import import_from_string

from TMTChatbot.ServiceWrapper import BaseApp
from TMTChatbot.Common.utils.logging_utils import setup_logging


class App(BaseApp):
    def __init__(self, config: Config = None):
        super(App, self).__init__(config=config, with_kafka_app=False, with_default_pipeline=False)
        self.processor = Processor(config=config)

        with open(self.config.routing_path) as f:
            modules_config = json.load(f)

        modules = dict()
        for controller, routes in modules_config.items():
            for route in routes:
                route[FUNC] = getattr(self.processor, route[FUNC])
                route[REQUEST_DATA_MODEL] = import_from_string(route[REQUEST_DATA_MODEL])
                route[RESPONSE_DATA_MODEL] = import_from_string(route[RESPONSE_DATA_MODEL])
            modules[controller] = routes

        [self.api_app.add_endpoint(**route) for routes in modules.values() for route in routes]


def create_app(multiprocess: bool = False):
    _config = Config()
    setup_logging(logging_folder=_config.logging_folder, log_name=_config.log_name)
    if multiprocess:
        raise NotImplementedError("Multiprocessing app not created")
    else:
        _app = App(config=_config)
    return _app


main_app = create_app(False)
app = main_app.api_app.app
