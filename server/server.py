import socket
import threading
import json
import random
from collections import Counter
import pathlib

class WordleServer:
    def __init__(self):
        self.host = 'localhost'
        self.port = 10100
        self.load_words()
        self.waiting_clients = []
        self.active_games = []
        
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
        server_socket.listen(5)
        
        print(f"Servidor iniciado en {self.host}:{self.port}")
        
        try:
            while True:
                client_socket, address = server_socket.accept()
                
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
        self.send_message(client_socket, {
            'type': 'waiting',
            'message': 'Esperando oponente...'
        })
        
        client_info = {
            'socket': client_socket,
            'address': address,
            'id': len(self.waiting_clients) + 1
        }
        
        self.waiting_clients.append(client_info)
        
        if len(self.waiting_clients) >= 2:
            client1 = self.waiting_clients.pop(0)
            client2 = self.waiting_clients.pop(0)
            self.start_game(client1, client2)
    
    def start_game(self, client1, client2):
        client1['id'] = 1
        client2['id'] = 2
        
        target_word = random.choice(self.game_words)
        
        self.send_message(client1['socket'], {
            'type': 'player_id',
            'player_id': 1,
            'opponent_id': 2
        })
        
        self.send_message(client2['socket'], {
            'type': 'player_id',
            'player_id': 2,
            'opponent_id': 1
        })
        
        self.send_message(client1['socket'], {
            'type': 'game_start',
            'opponent_id': 2
        })
        
        self.send_message(client2['socket'], {
            'type': 'game_start',
            'opponent_id': 1
        })
        
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
        
        self.active_games.append(game)
        
        for client in game['clients']:
            game_thread = threading.Thread(
                target=self.handle_game_client,
                args=(client, game)
            )
            game_thread.daemon = True
            game_thread.start()
    
    def handle_game_client(self, client, game):
        client_socket = client['socket']
        
        try:
            while not game['finished']:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    msg_type = message.get('type')
                    
                    if msg_type == 'attempt':
                        word = message.get('word', '').upper()
                        self.handle_attempt(client, game, word)
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception:
            pass
        finally:
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
            game['winner'] = client['id']
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
        
        opponent = None
        for c in game['clients']:
            if c['id'] != client['id']:
                opponent = c
                break
        
        if opponent:
            self.send_message(opponent['socket'], {
                'type': 'opponent_progress',
                'opponent_id': client['id'],
                'attempt': client['attempts'],
                'won': won,
                'finished': finished,
                'game_finished': game['finished'],
                'winner': game['winner']
            })
        
        if game['finished'] or all(c['finished'] for c in game['clients']):
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
                    'id': c['id'],
                    'attempts': c['attempts'],
                    'won': c['won']
                } for c in game['clients']
            ]
        }
        
        for client in game['clients']:
            self.send_message(client['socket'], final_message)
        
        self.handle_new_game_responses(game)
        
        if game in self.active_games:
            self.active_games.remove(game)
    
    def handle_new_game_responses(self, game):
        for client in game['clients']:
            self.send_message(client['socket'], {
                'type': 'ask_new_game',
                'message': '¿Quieres jugar otra partida?'
            })
        
        responses = {}
        response_threads = []
        
        for client in game['clients']:
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
        try:
            client['socket'].settimeout(30)
            data = client['socket'].recv(1024)
            
            if data:
                message = json.loads(data.decode('utf-8'))
                if message.get('type') == 'new_game_response':
                    responses[client['id']] = message.get('answer', False)
                else:
                    responses[client['id']] = False
            else:
                responses[client['id']] = False
                
        except Exception:
            responses[client['id']] = False
    
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
            data = json.dumps(message).encode('utf-8')
            client_socket.send(data)
            return True
        except Exception:
            return False
