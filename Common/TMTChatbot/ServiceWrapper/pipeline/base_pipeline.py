import traceback
from threading import Thread
from datetime import datetime
from multiprocessing import Process, Queue, Event
from uuid import uuid4, uuid5
import asyncio
import random
import time

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.singleton import Singleton
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.ServiceWrapper.common.status import ResultStatus
from TMTChatbot.ServiceWrapper.services.base_service import BaseService
from TMTChatbot.ServiceWrapper.services.buffer_manager import BufferManager


class BasePipeline(BaseService):
    def __init__(self, config: Config = None, default_workers: bool = True):
        super(BasePipeline, self).__init__(config=config)
        self.buffer_manager = BufferManager(config=config)

        self.num_done = [[self.get_current_time_step(), 0]]
        self.total_done = 0
        if default_workers:
            self.workers = [Thread(target=self.process_job, daemon=True)
                            for _ in range(self.config.max_process_workers)]
        else:
            self.workers = []
        self.logger.info(f"INIT {len(self.workers)} THREADS AS WORKERS. Default workers: {default_workers}")

        self.done = False

    def process_func(self, data: BaseDataModel) -> BaseDataModel:
        self.logger.warning("Need to implement or replace process_function")
        return data

    @property
    def start_time(self):
        if len(self.num_done) > 0:
            return self.num_done[0][0]
        else:
            return self.get_current_time_step()

    @property
    def end_time(self):
        if len(self.num_done) > 0:
            return self.num_done[-1][0]
        else:
            return self.get_current_time_step()

    @property
    def item_per_second(self):
        self.update_done_item(0)
        start_time = self.start_time
        end_time = self.end_time
        return self.total_done / max([1, end_time - start_time])

    @staticmethod
    def get_current_time_step():
        return int(datetime.now().timestamp())

    def add_process_func(self, func):
        self.process_func = func

    @property
    def current_time_step(self):
        return self.num_done[-1][0]

    @property
    def first_time_step(self):
        return self.num_done[0][0]

    def update_done_item(self, num=1):
        current_time_step = self.get_current_time_step()
        if current_time_step > self.current_time_step:
            self.num_done.append([current_time_step, num])
            while self.start_time < current_time_step - 60:
                _, last_num_done = self.num_done.pop(0)
                self.total_done -= last_num_done
        else:
            self.num_done[-1][1] += num
        self.total_done += num

    def process(self, data: BaseDataModel) -> BaseDataModel:
        data.update_receive_time()
        data.meta_data.status = ResultStatus.PROCESSING
        if self.process_func is None:
            self.logger.warning("Process function not created => return same data object")
        else:
            data: BaseDataModel = self.process_func(data)
        data.update_response_time()
        data.meta_data.status = ResultStatus.SUCCESS
        self.update_done_item(1)
        return data

    def __call__(self, input_data: BaseDataModel) -> BaseDataModel:
        return self.process(input_data)

    def process_job(self):
        while True:
            try:
                data: BaseDataModel = self.buffer_manager.get_data(INPUT_BUFFER, timeout=60)
                if data is None:
                    continue
                data = self.process(data)
                self.buffer_manager.put_data(OUTPUT_BUFFER, data)
            except Exception as e:
                error_msg = str(traceback.format_exc())
                self.logger.error(f'Failed processing data: {error_msg}. {e}')

    @property
    def info(self):
        return f"THROUGHPUT: {self.item_per_second} items/s"

    def start(self):
        [worker.start() for worker in self.workers]

    def join(self):
        [worker.join() for worker in self.workers]


class BasePipelineSingleton(BasePipeline, metaclass=Singleton):
    pass


class PipelineJob(Process, BasePipeline):
    def __init__(self, config: Config = None, name: str = None):
        BasePipeline.__init__(self, config=config, default_workers=False)
        Process.__init__(self, name=name if name is not None else f"{self.__class__.__name__}-{uuid4()}")
        self.in_buffer = Queue(maxsize=200)
        self.out_buffer = Queue(maxsize=200)

    @staticmethod
    def sample_0(data: BaseDataModel, *args, **kwargs) -> BaseDataModel:
        data.data["pid"] = "xxx"
        return data

    @staticmethod
    def sample_1(data: BaseDataModel, *args, **kwargs) -> BaseDataModel:
        data.data["pid"] = "yyy"
        return data

    def process(self, func=None, *args, **kwargs):
        if func is None:
            func = self.process_func
        if func is None:
            raise "Process function not created"
        else:
            output = func(*args, **kwargs)
        self.update_done_item(1)
        return output

    def run(self):
        while True:
            try:
                jid, func_name, args, kwargs = self.in_buffer.get(timeout=10)
                func = self.get_func(func_name)
                output = self.process(func, *args, **kwargs)
                self.out_buffer.put_nowait((jid, output))
            except Exception as e:
                self.logger.debug(f"Waiting for data. Error: {e}")
                continue


class ProcessPipeline(BasePipelineSingleton):
    def __init__(self, config: Config = None, name: str = None):
        super(ProcessPipeline, self).__init__(config=config, default_workers=False)
        self.workers = []
        self.logger.info(f"STARTED {len(self.workers)} for Job {name}")
        self.storage = {}
        self.name = name
        self.init()

    def init_workers(self):
        """
        Create n workers of PipelineJob class.
        >>> from TMTChatbot.ServiceWrapper.pipeline.base_pipeline import PipelineJob
        >>> n = self.config.max_process_workers
        >>> self.workers = [PipelineJob(config=self.config) for _ in range(n)]
        :return:
        """
        raise NotImplementedError("Need implementation")

    def start_worker(self):
        self._check_workers()
        [worker.start() for worker in self.workers]

    def init(self):
        self.init_workers()
        self.start_worker()
        self.logger.info(f"STARTED {len(self.workers)} for Job {self.name}")

    def _check_workers(self):
        if len(self.workers) == 0:
            raise "Need to create workers first"

    @staticmethod
    def _generate_random_id(key: str):
        return str(uuid5(uuid4(), str(datetime.now().timestamp()) + key))

    def process(self, data: BaseDataModel) -> BaseDataModel:
        self._check_workers()

        jid = self._generate_random_id(data.index)
        event = Event()
        event.clear()
        self.storage[jid] = {
            "output": None,
            "flag": event
        }
        worker = random.choice(self.workers)
        worker.in_buffer.put_nowait((jid, data))
        _jid, _output = worker.out_buffer.get()
        if _jid not in self.storage:
            worker.out_buffer.put((_jid, _output))
        else:
            self.storage[_jid]["output"] = _output
            self.storage[_jid]["flag"].set()

        event.wait()
        output = self.storage[jid]["output"]
        return output

    def get_process_func_with_name(self, func_name: str, is_async: bool = False):
        async def async_process_custom_func(*args, **kwargs) -> BaseDataModel:
            if len(self.storage) > self.config.max_process_workers:
                self.logger.info("SERVER BUSY")
                return
            s = time.time()
            self._check_workers()

            jid = self._generate_random_id(func_name + str(random.random()))
            event = asyncio.Event()
            event.clear()
            self.storage[jid] = {
                "output": None,
                "flag": event
            }
            worker = random.choice(self.workers)
            self.logger.debug(f"CHOOSE WORKER {id(worker)} in {[id(item) for item in self.workers]}")
            worker.in_buffer.put_nowait((jid, func_name, args, kwargs))
            while True:
                try:
                    self.logger.debug(f"{id(worker)}. WAITING FOR DATA {jid}")
                    _jid, _output = worker.out_buffer.get_nowait()
                    self.logger.debug(f"{id(worker)}. GET DATA for {_jid}")
                except:
                    await asyncio.sleep(0.1)
                    if self.storage[jid]["flag"].is_set():
                        self.logger.debug(f"{id(worker)}. HAS OUTPUT {jid}")
                        break
                    else:
                        self.logger.debug(f"{id(worker)}. NONE DATA FOR {jid}")
                    continue
                self.storage[_jid]["output"] = _output
                self.storage[_jid]["flag"].set()
                if _jid == jid:
                    break
                if self.storage[jid]["flag"].is_set():
                    self.logger.debug(f"{id(worker)}. HAS OUTPUT {jid}")
                    break
            output = self.storage[jid]["output"]
            del self.storage[jid]
            self.logger.info(f"{id(worker)}. DONE {func_name} in {time.time() - s} (s)")
            return output

        def sync_process_custom_func(*args, **kwargs) -> BaseDataModel:
            if len(self.storage) > self.config.max_process_workers:
                self.logger.info("SERVER BUSY")
                return
            s = time.time()
            self._check_workers()

            jid = self._generate_random_id(func_name + str(random.random()))
            event = Event()
            event.clear()
            self.storage[jid] = {
                "output": None,
                "flag": event
            }
            worker = random.choice(self.workers)
            self.logger.debug(f"CHOOSE WORKER {id(worker)} in {[id(item) for item in self.workers]}")
            worker.in_buffer.put_nowait((jid, func_name, args, kwargs))
            while True:
                try:
                    self.logger.debug(f"{id(worker)}. WAITING FOR DATA {jid}")
                    _jid, _output = worker.out_buffer.get(timeout=1)
                    self.logger.debug(f"{id(worker)}. GET DATA for {_jid}")
                except:
                    if self.storage[jid]["flag"].is_set():
                        self.logger.debug(f"{id(worker)}. HAS OUTPUT {jid}")
                        break
                    else:
                        self.logger.debug(f"{id(worker)}. NONE DATA FOR {jid}")
                    continue
                self.storage[_jid]["output"] = _output
                self.storage[_jid]["flag"].set()
                if _jid == jid:
                    break
                if self.storage[jid]["flag"].is_set():
                    break

            # event.wait()
            output = self.storage[jid]["output"]
            del self.storage[jid]
            self.logger.info(f"{id(worker)}. DONE {func_name} in {time.time() - s} (s)")
            return output

        if is_async:
            return async_process_custom_func
        else:
            return sync_process_custom_func
