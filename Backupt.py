import tkinter as tk
import time
import threading
import pygetwindow as gw
import json
import tkinter as tk
from pystray import MenuItem as item
from pystray import Icon
from PIL import Image
import threading
import time
import json
import pygetwindow as gw
from tkinter import ttk


from PIL import Image

def create_image():
    icon_path = 'icon.ico'
    image = Image.open(icon_path)
    return image


def show_window(icon, window):
    icon.stop()
    window.deiconify()


class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Time Tracker")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.window_width = 300
        self.window_height = 110
        x = screen_width - self.window_width - 20
        y = screen_height - self.window_height - 60

        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.overrideredirect(True)

        self.root.config(bg='#343a40')

        self.running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.active_windows = {}
        self.current_window_title = None

        self.top_frame = tk.Frame(self.root, bg='#343a40')
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.close_button = tk.Button(self.top_frame, text="❌", command=self.root.destroy,
                                    font=('Helvetica', 8), relief=tk.FLAT, padx=5, pady=4)
        self.close_button.pack(side=tk.RIGHT)
        self.close_button.config(bg='#343a40', activebackground='#343a40', fg='#ffffff', borderwidth=0)

        self.label = tk.Label(self.top_frame, text="00:00:00", font=("Helvetica", 24), fg='#f8f9fa', bg='#343a40')
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<ButtonRelease-1>", self.stop_move)
        self.label.bind("<B1-Motion>", self.do_move)

        self.start_pause_button = tk.Button(self.root, text="▶️ Start/Pause", command=self.toggle_timer,
                                            font=('Helvetica', 10), bg='#007bff', fg='#ffffff', relief=tk.FLAT, padx=10, pady=4)
        self.start_pause_button.pack(side=tk.TOP, fill=tk.X)

        self.stop_button = tk.Button(self.root, text="⏹ Stop", command=self.stop_timer,
                                     font=('Helvetica', 10), bg='#dc3545', fg='#ffffff', relief=tk.FLAT, padx=10, pady=4)
        self.stop_button.pack(side=tk.TOP, fill=tk.X)

        self.timer_thread = threading.Thread(target=self.update_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

        image = create_image()
        menu = (item('Abrir', lambda: show_window(icon, self.root)), item('Sair', lambda: self.exit_app(icon)))
        icon = Icon("Time Tracker", image, "Time Tracker", menu)
        icon.run()

    def exit_app(self, icon):
        icon.stop()
        self.root.destroy()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
            
    def toggle_timer(self):
        if self.running:
            self.running = False
            self.elapsed_time = time.time() - self.start_time
            self.start_pause_button.config(text="▶️ Start/Pause")
            
            if self.current_window_title and self.active_windows[self.current_window_title]['periods'][-1]['end'] is None:
                last_period = self.active_windows[self.current_window_title]['periods'][-1]
                last_period['end'] = time.time()
                period_duration = last_period['end'] - last_period['start']
                self.active_windows[self.current_window_title]['amount'] += period_duration
        else:
            self.running = True
            self.start_time = time.time() - self.elapsed_time
            self.start_pause_button.config(text="⏸️ Start/Pause")
            self.monitor_active_windows()

    def monitor_active_windows(self):
        if self.running:
            current_window = gw.getActiveWindow()
            if current_window:
                title = current_window.title
                if title:
                    if title not in self.active_windows:
                        self.active_windows[title] = {
                            'amount': 0,
                            'periods': [{'start': time.time(), 'end': None}]
                        }
                    else:
                        last_period = self.active_windows[title]['periods'][-1]
                        if last_period['end'] is not None:
                            self.active_windows[title]['periods'].append({'start': time.time(), 'end': None})
                if self.current_window_title != title:
                    if self.current_window_title and self.active_windows[self.current_window_title]['periods'][-1]['end'] is None:
                        last_period = self.active_windows[self.current_window_title]['periods'][-1]
                        last_period['end'] = time.time()
                        period_duration = last_period['end'] - last_period['start']
                        self.active_windows[self.current_window_title]['amount'] += period_duration
                    self.current_window_title = title
            self.root.after(500, self.monitor_active_windows)

    def stop_timer(self):
        self.running = False
        self.elapsed_time = time.time() - self.start_time
        self.label.config(text=time.strftime("%H:%M:%S", time.gmtime(self.elapsed_time)))
        self.start_pause_button.config(text="▶️ Start/Pause")
        
        if self.current_window_title and self.active_windows[self.current_window_title]['periods'][-1]['end'] is None:
            last_period = self.active_windows[self.current_window_title]['periods'][-1]
            last_period['end'] = time.time()
            period_duration = last_period['end'] - last_period['start']
            self.active_windows[self.current_window_title]['amount'] += period_duration
        self.show_summary_popup()

    def show_summary_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Activity Summary")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * 0.5)
        height = int(screen_height * 0.8)
        popup_x = (screen_width // 2) - (width // 2)
        popup_y = (screen_height // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{popup_x}+{popup_y}")
        popup.config(bg="#343a40")

        description_frame = tk.Frame(popup, bg="#343a40")
        description_frame.pack(fill=tk.X, padx=10, pady=10)

        description_label = tk.Label(description_frame, text="Activity Descrption:", bg="#343a40", fg="#ffffff", anchor='w')
        description_label.pack(side=tk.LEFT)

        description_entry = tk.Entry(description_frame, font=('Helvetica', 10), bd=2, relief=tk.FLAT, highlightthickness=1, width=60)
        description_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        description_entry.config(highlightbackground="#007bff", highlightcolor="#007bff")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#343a40",
                        foreground="#f8f9fa",
                        fieldbackground="#343a40",
                        rowheight=25,
                        borderwidth=0,
                        relief="flat")
        style.map("Treeview",
                background=[("selected", "#007bff")],
                foreground=[("selected", "#ffffff")])

        tree = ttk.Treeview(popup, columns=("Window Title", "Duration"), show="headings", style="Treeview")
        tree.column("Window Title", width=int(width * 0.7), anchor='w')
        tree.column("Duration", width=int(width * 0.3), anchor='center')
        tree.heading("Window Title", text="Window Title")
        tree.heading("Duration", text="Duration")

        for title, details in self.active_windows.items():
            duration_sec = int(details['amount'])
            hours, remainder = divmod(duration_sec, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            tree.insert("", tk.END, values=(title, duration_str))
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        button_frame = tk.Frame(popup, bg="#343a40")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        save_button = tk.Button(button_frame, text="Save", command=lambda: self.save_data(popup, description_entry.get()),
                                bg="#007bff", fg="#ffffff", relief=tk.FLAT, padx=10, pady=4, width=10)
        save_button.pack(side=tk.RIGHT, padx=10)

        discard_button = tk.Button(button_frame, text="Discard", command=popup.destroy,
                                bg="#dc3545", fg="#ffffff", relief=tk.FLAT, padx=10, pady=4, width=10)
        discard_button.pack(side=tk.RIGHT)
        

    def save_data(self, popup, description):
        total_duration = sum(details['amount'] for details in self.active_windows.values())
        data = {
            "description": description,
            "total_duration": total_duration,
            "windows": [
            {
                "title": title,
                "total_duration": int(details['amount']),
                "periods": [
                {"start": period['start'], "end": period['end']} for period in details['periods'] if period['end'] is not None
                ]
            }
            for title, details in self.active_windows.items()
            ]
        }
        try:
            with open("activity_data.json", "r") as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []
        
        existing_data.append(data)

        
        with open("activity_data.json", "w") as file:
            json.dump(existing_data, file, indent=4)

        popup.destroy()  

    def update_timer(self):
        while True:
            if self.running:
                elapsed = time.time() - self.start_time
                minutes, seconds = divmod(int(elapsed), 60)
                hours, minutes = divmod(minutes, 60)
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                self.label.config(text=time_str)
            time.sleep(0.1)
    

if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()
