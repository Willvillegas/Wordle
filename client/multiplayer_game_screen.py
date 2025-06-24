import tkinter as tk
from tkinter import messagebox
import config
from gui.matrix import Matrix
from gui.keyboard import VirtualKeyboard
from gui.status_panel import StatusPanel
from client.network_manager import NetworkManager
from collections import Counter

class MultiplayerGameScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wordle - Multijugador")
        self.root.configure(bg=config.BLACK_BG)
        self.root.resizable(False, False)
        self.root.geometry("900x700")
        self._center_window()
        
        # Estado de conexión
        self.network = NetworkManager()
        self.player_id = None
        self.opponent_id = None
        self.game_started = False
        self.target_word = None
        
        # UI
        self._setup_ui()
        
        # Estado del juego local
        self.row = 0
        self.column = 0
        self.finished = False
        self.win = False
        self.board = [[""] * 5 for _ in range(6)]
        
        # Configurar callbacks de red
        self._setup_network_callbacks()
        
        # Capturar teclado
        self.root.bind("<Key>", self.on_key)
        self.root.focus_set()
        
        # Conectar al servidor
        self._connect_to_server()
    
    def _setup_ui(self):
        # Frame principal
        self.main_frame = tk.Frame(self.root, bg=config.BLACK_BG)
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=20)
        
        # Frame superior
        self.top_frame = tk.Frame(self.main_frame, bg=config.BLACK_BG)
        self.top_frame.pack(fill="x", pady=(0, 30))
        
        # Matriz del juego
        self.matrix = Matrix(self.top_frame)
        self.matrix.frame.pack(side="left", padx=(0, 40))
        
        # Panel de estado
        self.status_panel = StatusPanel(self.top_frame)
        self.status_panel.frame.pack(side="right", fill="y")
        
        # Teclado virtual
        self.keyboard = VirtualKeyboard(self.main_frame, self._handle_virtual_key)
        self.keyboard.frame.pack(pady=(10, 0))
        
        # Estado inicial
        self._show_connection_status("Conectando al servidor...")
    
    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _show_connection_status(self, message):
        # Aquí puedes mostrar el estado en la UI
        self.root.title(f"Wordle - {message}")
    
    def _connect_to_server(self):
        if self.network.connect():
            self._show_connection_status("Conectado - Esperando jugadores...")
        else:
            messagebox.showerror("Error", "No se pudo conectar al servidor")
            self.root.destroy()
    
    def _setup_network_callbacks(self):
        self.network.register_callback('player_id', self._on_player_id)
        self.network.register_callback('game_start', self._on_game_start)
        self.network.register_callback('attempt_result', self._on_attempt_result)
        self.network.register_callback('opponent_progress', self._on_opponent_progress)
        self.network.register_callback('game_end', self._on_game_end)
        self.network.register_callback('invalid_word', self._on_invalid_word)
    
    def _on_player_id(self, message):
        self.player_id = message['player_id']
        waiting = message['waiting_for']
        if waiting > 0:
            self._show_connection_status(f"Jugador {self.player_id} - Esperando {waiting} jugador(es)")
        else:
            self._show_connection_status("Todos conectados - Iniciando juego...")
    
    def _on_game_start(self, message):
        self.game_started = True
        self.opponent_id = message['opponent_id']
        # En producción, no recibirías la palabra objetivo
        # self.target_word = message['target_word']
        
        self._show_connection_status(f"¡Juego iniciado! Eres el Jugador {self.player_id}")
        self.status_panel.update_attempts(1, 6)
    
    def _on_attempt_result(self, message):
        word = message['word']
        result = message['result']
        attempt = message['attempt']
        won = message['won']
        finished = message['finished']
        
        # Aplicar colores a la matriz
        for i in range(5):
            if result[i] == 2:  # Verde
                self.matrix.paint_square_perfect(self.row, i)
            elif result[i] == 1:  # Amarillo
                self.matrix.paint_square_good(self.row, i)
            else:  # Gris
                self.matrix.paint_square_bad(self.row, i)
        
        # Actualizar teclado
        self._update_keyboard_colors(word, result)
        
        if won:
            self.finished = True
            self.win = True
            messagebox.showinfo("¡Felicidades!", "¡Ganaste la partida!")
        elif finished:
            self.finished = True
            messagebox.showinfo("Perdiste", f"Se acabaron los intentos")
        else:
            # Continuar con siguiente fila
            if self.row < 5:
                self.row += 1
                self.column = 0
                self.status_panel.update_attempts(self.row + 1, 6)
    
    def _on_opponent_progress(self, message):
        attempt = message['attempt']
        won = message['won']
        finished = message['finished']
        
        # Actualizar indicador del oponente
        if won:
            self.status_panel.update_opponent_progress(attempt - 1, 'correct')
            if not self.finished:
                messagebox.showinfo("Juego terminado", "Tu oponente ganó")
        elif finished:
            self.status_panel.update_opponent_progress(attempt - 1, 'incorrect')
        else:
            self.status_panel.update_opponent_progress(attempt - 1, 'trying')
    
    def _on_game_end(self, message):
        target_word = message['target_word']
        winner = message['winner']
        
        if winner == self.player_id:
            result_msg = "¡Ganaste la partida!"
        elif winner:
            result_msg = f"Perdiste. El Jugador {winner} ganó."
        else:
            result_msg = "Empate - Nadie adivinó la palabra."
        
        messagebox.showinfo("Juego terminado", f"{result_msg}\n\nLa palabra era: {target_word}")
        self.finished = True
    
    def _on_invalid_word(self, message):
        self.matrix.shake_row(self.row)
    
    def _handle_virtual_key(self, key):
        if key == 'Return':
            event = type('Event', (), {'keysym': 'Return', 'char': ''})()
        elif key == 'BackSpace':
            event = type('Event', (), {'keysym': 'BackSpace', 'char': ''})()
        else:
            event = type('Event', (), {'keysym': key, 'char': key.lower()})()
        self.on_key(event)
    
    def on_key(self, event):
        if self.finished or not self.game_started:
            return
        
        char = event.char.upper()
        
        # Letra tipada
        if char.isalpha() and len(char) == 1:
            if self.column < 5:
                self.board[self.row][self.column] = char
                self.matrix.update_square(self.row, self.column, char)
                self.column += 1
        
        # Enter - enviar palabra al servidor
        elif event.keysym == "Return" or event.keysym == "KP_Enter":
            if self.column == 5:
                typed_word = "".join(self.board[self.row])
                self.network.send_attempt(typed_word)
                # El servidor responderá con el resultado
            else:
                self.matrix.shake_row(self.row)
        
        # Backspace
        elif event.keysym == "BackSpace":
            if self.column > 0:
                self.column -= 1
                self.board[self.row][self.column] = ""
                self.matrix.clear_square(self.row, self.column)
    
    def _update_keyboard_colors(self, word, result):
        letter_status = {}
        
        for i, letter in enumerate(word):
            current_status = result[i]
            
            if letter not in letter_status:
                letter_status[letter] = current_status
            else:
                if current_status == 2:
                    letter_status[letter] = 2
                elif current_status == 1 and letter_status[letter] == 0:
                    letter_status[letter] = 1
        
        for letter, status in letter_status.items():
            if status == 2:
                self.keyboard.update_key_color(letter, config.GREEN)
            elif status == 1:
                current_color = self.keyboard.key_buttons.get(letter, {}).cget('bg')
                if current_color != config.GREEN:
                    self.keyboard.update_key_color(letter, config.YELLOW)
            else:
                current_color = self.keyboard.key_buttons.get(letter, {}).cget('bg')
                if current_color not in [config.GREEN, config.YELLOW]:
                    self.keyboard.update_key_color(letter, config.GREY_USED)
    
    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.network.disconnect()