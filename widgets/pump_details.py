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
                yield Slider(min=0, max=100, value=0, id="flow_slider")
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
                yield PumpDigits(99999999.99, max_digits=10, max_decimals=2, id="totals_volume")
            with HorizontalGroup():
                yield Static("Money", classes="option_label")
                yield PumpDigits(99999999.99, max_digits=10, max_decimals=2, id="totals_money")
            with HorizontalGroup():
                yield Static("PPU", classes="option_label")
                yield PumpDigits(99999999.99, max_digits=6, id="grade_price")
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
                yield PumpDigits(99999.999, max_digits=6, id="last_sale_price")
        # last sale plot (volume/flow over time)
        yield PlotextPlot(id="last_sale_plot")

    def on_mount(self):
        # plt = self.query_one(PlotextPlot).plt
        # y = plt.sin() # sinusoidal test signal
        # plt.scatter(y, marker="fhd")
        # plt.title("Last Sale Progress") # to apply a title
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
        with self.query_one("#handle_select", Select).prevent(Select.Changed):
            self.query_one("#handle_select", Select).value = self.pump.calling_grade

    def on_pump_sale(self):
        if self.pump: sale = self.pump.sale
        else: sale = {"volume": 0, "money": 0, "price": 0}
        
        self.query_one("#last_sale_volume", PumpDigits).set_value(sale["volume"])
        self.query_one("#last_sale_money", PumpDigits).set_value(sale["money"])
        self.query_one("#last_sale_price", PumpDigits).set_value(sale["price"])

    def on_pump_rtm_history(self):
        if not self.pump: 
            plt_widget = self.query_one(PlotextPlot).plt.clear_data()
            return

        def calc_flows(rtm_history):
            seen_times = set()
            filtered_history = []

            for entry in rtm_history:
                t = entry["time"]
                if t not in seen_times:
                    filtered_history.append(entry)
                    seen_times.add(t)

            flows = []
            times = []
            for i in range(1, len(filtered_history)):
                t1 = filtered_history[i - 1]["time"]
                t2 = filtered_history[i]["time"]
                v1 = filtered_history[i - 1]["volume"]
                v2 = filtered_history[i]["volume"]

                dt = t2 - t1
                dv = v2 - v1

                if dt != 0:
                    flows.append(dv / dt)
                else:
                    flows.append(0.0)  # or None or float("nan"), depending on your needs
                times.append(t2)
            return flows, times

        plt_widget = self.query_one(PlotextPlot)
        plt = plt_widget.plt
        plt.clear_data()
        if self.pump.rtm_history:
            times = [d["time"] for d in self.pump.rtm_history]
            volumes = [d["volume"] for d in self.pump.rtm_history]
            flows, flow_times = calc_flows(self.pump.rtm_history)
            plt.plot(times, volumes, marker="fhd", label="Volume", )
            if flows: 
                plt.plot(flow_times, flows, marker="fhd", label="Flow", yside="right")
            plt.xfrequency(1)
            plt.xticks([])
        plt_widget.refresh()

    def on_pump_totals(self):
        if self.pump: total = self.pump.totals[0]
        else: total = {"volume": 0, "money": 0}
        
        self.query_one("#totals_volume", PumpDigits).set_value(total["volume"])
        self.query_one("#totals_money", PumpDigits).set_value(total["money"])

    def on_pump_prices(self):
        if self.pump:  price = self.pump.prices[0]
        else: price = 0.0
        self.query_one("#grade_price", PumpDigits).set_value(price)

    def on_pump_flow(self):
        if not self.pump: return
        with self.query_one("#flow_slider", Slider).prevent(Slider.Changed):
            self.query_one("#flow_slider", Slider).value = int(self.pump.emulator_flow * 10)
            self.query_one("#flow_label", Label).update(f"Flow: {self.pump.emulator_flow:.1f}")

    def on_pump_valve(self):
        if not self.pump: return
        with self.query_one("#valve_switch", Switch).prevent(Switch.Changed):
            self.query_one("#valve_switch", Switch).value = self.pump.emulator_valve

    def set_pump(self, pump: Optional[Pump]):
        self.set_reactive(PumpDetails.pump, pump)
        self.mutate_reactive(PumpDetails.pump)

    def watch_pump(self):
        # unwatch pump reactives and clear
        for unwatcher in self.pump_unwatchers:
            if unwatcher: unwatcher()
        self.pump_unwatchers.clear()

        # last sale
        self.on_pump_sale()

        # totals and price (start on grade 0)
        self.on_pump_totals()
        self.on_pump_prices()

        # calling grade
        self.on_pump_calling_grade()
        
        # rtm history
        self.on_pump_rtm_history()

        # watch pump reactives
        if self.pump:
            self.pump_unwatchers.append(self.watch(self.pump, "status", self.on_pump_status, False))
            self.pump_unwatchers.append(self.watch(self.pump, "grades", self.on_pump_grades, False))
            self.pump_unwatchers.append(self.watch(self.pump, "calling_grade", self.on_pump_calling_grade, False))
            self.pump_unwatchers.append(self.watch(self.pump, "sale", self.on_pump_sale, False))
            self.pump_unwatchers.append(self.watch(self.pump, "rtm_history", self.on_pump_rtm_history, False))
            self.pump_unwatchers.append(self.watch(self.pump, "totals", self.on_pump_totals, False))
            self.pump_unwatchers.append(self.watch(self.pump, "prices", self.on_pump_prices, False))
            self.pump_unwatchers.append(self.watch(self.pump, "emulator_flow", self.on_pump_flow, False))
            self.pump_unwatchers.append(self.watch(self.pump, "emulator_valve", self.on_pump_valve, False))