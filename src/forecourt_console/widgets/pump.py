from textual.app import ComposeResult
from textual import on
from textual.message import Message
from textual.widgets import ListItem, Label
from textual.containers import VerticalGroup, HorizontalGroup
from textual.reactive import reactive
from widgets.textual_mqtt import MqttMessageSubscription, MqttConnectionSubscription
from typing import List
import json
import csv
import io
import random
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

        # reactive pump data
        self.set_reactive(Pump.status, "closed") #type: ignore
        self.set_reactive(Pump.grades, 0) #type: ignore
        self.set_reactive(Pump.calling_grade, -1) #type: ignore
        self.set_reactive(Pump.sale, {"volume": 0.0, "money": 0.0, "price": 0.0})
        self.set_reactive(Pump.totals, [{"volume":0.0,"money":0.0} for _ in range(8)])
        self.set_reactive(Pump.prices, [0.0 for _ in range(8)])
        self.set_reactive(Pump.rtm_history, []) #type: ignore
        self.set_reactive(Pump.emulator_valve, False) #type: ignore
        self.set_reactive(Pump.emulator_flow, 0.0) #type: ignore

        # auto sale
        self.auto_sale_config = {"auth_types": [], "grades": []}
        self.preset_value: float = 0.0
        self.preset_is_money: bool = False

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
        # mqtt subscriptions
        yield MqttMessageSubscription(f"evt/pumps/{self.pump_id}/status", id="mqtt_status")
        yield MqttMessageSubscription(f"evt/pumps/{self.pump_id}/calling_grade", id="mqtt_calling_grade")
        yield MqttMessageSubscription(f"evt/pumps/{self.pump_id}/sale_start", id="mqtt_sale_start")
        yield MqttMessageSubscription(f"evt/pumps/{self.pump_id}/sale_end", id="mqtt_sale_end")
        yield MqttMessageSubscription(f"evt/pumps/{self.pump_id}/rtm", id="mqtt_rtm")
        yield MqttMessageSubscription(f"evt/pumps/{self.pump_id}/totals", id="mqtt_totals")
        yield MqttMessageSubscription(f"evt/pumps/{self.pump_id}/ppu", id="mqtt_ppu")
        # mqtt emulator subscriptions
        yield MqttMessageSubscription(f"eevt/pumps/{self.pump_id}/flow", id="mqtt_flow")
        yield MqttMessageSubscription(f"eevt/pumps/{self.pump_id}/valve", id="mqtt_valve")
        # mqtt response subscriptions
        yield MqttMessageSubscription(f"res/pumps/{self.pump_id}/grades", id="mqtt_grades_res")
        yield MqttMessageSubscription(f"res/pumps/{self.pump_id}/status", id="mqtt_status_res")
        yield MqttMessageSubscription(f"res/pumps/{self.pump_id}/grade", id="mqtt_calling_grade_res")
        yield MqttMessageSubscription(f"res/pumps/{self.pump_id}/sale", id="mqtt_sale_res")
        yield MqttMessageSubscription(f"res/pumps/{self.pump_id}/totals", id="mqtt_totals_res")
        yield MqttMessageSubscription(f"res/pumps/{self.pump_id}/ppu", id="mqtt_ppu_res")
        yield MqttMessageSubscription(f"res/pumps/{self.pump_id}/type", id="mqtt_type_res")
        # mqtt connection subscription
        yield MqttConnectionSubscription()

    def authorize(self, grades: List[int]) -> None:
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(grades)
        csv_string = output.getvalue()
        self.query_one(MqttMessageSubscription).publish(f"cmd/pumps/{self.pump_id}/auth", csv_string)
        # register auth for auto sale
        self.set_auto_sale_auth()

    def preset(self, value: float, is_money: bool, grades: List[int]) -> None:
        payload = {}
        if is_money: payload["money"] = value
        else: payload["volume"] = value
        payload["grades"] = grades
        self.query_one(MqttMessageSubscription).publish(f"cmd/pumps/{self.pump_id}/preset", json.dumps(payload))
        # register auth for auto sale
        self.set_auto_sale_auth(value, is_money)

    def stop(self):
        self.query_one(MqttMessageSubscription).publish(f"cmd/pumps/{self.pump_id}/stop", "")

    def resume(self):
        self.query_one(MqttMessageSubscription).publish(f"cmd/pumps/{self.pump_id}/resume", "")

    def price_change(self, value: float, grade: int) -> None:
        payload = {"ppu": value, "grade": grade}
        self.query_one(MqttMessageSubscription).publish(f"cmd/pumps/{self.pump_id}/price_change", json.dumps(payload))

    def set_handle(self, handle: int):
            self.query_one(MqttMessageSubscription).publish(f"ecmd/pumps/{self.pump_id}/set_handle", f"{handle}")

    def set_flow(self, flow: float):
            self.query_one(MqttMessageSubscription).publish(f"ecmd/pumps/{self.pump_id}/set_flow", f"{flow}")

    def force_valve(self, state: bool):
            self.query_one(MqttMessageSubscription).publish(f"ecmd/pumps/{self.pump_id}/force_valve", f"{state}")

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

    def on_sale(self, sale: dict):
        self.sale.update(sale)
        self.mutate_reactive(Pump.sale) # type: ignore

    @on(MqttConnectionSubscription.MqttConnected)
    def on_mqtt_connect(self, evt: MqttConnectionSubscription.MqttConnected):
        # stop event from bubbling
        evt.stop()
        # request data to MQTT
        evt.subscription.publish(f"cmd/pumps/{self.pump_id}/type", "")
        evt.subscription.publish(f"cmd/pumps/{self.pump_id}/status", "")
        evt.subscription.publish(f"cmd/pumps/{self.pump_id}/grades", "")
        evt.subscription.publish(f"cmd/pumps/{self.pump_id}/grade", "")
        evt.subscription.publish(f"cmd/pumps/{self.pump_id}/sale", "")
        for i in range(0,8):
            evt.subscription.publish(f"cmd/pumps/{self.pump_id}/totals", f"{i}")
            evt.subscription.publish(f"cmd/pumps/{self.pump_id}/ppu", f"{i}")

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_status")
    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_status_res")
    def on_mqtt_status(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        self.status = evt.payload
        # report for auto sale processing
        self.do_auto_sale_status()

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_grades_res")
    def on_mqtt_grades(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        self.grades = int(evt.payload)

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_calling_grade")
    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_calling_grade_res")
    def on_mqtt_calling_grade(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        self.calling_grade = int(evt.payload)

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_sale_end")
    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_sale_res")
    def on_mqtt_sale(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        self.on_sale(json.loads(evt.payload))

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_sale_start")
    def on_mqtt_sale_start(self, evt: MqttMessageSubscription.MqttMessageEvent):
        self.rtm_history = []
        self.on_mqtt_sale(evt)

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_rtm")
    def on_mqtt_rtm(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        rtm = json.loads(evt.payload)

        # process rtm as sale for display update
        sale = rtm.copy()
        del sale["time"]
        self.on_sale(sale)

        # remove undesired data for rtm
        if len(self.rtm_history) == 0 or self.rtm_history[-1]["time"] != rtm["time"]:
            del rtm["grade"]
            del rtm["money"]
            self.rtm_history.append(rtm)
            self.mutate_reactive(Pump.rtm_history) # type: ignore

        # report for auto sale processing
        self.do_auto_sale_rtm()

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_totals")
    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_totals_res")
    def on_mqtt_totals(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        total = json.loads(evt.payload)
        totalAux = {"volume": total["volume"], "money": total["money"]}
        self.totals[total["grade"]] = totalAux
        self.mutate_reactive(Pump.totals)

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_ppu")
    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_ppu_res")
    def on_mqtt_price(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        price = json.loads(evt.payload)
        priceAux = price["price"]
        self.prices[price["grade"]] = priceAux
        self.mutate_reactive(Pump.prices)

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_type_res")
    def on_mqtt_type(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        self.pump_type = evt.payload
        self.query_one("#pump_type", Label).update(f"Type: {self.pump_type}")

        # retrieve flow and valves states for emulator
        if self.pump_type == "emulator":
            self.query_one(MqttMessageSubscription).publish(f"ecmd/pumps/{self.pump_id}/flow", "")
            self.query_one(MqttMessageSubscription).publish(f"ecmd/pumps/{self.pump_id}/valve", "")

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_flow")
    def on_mqtt_flow(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        self.emulator_flow = float(evt.payload)

    @on(MqttMessageSubscription.MqttMessageEvent, "#mqtt_valve")
    def on_mqtt_valve(self, evt: MqttMessageSubscription.MqttMessageEvent):
        # stop event from bubbling
        evt.stop()
        self.emulator_valve = bool(evt.payload == '1')

    def set_auto_sale_config(self, auto_sale_config: dict):
        self.auto_sale_config = auto_sale_config
        # evaluate status this first time
        self.do_auto_sale_status()

    def set_auto_sale_auth(self, value: float = 0, is_money: bool = False):
        self.preset_value = value
        self.preset_is_money = is_money

    def do_auto_sale_status(self):
        if self.status.lower() == "idle":
            self.do_auto_sale_idle()
        elif self.status.lower() == "calling":
            self.do_auto_sale_calling()
        elif self.status.lower() == "fueling":
            self.do_auto_sale_fuelilng()

    def do_auto_sale_idle(self):
        # if pump type is emulator and auto sale handle is enabled
        if self.pump_type == "emulator" and len(self.auto_sale_config["grades"]) > 0:
            # set random handle between selected handles
            self.set_handle(random.randint(0, len(self.auto_sale_config["grades"])-1))

    def do_auto_sale_calling(self):
        # if auto sale auth is disabled, return
        if len(self.auto_sale_config["auth_types"]) == 0: return

        # select random auth from enabled types
        auth_type = self.auto_sale_config["auth_types"][random.randint(0, len(self.auto_sale_config["auth_types"])-1)]

        # fill-up
        if auth_type == 0:
            self.authorize([])
        # volume preset
        elif auth_type == 1:
            self.preset(round(random.uniform(self.auto_sale_config["volume_min"], self.auto_sale_config["volume_max"]), 2), False, []) # type: ignore
        # money preset
        elif auth_type == 2:
            self.preset(round(random.uniform(self.auto_sale_config["money_min"], self.auto_sale_config["money_max"]), 2), True, []) # type: ignore

    def do_auto_sale_fuelilng(self):
        # decide max end time?
        # launch flow timer?
        pass

    def do_auto_sale_rtm(self):
        # ignore if it's not a preset
        if self.preset_value == 0: return
        # check completed preset
        if ((self.preset_is_money and self.sale["money"] >= self.preset_value) or
            self.sale["volume"] >= self.preset_value):
                self.set_handle(-1)