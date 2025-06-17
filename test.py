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
        self.matrix = Matrix(self.root)
        # falta agregar el teclado y tal vez los indicadores del ptj del otro jugador
        # ademas del tiempo
        self.word_manager = WordManager()

        # game state
        self.row = 0
        self.column = 0
        self.finished = False
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
                print("Word to guess: ", self.word_manager.get_word())
                print("Current word: ", typed_word)


                # continue with next row
                if self.row < 6:
                    self.row += 1
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

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = GameScreen()
    game.run()

