from typing import List
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi_health import health

from TMTChatbot.Common.config.config import Config
from TMTChatbot.ServiceWrapper.interfaces.restful.routes.base_route import BaseRoute
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton


class APIApp(BaseServiceSingleton):
    def __init__(self, config: Config = None):
        super(APIApp, self).__init__(config)
        self.app = FastAPI()
        self.base_route = BaseRoute.default_route(prefix=config.default_api_route_prefix)
        self.app.add_api_route("/health", health([self.health_check]), methods=["GET"])
        self.app.include_router(self.base_route.router)
        self.logger.info(f"{self.__class__.__name__} create successfully")
        self.apply_cors()

    def apply_cors(self):
        self.app.add_middleware(CORSMiddleware,
                                allow_origins=["*"],
                                allow_credentials=True,
                                allow_methods=["*"],
                                allow_headers=["*"])

    @staticmethod
    def health_check(session: bool = True):
        return session

    def add_endpoint(self, endpoint: str, func, description: str, methods: [str],
                     request_data_model=None, response_data_model=None,
                     use_thread: bool = True, use_async: bool = True, **kwargs):
        """
        Add custom endpoint to FastAPI App
        :param endpoint: path to your function
        :param func: which function to be used
        :param description: describe your function
        :param methods: http methods = {GET, POST, PUT, PATCH, DELETE}
        :param request_data_model: input data model, which is input type of <func>
        :param response_data_model: response data model, which is output type of <func>
        :param use_thread: if your function is sync and you need a thread for async interface, then True, else False
        :param use_async: if your function is async then True, else False
        :return:

        if custom_data_model is None -> default = BaseDataModel
        if custom_response_data_model is None -> default = BaseDataModel
        """
        self.base_route.add_endpoint(endpoint=endpoint, func=func, description=description,
                                     methods=methods, use_thread=use_thread, use_async=use_async,
                                     request_data_model=request_data_model,
                                     response_data_model=response_data_model, **kwargs)
        self.app.include_router(self.base_route.router)

    def create_api_interface(self, routes: List[BaseRoute]):
        for route in routes:
            self.app.include_router(route.router)
        return self.app

    def start(self, n_workers: int = 1):
        uvicorn.run(self.app, host=self.config.api_host, port=self.config.api_port, reload=False, log_level="debug",
                    debug=False, workers=n_workers, factory=False, loop="asyncio", timeout_keep_alive=120)
