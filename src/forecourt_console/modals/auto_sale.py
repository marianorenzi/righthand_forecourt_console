from textual.app import ComposeResult
from textual.events import Key
from textual.screen import ModalScreen
from textual.containers import HorizontalGroup, VerticalGroup, Container, Grid, Center
from textual.widgets import Button, Input, Switch, Static, Checkbox, Select, Label
from widgets.pump import Pump
from typing import List

class AutoSaleModal(ModalScreen):
    def __init__(self, **kargs) -> None:
        super().__init__(**kargs)

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
                    yield Input(type="number", id="volume_preset_min")
                    yield Input(type="number", id="volume_preset_max")
                with HorizontalGroup(classes="preset"):
                    yield Checkbox("Money Preset", id="money_preset_enable")
                    yield Input(type="number", id="money_preset_min")
                    yield Input(type="number", id="money_preset_max")
                # emulator only settings
                with Center():
                    yield Label("[b]Emulator Settings")
                with HorizontalGroup():
                    yield Label("Preset Fullfilment", classes="option_label")
                    yield Select([("Always", 0), ("Sometimes", 1), ("Never", 2)], allow_blank=False, id="preset_fullfilment")
                with HorizontalGroup():
                    yield Label("Flow", classes="option_label")
                    yield Input(type="number", id="flow_min")
                    yield Input(type="number", id="flow_max")
                with HorizontalGroup():
                    yield Label("Duration (seconds)", classes="option_label")
                    yield Input(type="integer", id="duration_min")
                    yield Input(type="integer", id="duration_max")
                with HorizontalGroup():
                    yield Label("Grades", classes="option_label")
                    with VerticalGroup():
                        with HorizontalGroup():
                            yield Checkbox("All", True, id="all")
                            yield Checkbox("1")
                            yield Checkbox("2")
                            yield Checkbox("3")
                        with HorizontalGroup():
                            yield Checkbox("4")
                            yield Checkbox("5")
                            yield Checkbox("6")
                            yield Checkbox("7")
                            yield Checkbox("8")

            # modal buttons
            yield Button("Cancel", variant="error", id="cancel")
            yield Button("Preset", variant="primary", id="accept")

    def on_mount(self) -> None:
        self.query_one("#content", VerticalGroup).styles.column_span = 2

    def on_checkbox_changed(self, event: Checkbox.Changed):
        if event.checkbox.value == False: return
        if event.checkbox.id == "all":
            for checkbox in self.query(Checkbox):
                if (checkbox.id != "all"): checkbox.value = False
        else: self.query_one("#all", Checkbox).value = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        pass

    def on_key(self, event: Key):
        if event.key == "escape":
            self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "accept":
            pass
        else: self.app.pop_screen()