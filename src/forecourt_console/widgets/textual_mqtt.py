from __future__ import annotations
from textual import on, work
from textual.worker import get_current_worker
from textual.app import RenderResult
from textual.widget import Widget
from textual.message import Message
from textual.types import NoActiveAppError
from typing import Optional, Callable
import asyncio
import paho.mqtt.client as mqtt

class MqttEvent(Message):
    def __init__(self, sub: MqttSubscription) -> None:
        self.subscription: MqttSubscription = sub
        super().__init__()

    @property
    def control(self) -> MqttSubscription:
        return self.subscription

class MqttClient(Widget):
    def __init__(self, host: str="localhost", port: int=1883, **kwargs):
        super().__init__(**kwargs)
        self.display = False
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.host = host
        self.port = port
        self.subscribers: dict[str, Optional[MqttSubscription]] = {}
        self.subscribers_all: list[MqttSubscription] = []
        self.on_connect_subscribers = []
        self.on_disconnect_subscribers = []

    def on_mount(self) -> None:
        self.connect()

    @work(thread=True, group="mqtt")
    async def connect(self):
        try:
            self.ready = self.app._dom_ready  # type: ignore[unused-ignore]
        except NoActiveAppError:
            raise NoActiveAppError("No active app. Window manager has launched too early. Library bug.")
        except Exception as e:
            self.log.error(f"Error: {e}")
            raise e
        else:
            while not self.ready:
                await asyncio.sleep(0.2)
                self.ready = self.app._dom_ready  # type: ignore[unused-ignore]
                if not self.ready:
                    self.log("DOM not ready yet. Retrying...")

            self.log.debug("DOM is ready.")

            self.client.connect(self.host, self.port, keepalive=60)
            while (not get_current_worker().is_cancelled):
                self.client.loop()

    def on_connect(self, client: mqtt.Client, userdata, flags, rc):
        for topic in self.subscribers:
            client.subscribe(topic)
        if self.subscribe_all:
            client.subscribe('#')
        for callback in self.on_connect_subscribers:
            callback()

    def on_disconnect(self, client: mqtt.Client, userdata, rc):
        for callback in self.on_disconnect_subscribers:
            callback()

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        if msg.topic in self.subscribers:
            widget = self.subscribers[msg.topic]
            if widget: widget.post_message(MqttMessageSubscription.MqttMessageEvent(widget, msg.topic, msg.payload.decode()))
        for widget in self.subscribers_all:
            widget.post_message(MqttMessageSubscription.MqttMessageEvent(widget, msg.topic, msg.payload.decode()))

    def subscribe(self, pattern: str, widget: Optional[MqttSubscription], cb: Optional[Callable[...]] = None):
        # one must exist
        if widget == None and cb == None:
            return
        
        if pattern not in self.subscribers:
            self.client.subscribe(pattern)
            if cb: self.client.message_callback_add(pattern, cb)
        self.subscribers[pattern] = widget

    def unsubscribe(self, topic: str):
        if topic in self.subscribers:
            self.client.unsubscribe(topic)
            del self.subscribers[topic]


    def subscribe_all(self, widget: MqttSubscription):
        if not self.subscribers_all:
            self.client.subscribe('#')
        self.subscribers_all.append(widget)

    def subscribe_on_connect(self, callback: Callable[...]):
        if callback not in self.on_connect_subscribers:
            self.on_connect_subscribers.append(callback)
            if self.client.is_connected():
                callback()

    def unsubscribe_on_connect(self, callback: Callable[...]):
        if callback in self.on_connect_subscribers:
            self.on_connect_subscribers.remove(callback)

    def subscribe_on_disconnect(self, callback: Callable[...]):
        if callback not in self.on_disconnect_subscribers:
            self.on_disconnect_subscribers.append(callback)

    def unsubscribe_on_disconnect(self, callback: Callable[...]):
        if callback in self.on_disconnect_subscribers:
            self.on_disconnect_subscribers.remove(callback)

    def publish(self, topic: str, payload: str = "", qos: int = 0, retain: bool = False):
        self.client.publish(topic, payload, qos, retain)

class MqttSubscription(Widget): 
    def __init__(self, client: Optional[MqttClient] = None, **kwargs):
        super().__init__(**kwargs)
        self.display = False
        self.mqtt_client = client

    def client(self) -> Optional[MqttClient]:
        client = self.mqtt_client
        if client == None:
            clientList = self.app.query(MqttClient)
            if len(clientList) > 0: client = clientList[0]

        return client
    
    def publish(self, topic: str, payload: str = "", qos: int = 0, retain: bool = False):
        client = self.client()
        if client: client.publish(topic, payload, qos, retain)

class MqttMessageSubscription(MqttSubscription):
    def __init__(self, pattern: str, client: Optional[MqttClient] = None, **kwargs):
        super().__init__(client, **kwargs)
        self.pattern = pattern

    class MqttMessageEvent(MqttEvent):
        def __init__(self, sub: MqttSubscription, topic: str, payload: str) -> None:
            super().__init__(sub)
            self.topic = topic
            self.payload = payload

    def on_mount(self) -> None:
        return
        # subscribe to MqttClient
        client = self.client()
        if client:
            client.subscribe(self.pattern, None, self.on_message)

    def on_unmount(self) -> None:
        # unsubscribe to MqttClient
        client = self.client()
        if client:
            client.unsubscribe(self.pattern)

    def on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        self.post_message(self.MqttMessageEvent(self, msg.topic, msg.payload.decode()))

    def on_ready(self):
        # subscribe to MqttClient
        client = self.client()
        if client:
            client.subscribe(self.pattern, None, self.on_message)


class MqttConnectionSubscription(MqttSubscription):
    class MqttConnected(MqttEvent): pass
    class MqttDisconnected(MqttEvent): pass

    def on_mount(self) -> None:
        # subscribe to MqttClient
        client = self.client()
        if client:
            client.subscribe_on_connect(self.on_connect)
            client.subscribe_on_disconnect(self.on_disconnect)

    def on_unmount(self) -> None:
        # subscribe to MqttClient
        client = self.client()
        if client:
            client.unsubscribe_on_connect(self.on_connect)
            client.unsubscribe_on_disconnect(self.on_disconnect)

    def on_connect(self):
        self.post_message(self.MqttConnected(self))

    def on_disconnect(self):
        self.post_message(self.MqttDisconnected(self))