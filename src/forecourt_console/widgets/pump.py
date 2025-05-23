from textual.app import ComposeResult
from textual import on
from textual.message import Message
from textual.widgets import ListItem, Label
from textual.containers import VerticalGroup, HorizontalGroup
from textual.reactive import reactive
from widgets.mqtt_console import MqttClient
from typing import List
import json
import csv
import io
import threading
import copy

class PumpValue(HorizontalGroup):

    value = reactive("", init=False)

    def __init__(self, label_text: str, **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text

    def compose(self) -> ComposeResult:
        yield Label(self.label_text, classes="pump_value_label")
        yield Label(self.value, id="val", classes="pump_value")

    def watch_value(self):
        self.query_one("#val", Label).update(self.value)

    def update(self, value: str):
        self.value = value

class Pump(ListItem):

    pump_type = ""
    status = reactive(str, init=False)
    grades = reactive(int, init=False)
    calling_grade = reactive(int, init=False)
    sale = reactive(dict, init=False)
    totals = reactive(list[dict], init=False)
    prices = reactive(list[float], init=False)
    rtm_history = reactive(list[dict], init=False)
    emulator_valve = reactive(bool, init=False)
    emulator_flow = reactive(float, init=False)

    def __init__(self, pump_id: int, **kwargs):
        super().__init__(**kwargs)
        self.pump_id = pump_id
        self.mqtt_client: MqttClient = self.app.mqtt

        self.set_reactive(Pump.status, "closed") #type: ignore
        self.set_reactive(Pump.grades, 0) #type: ignore
        self.set_reactive(Pump.calling_grade, -1) #type: ignore
        self.set_reactive(Pump.sale, {"volume": 0.0, "money": 0.0, "price": 0.0})
        self.set_reactive(Pump.totals, [{"volume":0.0,"money":0.0} for _ in range(8)])
        self.set_reactive(Pump.prices, [0.0 for _ in range(8)])
        self.set_reactive(Pump.rtm_history, []) #type: ignore
        self.set_reactive(Pump.emulator_valve, False) #type: ignore
        self.set_reactive(Pump.emulator_flow, 0.0) #type: ignore

    class StatusEvent(Message):
        def __init__(self, status: str, **kwargs):
            super().__init__(**kwargs)
            self.status = status

    class GradesEvent(Message):
        def __init__(self, grades: int, **kwargs):
            super().__init__(**kwargs)
            self.grades = grades

    class CallingGradeEvent(Message):
        def __init__(self, calling_grade: int, **kwargs):
            super().__init__(**kwargs)
            self.calling_grade = calling_grade

    class SaleEvent(Message):
        def __init__(self, sale: dict, **kwargs):
            super().__init__(**kwargs)
            self.sale = sale

    class RtmHistoryEvent(Message):
        def __init__(self, rtm_history: list[dict], **kwargs):
            super().__init__(**kwargs)
            self.rtm_history = rtm_history

    class TotalsEvent(Message):
        def __init__(self, totals: list[dict], **kwargs):
            super().__init__(**kwargs)
            self.totals = totals

    class PricesEvent(Message):
        def __init__(self, prices: list[float], **kwargs):
            super().__init__(**kwargs)
            self.prices = prices

    class FlowEvent(Message):
        def __init__(self, flow: float, **kwargs):
            super().__init__(**kwargs)
            self.flow = flow

    class ValveEvent(Message): 
        def __init__(self, valve: bool, **kwargs):
            super().__init__(**kwargs)
            self.valve = valve

    def compose(self) -> ComposeResult:
        yield Label(f"Pump {self.pump_id}", classes="pump_id")
        yield Label(f"Type: unknown", id="pump_type")
        yield PumpValue("Status", id="pump_status")
        yield PumpValue("V", id="sale_volume")
        yield PumpValue("$", id="sale_money")
        yield PumpValue("$/V", id="sale_price")

    def on_mount(self):
        self.mqtt_subscribe()

    def on_unmount(self):
        self.mqtt_unsubscribe()

    def authorize(self, grades: List[int]) -> None:

        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(grades)
        csv_string = output.getvalue()
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/auth", csv_string)

    def preset(self, value: float, is_money: bool, grades: List[int]) -> None:
        payload = {}
        if is_money: payload["money"] = value
        else: payload["volume"] = value
        payload["grades"] = grades
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/preset", json.dumps(payload))

    def stop(self):
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/stop", "")

    def resume(self):
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/resume", "")

    def price_change(self, value: float, grade: int) -> None:
        payload = {"ppu": value, "grade": grade}
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/price_change", json.dumps(payload))

    def set_handle(self, handle: int):
            self.mqtt_client.publish(f"ecmd/pumps/{self.pump_id}/set_handle", f"{handle}")

    def set_flow(self, flow: float):
            self.mqtt_client.publish(f"ecmd/pumps/{self.pump_id}/set_flow", f"{flow}")

    def force_valve(self, state: bool):
            self.mqtt_client.publish(f"ecmd/pumps/{self.pump_id}/force_valve", f"{state}")

    def watch_status(self):
        self.query_one("#pump_status", PumpValue).update(self.status)
        if self.highlighted:
            self.post_message(self.StatusEvent(self.status))
        if self.status == "idle": 
            self.calling_grade = -1
            if self.highlighted:
                self.post_message(self.CallingGradeEvent(self.calling_grade))

    def watch_grades(self):
        if self.highlighted:
            self.post_message(self.GradesEvent(self.grades))
    
    def watch_calling_grade(self):
        if self.highlighted:
            self.post_message(self.CallingGradeEvent(self.calling_grade))

    def watch_totals(self):
        if self.highlighted:
            self.post_message(self.TotalsEvent(self.totals.copy()))

    def watch_prices(self):
        if self.highlighted:
            self.post_message(self.PricesEvent(self.prices.copy()))

    def watch_rtm_history(self):
        if self.highlighted:
            self.post_message(self.RtmHistoryEvent(self.rtm_history.copy()))

    def watch_sale(self):
        self.query_one("#sale_volume", PumpValue).update(f"{self.sale["volume"]:.3f}")
        self.query_one("#sale_money", PumpValue).update(f"{self.sale["money"]:.3f}")
        self.query_one("#sale_price", PumpValue).update(f"{self.sale["price"]:.3f}")
        if self.highlighted:
            self.post_message(self.SaleEvent(self.sale.copy()))

    def watch_emulator_flow(self):
        if self.highlighted:
            self.post_message(self.FlowEvent(self.emulator_flow))

    def watch_emulator_valve(self):
        if self.highlighted:
            self.post_message(self.ValveEvent(self.emulator_valve))

    @on(MqttClient.MqttMessage)
    def on_mqtt_message(self, message: MqttClient.MqttMessage):
        if message.topic == f"evt/pumps/{self.pump_id}/status" or message.topic == f"res/pumps/{self.pump_id}/status":
            self.on_mqtt_status(message.payload)
        elif message.topic == f"evt/pumps/{self.pump_id}/calling_grade" or message.topic == f"res/pumps/{self.pump_id}/grade":
            self.on_mqtt_calling_grade(message.payload)
        elif message.topic == f"evt/pumps/{self.pump_id}/totals" or message.topic == f"res/pumps/{self.pump_id}/totals":
            self.on_mqtt_totals(message.payload)
        elif message.topic == f"evt/pumps/{self.pump_id}/ppu" or message.topic == f"res/pumps/{self.pump_id}/ppu":
            self.on_mqtt_price(message.payload)
        elif message.topic == f"evt/pumps/{self.pump_id}/sale_start":
            self.on_mqtt_sale_start(message.payload)
        elif message.topic == f"evt/pumps/{self.pump_id}/sale_end":
            self.on_mqtt_sale(message.payload)
        elif message.topic == f"evt/pumps/{self.pump_id}/rtm":
            self.on_mqtt_rtm(message.payload)
        elif message.topic == f"eevt/pumps/{self.pump_id}/flow":
            self.on_mqtt_flow(message.payload)
        elif message.topic == f"eevt/pumps/{self.pump_id}/valve":
            self.on_mqtt_valve(message.payload)
        elif message.topic == f"res/pumps/{self.pump_id}/grades":
            self.on_mqtt_grades(message.payload)
        elif message.topic == f"res/pumps/{self.pump_id}/sale":
            self.on_mqtt_sale(message.payload)
        elif message.topic == f"res/pumps/{self.pump_id}/type":
            self.on_mqtt_type(message.payload)
        else:
            return
        
        # message handled, stop the message from bubbling
        message.stop()

    def mqtt_subscribe(self):
        self.mqtt_client.subscribe(f"evt/pumps/{self.pump_id}/status", self)
        self.mqtt_client.subscribe(f"evt/pumps/{self.pump_id}/calling_grade", self)
        self.mqtt_client.subscribe(f"evt/pumps/{self.pump_id}/sale_start", self)
        self.mqtt_client.subscribe(f"evt/pumps/{self.pump_id}/sale_end", self)
        self.mqtt_client.subscribe(f"evt/pumps/{self.pump_id}/rtm", self)
        self.mqtt_client.subscribe(f"evt/pumps/{self.pump_id}/totals", self)
        self.mqtt_client.subscribe(f"evt/pumps/{self.pump_id}/ppu", self)
        # subscribe to MQTT emulator extended events
        self.mqtt_client.subscribe(f"eevt/pumps/{self.pump_id}/flow", self)
        self.mqtt_client.subscribe(f"eevt/pumps/{self.pump_id}/valve", self)
        # subscribe to MQTT responses
        self.mqtt_client.subscribe(f"res/pumps/{self.pump_id}/grades", self)
        self.mqtt_client.subscribe(f"res/pumps/{self.pump_id}/status", self)
        self.mqtt_client.subscribe(f"res/pumps/{self.pump_id}/grade", self)
        self.mqtt_client.subscribe(f"res/pumps/{self.pump_id}/sale", self)
        self.mqtt_client.subscribe(f"res/pumps/{self.pump_id}/totals", self)
        self.mqtt_client.subscribe(f"res/pumps/{self.pump_id}/ppu", self)
        self.mqtt_client.subscribe(f"res/pumps/{self.pump_id}/type", self)
        # subscribe to on_connect
        self.mqtt_client.subscribe_on_connect(self.on_mqtt_connect)

    def mqtt_unsubscribe(self):
        self.mqtt_client.unsubscribe(f"evt/pumps/{self.pump_id}/status")
        self.mqtt_client.unsubscribe(f"evt/pumps/{self.pump_id}/calling_grade")
        self.mqtt_client.unsubscribe(f"evt/pumps/{self.pump_id}/sale_start")
        self.mqtt_client.unsubscribe(f"evt/pumps/{self.pump_id}/sale_end")
        self.mqtt_client.unsubscribe(f"evt/pumps/{self.pump_id}/rtm")
        self.mqtt_client.unsubscribe(f"evt/pumps/{self.pump_id}/totals")
        self.mqtt_client.unsubscribe(f"evt/pumps/{self.pump_id}/ppu")
        # subscribe to MQTT emulator extended events
        self.mqtt_client.unsubscribe(f"eevt/pumps/{self.pump_id}/flow")
        self.mqtt_client.unsubscribe(f"eevt/pumps/{self.pump_id}/valve")
        # subscribe to MQTT responses
        self.mqtt_client.unsubscribe(f"res/pumps/{self.pump_id}/grades")
        self.mqtt_client.unsubscribe(f"res/pumps/{self.pump_id}/status")
        self.mqtt_client.unsubscribe(f"res/pumps/{self.pump_id}/grade")
        self.mqtt_client.unsubscribe(f"res/pumps/{self.pump_id}/sale")
        self.mqtt_client.unsubscribe(f"res/pumps/{self.pump_id}/totals")
        self.mqtt_client.unsubscribe(f"res/pumps/{self.pump_id}/ppu")
        self.mqtt_client.unsubscribe(f"res/pumps/{self.pump_id}/type")
        # subscribe to on_connect
        self.mqtt_client.unsubscribe_on_connect(self.on_mqtt_connect)

    def on_mqtt_connect(self, rc):
        # request data to MQTT
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/type", "")
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/status", "")
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/grades", "")
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/grade", "")
        self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/sale", "")
        for i in range(0,8):
            self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/totals", f"{i}")
            self.mqtt_client.publish(f"cmd/pumps/{self.pump_id}/ppu", f"{i}")

    def on_mqtt_status(self, payload: str):
        self.status = payload

    def on_mqtt_grades(self, payload: str):
        self.grades = int(payload)

    def on_mqtt_calling_grade(self, payload: str):
        self.calling_grade = int(payload)

    def on_mqtt_sale(self, payload: str):
        self.sale.update(json.loads(payload))
        self.mutate_reactive(Pump.sale) # type: ignore

    def on_mqtt_sale_start(self, payload: str):
        self.rtm_history = []
        self.on_mqtt_sale(payload)

    def on_mqtt_rtm(self, payload: str):
        rtm = json.loads(payload)

        # process rtm as sale for display update
        sale = rtm.copy()
        del sale["time"]
        payload = json.dumps(sale)
        self.on_mqtt_sale(payload)

        # remove undesired data for rtm
        if len(self.rtm_history) == 0 or self.rtm_history[-1]["time"] != rtm["time"]:
            del rtm["grade"]
            del rtm["money"]
            self.rtm_history.append(rtm)
            self.mutate_reactive(Pump.rtm_history) # type: ignore

    def on_mqtt_totals(self, payload: str):
        total = json.loads(payload)
        totalAux = {"volume": total["volume"], "money": total["money"]}
        self.totals[total["grade"]] = totalAux
        self.mutate_reactive(Pump.totals)

    def on_mqtt_price(self, payload: str):
        price = json.loads(payload)
        priceAux = price["price"]
        self.prices[price["grade"]] = priceAux
        self.mutate_reactive(Pump.prices)

    def on_mqtt_type(self, payload: str):
        self.pump_type = payload
        self.query_one("#pump_type", Label).update(f"Type: {payload}")

        # retrieve flow and valves states for emulator
        if payload == "emulator":
            self.mqtt_client.publish(f"ecmd/pumps/{self.pump_id}/flow", "")
            self.mqtt_client.publish(f"ecmd/pumps/{self.pump_id}/valve", "")

    def on_mqtt_flow(self, payload: str):
        self.emulator_flow = float(payload)

    def on_mqtt_valve(self, payload: str):
        self.emulator_valve = bool(payload == '1')
