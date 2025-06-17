import random
import tkinter as tk
from tkinter import messagebox
import string
import pathlib

# palette
BLACK_BG = "#121213"
GREY_USED = "#3A3A3C"
GREY = "#818384"
YELLOW = "#B59F3B"
WHITE = "#F8F8F8"
GREEN = "#538D4E"
GREY_LINE = "#2D2D2F"

# test words
WORDS = [
    "GRASS", "HOARD", "BOARD", "PLANE", "APPLE", "ABOUT", "OTHER",
    "BRAKE", "CRANE", "CIDER", "EARTH", "FLAIR", "GHOST", "HONEY"
]

WORD = random.choice(WORDS).upper()


def load_words(filename):
    print("Loading words from", filename, "...")
    words = set()
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            word = line.strip().upper()
            if len(word) == 5:
                words.add(word)
    return words


class WordleApp:

    def __init__(self):
        self.valid_words = load_words("data/palabras5.txt")
        self.root = tk.Tk()
        self.root.title("Wordle")
        self.root.configure(bg=BLACK_BG)
        self.root.resizable(False, False)

        # game state
        self._row = 0
        self._column = 0
        self.finished = False
        self.board = [[""] * 5 for _ in range(6)]

        # matrix
        self.labels = []
        for r in range(6):
            row_labels = []
            for c in range(5):
                lbl = tk.Label(
                    self.root,
                    text="",
                    width=2,
                    height=1,
                    font=("Helvetica", 20, "bold"),
                    bg=BLACK_BG,
                    fg=WHITE,
                    relief="solid",
                    bd=2,
                    highlightbackground=GREY_USED,
                    highlightthickness=1,
                )
                lbl.grid(row=r, column=c, padx=2, pady=2)
                row_labels.append(lbl)
            self.labels.append(row_labels)
        # capture keyboard
        self.root.bind("<Key>", self.on_key)

    def update_square(self, char, delete_sqr=False):
        lbl = self.labels[self._row][self._column]
        if delete_sqr:
            lbl.configure(text="")
        else:
            lbl.configure(text=char)

    def shake_row(self, row):
        def animate_shake(step=0):
            if step < 6:
                if step % 2 == 0:
                    padx = (9, 4)
                else:
                    padx = (4, 9)
                for col in range(5):
                    self.labels[row][col].grid(row=row, column=col, padx=padx, pady=4)
                self.root.after(80, lambda: animate_shake(step + 1))
            else:
                for col in range(5):
                    self.labels[row][col].grid(row=row, column=col, padx=4, pady=4)

        animate_shake()

    def on_key(self, event):
        if self.finished:
            return

        char = event.char.upper()



        # A - Z
        if char in string.ascii_uppercase and len(char) == 1:
            if self._column < 5:
                self.board[self._row][self._column] = char
                self.update_square(char)
                self._column += 1

        elif event.keysym == "Return" or event.keysym == "KP_Enter": # numeric keyboard enter
            print("column ", self._column, "row ", self._row)
            if self._column == 5:
                # validate word
                current_word = "".join(self.board[self._row])
                print("current word", current_word)
            else:
                # shake box
                self.shake_row(self._row)

        # backspace
        elif event.keysym == "BackSpace":
            if self._column > 0:
                self._column -= 1
                self.board[self._row][self._column] = ""
                self.update_square("", delete_sqr=True)



    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = WordleApp()
    app.run()




# Referencias:
# usar sets para busquedas O(1) - https://www.freecodecamp.org/news/how-to-search-large-datasets-in-python/
# https://www.geeksforgeeks.org/sets-in-python/
# Tkinter tecla "Enter" - https://stackoverflow.com/questions/41960185/keysym-for-tkinter-not-working-enter-and-escape
# Crear borde para un label - https://stackoverflow.com/questions/39416021/border-for-tkinter-label
# Animacion de "shake" - https://stackoverflow.com/questions/36412636/text-animation-in-tkinter-python


