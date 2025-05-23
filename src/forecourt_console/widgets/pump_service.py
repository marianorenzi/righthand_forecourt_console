from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Label, TabPane, ListView
from textual.containers import Container
from widgets.pump_details import PumpDetails
from widgets.pump_grid import PumpGrid
from widgets.pump import Pump
from widgets.mqtt_console import MqttViewer
from widgets.mqtt_console import MqttClient
from widgets.maximizable_plot import MaximizablePlotextPlot
from modals.pump_preset import PresetModal
from modals.price_change import PriceChangeModal

class PumpServicePane(TabPane):
    def __init__(self, title: str, mqtt_client: MqttClient, **kwargs):
        super().__init__(title, **kwargs)
        self.mqtt_client = mqtt_client

    BINDINGS = [
    ("[", "prev_pump", "Previous Pump"),
    ("]", "next_pump", "Next Pump"),
    ("a", "auth_pump", "Authorize Pump"),
    ("p", "preset_pump", "Preset Pump"),
    ("s", "stop_pump", "Stop Pump"),
    ("r", "resume_pump", "Resume Pump"),
    ("r", "change_price", "Change Pump Price"),
    ("1-8", "", "Handle N"),
    ("0", "handle_pump(-1)", "Handle Off"),
    Binding("1", "handle_pump(0)", "Handle 1", show=False),
    Binding("2", "handle_pump(1)", "Handle 2", show=False),
    Binding("3", "handle_pump(2)", "Handle 3", show=False),
    Binding("4", "handle_pump(3)", "Handle 4", show=False),
    Binding("5", "handle_pump(4)", "Handle 5", show=False),
    Binding("6", "handle_pump(5)", "Handle 6", show=False),
    Binding("7", "handle_pump(6)", "Handle 7", show=False),
    Binding("8", "handle_pump(7)", "Handle 8", show=False),
    ("p", "maximize_plot", "Maximize Plot")
    ]
        
    def compose(self) -> ComposeResult:
        yield PumpDetails()
        with Container():
            yield PumpGrid()

    def on_mount(self):
        self.query_one(PumpGrid).focus()

    def on_list_view_selected(self, event: ListView.Selected):
        if isinstance(event.item, Pump):
            self.query_one(PumpDetails).set_pump(event.item)
        else:
            self.query_one(PumpDetails).set_pump(None)

    def action_maximize_plot(self):
        self.app.screen.maximize(self.query_one(PumpDetails).query_one(MaximizablePlotextPlot), False)

    def action_prev_pump(self):
        self.query_one(PumpGrid).action_cursor_up()
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): self.query_one(PumpDetails).set_pump(pump)
        

    def action_next_pump(self):
        self.query_one(PumpGrid).action_cursor_down()
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): self.query_one(PumpDetails).set_pump(pump)

    def action_auth_pump(self):
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): pump.authorize()

    def action_stop_pump(self):
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): pump.stop()

    def action_resume_pump(self):
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): pump.resume()

    def action_handle_pump(self, handle: int):
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): pump.set_handle(handle)

    def action_preset_pump(self):
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): self.app.push_screen(PresetModal(pump))

    def action_change_price(self):
        pump = self.query_one(PumpGrid).highlighted_child
        if pump and isinstance(pump, Pump): self.app.push_screen(PriceChangeModal(pump))

    @on(Pump.StatusEvent)
    def on_pump_status(self, message: Pump.StatusEvent):
        self.query_one(PumpDetails).set_pump_status(message.status)
        message.stop()

    @on(Pump.GradesEvent)
    def on_pump_grades(self, message: Pump.GradesEvent):
        self.query_one(PumpDetails).set_pump_grades(message.grades)
        message.stop()

    @on(Pump.CallingGradeEvent)
    def on_pump_calling_grade(self, message: Pump.CallingGradeEvent):
        self.query_one(PumpDetails).set_pump_calling_grade(message.calling_grade)
        message.stop()

    @on(Pump.SaleEvent)
    def on_pump_sale(self, message: Pump.SaleEvent):
        self.query_one(PumpDetails).set_pump_sale(message.sale)
        message.stop()

    @on(Pump.RtmHistoryEvent)
    def on_pump_rtm(self, message: Pump.RtmHistoryEvent):
        self.query_one(PumpDetails).set_pump_rtm_history(message.rtm_history)
        message.stop()

    @on(Pump.TotalsEvent)
    def on_pump_totals(self, message: Pump.TotalsEvent):
        self.query_one(PumpDetails).set_pump_totals(message.totals)
        message.stop()

    @on(Pump.PricesEvent)
    def on_pump_prices(self, message: Pump.PricesEvent):
        self.query_one(PumpDetails).set_pump_prices(message.prices)
        message.stop()

    @on(Pump.FlowEvent)
    def on_pump_flow(self, message: Pump.FlowEvent):
        self.query_one(PumpDetails).set_pump_flow(message.flow)
        message.stop()

    @on(Pump.ValveEvent)
    def on_pump_valve(self, message: Pump.ValveEvent):
        self.query_one(PumpDetails).set_pump_valve(message.valve)
        message.stop()