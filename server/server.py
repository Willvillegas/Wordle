import socket
import threading
import json
import random
from collections import Counter
import time
import traceback

class WordleServer:
    def __init__(self, host='localhost', port=10100):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
        # Estado del juego
        self.clients = []
        self.game_words = [
            "GRASS", "HOARD", "BOARD", "PLANE", "APPLE", "ABOUT", "OTHER",
            "BRAKE", "CRANE", "CIDER", "EARTH", "FLAIR", "GHOST", "HONEY",
            "LIGHT", "MAGIC", "NIGHT", "QUEEN", "RADIO", "SMILE", "TIGER",
            "WATER", "YOUTH", "ZEBRA", "STORM", "FLAME", "DREAM", "WORLD"
        ]
        self.valid_words = set(self.game_words + [
            "HOUSE", "MOUSE", "STONE", "PHONE", "CHAIR", "TABLE", "PAPER",
            "MONEY", "POWER", "HEART", "VOICE", "SOUND", "MUSIC", "DANCE"
        ])
        self.target_word = None
        self.game_started = False
        self.game_finished = False
        self.winner = None
        
        # Lock para thread safety
        self.lock = threading.Lock()
    
    def start_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(2)
            self.running = True
            
            print(f"🚀 Servidor iniciado en {self.host}:{self.port}")
            print("📝 Palabras disponibles:", len(self.valid_words))
            print("⏳ Esperando jugadores...")
            
            while self.running and len(self.clients) < 2:
                try:
                    # Timeout para poder chequear self.running
                    self.socket.settimeout(1.0)
                    try:
                        client_socket, address = self.socket.accept()
                    except socket.timeout:
                        continue
                    
                    player_id = len(self.clients) + 1
                    
                    client_info = {
                        'socket': client_socket,
                        'address': address,
                        'id': player_id,
                        'attempts': 0,
                        'finished': False,
                        'won': False,
                        'connected': True
                    }
                    
                    with self.lock:
                        self.clients.append(client_info)
                    
                    print(f"👤 Jugador {player_id} conectado desde {address}")
                    
                    # Enviar ID del jugador
                    self.send_message(client_socket, {
                        'type': 'player_id',
                        'player_id': player_id,
                        'waiting_for': 2 - len(self.clients)
                    })
                    
                    # Iniciar thread para manejar cliente
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_info,),
                        name=f"Client-{player_id}"
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"❌ Error aceptando conexión: {e}")
                    continue
            
            # Ambos jugadores conectados
            if len(self.clients) == 2:
                self.start_game()
                
                # Mantener el servidor corriendo
                try:
                    while self.running:
                        time.sleep(1)
                        # Verificar si ambos clientes siguen conectados
                        with self.lock:
                            connected_clients = [c for c in self.clients if c['connected']]
                            if len(connected_clients) < 2 and self.game_started:
                                print("🔌 Cliente desconectado, terminando juego...")
                                self.end_game_early()
                                break
                except KeyboardInterrupt:
                    print("\n🛑 Servidor detenido por usuario")
            else:
                print("⚠️ No se conectaron suficientes jugadores")
                
        except Exception as e:
            print(f"💥 Error crítico del servidor: {e}")
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def start_game(self):
        try:
            with self.lock:
                self.target_word = random.choice(self.game_words)
                self.game_started = True
                
            print(f"🎮 ¡Juego iniciado!")
            print(f"🔤 Palabra objetivo: {self.target_word}")
            
            # Notificar a ambos jugadores
            for client in self.clients:
                if client['connected']:
                    self.send_message(client['socket'], {
                        'type': 'game_start',
                        'opponent_id': 3 - client['id']
                    })
        except Exception as e:
            print(f"❌ Error iniciando juego: {e}")
    
    def handle_client(self, client_info):
        client_socket = client_info['socket']
        player_id = client_info['id']
        
        print(f"🔄 Iniciando manejo de jugador {player_id}")
        
        try:
            while self.running and client_info['connected']:
                try:
                    # Timeout para evitar bloqueo indefinido
                    client_socket.settimeout(5.0)
                    data = client_socket.recv(1024)
                    
                    if not data:
                        print(f"📡 Jugador {player_id} cerró la conexión")
                        break
                    
                    try:
                        message = json.loads(data.decode('utf-8'))
                        print(f"📨 Mensaje de jugador {player_id}: {message.get('type', 'unknown')}")
                        self.process_message(client_info, message)
                    except json.JSONDecodeError:
                        print(f"⚠️ Mensaje JSON inválido de jugador {player_id}: {data}")
                        continue
                        
                except socket.timeout:
                    # Timeout normal, continuar
                    continue
                except ConnectionResetError:
                    print(f"🔌 Jugador {player_id} se desconectó abruptamente")
                    break
                except Exception as e:
                    print(f"❌ Error recibiendo de jugador {player_id}: {e}")
                    break
                
        except Exception as e:
            print(f"💥 Error crítico manejando jugador {player_id}: {e}")
            traceback.print_exc()
        finally:
            self.disconnect_client(client_info)
    
    def process_message(self, client_info, message):
        try:
            msg_type = message.get('type')
            
            if msg_type == 'attempt':
                word = message.get('word', '').strip().upper()
                if word:
                    self.handle_attempt(client_info, word)
                else:
                    print(f"⚠️ Intento vacío de jugador {client_info['id']}")
            elif msg_type == 'heartbeat':
                # Keep alive - responder
                self.send_message(client_info['socket'], {'type': 'heartbeat_ack'})
            else:
                print(f"⚠️ Tipo de mensaje desconocido: {msg_type}")
                
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    def handle_attempt(self, client_info, word):
        try:
            if not self.game_started or self.game_finished:
                print(f"⚠️ Intento fuera de tiempo de jugador {client_info['id']}")
                return
            
            player_id = client_info['id']
            print(f"🎯 Jugador {player_id} intenta: {word}")
            
            # Validar palabra
            if len(word) != 5:
                print(f"⚠️ Palabra de longitud incorrecta: {word}")
                self.send_message(client_info['socket'], {
                    'type': 'invalid_word',
                    'word': word,
                    'reason': 'Debe tener 5 letras'
                })
                return
                
            if not word.isalpha():
                print(f"⚠️ Palabra con caracteres inválidos: {word}")
                self.send_message(client_info['socket'], {
                    'type': 'invalid_word',
                    'word': word,
                    'reason': 'Solo letras permitidas'
                })
                return
                
            if word not in self.valid_words:
                print(f"⚠️ Palabra no válida: {word}")
                self.send_message(client_info['socket'], {
                    'type': 'invalid_word',
                    'word': word,
                    'reason': 'Palabra no encontrada'
                })
                return
            
            # Incrementar intentos
            with self.lock:
                client_info['attempts'] += 1
                current_attempt = client_info['attempts']
            
            print(f"📊 Jugador {player_id} - Intento {current_attempt}/6")
            
            # Calcular resultado
            result = self.check_word(word, self.target_word)
            print(f"🎨 Resultado: {result}")
            
            # Verificar si ganó
            won = word == self.target_word
            finished = won or current_attempt >= 6
            
            with self.lock:
                client_info['finished'] = finished
                client_info['won'] = won
                
                if won and not self.game_finished:
                    self.winner = player_id
                    self.game_finished = True
                    print(f"🏆 ¡Jugador {player_id} GANÓ!")
            
            # Responder al jugador
            response = {
                'type': 'attempt_result',
                'word': word,
                'result': result,
                'attempt': current_attempt,
                'won': won,
                'finished': finished,
                'game_finished': self.game_finished,
                'winner': self.winner
            }
            self.send_message(client_info['socket'], response)
            
            # Notificar al oponente
            opponent = self.get_opponent(client_info)
            if opponent and opponent['connected']:
                opponent_msg = {
                    'type': 'opponent_progress',
                    'opponent_id': player_id,
                    'attempt': current_attempt,
                    'won': won,
                    'finished': finished,
                    'game_finished': self.game_finished,
                    'winner': self.winner
                }
                self.send_message(opponent['socket'], opponent_msg)
            
            # Verificar fin del juego
            if self.game_finished or all(c['finished'] for c in self.clients if c['connected']):
                self.end_game()
                
        except Exception as e:
            print(f"💥 Error manejando intento: {e}")
            traceback.print_exc()
    
    def check_word(self, guess, target):
        """Algoritmo correcto de Wordle"""
        result = [0] * 5  # 0=gris, 1=amarillo, 2=verde
        target_count = Counter(target)
        
        # Primera pasada: verdes
        for i in range(5):
            if guess[i] == target[i]:
                result[i] = 2
                target_count[guess[i]] -= 1
        
        # Segunda pasada: amarillos
        for i in range(5):
            if result[i] == 0:
                if guess[i] in target_count and target_count[guess[i]] > 0:
                    result[i] = 1
                    target_count[guess[i]] -= 1
        
        return result
    
    def get_opponent(self, client_info):
        for client in self.clients:
            if client['id'] != client_info['id']:
                return client
        return None
    
    def end_game(self):
        try:
            print("🏁 Terminando juego...")
            
            with self.lock:
                final_message = {
                    'type': 'game_end',
                    'target_word': self.target_word,
                    'winner': self.winner,
                    'players': [
                        {
                            'id': c['id'],
                            'attempts': c['attempts'],
                            'won': c['won']
                        } for c in self.clients if c['connected']
                    ]
                }
            
            for client in self.clients:
                if client['connected']:
                    self.send_message(client['socket'], final_message)
            
            print(f"🎯 Palabra era: {self.target_word}")
            if self.winner:
                print(f"🏆 Ganador: Jugador {self.winner}")
            else:
                print("🤝 Empate o juego incompleto")
                
        except Exception as e:
            print(f"❌ Error terminando juego: {e}")
    
    def end_game_early(self):
        """Terminar juego por desconexión"""
        with self.lock:
            self.game_finished = True
            
        print("⚠️ Juego terminado prematuramente")
        
        # Notificar a clientes conectados
        for client in self.clients:
            if client['connected']:
                self.send_message(client['socket'], {
                    'type': 'game_end',
                    'target_word': self.target_word,
                    'winner': None,
                    'reason': 'Oponente desconectado'
                })
    
    def send_message(self, client_socket, message):
        try:
            data = json.dumps(message).encode('utf-8')
            client_socket.send(data)
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
    
    def disconnect_client(self, client_info):
        try:
            with self.lock:
                client_info['connected'] = False
                
            print(f"👋 Jugador {client_info['id']} desconectado")
            
            try:
                client_info['socket'].close()
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error desconectando cliente: {e}")
    
    def shutdown(self):
        try:
            print("🔄 Cerrando servidor...")
            self.running = False
            
            # Cerrar conexiones de clientes
            for client in self.clients:
                if client['connected']:
                    try:
                        client['socket'].close()
                    except:
                        pass
            
            # Cerrar socket del servidor
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                    
            print("✅ Servidor cerrado")
            
        except Exception as e:
            print(f"❌ Error cerrando servidor: {e}")

# run_server.py (versión mejorada)
if __name__ == "__main__":
    print("🎮 WORDLE MULTIPLAYER SERVER")
    print("=" * 40)
    
    server = WordleServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por usuario")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        traceback.print_exc()
    finally:
        print("👋 ¡Hasta luego!")

# client/robust_network_manager.py (versión mejorada del cliente)
import socket
import json
import threading
from queue import Queue, Empty
import time

class RobustNetworkManager:
    def __init__(self, host='localhost', port=10100):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.message_queue = Queue()
        self.callbacks = {}
        self.player_id = None
        self.receive_thread = None
        self.process_thread = None
        
    def connect(self):
        try:
            print(f"🔌 Conectando a {self.host}:{self.port}...")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Timeout de conexión
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            print("✅ Conectado al servidor")
            
            # Iniciar threads
            self.receive_thread = threading.Thread(target=self._receive_messages, name="NetworkReceive")
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self.process_thread = threading.Thread(target=self._process_messages, name="NetworkProcess")
            self.process_thread.daemon = True
            self.process_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            self.connected = False
            return False
    
    def _receive_messages(self):
        print("📡 Iniciando recepción de mensajes...")
        
        while self.connected:
            try:
                self.socket.settimeout(1.0)
                data = self.socket.recv(1024)
                
                if not data:
                    print("📡 Servidor cerró la conexión")
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    print(f"📨 Recibido: {message.get('type', 'unknown')}")
                    self.message_queue.put(message)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Error decodificando JSON: {e}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"❌ Error recibiendo: {e}")
                break
        
        print("📡 Recepción de mensajes terminada")
        self.connected = False
    
    def _process_messages(self):
        print("⚙️ Iniciando procesamiento de mensajes...")
        
        while self.connected:
            try:
                message = self.message_queue.get(timeout=1)
                msg_type = message.get('type')
                
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
                print(f"❌ Error procesando mensaje: {e}")
        
        print("⚙️ Procesamiento de mensajes terminado")
    
    def send_attempt(self, word):
        if self.connected:
            message = {
                'type': 'attempt',
                'word': word
            }
            self._send_message(message)
        else:
            print("⚠️ No conectado - no se puede enviar intento")
    
    def _send_message(self, message):
        try:
            if not self.connected:
                return False
                
            data = json.dumps(message).encode('utf-8')
            self.socket.send(data)
            print(f"📤 Enviado: {message.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            self.connected = False
            return False
    
    def register_callback(self, message_type, callback):
        self.callbacks[message_type] = callback
        print(f"📋 Callback registrado para: {message_type}")
    
    def disconnect(self):
        print("🔌 Desconectando...")
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("✅ Desconectado")