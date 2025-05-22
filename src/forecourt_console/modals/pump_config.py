import json
import time
from textual.app import ComposeResult
from textual.widgets import Label
from textual.screen import ModalScreen

class PumpConfigModal(ModalScreen):

    CSS = """
    Label {
        margin:1 1;
        width: 80%;
        height: 80%;
        background: $panel;
        border: tall $primary;
        content-align: center middle;
    }
    """
        
    def compose(self) -> ComposeResult:
        yield Label("WIP")