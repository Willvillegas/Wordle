import tkinter as tk
import config

class StatusPanel:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=config.BLACK_BG)
        self._create_panel()
    
    def _create_panel(self):
        # Header
        header_frame = tk.Frame(self.frame, bg=config.BLACK_BG)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = tk.Label(
            header_frame,
            text="WORDLE",
            font=("Helvetica", 18, "bold"),
            bg=config.BLACK_BG,
            fg=config.WHITE
        )
        title.pack()
        
        subtitle = tk.Label(
            header_frame,
            text="Dual Player",
            font=("Helvetica", 10),
            bg=config.BLACK_BG,
            fg=config.GREY
        )
        subtitle.pack()
        
        # Separador
        separator = tk.Frame(header_frame, height=2, bg=config.GREY_LINE)
        separator.pack(fill="x", pady=10)
        
        # Tu progreso
        self.your_progress_frame = tk.Frame(self.frame, bg=config.BLACK_BG)
        self.your_progress_frame.pack(fill="x", pady=(0, 15))
        
        your_label = tk.Label(
            self.your_progress_frame,
            text="Tu Progreso",
            font=("Helvetica", 12, "bold"),
            bg=config.BLACK_BG,
            fg=config.WHITE
        )
        your_label.pack()
        
        self.attempts_label = tk.Label(
            self.your_progress_frame,
            text="Intento: 1/6",
            font=("Helvetica", 10),
            bg=config.BLACK_BG,
            fg=config.GREY
        )
        self.attempts_label.pack(pady=(2, 0))
        
        # Progreso del oponente
        opponent_label = tk.Label(
            self.frame,
            text="Oponente",
            font=("Helvetica", 12, "bold"),
            bg=config.BLACK_BG,
            fg=config.WHITE
        )
        opponent_label.pack(pady=(0, 8))
        
        # Indicadores del oponente (manteniendo tu implementación)
        self.opponent_progress = []
        for i in range(6):
            indicator = tk.Label(
                self.frame,
                text="○",
                width=15,
                height=1,
                bg=config.BLACK_BG,
                fg=config.GREY_LINE,
                relief="flat",
                font=("Helvetica", 12)
            )
            indicator.pack(pady=2)
            self.opponent_progress.append(indicator)
        
        # Timer (opcional para futuro)
        self.timer_frame = tk.Frame(self.frame, bg=config.BLACK_BG)
        self.timer_frame.pack(fill="x", pady=(20, 0))
        
        timer_label = tk.Label(
            self.timer_frame,
            text="Tiempo",
            font=("Helvetica", 10, "bold"),
            bg=config.BLACK_BG,
            fg=config.WHITE
        )
        timer_label.pack()
        
        self.timer_display = tk.Label(
            self.timer_frame,
            text="--:--",
            font=("Helvetica", 14, "bold"),
            bg=config.BLACK_BG,
            fg=config.YELLOW
        )
        self.timer_display.pack(pady=(2, 0))
    
    def update_attempts(self, current, total):
        self.attempts_label.configure(text=f"Intento: {current}/{total}")
    
    def update_opponent_progress(self, row, status):
        # status: 'empty', 'trying', 'correct', 'incorrect'
        symbols = {
            'empty': '○',
            'trying': '◐',
            'correct': '●',
            'incorrect': '◯'
        }
        colors = {
            'empty': config.GREY_LINE,
            'trying': config.YELLOW,
            'correct': config.GREEN,
            'incorrect': config.GREY_USED
        }
        
        if row < len(self.opponent_progress):
            self.opponent_progress[row].configure(
                text=symbols.get(status, '○'),
                fg=colors.get(status, config.GREY_LINE)
            )
    
    def update_timer(self, time_str):
        self.timer_display.configure(text=time_str)
