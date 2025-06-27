import socket
import json
import threading
from queue import Queue, Empty

class NetworkManager:
    def __init__(self):
        self.host = 'localhost'
        self.port = 10100
        self.socket = None
        self.connected = False
        self.message_queue = Queue()
        self.callbacks = {}
        
    def connect(self):
        try:
            print("Conectando al servidor...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print("Conectado!")
            
            # Thread para recibir
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Thread para procesar
            process_thread = threading.Thread(target=self._process_messages)
            process_thread.daemon = True
            process_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error conectando: {e}")
            return False
    
    def _receive_messages(self):
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                print(f"Mensaje recibido: {message.get('type')}")
                self.message_queue.put(message)
                
            except Exception as e:
                print(f"Error recibiendo: {e}")
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
            except Exception as e:
                print(f"Error procesando: {e}")
    
    def send_attempt(self, word):
        if self.connected:
            message = {'type': 'attempt', 'word': word}
            try:
                data = json.dumps(message).encode('utf-8')
                self.socket.send(data)
                print(f"Intento enviado: {word}")
            except Exception as e:
                print(f"Error enviando: {e}")
    
    def register_callback(self, message_type, callback):
        self.callbacks[message_type] = callback
    
    def send_new_game_response(self, answer):
        if self.connected:
            message = {'type': 'new_game_response', 'answer': answer}
            try:
                data = json.dumps(message).encode('utf-8')
                self.socket.send(data)
                print(f"Respuesta nueva partida enviada: {answer}")
            except Exception as e:
                print(f"Error enviando respuesta: {e}")
    
    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass