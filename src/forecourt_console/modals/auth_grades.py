from textual.app import ComposeResult
from textual.events import Key
from textual.screen import ModalScreen
from textual.containers import HorizontalGroup, VerticalGroup, Container, Grid
from textual.widgets import Button, Input, Switch, Static, Checkbox
from widgets.pump import Pump
from typing import List

class AuthGradesModal(ModalScreen):
    def __init__(self, pump: Pump, **kargs) -> None:
        super().__init__(**kargs)
        self.pump = pump

    def do_auth(self) -> None:
        grades: List[int] = []
        if self.query_one("#all", Checkbox).value is not True:
            for checkbox in self.query(Checkbox):
                if checkbox.id != "all" and checkbox.value:
                    grades.append(int(str(checkbox.label)))
        self.pump.authorize(grades)
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalGroup():
                with HorizontalGroup():
                    yield Static("Grades", classes="option_label")
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
            yield Button("Cancel", variant="error", id="cancel")
            yield Button("Preset", variant="primary", id="accept")

    def on_mount(self) -> None:
        self.query_one(VerticalGroup).styles.column_span = 2

    def on_checkbox_changed(self, event: Checkbox.Changed):
        if event.checkbox.value == False: return
        if event.checkbox.id == "all":
            for checkbox in self.query(Checkbox):
                if (checkbox.id != "all"): checkbox.value = False
        else: self.query_one("#all", Checkbox).value = False

    def on_key(self, event: Key):
        if event.key == "escape":
            self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "accept":
            self.do_auth()
        else: self.app.pop_screen()