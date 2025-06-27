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
            
            print(f"Palabras cargadas: {len(self.game_words)} jugables, {len(self.valid_words)} válidas")
            
        except Exception as e:
            print(f"Error cargando palabras: {e}")
            self.game_words = ["BRAKE", "CRANE", "SLATE", "AROSE", "AUDIO"]
            self.valid_words = set(self.game_words)
    
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        
        print(f"Servidor iniciado en {self.host}:{self.port}")
        
        try:
            while True:
                client_socket, address = server_socket.accept()
                print(f"Cliente conectado: {address}")
                
                client_thread = threading.Thread(
                    target=self.handle_new_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("Servidor detenido")
        finally:
            server_socket.close()
    
    def handle_new_client(self, client_socket, address):
        try:
            with self.lock:
                self.client_counter += 1
                client_id = self.client_counter
            
            success = self.send_message(client_socket, {
                'type': 'waiting',
                'message': 'Esperando oponente...'
            })
            
            if not success:
                client_socket.close()
                return
            
            client_info = {
                'socket': client_socket,
                'address': address,
                'id': client_id,
                'connected': True
            }
            
            with self.lock:
                self.waiting_clients.append(client_info)
                waiting_count = len(self.waiting_clients)
                
                if waiting_count >= 2:
                    client1 = self.waiting_clients.pop(0)
                    client2 = self.waiting_clients.pop(0)
                    
                    game_thread = threading.Thread(
                        target=self.start_game,
                        args=(client1, client2)
                    )
                    game_thread.daemon = True
                    game_thread.start()
                    
        except Exception as e:
            print(f"Error manejando cliente {address}: {e}")
            try:
                client_socket.close()
            except:
                pass
    
    def start_game(self, client1, client2):
        try:
            client1['game_id'] = 1
            client2['game_id'] = 2
            
            target_word = random.choice(self.game_words)
            
            # Enviar player_id a ambos
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
                return
            
            time.sleep(0.1)
            
            # Enviar game_start
            success1 = self.send_message(client1['socket'], {
                'type': 'game_start',
                'opponent_id': 2
            })
            
            success2 = self.send_message(client2['socket'], {
                'type': 'game_start',
                'opponent_id': 1
            })
            
            if not success1 or not success2:
                return
            
            game = {
                'clients': [client1, client2],
                'target_word': target_word,
                'finished': False,
                'winner': None
            }
            
            for client in game['clients']:
                client['attempts'] = 0
                client['finished'] = False
                client['won'] = False
            
            with self.lock:
                self.active_games.append(game)
            
            for client in game['clients']:
                game_thread = threading.Thread(
                    target=self.handle_game_client,
                    args=(client, game)
                )
                game_thread.daemon = True
                game_thread.start()
                
        except Exception as e:
            print(f"Error iniciando juego: {e}")
    
    def handle_game_client(self, client, game):
        client_socket = client['socket']
        buffer = ""
        
        try:
            while client['connected'] and not game['finished']:
                try:
                    client_socket.settimeout(60.0)
                    data = client_socket.recv(1024)
                    
                    if not data:
                        break
                    
                    buffer += data.decode('utf-8')
                    
                    while '\n' in buffer:
                        message_str, buffer = buffer.split('\n', 1)
                        
                        if message_str.strip():
                            try:
                                message = json.loads(message_str.strip())
                                msg_type = message.get('type')
                                
                                if msg_type == 'attempt':
                                    word = message.get('word', '').upper()
                                    self.handle_attempt(client, game, word)
                                    
                            except json.JSONDecodeError:
                                continue
                        
                except socket.timeout:
                    if game['finished'] or not client['connected']:
                        break
                    continue
                except Exception:
                    break
                    
        except Exception:
            pass
        finally:
            with self.lock:
                client['connected'] = False
            try:
                client_socket.close()
            except:
                pass
    
    def handle_attempt(self, client, game, word):
        if len(word) != 5 or word not in self.valid_words:
            self.send_message(client['socket'], {
                'type': 'invalid_word',
                'word': word
            })
            return
        
        client['attempts'] += 1
        result = self.check_word(word, game['target_word'])
        
        won = word == game['target_word']
        finished = won or client['attempts'] >= 6
        
        client['finished'] = finished
        client['won'] = won
        
        if won and not game['finished']:
            game['winner'] = client['game_id']
            game['finished'] = True
        
        self.send_message(client['socket'], {
            'type': 'attempt_result',
            'word': word,
            'result': result,
            'attempt': client['attempts'],
            'won': won,
            'finished': finished,
            'game_finished': game['finished'],
            'winner': game['winner']
        })
        
        # Notificar oponente
        for c in game['clients']:
            if c['game_id'] != client['game_id'] and c['connected']:
                self.send_message(c['socket'], {
                    'type': 'opponent_progress',
                    'opponent_id': client['game_id'],
                    'attempt': client['attempts'],
                    'won': won,
                    'finished': finished,
                    'game_finished': game['finished'],
                    'winner': game['winner']
                })
                break
        
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
        final_message = {
            'type': 'game_end',
            'target_word': game['target_word'],
            'winner': game['winner'],
            'players': [
                {
                    'id': c['game_id'],
                    'attempts': c['attempts'],
                    'won': c['won']
                } for c in game['clients'] if c['connected']
            ]
        }
        
        # Enviar game_end a AMBOS clientes
        for client in game['clients']:
            if client['connected']:
                self.send_message(client['socket'], final_message)
        
        # Dar tiempo para que procesen el mensaje
        time.sleep(0.5)
        
        # Preguntar nueva partida a AMBOS
        for client in game['clients']:
            if client['connected']:
                self.send_message(client['socket'], {
                    'type': 'ask_new_game',
                    'message': '¿Quieres jugar otra partida?'
                })
        
        # Manejar respuestas
        new_game_thread = threading.Thread(
            target=self.handle_new_game_responses,
            args=(game,)
        )
        new_game_thread.daemon = True
        new_game_thread.start()
        
        with self.lock:
            if game in self.active_games:
                self.active_games.remove(game)
    
    def handle_new_game_responses(self, game):
        responses = {}
        response_threads = []
        
        for client in game['clients']:
            if client['connected']:
                thread = threading.Thread(
                    target=self.get_new_game_response,
                    args=(client, responses)
                )
                thread.daemon = True
                thread.start()
                response_threads.append(thread)
        
        for thread in response_threads:
            thread.join(timeout=30)
        
        self.process_new_game_responses(game, responses)
    
    def get_new_game_response(self, client, responses):
        buffer = ""
        
        try:
            client['socket'].settimeout(30)
            
            while True:
                data = client['socket'].recv(1024)
                if not data:
                    break
                    
                buffer += data.decode('utf-8')
                
                if '\n' in buffer:
                    message_str, buffer = buffer.split('\n', 1)
                    
                    try:
                        message = json.loads(message_str.strip())
                        if message.get('type') == 'new_game_response':
                            responses[client['game_id']] = message.get('answer', False)
                            return
                    except json.JSONDecodeError:
                        continue
                
        except Exception:
            pass
            
        responses[client['game_id']] = False
    
    def process_new_game_responses(self, game, responses):
        client1_wants = responses.get(1, False)
        client2_wants = responses.get(2, False)
        
        if client1_wants and client2_wants:
            self.start_game(game['clients'][0], game['clients'][1])
            
        elif client1_wants and not client2_wants:
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
        except Exception:
            return False

if __name__ == "__main__":
    server = WordleServer()
    server.start()