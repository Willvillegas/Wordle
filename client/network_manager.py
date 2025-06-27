import socket
import json
import threading
from queue import Queue, Empty

class NetworkManager:
    def __init__(self, host='64.23.137.192', port=10100):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.message_queue = Queue()
        self.callbacks = {}
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(15)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            process_thread = threading.Thread(target=self._process_messages)
            process_thread.daemon = True
            process_thread.start()
            
            return True
            
        except Exception:
            self.connected = False
            return False
    
    def _receive_messages(self):
        buffer = ""
        
        while self.connected:
            try:
                self.socket.settimeout(5.0)
                data = self.socket.recv(1024)
                
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer or buffer.count('{') > 0:
                    try:
                        if '\n' in buffer:
                            message_str, buffer = buffer.split('\n', 1)
                        else:
                            decoder = json.JSONDecoder()
                            message, idx = decoder.raw_decode(buffer)
                            message_str = buffer[:idx]
                            buffer = buffer[idx:].strip()
                            
                        if message_str.strip():
                            try:
                                message = json.loads(message_str.strip())
                                self.message_queue.put(message)
                            except json.JSONDecodeError:
                                break
                        else:
                            break
                            
                    except (json.JSONDecodeError, ValueError):
                        break
                    
            except socket.timeout:
                continue
            except Exception:
                break
        
        self.connected = False
    
    def _process_messages(self):
        while self.connected:
            try:
                message = self.message_queue.get(timeout=1)
                msg_type = message.get('type')
                
                if msg_type in self.callbacks:
                    self.callbacks[msg_type](message)
                    
            except Empty:
                continue
            except Exception:
                pass
    
    def send_attempt(self, word):
        if self.connected:
            message = {'type': 'attempt', 'word': word}
            return self._send_message(message)
        return False
    
    def send_new_game_response(self, answer):
        if self.connected:
            message = {'type': 'new_game_response', 'answer': answer}
            return self._send_message(message)
        return False
    
    def _send_message(self, message):
        try:
            if not self.connected:
                return False
                
            data = json.dumps(message).encode('utf-8') + b'\n'
            self.socket.send(data)
            return True
            
        except Exception:
            self.connected = False
            return False
    
    def register_callback(self, message_type, callback):
        self.callbacks[message_type] = callback
    
    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass