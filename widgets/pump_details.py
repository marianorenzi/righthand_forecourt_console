from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup, Container, Grid
from textual.widgets import Button, Label, Select, Switch, Static
from textual.reactive import reactive
from textual_plotext import PlotextPlot
from textual_slider import Slider
from widgets.pump import Pump
from widgets.pump_digits import PumpDigits
from modals.pump_preset import PresetModal
from modals.price_change import PriceChangeModal
from modals.auth_grades import AuthGradesModal
from typing import Optional



class PumpDetails(HorizontalGroup):

    pump: reactive[Optional[Pump]] = reactive(None, init=False)
    pump_unwatchers = []
    
    def compose(self) -> ComposeResult:
        # pump actions
        with VerticalGroup(id="pump_actions"):
            yield Static("[b]Pump Actions", classes="option_title")
            with HorizontalGroup():
                with VerticalGroup():
                    yield Button("Auth", id="auth_button")
                    yield Button("Stop", id="stop_button")
                    yield Button("Preset", id="preset_button")
                with VerticalGroup():
                    yield Button("Auth Grades", id="auth_grades_button")
                    yield Button("Resume", id="resume_button")
                    yield Button("Change Price", id="change_price_button")
        # emulator actions
        with VerticalGroup(classes="emulator_actions"):
            yield Static("[b]Emulator Actions", classes="option_title")
            with HorizontalGroup():
                yield Static("Handle", classes="option_label")
                yield Select([("None", -1), ("1", 0), ("2", 1), ("3", 2), ("4", 3), ("5", 4), ("6", 5), ("7", 6), ("8", 7)], id="handle_select", allow_blank=False)
            with HorizontalGroup():
                yield Label("Flow: 0", id="flow_label", classes="option_label")
                yield Slider(min=0, max=1000, value=0, id="flow_slider")
            with HorizontalGroup():
                yield Static("Force Valve", classes="option_label")
                yield Switch(id="valve_switch")
        # empty buffer space
        yield VerticalGroup()
        # grades totals and price
        with VerticalGroup(id="grades_info"):
            yield Static("[b]Grades Info", classes="option_title")
            with HorizontalGroup():
                yield Static("Volume", classes="option_label")
                yield PumpDigits(99999999.99, max_digits=10, max_decimals=2)
            with HorizontalGroup():
                yield Static("Money", classes="option_label")
                yield PumpDigits(99999999.99, max_digits=10, max_decimals=2)
            with HorizontalGroup():
                yield Static("PPU", classes="option_label")
                yield PumpDigits(99999999.99, max_digits=10, max_decimals=2)
        # last/current sale
        with Container(id="last_sale"):
            yield Static("[b]Last Sale", classes="option_title")
            with HorizontalGroup():
                yield Static("Volume", classes="option_label")
                yield PumpDigits(99999.999, max_digits=8, id="last_sale_volume")
            with HorizontalGroup():
                yield Static("Money", classes="option_label")
                yield PumpDigits(999999.999, max_digits=8, id="last_sale_money")
            with HorizontalGroup():
                yield Static("PPU", classes="option_label")
                yield PumpDigits(99999.999, max_digits=8, id="last_sale_price")
        # last sale plot (volume/flow over time)
        yield PlotextPlot(id="last_sale_plot")

    def on_mount(self):
        plt = self.query_one(PlotextPlot).plt
        y = plt.sin() # sinusoidal test signal
        plt.scatter(y, marker="fhd")
        plt.title("Last Sale Progress") # to apply a title
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.pump:
            # pump actions
            if event.button.id == "auth_button":
                self.pump.authorize()
            if event.button.id == "auth_grades_button":
                self.app.push_screen(AuthGradesModal(self.pump))
            if event.button.id == "preset_button":
                self.app.push_screen(PresetModal(self.pump))
            if event.button.id == "stop_button":
                self.pump.stop()
            if event.button.id == "resume_button":
                self.pump.resume()
            if event.button.id == "change_price_button":
                self.app.push_screen(PriceChangeModal(self.pump))

    @on(Slider.Changed, "#flow_slider")
    def on_flow_slider_changed_value(self) -> None:
        flow = self.query_one("#flow_slider", Slider).value / 10.0
        self.query_one("#flow_label", Label).update(f"Flow: {flow:.1f}")
        if self.pump: self.pump.set_flow(flow)

    @on(Select.Changed, "#handle_select")
    def on_handle_select_changed(self, event: Select.Changed) -> None:
        if self.pump: self.pump.set_handle(int(str(event.value)))

    @on(Switch.Changed, "#valve_switch")
    def on_valve_switch_changed(self, event: Select.Changed) -> None:
        if self.pump: self.pump.force_valve(bool(event.value))

    def on_pump_status(self):
        if not self.pump: return

    def on_pump_grades(self):
        if not self.pump: return

    def on_pump_calling_grade(self):
        if not self.pump: return

    def on_pump_sale(self):
        if not self.pump: return
        self.query_one("#last_sale_volume", PumpDigits).set_value(self.pump.sale["volume"])
        self.query_one("#last_sale_money", PumpDigits).set_value(self.pump.sale["money"])
        self.query_one("#last_sale_price", PumpDigits).set_value(self.pump.sale["price"])

    def on_pump_totals(self):
        if not self.pump: return

    def on_pump_prices(self):
        if not self.pump: return

    def on_pump_flow(self):
        if not self.pump: return
        self.query_one("#flow_slider", Slider).value = int(self.pump.emulator_flow * 10)

    def on_pump_valve(self):
        if not self.pump: return
        self.query_one("#valve_switch", Switch).value = self.pump.emulator_valve

    def set_pump(self, pump: Pump):
        self.pump = pump

    def watch_pump(self):
        # unwatch pump reactives and clear
        for unwatcher in self.pump_unwatchers:
            unwatcher()
        self.pump_unwatchers.clear()

        if not self.pump: return
        # last sale
        self.query_one("#last_sale_volume", PumpDigits).set_value(self.pump.sale["volume"])
        self.query_one("#last_sale_money", PumpDigits).set_value(self.pump.sale["money"])
        self.query_one("#last_sale_price", PumpDigits).set_value(self.pump.sale["price"])

        # totals and price (start on grade 0)
        # TODO

        # calling grade
        self.query_one("#handle_select", Select).value = self.pump.calling_grade
        
        # rtm history
        # TODO

        # watch pump reactives
        self.pump_unwatchers.append( self.watch(self.pump, "status", self.on_pump_status))
        self.pump_unwatchers.append( self.watch(self.pump, "grades", self.on_pump_grades))
        self.pump_unwatchers.append( self.watch(self.pump, "calling_grade", self.on_pump_calling_grade))
        self.pump_unwatchers.append( self.watch(self.pump, "sale", self.on_pump_sale))
        self.pump_unwatchers.append( self.watch(self.pump, "emulator_flow", self.on_pump_flow))
        self.pump_unwatchers.append( self.watch(self.pump, "emulator_valve", self.on_pump_valve))
        # self.pump_unwatchers.append( self.watch(self.pump, "totals", self.on_pump_totals))
        # self.pump_unwatchers.append( self.watch(self.pump, "prices", self.on_pump_prices))