import asyncio
import json
import os
from stat import S_IRGRP, S_IROTH, S_IRUSR

import zmq
from movai_core_shared import Log
from zmq.asyncio import Context

MOVAI_ZMQ_TIMEOUT_MS = os.getenv("MOVAI_ZMQ_TIMEOUT_MS", 300000)
MOVAI_OUTER_SOCKET = os.getenv("MOVAI_OUTER_SOCKET", "tcp://0.0.0.0:5555")
MOVAI_KEYS_LOC = os.getenv("MOVAI_KEYS_LOC", "//run/movai/")

class ZmqClient:
    """
    A ZMQ client to communicate with zmq protocol
    """
    def __init__(self, ip: str = "", port: str = "5555", pub_key: str = "", name :str = "") -> None:
        """Constractor for zmq client

        Args:
            ip: the dest ip in string
            port: the dest port in string
            pub_key: public key of the dest
            name: name of the client

        Returns:
            None: None
        """
        self.log = Log.get_logger("zmq socket")
        try:
            self.ctx = zmq.Context()
            self.sock = self.ctx.socket(zmq.REQ)
            if name == "":
                name =  f"uid_{os.getuid()}"
            self.sock.identity =  name.encode('utf8')
            self.sock.setsockopt(zmq.RCVTIMEO, int(MOVAI_ZMQ_TIMEOUT_MS))
            if ip == "":
                addr = MOVAI_OUTER_SOCKET
            else:
                addr = "tcp://{ip}:{port}"
            self.sock.curve_publickey = pub_key
            self.sock.curve_secretkey, self.my_pub = create_certificates(MOVAI_KEYS_LOC, "key")
            self.sock.bind(addr)
        except OSError as e:
            self.log.error("failed to bind zmq socket")
            self.log.error(e)

    def send_msg(self, msg: dict) -> dict:
        """send fucntion

        send message to the zmq server
        socket will wait for response

        Args:
            msg: the message in dict

        Returns:
            dict: response in dict
        """
        try:
            raw_data = json.dumps(msg).encode('utf8')
            self.sock.send(raw_data)
            msg_data = bytearray()
            response = self.sock.recv()
            msg_data.extend(response)
            response = json.loads(msg_data.decode())

        except FileNotFoundError:
            response = {'error': "can't send to server, check that it is running"}
        except OSError as err:
            response = {'error': str(err)}
        except json.JSONDecodeError:
            response = {'error': "can't parse data from server."}
        except zmq.error.Again:
            response = {'error': "movai socket doesn't respond,\n" +
                                 "please check that the service is running with:" +
                                 "'service movai-service status'"}
        return response




def create_certificates(key_dir, name):
    """Create zmq certificates.
    Returns the file paths to the public and secret certificate files.
    """
    base_filename = os.path.join(key_dir, name)
    if os.path.exists(f"{base_filename}.public") and os.path.exists(f"{base_filename}.secret"):
        with open(base_filename + ".public", 'r', encoding='utf8') as f:
            public_key = f.readlines()[0]
        with open(base_filename + ".secret", 'r', encoding='utf8') as f:
            secret_key = f.readlines()[0]
    else:
        public_key, secret_key = zmq.curve_keypair()
        with open(base_filename + ".public", 'w', encoding='utf8') as f:
            f.write(public_key.decode('utf8'))
            os.chmod(base_filename+'.public', S_IRUSR | S_IRGRP | S_IROTH)
        with open(base_filename + ".secret", 'w', encoding='utf8') as f:
            f.write(secret_key.decode('utf8'))
            os.chmod(base_filename+'.secret', S_IRUSR)

    return public_key, secret_key
