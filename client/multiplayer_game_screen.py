import tkinter as tk
from tkinter import messagebox
import config
from gui.matrix import Matrix
from gui.keyboard import VirtualKeyboard
from gui.status_panel import StatusPanel
from client.network_manager import NetworkManager

class MultiplayerGameScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wordle - Multijugador")
        self.root.configure(bg=config.BLACK_BG)
        self.root.resizable(False, False)
        self.root.geometry("900x700")
        self._center_window()
        
        self.network = NetworkManager()
        self.player_id = None
        self.opponent_id = None
        self.game_started = False
        
        self._setup_ui()
        
        self.row = 0
        self.column = 0
        self.finished = False
        self.win = False
        self.board = [[""] * 5 for _ in range(6)]
        
        self.root.bind("<Key>", self.on_key)
        self.root.focus_set()
        
        self._connect_to_server()
    
    def _setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=config.BLACK_BG)
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=20)
        
        self.top_frame = tk.Frame(self.main_frame, bg=config.BLACK_BG)
        self.top_frame.pack(fill="x", pady=(0, 30))
        
        self.matrix = Matrix(self.top_frame)
        self.matrix.frame.pack(side="left", padx=(0, 40))
        
        self.status_panel = StatusPanel(self.top_frame)
        self.status_panel.frame.pack(side="right", fill="y")
        
        self.keyboard = VirtualKeyboard(self.main_frame, self._handle_virtual_key)
        self.keyboard.frame.pack(pady=(10, 0))
        
        self._show_connection_status("Conectando...")
    
    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _show_connection_status(self, message):
        self.root.title(f"Wordle - {message}")
    
    def _connect_to_server(self):
        self._setup_network_callbacks()
        
        if self.network.connect():
            self._show_connection_status("Conectado")
        else:
            messagebox.showerror("Error", "No se pudo conectar al servidor")
            self.root.destroy()
    
    def _setup_network_callbacks(self):
        self.network.register_callback('waiting', self._on_waiting)
        self.network.register_callback('player_id', self._on_player_id)
        self.network.register_callback('game_start', self._on_game_start)
        self.network.register_callback('attempt_result', self._on_attempt_result)
        self.network.register_callback('opponent_progress', self._on_opponent_progress)
        self.network.register_callback('game_end', self._on_game_end)
        self.network.register_callback('invalid_word', self._on_invalid_word)
        self.network.register_callback('ask_new_game', self._on_ask_new_game)
        self.network.register_callback('disconnect', self._on_disconnect)
    
    def _on_waiting(self, message):
        self._show_connection_status("Esperando oponente...")
    
    def _on_player_id(self, message):
        self.player_id = message['player_id']
        self.opponent_id = message.get('opponent_id')
        waiting = message.get('waiting_for', 0)
        
        if waiting > 0:
            self._show_connection_status(f"Jugador {self.player_id} - Esperando oponente")
        else:
            self._show_connection_status("Iniciando juego...")
    
    def _on_game_start(self, message):
        self.game_started = True
        self.opponent_id = message['opponent_id']
        
        self._show_connection_status(f"Jugando - Jugador {self.player_id}")
        self.status_panel.update_attempts(1, 6)
    
    def _on_attempt_result(self, message):
        result = message['result']
        won = message['won']
        finished = message['finished']
        
        for i in range(5):
            if result[i] == 2:
                self.matrix.paint_square_perfect(self.row, i)
            elif result[i] == 1:
                self.matrix.paint_square_good(self.row, i)
            else:
                self.matrix.paint_square_bad(self.row, i)
        
        self._update_keyboard_colors(message['word'], result)
        
        if won:
            self.finished = True
            self.win = True
            messagebox.showinfo("¡Felicidades!", "¡Ganaste!")
        elif finished:
            self.finished = True
            messagebox.showinfo("Perdiste", "Se acabaron los intentos")
        else:
            if self.row < 5:
                self.row += 1
                self.column = 0
                self.status_panel.update_attempts(self.row + 1, 6)
    
    def _on_opponent_progress(self, message):
        attempt = message['attempt']
        won = message['won']
        finished = message['finished']
        
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
        reason = message.get('reason', '')
        
        if reason:
            result_msg = f"Juego terminado: {reason}"
        elif winner == self.player_id:
            result_msg = "¡Ganaste la partida!"
        elif winner:
            result_msg = f"Perdiste. El Jugador {winner} ganó."
        else:
            result_msg = "Empate"
        
        messagebox.showinfo("Juego terminado", f"{result_msg}\n\nLa palabra era: {target_word}")
        self.finished = True
    
    def _on_ask_new_game(self, message):
        wants_new_game = messagebox.askyesno("Nueva partida", "¿Quieres jugar otra partida?")
        
        self.network.send_new_game_response(wants_new_game)
        
        if wants_new_game:
            self._reset_game_for_new_match()
            self._show_connection_status("Esperando respuesta del oponente...")
    
    def _on_disconnect(self, message):
        messagebox.showinfo("Desconectado", message.get('message', 'Desconectado del servidor'))
        self.root.destroy()
    
    def _on_invalid_word(self, message):
        self.matrix.shake_row(self.row)
    
    def _reset_game_for_new_match(self):
        self.row = 0
        self.column = 0
        self.finished = False
        self.win = False
        self.game_started = False
        self.board = [[""] * 5 for _ in range(6)]
        
        for r in range(6):
            for c in range(5):
                self.matrix.clear_square(r, c)
                self.matrix.labels[r][c].configure(bg=config.BLACK_BG)
        
        for key, button in self.keyboard.key_buttons.items():
            button.configure(bg=config.GREY_USED)
        
        self.status_panel.update_attempts(1, 6)
        for i in range(6):
            self.status_panel.update_opponent_progress(i, 'empty')
    
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
        
        if char.isalpha() and len(char) == 1:
            if self.column < 5:
                self.board[self.row][self.column] = char
                self.matrix.update_square(self.row, self.column, char)
                self.column += 1
        
        elif event.keysym == "Return" or event.keysym == "KP_Enter":
            if self.column == 5:
                typed_word = "".join(self.board[self.row])
                self.network.send_attempt(typed_word)
            else:
                self.matrix.shake_row(self.row)
        
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

if __name__ == "__main__":
    game = MultiplayerGameScreen()
    game.run()