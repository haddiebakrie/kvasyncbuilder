"""
Demo flower
============

Defines the Kivy garden :class:`FlowerLabel` class which is the widget provided
by the demo flower.
"""

from enum import Enum, auto
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
import requests
from kivy.properties import ObjectProperty, StringProperty
import asynckivy as ak
from kivy.lang.builder import Builder
from kivy.clock import mainthread

from kivy.factory import Factory

__all__ = ('AsyncBuilder', )

# from ._version import __version__

Builder.load_string("""
#:import waiting demo.waiting
#:import Label kivymd.uix.label.MDLabel
#:import Spinner kivymd.uix.spinner.MDSpinner
#:import BoxLayout kivy.uix.boxlayout.BoxLayout

<Waiting@BoxLayout>:
    size_hint: None, None
    size: 50, 50
    pos_hint: {'center_x': 0.5,'center_y': 0.5}
    MDSpinner:

<Done@BoxLayout>:
    snapshot: ''
    size_hint: None, None
    size: 50, 50
    pos_hint: {'center_x': 0.5,'center_y': 0.5}
    MDLabel:
        text: root.snapshot

<AsyncBuilder>:
    waiting: lambda : 'Waiting'
    done: lambda x: 'Done'
    error: lambda x: Label(text=str(x))

""")


class ConnectionState(Enum):
    DONE = auto()
    WAITING = auto()
    ERROR = auto()
    NONE = auto()


class AsyncBuilder(FloatLayout):

    """
    AsyncBuilder
    ============

    A class that builds an asynchronous widget and
    updates the UI based on the state of the task.

    Attributes:
        :attr:`builder` :class:`ObjectProperty`: The asynchronous task to be
         executed.
        :attr:`value` :class:`StringProperty`: The result of the asynchronous
         task.
        :attr:`async_state` :class:`ObjectProperty`: The current state of the
         asynchronous task.
        :attr:`waiting` :class:`ObjectProperty`: The widget displayed while
         the task is running.
        :attr:`done` :class:`ObjectProperty`: The widget displayed with the
         result of the task once it is complete.

    Both `waiting` and `done` can either be a `str` or a `function`.
    If a `string` is passed, :meth:`kivy.factory.Factory.get` is called to
    obtain the Widget.
    If a function is passed, the fuction must return a `Widget`.
    """

    builder = ObjectProperty()
    value = ObjectProperty()
    async_state = ObjectProperty()
    waiting = ObjectProperty()
    error = ObjectProperty()
    done = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.async_state = ConnectionState.NONE
        self._waiting = self.waiting()
        if type(self._waiting) == str:
            self._waiting = Factory.get(self._waiting)()
        self.add_widget(self._waiting)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._start_builder()
        self.bind(async_state=self.update)

    def update(self, instance, value):
        """
        A method that is called when the async_state property changes.

        Args:
            instance: The instance of the class.
            value: The new value of async_state.
        """
        if value == ConnectionState.DONE:
            if self._waiting:
                self.remove_widget(self._waiting)
                self._done = self.done(self.value)
                if type(self._done) == str:
                    self._done = Factory.get(self._done)()
        elif value == ConnectionState.ERROR:
            if self._waiting:
                self.remove_widget(self._waiting)
                self._error = self.error(self.value)
                if type(self._error) == str:
                    self._error = Factory.get(self._error)()

    def _start_builder(self):
        """
        A method that starts the asynchronous task.
        """
        async def run():
            await ak.sleep(1)
            try:
                snapshot = await ak.run_in_thread(self.builder)
                self.value = lambda data: snapshot
                self.async_state = ConnectionState.DONE
                self._done.snapshot = self.value
                self.add_widget(self._done())
            except Exception as e:
                self.value = e
                self.async_state = ConnectionState.ERROR
                self._error.snapshot = self.value
                self.add_widget(self._error)
        build = ak.start(run())


if __name__ == "__main__":
    from kivymd.app import MDApp
    from kivy.uix.recycleview import RecycleView
    from kivy.properties import ListProperty
    import json

    Builder.load_string("""
<RV>:
    viewclass: 'MDLabel'
    RecycleBoxLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'

""")

    def network_request():
        response = requests.get("https://jsonplaceholder.typicode.com/users")
        for i in range(1000):
            print(i)
        li = []
        p = response.json()
        for idx, i in enumerate(p):
            li.append({"text": i['email']})
        return li

    class RV(RecycleView):
        snapshot = ObjectProperty()

        def __init__(self, **kwargs):
            super(RV, self).__init__(**kwargs)
            self.data = self.snapshot()

    class TestBuilder(MDApp):
        def build(self):
            builder = AsyncBuilder()
            builder.builder = network_request
            builder.done = lambda data: RV

            return builder

    TestBuilder().run()
