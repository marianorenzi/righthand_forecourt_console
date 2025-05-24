from textual.app import ComposeResult
from textual.events import Key
from textual.screen import ModalScreen
from textual.containers import HorizontalGroup, VerticalGroup, Grid
from textual.widgets import Button, Input, Static, Select
from widgets.pump import Pump

class PriceChangeModal(ModalScreen):
    def __init__(self, pump: Pump, **kargs) -> None:
        super().__init__(**kargs)
        self.pump = pump

    def do_price_change(self) -> None:
        if len(self.query_one(Input).value) == 0: return

        value: float = float(self.query_one(Input).value)
        grade: int = int(str(self.query_one(Select).value))
        self.pump.price_change(value, grade)
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalGroup():
                with HorizontalGroup():
                    yield Static("Price", classes="option_label")
                    yield Input(type="number")
                with HorizontalGroup():
                    yield Static("Grade", classes="option_label")
                    yield Select([("1", 0), ("2", 1), ("3", 2), ("4", 3), ("5", 4), ("6", 5), ("7", 6), ("8", 7)], id="handle_select", allow_blank=False)
            yield Button("Cancel", variant="error", id="cancel")
            yield Button("Change Price", variant="primary", id="accept")

    def on_mount(self) -> None:
        self.query_one(VerticalGroup).styles.column_span = 2

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.do_price_change()

    def on_key(self, event: Key):
        if event.key == "escape":
            event.stop()
            self.app.pop_screen()
        if event.key == "enter":
            event.stop()
            self.do_price_change()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "accept":
            self.do_price_change()
        else: self.app.pop_screen()