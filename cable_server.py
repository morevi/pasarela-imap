from cable.thread_controller import ThreadController
from cable.usb_reader import USBReader

thread_controller = ThreadController()
reader = USBReader(thread_controller)
reader.start()
