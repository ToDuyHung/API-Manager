from TMTChatbot.Common.utils import setup_logging
from TMTChatbot import Config
from TMTChatbot import BaseApp


if __name__ == "__main__":
    _config = Config()
    setup_logging(logging_folder=_config.logging_folder, log_name=_config.log_name)
    app = BaseApp(_config)
    app.add_process_function(lambda x: x)
    app.start()
    app.join()

