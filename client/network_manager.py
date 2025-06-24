import socket
import json
import threading
from queue import Queue

class NetworkManager:
    def __init__(self, host='localhost', port=10100):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.message_queue = Queue()
        self.callbacks = {}
        self.player_id = None
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Iniciar thread para recibir mensajes
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Iniciar thread para procesar mensajes
            process_thread = threading.Thread(target=self._process_messages)
            process_thread.daemon = True
            process_thread.start()
            
            return True
        except Exception as e:
            print(f"Error conectando al servidor: {e}")
            return False
    
    def _receive_messages(self):
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                self.message_queue.put(message)
                
            except Exception as e:
                print(f"Error recibiendo mensaje: {e}")
                break
        
        self.connected = False
    
    def _process_messages(self):
        while self.connected:
            try:
                if not self.message_queue.empty():
                    message = self.message_queue.get(timeout=1)
                    msg_type = message.get('type')
                    
                    if msg_type in self.callbacks:
                        self.callbacks[msg_type](message)
                    
            except:
                continue
    
    def send_attempt(self, word):
        if self.connected:
            message = {
                'type': 'attempt',
                'word': word
            }
            self._send_message(message)
    
    def _send_message(self, message):
        try:
            data = json.dumps(message).encode('utf-8')
            self.socket.send(data)
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
    
    def register_callback(self, message_type, callback):
        self.callbacks[message_type] = callback
    
    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass