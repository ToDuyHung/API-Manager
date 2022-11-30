import time
from threading import Thread
from datetime import datetime
import random
from uuid import uuid4, uuid5

from TMTChatbot.ServiceWrapper.services.stomp_socket.frame import Frame
import websocket
import logging

VERSIONS = '1.0,1.1'


class Client:
    def __init__(self, host: str, port: str, endpoint, client_id: str = None, reconnect_callback=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.client_id = client_id
        self.session_id = None
        self.ws = None

        self.opened = False
        self.connected = False
        self.subscribed = False

        self.counter = 0
        self.subscriptions = {}

        self._connect_callback = None
        self.error_callback = None
        self.init_socket()
        self.reconnect_callback = reconnect_callback

    def init_socket(self):
        self.init_id()
        print(f"TRY TO CONNECT TO SOCKET AT {self.url} {self.connected}")
        if self.ws is not None:
            self.ws.close()
        self.ws = websocket.WebSocketApp(self.url)
        self.ws.on_open = self._on_open
        self.ws.on_message = self._on_message
        self.ws.on_error = self._on_error
        self.ws.on_close = self._on_close
        self.connect(login=self.client_id, passcode=self.session_id, timeout=0)
        while not self.connected:
            time.sleep(1)
        for destination in self.subscriptions:
            print("AUTO SUBSCRIBE")
            self.auto_subscribe(destination=destination, callback_func=self.subscriptions[destination])
        time.sleep(1)

    @property
    def url(self):
        return f"ws://{self.host}:{self.port}/{self.endpoint}/{self.client_id}/{self.session_id}/websocket"

    def init_id(self):
        if self.client_id is None:
            self.client_id = str(random.randint(0, 1000000)) + str(int(datetime.now().timestamp()))
        self.session_id = str(uuid5(uuid4(), self.client_id))
        print("INIT CONNECTION WITH", self.client_id, self.session_id)

    def _connect(self, timeout=0):
        thread = Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()

        total_ms = 0
        while self.opened is False:
            time.sleep(0.25)
            total_ms += 250
            if 0 < timeout < total_ms:
                raise TimeoutError(f"Connection to {self.url} timed out")

    def _on_open(self):
        self.opened = True

    def _on_close(self):
        self.subscribed = True
        self.logger.debug("Whoops! Lost connection to " + self.ws.url)
        print("Whoops! Lost connection to " + self.ws.url)
        self._clean_up()
        self.ws.close()
        self.ws = None
        if self.reconnect_callback is not None:
            self.reconnect_callback()

    def _on_error(self, error):
        self.logger.debug(error)

    def _on_message(self, message):
        self.logger.debug("\n<<< " + str(message))
        frame = Frame.unmarshall_single(message)
        _results = []
        if frame.command == "CONNECTED":
            self.connected = True
            self.logger.debug("connected to server " + self.url)
            if self._connect_callback is not None:
                _results.append(self._connect_callback(frame))
        elif frame.command == "MESSAGE":

            subscription = frame.headers['subscription']

            if subscription in self.subscriptions:
                on_receive = self.subscriptions[subscription]
                message_id = frame.headers['message-id']

                def ack(headers):
                    if headers is None:
                        headers = {}
                    return self.ack(message_id, subscription, headers)

                def nack(headers):
                    if headers is None:
                        headers = {}
                    return self.nack(message_id, subscription, headers)

                frame.ack = ack
                frame.nack = nack
                ack(None)
                _results.append(on_receive(frame))
            else:
                info = "Unhandled received MESSAGE: " + str(frame)
                self.logger.debug(info)
                _results.append(info)
        elif frame.command == 'RECEIPT':
            pass
        elif frame.command == 'ERROR':
            if self.error_callback is not None:
                _results.append(self.error_callback(frame))
        else:
            info = "Unhandled received MESSAGE: " + frame.command
            self.logger.debug(info)
            _results.append(info)

        return _results

    def _transmit(self, command, headers, body=None):
        out = Frame.marshall(command, headers, body)
        self.logger.debug("\n>>> " + out)
        self.ws.send(out)

    def connect(self, login=None, passcode=None, headers=None, connect_callback=None, error_callback=None,
                timeout=0):
        self.logger.debug("Opening web socket...")
        self._connect(timeout)

        headers = headers if headers is not None else {}
        headers['host'] = self.url
        headers['accept-version'] = VERSIONS
        headers['heart-beat'] = '10000,10000'

        if login is not None:
            headers['login'] = login
        if passcode is not None:
            headers['passcode'] = passcode

        self._connect_callback = connect_callback
        self.error_callback = error_callback

        self._transmit('CONNECT', headers)

    def send_heart_beat(self):
        self.ws.send("\\o")

    def disconnect(self, disconnect_callback=None, headers=None):
        if headers is None:
            headers = {}

        self._transmit("DISCONNECT", headers)
        self.ws.on_close = None
        self.ws.close()
        self._clean_up()

        if disconnect_callback is not None:
            disconnect_callback()

    def _clean_up(self):
        self.client_id = None
        self.connected = False

    def send(self, destination, headers=None, body=None):
        if headers is None:
            headers = {}
        if body is None:
            body = ''
        headers['destination'] = destination
        return self._transmit("SEND", headers, body)

    def subscribe(self, destination, callback=None, headers=None):
        destination = destination + self.client_id
        if headers is None:
            headers = {}
        if 'id' not in headers:
            headers["id"] = "sub-" + str(self.counter)
            self.counter += 1
        headers['destination'] = destination
        self.subscriptions[headers["id"]] = callback
        self._transmit("SUBSCRIBE", headers)
        time.sleep(1)
        self.subscribed = True

        def unsubscribe():
            self.unsubscribe(headers["id"])

        self.logger.info(f"SUBSCRIBE to {destination}")
        return headers["id"], unsubscribe

    def auto_subscribe(self, destination, callback_func):
        if self.connected:
            headers = {"id": destination}
            self.subscribe(destination, callback=callback_func, headers=headers)
        else:
            self.subscriptions[destination] = callback_func

    def unsubscribe(self, _id):
        del self.subscriptions[_id]
        return self._transmit("UNSUBSCRIBE", {
            "id": _id
        })

    def ack(self, message_id, subscription, headers):
        if headers is None:
            headers = {}
        headers["message-id"] = message_id
        headers['subscription'] = subscription
        return self._transmit("ACK", headers)

    def nack(self, message_id, subscription, headers):
        if headers is None:
            headers = {}
        headers["message-id"] = message_id
        headers['subscription'] = subscription
        return self._transmit("NACK", headers)
