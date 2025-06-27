# server/server.py
import socket
import threading
import json
import random
from collections import Counter
import pathlib
import time

class WordleServer:
    def __init__(self, host='0.0.0.0', port=10100):
        self.host = host
        self.port = port
        self.load_words()
        self.waiting_clients = []
        self.active_games = []
        self.client_counter = 0
        self.lock = threading.Lock()
        
    def load_words(self):
        try:
            base_path = pathlib.Path(__file__).resolve().parent.parent
            pr_path = base_path / 'data' / 'pr.txt'
            sedout_path = base_path / 'data' / 'sedout.txt'
            
            self.game_words = []
            with open(pr_path, 'r', encoding='utf-8') as file:
                for line in file:
                    word = line.strip().upper()
                    if len(word) == 5:
                        self.game_words.append(word)
            
            self.valid_words = set(self.game_words)
            try:
                with open(sedout_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        word = line.strip().upper()
                        if len(word) == 5:
                            self.valid_words.add(word)
            except FileNotFoundError:
                pass
            
            print(f"Palabras cargadas: {len(self.game_words)} jugables, {len(self.valid_words)} validas")
            
        except Exception as e:
            print(f"Error cargando palabras: {e}")
            self.game_words = ["BRAKE", "CRANE", "SLATE", "AROSE", "AUDIO"]
            self.valid_words = set(self.game_words)
    
    def start(self):
        print("=== WORDLE SERVER ===")
        
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            print(f"Binding a {self.host}:{self.port}")
            server_socket.bind((self.host, self.port))
            
            print(f"Listening en puerto {self.port}")
            server_socket.listen(10)
            
            print(f"Servidor listo en {self.host}:{self.port}")
            print("Esperando conexiones...")
            
            while True:
                try:
                    print("--- Esperando siguiente cliente ---")
                    
                    client_socket, address = server_socket.accept()
                    print(f"Cliente conectado desde: {address}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_new_client_safe,
                        args=(client_socket, address),
                        name=f"Client-{address[1]}"
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    print(f"Thread iniciado para {address}")
                    
                except Exception as e:
                    print(f"Error aceptando conexion: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error critico del servidor: {e}")
        finally:
            try:
                server_socket.close()
            except:
                pass
    
    def handle_new_client_safe(self, client_socket, address):
        try:
            self.handle_new_client(client_socket, address)
        except Exception as e:
            print(f"Error manejando cliente {address}: {e}")
            try:
                client_socket.close()
            except:
                pass
    
    def handle_new_client(self, client_socket, address):
        print(f"Manejando cliente {address}")
        
        with self.lock:
            self.client_counter += 1
            client_id = self.client_counter
        
        print(f"Enviando mensaje de espera a {address}")
        
        success = self.send_message(client_socket, {
            'type': 'waiting',
            'message': 'Esperando oponente...'
        })
        
        if not success:
            print(f"Error enviando mensaje de espera a {address}")
            try:
                client_socket.close()
            except:
                pass
            return
        
        print(f"Mensaje de espera enviado a {address}")
        
        client_info = {
            'socket': client_socket,
            'address': address,
            'id': client_id,
            'connected': True
        }
        
        with self.lock:
            self.waiting_clients.append(client_info)
            waiting_count = len(self.waiting_clients)
            print(f"Clientes esperando: {waiting_count}")
            
            if waiting_count >= 2:
                client1 = self.waiting_clients.pop(0)
                client2 = self.waiting_clients.pop(0)
                
                print(f"Emparejando: {client1['address']} vs {client2['address']}")
                
                game_thread = threading.Thread(
                    target=self.start_game_safe,
                    args=(client1, client2),
                    name=f"Game-{client1['id']}-{client2['id']}"
                )
                game_thread.daemon = True
                game_thread.start()
    
    def start_game_safe(self, client1, client2):
        try:
            self.start_game(client1, client2)
        except Exception as e:
            print(f"Error iniciando juego: {e}")
    
    def start_game(self, client1, client2):
        print(f"Iniciando juego entre {client1['address']} y {client2['address']}")
        
        client1['game_id'] = 1
        client2['game_id'] = 2
        
        target_word = random.choice(self.game_words)
        print(f"Palabra objetivo: {target_word}")
        
        print("Enviando player_id a ambos jugadores")
        
        success1 = self.send_message(client1['socket'], {
            'type': 'player_id',
            'player_id': 1,
            'opponent_id': 2
        })
        
        success2 = self.send_message(client2['socket'], {
            'type': 'player_id',
            'player_id': 2,
            'opponent_id': 1
        })
        
        if not success1 or not success2:
            print("Error enviando player_id")
            return
        
        print("Player IDs enviados")
        
        time.sleep(0.1)
        
        print("Enviando game_start")
        
        success1 = self.send_message(client1['socket'], {
            'type': 'game_start',
            'opponent_id': 2
        })
        
        success2 = self.send_message(client2['socket'], {
            'type': 'game_start',
            'opponent_id': 1
        })
        
        if not success1 or not success2:
            print("Error enviando game_start")
            return
        
        print("Game start enviado - Juego iniciado")
        
        game = {
            'clients': [client1, client2],
            'target_word': target_word,
            'finished': False,
            'winner': None,
            'created_at': time.time()
        }
        
        for client in game['clients']:
            client['attempts'] = 0
            client['finished'] = False
            client['won'] = False
        
        with self.lock:
            self.active_games.append(game)
            print(f"Juegos activos: {len(self.active_games)}")
        
        for client in game['clients']:
            game_thread = threading.Thread(
                target=self.handle_game_client_safe,
                args=(client, game),
                name=f"GameClient-{client['id']}"
            )
            game_thread.daemon = True
            game_thread.start()
    
    def handle_game_client_safe(self, client, game):
        try:
            self.handle_game_client(client, game)
        except Exception as e:
            print(f"Error manejando cliente de juego {client['address']}: {e}")
    
    def handle_game_client(self, client, game):
        client_socket = client['socket']
        player_id = client.get('game_id', client['id'])
        
        print(f"Manejando juego para jugador {player_id} ({client['address']})")
        
        buffer = ""
        
        try:
            while client['connected'] and not game['finished']:
                try:
                    client_socket.settimeout(60.0)
                    data = client_socket.recv(1024)
                    
                    if not data:
                        print(f"Cliente {player_id} cerro conexion")
                        break
                    
                    buffer += data.decode('utf-8')
                    
                    while '\n' in buffer:
                        message_str, buffer = buffer.split('\n', 1)
                        
                        if message_str.strip():
                            try:
                                message = json.loads(message_str.strip())
                                msg_type = message.get('type')
                                
                                print(f"Jugador {player_id}: {msg_type}")
                                
                                if msg_type == 'attempt':
                                    word = message.get('word', '').upper()
                                    self.handle_attempt(client, game, word)
                                elif msg_type == 'new_game_response':
                                    # Almacenar respuesta para procesamiento posterior
                                    client['new_game_response'] = message.get('answer', False)
                                    print(f"Jugador {player_id} respondio nueva partida: {client['new_game_response']}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"Error JSON de jugador {player_id}: {e}")
                                continue
                        
                except socket.timeout:
                    if game['finished'] or not client['connected']:
                        break
                    continue
                    
                except Exception as e:
                    print(f"Error recibiendo de jugador {player_id}: {e}")
                    break
                    
        except Exception as e:
            print(f"Error en handle_game_client para {player_id}: {e}")
        finally:
            print(f"Cerrando conexion de jugador {player_id}")
            with self.lock:
                client['connected'] = False
            try:
                client_socket.close()
            except:
                pass
    
    def handle_attempt(self, client, game, word):
        player_id = client.get('game_id', client['id'])
        
        print(f"Jugador {player_id} intenta: {word}")
        
        if len(word) != 5 or word not in self.valid_words:
            print(f"Palabra invalida: {word}")
            self.send_message(client['socket'], {
                'type': 'invalid_word',
                'word': word
            })
            return
        
        client['attempts'] += 1
        current_attempt = client['attempts']
        
        result = self.check_word(word, game['target_word'])
        print(f"Resultado: {result}")
        
        won = word == game['target_word']
        finished = won or current_attempt >= 6
        
        client['finished'] = finished
        client['won'] = won
        
        if won and not game['finished']:
            game['winner'] = player_id
            game['finished'] = True
            print(f"Jugador {player_id} GANO!")
        
        response = {
            'type': 'attempt_result',
            'word': word,
            'result': result,
            'attempt': current_attempt,
            'won': won,
            'finished': finished,
            'game_finished': game['finished'],
            'winner': game['winner']
        }
        
        success = self.send_message(client['socket'], response)
        if not success:
            print(f"Error enviando resultado a jugador {player_id}")
        
        opponent = None
        for c in game['clients']:
            if c.get('game_id', c['id']) != player_id:
                opponent = c
                break
        
        if opponent and opponent['connected']:
            opponent_msg = {
                'type': 'opponent_progress',
                'opponent_id': player_id,
                'attempt': current_attempt,
                'won': won,
                'finished': finished,
                'game_finished': game['finished'],
                'winner': game['winner']
            }
            
            success = self.send_message(opponent['socket'], opponent_msg)
            if not success:
                print("Error enviando progreso a oponente")
        
        if game['finished'] or all(c['finished'] for c in game['clients'] if c['connected']):
            self.end_game(game)
    
    def check_word(self, guess, target):
        result = [0] * 5
        target_count = Counter(target)
        
        for i in range(5):
            if guess[i] == target[i]:
                result[i] = 2
                target_count[guess[i]] -= 1
        
        for i in range(5):
            if result[i] == 0:
                if guess[i] in target_count and target_count[guess[i]] > 0:
                    result[i] = 1
                    target_count[guess[i]] -= 1
        
        return result
    
    def end_game(self, game):
        print(f"Terminando juego. Ganador: {game['winner']}")
        
        final_message = {
            'type': 'game_end',
            'target_word': game['target_word'],
            'winner': game['winner'],
            'players': [
                {
                    'id': c.get('game_id', c['id']),
                    'attempts': c['attempts'],
                    'won': c['won']
                } for c in game['clients'] if c['connected']
            ]
        }
        
        # Enviar game_end a AMBOS clientes
        for client in game['clients']:
            if client['connected']:
                success = self.send_message(client['socket'], final_message)
                if not success:
                    print(f"Error enviando final a jugador {client.get('game_id', client['id'])}")
        
        print("Esperando antes de preguntar nueva partida...")
        time.sleep(1.0)  # Dar más tiempo
        
        # Preguntar nueva partida a AMBOS
        print("Enviando ask_new_game a ambos clientes")
        for client in game['clients']:
            if client['connected']:
                success = self.send_message(client['socket'], {
                    'type': 'ask_new_game',
                    'message': 'Quieres jugar otra partida?'
                })
                if success:
                    print(f"ask_new_game enviado a jugador {client.get('game_id', client['id'])}")
                else:
                    print(f"Error enviando ask_new_game a jugador {client.get('game_id', client['id'])}")
        
        # Esperar respuestas
        print("Esperando respuestas de nueva partida...")
        time.sleep(5.0)  # Esperar 5 segundos para respuestas
        
        # Procesar respuestas
        responses = {}
        for client in game['clients']:
            if client['connected']:
                player_id = client.get('game_id', client['id'])
                responses[player_id] = client.get('new_game_response', False)
                print(f"Respuesta jugador {player_id}: {responses[player_id]}")
        
        self.process_new_game_responses(game, responses)
        
        with self.lock:
            if game in self.active_games:
                self.active_games.remove(game)
                print(f"Juegos activos: {len(self.active_games)}")
    
    def process_new_game_responses(self, game, responses):
        print(f"Respuestas recibidas: {responses}")
        
        client1_wants = responses.get(1, False)
        client2_wants = responses.get(2, False)
        
        if client1_wants and client2_wants:
            print("Ambos quieren nueva partida")
            # Limpiar respuestas anteriores
            for client in game['clients']:
                client.pop('new_game_response', None)
            self.start_game(game['clients'][0], game['clients'][1])
            
        elif client1_wants and not client2_wants:
            print("Solo jugador 1 quiere jugar")
            self.send_message(game['clients'][0]['socket'], {
                'type': 'waiting',
                'message': 'Tu oponente se fue. Esperando nuevo oponente...'
            })
            
            with self.lock:
                self.waiting_clients.append(game['clients'][0])
            
            self.send_message(game['clients'][1]['socket'], {
                'type': 'disconnect',
                'message': 'Gracias por jugar'
            })
            try:
                game['clients'][1]['socket'].close()
            except:
                pass
                
        elif not client1_wants and client2_wants:
            print("Solo jugador 2 quiere jugar")
            self.send_message(game['clients'][1]['socket'], {
                'type': 'waiting',
                'message': 'Tu oponente se fue. Esperando nuevo oponente...'
            })
            
            with self.lock:
                self.waiting_clients.append(game['clients'][1])
            
            self.send_message(game['clients'][0]['socket'], {
                'type': 'disconnect',
                'message': 'Gracias por jugar'
            })
            try:
                game['clients'][0]['socket'].close()
            except:
                pass
                
        else:
            print("Ninguno quiere nueva partida")
            for client in game['clients']:
                if client['connected']:
                    self.send_message(client['socket'], {
                        'type': 'disconnect',
                        'message': 'Gracias por jugar'
                    })
                    try:
                        client['socket'].close()
                    except:
                        pass
    
    def send_message(self, client_socket, message):
        try:
            data = json.dumps(message).encode('utf-8') + b'\n'
            client_socket.send(data)
            return True
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
            return False

if __name__ == "__main__":
    server = WordleServer()
    server.start()