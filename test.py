import tkinter as tk
from tkinter import messagebox
import config
from gui.matrix import Matrix
from gui.keyboard import VirtualKeyboard
from gui.status_panel import StatusPanel
from logic.word_manager import WordManager

class GameScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wordle - Dual Player")
        self.root.configure(bg=config.BLACK_BG)
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.root.geometry("900x700")
        self._center_window()
        
        # Frame principal
        self.main_frame = tk.Frame(self.root, bg=config.BLACK_BG)
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=20)
        
        # Frame superior para matriz y estado
        self.top_frame = tk.Frame(self.main_frame, bg=config.BLACK_BG)
        self.top_frame.pack(fill="x", pady=(0, 30))
        
        # Matriz del juego (tu implementación)
        self.matrix = Matrix(self.top_frame)
        self.matrix.frame.pack(side="left", padx=(0, 40))
        
        # Panel de estado (mejorado)
        self.status_panel = StatusPanel(self.top_frame)
        self.status_panel.frame.pack(side="right", fill="y")
        
        # Teclado virtual
        self.keyboard = VirtualKeyboard(self.main_frame, self._handle_virtual_key)
        self.keyboard.frame.pack(pady=(10, 0))
        
        # Tu lógica existente
        self.word_manager = WordManager()
        self.chosen_word = self.word_manager.get_word()
        
        # Estado del juego (manteniendo tus variables)
        self.row = 0
        self.column = 0
        self.finished = False
        self.win = False
        self.board = [[""] * 5 for _ in range(6)]
        
        # Capturar teclado (tu implementación)
        self.root.bind("<Key>", self.on_key)
        self.root.focus_set()
        
        print(f"Palabra a adivinar: {self.chosen_word}")
    
    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _handle_virtual_key(self, key):
        """Convierte clicks del teclado virtual a eventos de teclado"""
        if key == 'Return':
            event = type('Event', (), {'keysym': 'Return', 'char': ''})()
        elif key == 'BackSpace':
            event = type('Event', (), {'keysym': 'BackSpace', 'char': ''})()
        else:
            event = type('Event', (), {'keysym': key, 'char': key.lower()})()
        self.on_key(event)
    
    def _update_keyboard_colors(self, typed_word, result):
        """Actualiza los colores del teclado según el resultado"""
        letter_status = {}
    
        for i, letter in enumerate(typed_word):
            current_status = result[i]
            
            if letter not in letter_status:
                letter_status[letter] = current_status
            else:
                # Mantener el mejor estado: Verde > Amarillo > Gris
                if current_status == 2:  # Verde siempre gana
                    letter_status[letter] = 2
                elif current_status == 1 and letter_status[letter] == 0:  # Amarillo solo si era gris
                    letter_status[letter] = 1
        
        # Aplicar colores al teclado
        for letter, status in letter_status.items():
            if status == 2:
                self.keyboard.update_key_color(letter, config.GREEN)
            elif status == 1:
                # Solo actualizar a amarillo si no es verde
                current_color = self.keyboard.key_buttons.get(letter, {}).cget('bg')
                if current_color != config.GREEN:
                    self.keyboard.update_key_color(letter, config.YELLOW)
            else:  # status == 0
                # Solo actualizar a gris si no es verde ni amarillo
                current_color = self.keyboard.key_buttons.get(letter, {}).cget('bg')
                if current_color not in [config.GREEN, config.YELLOW]:
                    self.keyboard.update_key_color(letter, config.GREY_USED)
    
    def on_key(self, event):
        """Tu lógica existente con algoritmo de colores corregido"""
        if self.finished:
            return
        
        char = event.char.upper()
        
        # Letra tipada (tu lógica)
        if char.isalpha() and len(char) == 1:
            if self.column < 5:
                self.board[self.row][self.column] = char
                self.matrix.update_square(self.row, self.column, char)
                self.column += 1
        
        # Enter (con algoritmo corregido)
        elif event.keysym == "Return" or event.keysym == "KP_Enter":
            print("Column ", self.column, "row ", self.row)
            if self.column == 5:
                typed_word = "".join(self.board[self.row])
                print("Word to guess: ", self.chosen_word)
                print("Current word: ", typed_word)
                
                # Validar palabra
                if not self.word_manager.is_valid(typed_word):
                    self.matrix.shake_row(self.row)
                    return
                
                # ALGORITMO CORREGIDO para colores
                from collections import Counter
                result = [0] * 5
                target_count = Counter(self.chosen_word)
                
                # Primera pasada: letras en posición correcta (verdes)
                for i in range(5):
                    if typed_word[i] == self.chosen_word[i]:
                        result[i] = 2  # Verde
                        target_count[typed_word[i]] -= 1
                
                # Segunda pasada: letras en posición incorrecta (amarillas)
                for i in range(5):
                    if result[i] == 0:  # Solo si no es verde
                        if typed_word[i] in target_count and target_count[typed_word[i]] > 0:
                            result[i] = 1  # Amarillo
                            target_count[typed_word[i]] -= 1
                
                # Aplicar colores a la matriz
                for i in range(5):
                    if result[i] == 2:  # Verde
                        self.matrix.paint_square_perfect(self.row, i)
                    elif result[i] == 1:  # Amarillo
                        self.matrix.paint_square_good(self.row, i)
                    else:  # Gris
                        self.matrix.paint_square_bad(self.row, i)
                
                # Actualizar teclado con lógica corregida
                self._update_keyboard_colors(typed_word, result)
                
                # ¿Ganó el jugador? (tu lógica)
                if typed_word == self.chosen_word:
                    self.finished = True
                    self.win = True
                    from tkinter import messagebox
                    messagebox.showinfo("¡Felicidades!", f"¡Adivinaste la palabra '{self.chosen_word}'!")
                    return
                
                # Continuar con siguiente fila (tu lógica)
                if self.row < 5:
                    self.row += 1
                    self.column = 0
                    self.status_panel.update_attempts(self.row + 1, 6)
                else:
                    self.finished = True
                    from tkinter import messagebox
                    messagebox.showinfo("Juego terminado", f"La palabra era: {self.chosen_word}")
            else:
                self.matrix.shake_row(self.row)
        
        # Backspace (tu lógica)
        elif event.keysym == "BackSpace":
            if self.column > 0:
                self.column -= 1
                self.board[self.row][self.column] = ""
                self.matrix.clear_square(self.row, self.column)
        
        print("Row: ", self.row, "Column: ", self.column)

    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = GameScreen()
    game.run()