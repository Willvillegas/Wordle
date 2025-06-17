import tkinter as tk
import config

class Matrix:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=config.BLACK_BG)
        self.root = parent
        self.frame.pack(pady=20)
        self.labels = []
        for r in range(6):
            row_labels = []
            for c in range(5):
                lbl = tk.Label(
                    self.frame,
                    text="",
                    width=2,
                    height=1,
                    font=("Helvetica", 20, "bold"),
                    bg=config.BLACK_BG,
                    fg=config.WHITE,
                    relief="solid",
                    bd=2,
                    highlightbackground=config.GREY_USED,
                    highlightthickness=1,
                )
                lbl.grid(row=r, column=c, padx=2, pady=2)
                row_labels.append(lbl)
            self.labels.append(row_labels)

    def update_square(self, row, column, char):
        self.labels[row][column].configure(text=char)

    def clear_square(self, row, column):
        self.labels[row][column].configure(text="")

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
