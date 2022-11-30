import asyncio
from fastapi import APIRouter, Depends
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.singleton import BaseSingleton
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel


class WorkerManager(BaseSingleton):
    def __init__(self):
        super(WorkerManager, self).__init__()
        self.thread_executor = ThreadPoolExecutor(max_workers=100)

    async def wait(self, job, *args):
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(self.thread_executor, job, *args)
        return output

    @staticmethod
    async def wait_async(job, *args):
        output = await job(*args)
        return output


class BaseRoute(BaseSingleton):
    def __init__(self, prefix="/", config: Config = None):
        self.config = config if config is not None else Config()
        self.router = APIRouter(
            prefix=prefix,
            responses={404: {"description": "Not found"}},
        )
        self.worker_manager = WorkerManager()

    @staticmethod
    def wait_sync(job, *args, **kwargs):
        return job(*args, **kwargs)

    async def wait(self, job, *args, use_thread: bool = True, **kwargs):
        if use_thread:
            def run_job_sync():
                return job(*args, **kwargs)

            output = await self.worker_manager.wait(run_job_sync)
        else:
            async def run_job_async():
                return await job(*args, **kwargs)

            output = await self.worker_manager.wait_async(run_job_async)
        return output

    def add_endpoint(self, endpoint: str, func, description: str, methods: List[str],
                     use_thread: bool = True, use_async: bool = True,
                     request_data_model: Optional[type] = None,
                     response_data_model: Optional[type] = None, **kwargs):
        router = self.router
        endpoint = endpoint.strip()
        if endpoint[0] != "/":
            endpoint = "/" + endpoint

        async def request_func(in_data: BaseDataModel):
            output = await self.wait(func, in_data, use_thread=use_thread)
            return output

        async def request_func_custom(data: request_data_model = Depends()):
            output = await self.wait(job=func, use_thread=use_thread, **data.__dict__)
            return output

        def sync_request_func(in_data: BaseDataModel):
            output = self.wait_sync(func, in_data)
            return output

        def sync_request_func_custom(data: request_data_model = Depends()):
            output = self.wait_sync(job=func, **data.__dict__)
            return output

        if use_async:
            if request_data_model is None:
                router.add_api_route(endpoint, methods=methods, endpoint=request_func,
                                     response_model=BaseDataModel, description=description, **kwargs)
            else:
                router.add_api_route(endpoint, methods=methods, endpoint=request_func_custom,
                                     response_model=response_data_model, description=description, **kwargs)
        else:
            if request_data_model is None:
                router.add_api_route(endpoint, methods=methods, endpoint=sync_request_func,
                                     response_model=BaseDataModel, description=description, **kwargs)
            else:
                router.add_api_route(endpoint, methods=methods, endpoint=sync_request_func_custom,
                                     response_model=response_data_model, description=description, **kwargs)

    @staticmethod
    def create_route(prefix: str):
        return BaseRoute(prefix=prefix)

    @staticmethod
    def default_route(prefix="/process", config: Config = None):
        route = BaseRoute(prefix=prefix, config=config)
        # route.add_endpoint("/", lambda: "hello world", methods=["POST"], use_async=False, use_thread=False)
        return route
