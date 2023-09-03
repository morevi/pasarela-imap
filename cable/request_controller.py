from cable.usb_writer import USBWriter
from config import PAGE_SIZE
from checks import avscan
from enum import Enum
from imap_tools import MailBox, BaseMailBox, MailBoxTls, AND, MailMessageFlags
from imap_tools.errors import MailboxLoginError
from threading import Thread
import base64
import json
import os
import threading

class PacketType(Enum):
    KEEP_ON = 0
    END = 1
    ERR = 2
    OTHER_ERR = 3

cache_lock = threading.Lock()

with open('config.json', 'r') as f:
    config = json.load(f)

def read_in_chunks(f, chunk_size = USBWriter.PACKET_MAX_SIZE - 41):
    while True:
        data = f.read(chunk_size)
        if not data:
            return bytearray(0)
        yield data

class Action(Enum):
    RECV = 1
    FOLDERS = 2
    MAILS = 3
    DELETE = 4
    DOWNLOAD = 5
    UNSEEN = 6

class OtherSideException(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status
        super(OtherSideException, self).__init__(self.message)

class RequestController(Thread):
    thread_controller = None
    def __init__(self, thread_controller):
        self.thread_controller = thread_controller

        self.packet = None
        self.rw_packet = threading.Lock()
        self.r_packet = threading.Condition()

        self.dest = None
        self.action: int = -1

        self.actions_functions = {
            Action.RECV: self.recv_json,
            Action.FOLDERS: self.folders,
            Action.MAILS: self.mails,
            Action.DELETE: self.delete,
            Action.DOWNLOAD: self.download,
            Action.UNSEEN: self.unseen,
        }
        Thread.__init__(self)
        self._return = None

    def __str__(self):
        return 'named({}) id({}) action({})'.format(self.name, self.ident, self.action)

    def set_packet(self, packet):
        with self.r_packet:
            if self.packet != None:
                self.r_packet.wait()

            with self.rw_packet:
                self.packet = packet
                self.r_packet.notify()
    
    def get_packet(self):
        packet = None

        with self.r_packet:
            if self.packet == None:
                self.r_packet.wait()

            with self.rw_packet:
                packet = self.packet
                self.packet = None
                self.r_packet.notify()

        if packet != None:
            if packet['last'] == PacketType.OTHER_ERR.value:
                raise ConnectionError
            elif packet['last'] == PacketType.ERR.value:
                info = json.loads(packet['data'].decode())
                raise OtherSideException(info['error'], info['status'])

        return packet

    def run(self):
        # catch possible cable errors
        try:
            self._return = self.actions_functions[Action(self.action)]()

        except OtherSideException as e:
            # got an error from the other side
            print(str(e))
            self._return = {"error" : e.message}, e.status

        except ConnectionError as e:
            # i could not send my notification
            print(str(e))
            self._return = {"error" : "Service not available"}, 503

        except Exception as e:
            # was it me? send notification and end
            self.answer_error({"error": str(e), "status": 500})
            self._return = {"error" : str(e)}, 500

        self.thread_controller.delete_thread(self)

    def join(self) -> tuple:
        Thread.join(self)
        return self._return

    def raise_error(self, msg, action):
        data = json.dumps(msg).encode()
        p = USBWriter.build_packet(self.ident, self.dest, PacketType.ERR.value, action, data)
        USBWriter.usb_write_package(p)

    def send(self, action: int, msg: bytes, end: bool = True):
        n = USBWriter.PACKET_MAX_SIZE - 41

        for i in range(0, len(msg), n):
            chunk = msg[i:i+n]
            packet = USBWriter.build_packet(self.ident, self.dest, PacketType.KEEP_ON.value, action, chunk)
            USBWriter.usb_write_package(packet)

        if end:
            self.end(action)

    def recv(self) -> tuple[dict, bytes]:
        ''' Receives a big message until END without decoding '''

        packet = self.get_packet()
        data = packet['data']

        while packet['last'] != PacketType.END.value:
            packet = self.get_packet()
            data += packet['data']

        # return last packet metadata and all data

        del packet['data']
        del packet['util_data']

        return packet, data

    def end(self, action):
        packet = USBWriter.build_packet(self.ident, self.dest, PacketType.END.value, action, b'')
        USBWriter.usb_write_package(packet)

    def answer(self, msg):
        self.send(Action.RECV.value, msg)

    def answer_error(self, msg):
        self.raise_error(msg, Action.RECV.value)

    def login(self, server: str, port: int, user: str, pwd: str) -> BaseMailBox:
        try:
            mailbox = MailBoxTls(server, port) # TLS
        except:
            mailbox = MailBox(server, port) # SSL
        
        # try credentials
        mailbox.login(user, pwd)

        return mailbox

    def folders(self) -> None:
        _, data = self.recv()
        data = json.loads(data.decode())

        try:
            mailbox = self.login(data['server'], data['port'], data['email'], data['pwd'])
        except MailboxLoginError as e: 
            self.answer_error({"error": "Unauthorized", "status": 401})
            return
        except KeyError as e:
            self.answer_error({"error": str(e), "status": 400})
            return

        # get folders
        folders = [x.name for x in mailbox.folder.list()]
        self.answer(json.dumps(folders).encode())
        mailbox.logout()

    def msg_to_json(self, msg) -> dict:
        return {
            "uid": msg.uid,
            "date": msg.date.strftime("%Y/%m/%d, %H:%M:%S"),
            "subject": msg.subject,
            "from": msg.from_,
            "cc": msg.cc,
            "bcc": msg.bcc,
            "to": msg.to,
            "flags": msg.flags,
        }

    def recv_json(self):
        _, data = self.recv()
        info = json.loads(data.decode())
        return info, 200

    def mails(self):
        _, data = self.recv()
        data = json.loads(data.decode())

        # split data a
        page = data.get('page', 0)
        page_size = data.get('page_size', PAGE_SIZE)
        criteria = data.get('criteria', 'ALL')

        try:
            mailbox = self.login(data['server'], data['port'], data['email'], data['pwd'])
        except MailboxLoginError as e: 
            self.answer_error({"error": "Unauthorized", "status": 401})
            return
        except KeyError as e:
            self.answer_error({"error": str(e), "status": 400})
            return

        try:
            mailbox.folder.set(data['folder'])

        except:
            self.answer_error({"error": "Folder not found", "status": 404})
            return

        # pagination
        page_limit = slice(page * page_size, page * page_size + page_size)
        mails = []
        for msg in mailbox.fetch(criteria, bulk=True, limit=page_limit, mark_seen=False, headers_only=True):
            mails.append(self.msg_to_json(msg))

        self.answer(json.dumps({"mails": mails}).encode())

        # release
        mailbox.logout()

    def download(self):
        _, data = self.recv()
        data = json.loads(data.decode())

        # split data a
        try:
            email = data['email']
            uid = data['uid']
            mailbox = self.login(data['server'], data['port'], data['email'], data['pwd'])
        except KeyError as e:
            self.answer_error({"error": str(e), "status": 400})
            return
        except MailboxLoginError as e: 
            self.answer_error({"error": "Unauthorized", "status": 401})
            return

        try:
            mailbox.folder.set(data['folder'])
        except:
            self.answer_error({"error": "Folder not found", "status": 404})
            return
        
        # get the "first", there is only one uid
        mails = mailbox.fetch(AND(uid=[uid]), mark_seen=True) 
        msg = next(mails)

        # release
        mailbox.logout()

        # convert to json
        msg_data = self.msg_to_json(msg)
        msg_data['text'] = msg.text
        msg_data['html'] = msg.html
        msg_data['attachments'] = []

        for attachment in msg.attachments:
            attachment_data = {
                'filename': attachment.filename,
                'content_type': attachment.content_type,
                'size': attachment.size,
            }

            # write to tmp
            tmp_path = f"/tmp/{email}_{uid}_{attachment.filename}"
            with open(tmp_path, 'wb') as f:
                f.write(attachment.payload)

            # av
            ok, msg = avscan(tmp_path)
            if not ok:
                attachment_data['av'] = msg
            else:
                attachment_data['payload'] = base64.b64encode(attachment.payload).decode()

            msg_data['attachments'].append(attachment_data)
            os.remove(tmp_path)

        self.answer(json.dumps(msg_data).encode())

    def delete(self):
        _, data = self.recv()

        data = json.loads(data.decode())

        try:
            mailbox = self.login(data['server'], data['port'], data['email'], data['pwd'])
        except KeyError as e:
            self.answer_error({"error": str(e), "status": 400})
            return
        except MailboxLoginError as e: 
            self.answer_error({"error": "Unauthorized", "status": 401})
            return

        try:
            mailbox.folder.set(data['folder'])
        except:
            self.answer_error({"error": "Folder not found", "status": 404})
            return

        mailbox.delete([data['uid']])

        self.answer(json.dumps({"msg": "OK"}).encode())

        # release
        mailbox.logout()

    def unseen(self):
        _, data = self.recv()
        data = json.loads(data.decode())

        try:
            uid = data['uid']
            mailbox = self.login(data['server'], data['port'], data['email'], data['pwd'])
        except KeyError as e:
            self.answer_error({"error": str(e), "status": 400})
            return
        except MailboxLoginError as e: 
            self.answer_error({"error": "Unauthorized", "status": 401})
            return

        try:
            mailbox.folder.set(data['folder'])
        except:
            self.answer_error({"error": "Folder not found", "status": 404})
            return

        mailbox.flag([uid], (MailMessageFlags.SEEN), False)
        self.answer(json.dumps({"msg": "OK"}).encode())
        mailbox.logout()
