from cable.request_controller import Action, PacketType, RequestController
from cable.thread_controller import ThreadController
from cable.usb_reader import USBReader
from cable.usb_writer import USBWriter
import json

thread_controller = ThreadController()
writer = USBWriter()
reader = USBReader(thread_controller)
reader.start()


class Request:
    def __init__(self, msg: bytes, action: Action):
        self.msg = msg
        self.action = action.value
        self.controller = self._create_controller()

    def _create_controller(self):
        controller = RequestController(thread_controller)
        controller.action = Action.RECV.value
        controller.start()
        thread_controller.add_thread(controller)
        return controller

    def _send(self) -> int:
        packet = writer.build_packet(
            self.controller.ident, 0, PacketType.END.value, self.action, self.msg)
        status = writer.usb_write_package(packet)
        return status

    def _join(self) -> tuple[bytes, int]:
        return self.controller.join()

    def send(self) -> tuple:
        self._send()
        return self._join()


class JsonRequest(Request):
    def __init__(self, msg: dict, action: Action):
        bmsg = json.dumps(msg).encode()
        super().__init__(bmsg, action)
