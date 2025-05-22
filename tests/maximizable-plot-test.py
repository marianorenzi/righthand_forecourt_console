#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Header, Footer, TabbedContent, TabPane, ListView, Log, ListItem
from widgets.maximizable_plot import MaximizablePlotextPlot

class MaximizablePlotTest(App):

    CSS="""
    Horizontal {
        align: center middle;
        background: blue;
        width: 50%;
        height: 50%;
    }

    HorizontalGroup#details {
        background: blue 20%;
        color: blue;
        border: solid blue;
        height: 22%;
        grid-size: 7;
    }

    ListView {
        background: green 20%;
        color: green;
        border: solid green;
        layout: grid;
        align: left top;
        grid-gutter: 1 2;
        grid-size: 10;
    }

    Log#log_1 {
        height: 15%;
    }
    """

    BINDINGS = [
    ("o", "maximize_plot(1)", "Maximize Plot 1"),
    ("p", "maximize_plot(2)", "Maximize Plot 2"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="pane_1"):
            with TabPane("Pane 1", id="pane_1"):
                with HorizontalGroup(id="details"):
                    yield VerticalGroup()
                    yield VerticalGroup()
                    yield VerticalGroup()
                    yield VerticalGroup()
                    with VerticalGroup():
                        yield MaximizablePlotextPlot(id="plot_1")
                with ListView():
                    yield ListItem()
                    yield ListItem()
                    yield ListItem()
                yield Log(id="log_1")
            with TabPane("Pane 2"):
                yield Log()
        yield MaximizablePlotextPlot(id="plot_2")
        yield Footer()

    def on_mount(self) -> None:
        pass

    def action_maximize_plot(self, plot):
        self.app.screen.maximize(self.query_one(f"#plot_{plot}", MaximizablePlotextPlot), False)

if __name__ == "__main__":
    MaximizablePlotTest().run()