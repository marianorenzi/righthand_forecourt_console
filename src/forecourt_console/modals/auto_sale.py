from textual import on
from textual.app import ComposeResult
from textual.events import Key
from textual.screen import ModalScreen
from textual.containers import HorizontalGroup, VerticalGroup, Container, Grid, Center
from textual.widgets import Button, Input, Switch, Static, Checkbox, Select, Label
from widgets.pump import Pump
from typing import List

class AutoSaleModal(ModalScreen[dict]):
    def __init__(self, **kargs) -> None:
        super().__init__(**kargs)

    def do_auto_sale(self) -> None:
        auto_sale = {}
        auto_sale["pumps"] = self.query_one("#affected_pumps", Select).value
        auto_sale["auth_types"] = []
        if self.query_one("#fillup_enable", Checkbox).value is True: auto_sale["auth_types"].append(0)
        if self.query_one("#preset_enable", Checkbox).value is True: auto_sale["auth_types"].append(1)
        if self.query_one("#money_preset_enable", Checkbox).value is True: auto_sale["auth_types"].append(2)
        value = self.query_one("#volume_preset_min", Input).value
        auto_sale["volume_min"] = float(value if len(value) > 0 else "0")
        value = self.query_one("#volume_preset_max", Input).value
        auto_sale["volume_max"] = float(value if len(value) > 0 else "0")
        value = self.query_one("#money_preset_min", Input).value
        auto_sale["money_min"] = float(value if len(value) > 0 else "0")
        value = self.query_one("#money_preset_max", Input).value
        auto_sale["money_max"] = float(value if len(value) > 0 else "0")
        auto_sale["fullfilment"] = self.query_one("#preset_fullfilment", Select).value
        value = self.query_one("#flow_min", Input).value
        auto_sale["flow_min"] = float(value if len(value) > 0 else "0")
        value = self.query_one("#flow_max", Input).value
        auto_sale["flow_max"] = float(value if len(value) > 0 else "0")
        value = self.query_one("#duration_min", Input).value
        auto_sale["duration_min"] = int(value if len(value) > 0 else "0")
        value = self.query_one("#duration_max", Input).value
        auto_sale["duration_max"] = int(value if len(value) > 0 else "0")
        auto_sale["grades"] = []
        if self.query_one("#all", Checkbox).value is  True:
            auto_sale["grades"] = list(range(0, 8))
        else:
            for checkbox in self.query(".grade_checkbox").results(Checkbox):
                if checkbox.id != "all" and checkbox.value:
                    auto_sale["grades"].append(int(str(checkbox.label))-1)
        self.dismiss(auto_sale)

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalGroup(id="content"):
                with Center():
                    yield Label("[b]Auto Sale Settings")
                with Center():
                    yield Label("Authorizations will be sent after calling state is detected, and will also apply to non-emulator pumps.")

                yield Checkbox("Fill-Up", id="fillup_enable")
                with HorizontalGroup(classes="preset"):
                    yield Checkbox("Volume Preset", id="preset_enable")
                    yield Input(type="number", placeholder="Min", id="volume_preset_min")
                    yield Input(type="number", placeholder="Max", id="volume_preset_max")
                with HorizontalGroup(classes="preset"):
                    yield Checkbox("Money Preset", id="money_preset_enable")
                    yield Input(type="number", placeholder="Min", id="money_preset_min")
                    yield Input(type="number", placeholder="Max", id="money_preset_max")
                # emulator only settings
                with Center():
                    yield Label("[b]Emulator Settings")
                with HorizontalGroup():
                    yield Label("Preset Fullfilment", classes="option_label")
                    yield Select([("Always", 0), ("Sometimes", 1), ("Never", 2)], allow_blank=False, id="preset_fullfilment")
                with HorizontalGroup():
                    yield Label("Flow", classes="option_label")
                    yield Input(type="number", placeholder="Min", id="flow_min")
                    yield Input(type="number", placeholder="Max", id="flow_max")
                with HorizontalGroup():
                    yield Label("Duration (seconds)", classes="option_label")
                    yield Input(type="integer", placeholder="Min", id="duration_min")
                    yield Input(type="integer", placeholder="Max", id="duration_max")
                with HorizontalGroup():
                    yield Label("Grades", classes="option_label")
                    with VerticalGroup():
                        with HorizontalGroup():
                            yield Checkbox("All", True, id="all", classes="grade_checkbox")
                            yield Checkbox("1", classes="grade_checkbox")
                            yield Checkbox("2", classes="grade_checkbox")
                            yield Checkbox("3", classes="grade_checkbox")
                        with HorizontalGroup():
                            yield Checkbox("4", classes="grade_checkbox")
                            yield Checkbox("5", classes="grade_checkbox")
                            yield Checkbox("6", classes="grade_checkbox")
                            yield Checkbox("7", classes="grade_checkbox")
                            yield Checkbox("8", classes="grade_checkbox")
                with HorizontalGroup():
                    yield Label("Pumps", classes="option_label")
                    yield Select([("All Pumps", 0), ("Current Pump", 1)], allow_blank=False, id="affected_pumps")

            # modal buttons
            yield Button("Cancel", variant="error", id="cancel")
            yield Button("Preset", variant="primary", id="accept")

    def on_mount(self) -> None:
        self.query_one("#content", VerticalGroup).styles.column_span = 2

    @on(Checkbox.Changed, ".grade_checkbox")
    def on_grade_checkbox_changed(self, event: Checkbox.Changed):
        if event.checkbox.value == False: return
        if event.checkbox.id == "all":
            for checkbox in self.query(".grade_checkbox").results(Checkbox):
                if (checkbox.id != "all"): checkbox.value = False
        else: self.query_one("#all", Checkbox).value = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.do_auto_sale()

    def on_key(self, event: Key):
        if event.key == "escape":
            event.stop()
            self.app.pop_screen()
        if event.key == "enter":
            event.stop()
            self.do_auto_sale()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "accept":
            self.do_auto_sale()
        else: self.app.pop_screen()