import json
import time
from textual.app import ComposeResult
from textual.widgets import Label, TabPane

class PumpConfigPane(TabPane):

    CSS = """
    Label {
        margin:1 1;
        width: 100%;
        height: 100%;
        background: $panel;
        border: tall $primary;
        content-align: center middle;
    }
    """
        
    def compose(self) -> ComposeResult:
        yield Label("WIP")