from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, HorizontalScroll, VerticalGroup, Container, Grid
from textual.widgets import Button, Label, Select, Switch, Static
from textual.reactive import reactive
from textual_slider import Slider
from widgets.pump import Pump
from widgets.pump_digits import PumpDigits
from widgets.maximizable_plot import MaximizablePlotextPlot
from modals.pump_preset import PresetModal
from modals.price_change import PriceChangeModal
from modals.auth_grades import AuthGradesModal
from modals.auto_sale import AutoSaleModal
from typing import Optional

class PumpDetails(HorizontalGroup):

    pump: reactive[Pump | None] = reactive(None, init=False)
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
        with VerticalGroup(id="emulator_actions"):
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
        with VerticalGroup():
            yield Button("Auto Sale", id="auto_sale_button")
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
        with Container(id="last_sale_plot_container"):
            yield MaximizablePlotextPlot(id="last_sale_plot")

    def on_mount(self):
        pass

    def set_pump(self, pump: Optional[Pump]):
        # self.set_reactive(PumpDetails.pump, pump)
        # self.mutate_reactive(PumpDetails.pump)

        self.pump = pump

        if pump:
            self.set_pump_status(pump.status)
            self.set_pump_grades(pump.grades)
            self.set_pump_calling_grade(pump.calling_grade)
            self.set_pump_sale(pump.sale)
            self.set_pump_rtm_history(pump.rtm_history)
            self.set_pump_totals(pump.totals)
            self.set_pump_prices(pump.prices)
            self.set_pump_flow(pump.emulator_flow)
            self.set_pump_valve(pump.emulator_valve)

    # def watch_pump(self):
    #     return
    #     # unwatch pump reactives and clear
    #     for unwatcher in self.pump_unwatchers:
    #         if unwatcher: unwatcher()
    #     self.pump_unwatchers.clear()

    #     # watch pump reactives
    #     if self.pump:
    #         self.pump_unwatchers.append(self.watch(self.pump, "status", self.on_pump_status, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "grades", self.on_pump_grades, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "calling_grade", self.on_pump_calling_grade, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "sale", self.on_pump_sale, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "rtm_history", self.on_pump_rtm_history, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "totals", self.on_pump_totals, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "prices", self.on_pump_prices, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "emulator_flow", self.on_pump_flow, True))
    #         self.pump_unwatchers.append(self.watch(self.pump, "emulator_valve", self.on_pump_valve, True))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.pump:
            # pump actions
            if event.button.id == "auth_button":
                self.pump.authorize([])
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
            if event.button.id == "auto_sale_button":
                self.app.push_screen(AutoSaleModal(), self.parent.set_auto_sale_config)

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

    def set_pump_status(self, status: str = "closed"):
        if not self.pump: return

    def set_pump_grades(self, grades: int = 0):
        if not self.pump: return

    def set_pump_calling_grade(self, calling_grade: int = -1):
        with self.query_one("#handle_select", Select).prevent(Select.Changed):
            self.query_one("#handle_select", Select).value = calling_grade

    def set_pump_sale(self, sale: dict = {"volume": 0, "money": 0, "price": 0}):
        self.query_one("#last_sale_volume", PumpDigits).set_value(sale["volume"])
        self.query_one("#last_sale_money", PumpDigits).set_value(sale["money"])
        self.query_one("#last_sale_price", PumpDigits).set_value(sale["price"])

    def set_pump_totals(self, totals: list[dict]):
        if len(totals): total = totals[0]
        else: total = {"volume": 0, "money": 0}
        
        self.query_one("#totals_volume", PumpDigits).set_value(total["volume"])
        self.query_one("#totals_money", PumpDigits).set_value(total["money"])

    def set_pump_prices(self, prices: list[float]):
        if len(prices):  price = prices[0]
        else: price = 0.0
        self.query_one("#grade_price", PumpDigits).set_value(price)

    def set_pump_flow(self, flow: float = 0.0):
        with self.query_one("#flow_slider", Slider).prevent(Slider.Changed):
            self.query_one("#flow_slider", Slider).value = int(flow * 10)
            self.query_one("#flow_label", Label).update(f"Flow: {flow:.1f}")

    def set_pump_valve(self, valve: bool = False):
        with self.query_one("#valve_switch", Switch).prevent(Switch.Changed):
            self.query_one("#valve_switch", Switch).value = valve

    def set_pump_rtm_history(self, rtm_history: list[dict]):
        plt_widget = self.query_one(MaximizablePlotextPlot)
        if not plt_widget: return

        if len(rtm_history) == 0: 
            plt_widget.plt.clear_data()
            return
        
        def median_filter(data, window_size=3):
            if window_size < 3 or window_size % 2 == 0:
                raise ValueError("Window size must be odd and >= 3")
            
            half = window_size // 2
            padded = [data[0]] * half + data + [data[-1]] * half
            result = []

            for i in range(half, len(padded) - half):
                window = padded[i - half:i + half + 1]
                result.append(sorted(window)[window_size // 2])
    
            return result
            
        def smooth_ema(data, alpha=0.3):
            if not data:
                return []
            smoothed = [data[0]]
            for val in data[1:]:
                smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
            return smoothed

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
                    # time was in ms
                    flow = (dv / dt)
                    flows.append(flow)
                else:
                    flows.append(0.0)  # or None or float("nan"), depending on your needs
                times.append(t2)
            return flows, times

        plt_widget.plt.clear_data()
        if rtm_history:
            times = [d["time"] for d in rtm_history]
            volumes = [d["volume"] for d in rtm_history]
            flows, flow_times = calc_flows(rtm_history)
            plt_widget.plt.plot(times, volumes, marker="fhd", label="Volume", )
            if flows: 
                smoothed_flows = median_filter(flows, 3)
                plt_widget.plt.plot(flow_times, smoothed_flows, marker="fhd", label="Flow", yside="right")
                plt_widget.plt.colorize
            plt_widget.plt.xfrequency(1)
            plt_widget.plt.xticks([])
        plt_widget.refresh()