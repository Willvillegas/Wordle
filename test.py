import tkinter as tk
import config
from gui.matrix import Matrix
from logic.word_manager import WordManager

class GameScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wordle")
        self.root.configure(bg=config.BLACK_BG)
        self.root.resizable(False, False)
        self.main_frame = tk.Frame(self.root, bg=config.BLACK_BG)
        self.main_frame.pack(padx=20, pady=20)

        self.matrix = Matrix(self.main_frame)
        self.matrix.frame.pack(side="left", padx=(0,20))

        # other player progress
        self.opponent_frame = tk.Frame(self.main_frame, bg=config.BLACK_BG)
        self.opponent_frame.pack(side="right")
        self.opponent_progress = []
        for i in range(6):
            indicator = tk.Label(self.opponent_frame, text="", width=2, height=1,
                        bg=config.GREY_LINE, relief="ridge", bd=2)
            indicator.pack(pady=6)
            self.opponent_progress.append(indicator)

        # falta agregar el teclado y tal vez los indicadores del ptj del otro jugador
        # ademas del tiempo
        self.word_manager = WordManager()
        self.chosen_word = self.word_manager.get_word()
        # game state
        self.row = 0
        self.column = 0
        self.finished = False
        self.win = False
        self.board = [[""] * 5 for _ in range(6)]
        # capture keyboard
        self.root.bind("<Key>", self.on_key)

    def on_key(self, event):
        if self.finished:
            return
        char = event.char.upper()
        # typed letter
        if char.isalpha() and len(char) == 1:
            if self.column < 5:
                self.board[self.row][self.column] = char
                self.matrix.update_square(self.row, self.column,char)
                self.column += 1
        # enter
        elif event.keysym == "Return" or event.keysym == "KP_Enter":
            print("Column ", self.column, "row ", self.row)
            if self.column == 5:
                # validate word
                typed_word = "".join(self.board[self.row])
                print("Word to guess: ", self.chosen_word)
                print("Current word: ", typed_word)
                for i in range(5):
                    # properly placed letter
                    if typed_word[i] == self.chosen_word[i]:
                        self.matrix.paint_square_perfect(self.row, i)
                    # letter in incorrect spot
                    elif typed_word[i] in self.chosen_word:
                        self.matrix.paint_square_good(self.row, i)
                    else:
                        self.matrix.paint_square_bad(self.row, i)
                # did the player win ?
                if typed_word == self.chosen_word:
                    self.finished = True
                    self.win = True
                # continue with next row
                if self.row < 5:
                    self.row += 1
                    self.column = 0
                else:
                    self.finished = True
            else:
                self.matrix.shake_row(self.row)
        # backspace -> delete
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

