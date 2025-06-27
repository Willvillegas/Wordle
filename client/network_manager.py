import socket
import json
import threading
from queue import Queue, Empty

class NetworkManager:
    def __init__(self, host='64.23.137.192', port=10100):  # IP de tu VM
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.message_queue = Queue()
        self.callbacks = {}
        
    def connect(self):
        try:
            print(f"🔌 Conectando a {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Timeout más largo para conexiones de red
            self.socket.settimeout(15)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            print(f"✅ Conectado a {self.host}:{self.port}")
            
            receive_thread = threading.Thread(target=self._receive_messages, name="NetworkReceive")
            receive_thread.daemon = True
            receive_thread.start()
            
            process_thread = threading.Thread(target=self._process_messages, name="NetworkProcess")
            process_thread.daemon = True
            process_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def _receive_messages(self):
        print(f"📡 Iniciando recepción de mensajes...")
        
        while self.connected:
            try:
                self.socket.settimeout(5.0)
                data = self.socket.recv(1024)
                
                if not data:
                    print(f"📡 Servidor cerró la conexión")
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    print(f"📨 Recibido: {message.get('type')}")
                    self.message_queue.put(message)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Error JSON: {e}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"❌ Error recibiendo: {e}")
                break
        
        print(f"📡 Recepción terminada")
        self.connected = False
    
    def _process_messages(self):
        print(f"⚙️ Iniciando procesamiento...")
        
        while self.connected:
            try:
                message = self.message_queue.get(timeout=1)
                msg_type = message.get('type')
                
                print(f"⚙️ Procesando: {msg_type}")
                
                if msg_type in self.callbacks:
                    try:
                        self.callbacks[msg_type](message)
                    except Exception as e:
                        print(f"❌ Error en callback {msg_type}: {e}")
                else:
                    print(f"⚠️ No hay callback para: {msg_type}")
                    
            except Empty:
                continue
            except Exception as e:
                print(f"❌ Error procesando: {e}")
        
        print(f"⚙️ Procesamiento terminado")
    
    def send_attempt(self, word):
        if self.connected:
            message = {'type': 'attempt', 'word': word}
            print(f"📤 Enviando intento: {word}")
            return self._send_message(message)
        else:
            print(f"⚠️ No conectado")
            return False
    
    def send_new_game_response(self, answer):
        if self.connected:
            message = {'type': 'new_game_response', 'answer': answer}
            print(f"📤 Enviando respuesta: {answer}")
            return self._send_message(message)
        else:
            return False
    
    def _send_message(self, message):
        try:
            if not self.connected:
                return False
                
            data = json.dumps(message).encode('utf-8')
            self.socket.send(data)
            return True
            
        except Exception as e:
            print(f"❌ Error enviando: {e}")
            self.connected = False
            return False
    
    def register_callback(self, message_type, callback):
        self.callbacks[message_type] = callback
        print(f"📋 Callback registrado: {message_type}")
    
    def disconnect(self):
        print(f"🔌 Desconectando...")
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print(f"✅ Desconectado")

if __name__ == "__main__":
    from server.server import WordleServer
    server = WordleServer()
    server.start()