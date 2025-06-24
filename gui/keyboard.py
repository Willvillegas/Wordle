import tkinter as tk
import config

class VirtualKeyboard:
    def __init__(self, parent, callback):
        self.frame = tk.Frame(parent, bg=config.BLACK_BG)
        self.callback = callback
        self.key_buttons = {}
        self._create_keyboard()
    
    def _create_keyboard(self):
        keyboard_layout = [
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['ENTER','Z','X','C','V','B','N','M','⌫']
        ]
        
        for row_idx, row in enumerate(keyboard_layout):
            row_frame = tk.Frame(self.frame, bg=config.BLACK_BG)
            row_frame.pack(pady=3)
            
            for key in row:
                width = 8 if key in ['ENTER', '⌫'] else 4
                font_size = 9 if key == 'ENTER' else 11
                
                btn = tk.Button(
                    row_frame,
                    text=key,
                    width=width,
                    height=2,
                    font=("Helvetica", font_size, "bold"),
                    bg=config.GREY_USED,
                    fg=config.WHITE,
                    relief="raised",
                    bd=1,
                    activebackground=config.GREY,
                    activeforeground=config.WHITE,
                    command=lambda k=key: self._handle_click(k)
                )
                btn.pack(side="left", padx=2)
                
                if key not in ['ENTER', '⌫']:
                    self.key_buttons[key] = btn
    
    def _handle_click(self, key):
        if key == 'ENTER':
            self.callback('Return')
        elif key == '⌫':
            self.callback('BackSpace')
        else:
            self.callback(key)
    
    def update_key_color(self, key, color):
        if key in self.key_buttons:
            current_bg = self.key_buttons[key].cget('bg')
            # Solo actualizar si no es verde (para mantener las letras correctas)
            if current_bg != config.GREEN or color == config.GREEN:
                self.key_buttons[key].configure(bg=color)