#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual import on
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Label, Switch, Select, Input, Button
from textual_slider import Slider

class RightHandForecourtConsole(App):

    CSS="""
    Screen {
        align: center middle;
    }

    Vertical {
        align: center top;
    }

    Horizontal {
        align: center middle;
        background: blue;
        width: auto;
        height: auto;
    }

    Input {
        width: 10;
    }

    Select {
        width: 20;
    }

    Label {
        background: green;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Horizontal():
                yield Switch()
                yield Label("OFF", id="switch_event")
                yield Button("ON", id="switch_on")
                yield Button("OFF", id="switch_off")
                yield Button("ON", id="switch_on_no_event")
                yield Button("OFF", id="switch_off_no_event")
                yield Button("Refresh", id="switch_refresh")
            with Horizontal():
                yield Slider(0, 10)
                yield Label("0", id="slider_event")
                yield Input(type="integer", id="slider_input")
                yield Input(type="integer", id="slider_input_no_event")
                yield Button("Refresh", id="slider_refresh")
            with Horizontal():
                yield Select([("0", 0), ("1", 1), ("2", 2)], allow_blank=False)
                yield Label("0", id="select_event")
                yield Input(type="integer", id="select_input")
                yield Input(type="integer", id="select_input_no_event")
                yield Button("Refresh", id="select_refresh")
        yield Footer()

    @on(Slider.Changed)
    def on_flow_slider_changed_value(self, event: Slider.Changed) -> None:
        self.query_one("#slider_event", Label).update(f"{event.value}")

    @on(Select.Changed)
    def on_handle_select_changed(self, event: Select.Changed) -> None:
        self.query_one("#select_event", Label).update(f"{event.value}")

    @on(Switch.Changed)
    def on_valve_switch_changed(self, event: Select.Changed) -> None:
        self.query_one("#switch_event", Label).update(f"{event.value}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "slider_input":
            self.query_one(Slider).value = int(event.value)
        if event.input.id == "select_input":
            self.query_one(Select).value = int(event.value)
        if event.input.id == "slider_input_no_event":
            # self.query_one(Slider).set_reactive(Slider.value, int(event.value))
            with self.query_one(Slider).prevent(Slider.Changed):
                self.query_one(Slider).value  = int(event.value)
        if event.input.id == "select_input_no_event":
            # self.query_one(Select).set_reactive(Select.value, int(event.value))
            with self.query_one(Select).prevent(Select.Changed):
                self.query_one(Select).value  = int(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "switch_on":
            self.query_one(Switch).value = True
        if event.button.id == "switch_off":
            self.query_one(Switch).value = False
        if event.button.id == "switch_on_no_event":
            self.query_one(Switch).set_reactive(Switch.value, True)
        if event.button.id == "switch_off_no_event":
            self.query_one(Switch).set_reactive(Switch.value, False)
        if event.button.id == "switch_refresh":
            self.query_one(Switch).refresh()
            # self.query_one(Switch).mutate_reactive(Slider.value)
        if event.button.id == "slider_refresh":
            self.query_one(Slider).refresh()
            # self.query_one(Slider).mutate_reactive(Slider.value)
        if event.button.id == "select_refresh":
            self.query_one(Select).refresh()
            # self.query_one(Select).mutate_reactive(Slider.value)

    def on_mount(self) -> None:
        pass

if __name__ == "__main__":
    RightHandForecourtConsole().run()