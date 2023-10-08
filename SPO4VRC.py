import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pythonosc import udp_client
import configparser

# Lese die Konfigurationswerte aus der INI-Datei
config = configparser.ConfigParser()
config.read('config.ini')

# Holen Sie die Spotify-API-Konfigurationswerte aus der INI-Datei
spotify_client_id = config['Spotify']['client_id']
spotify_client_secret = config['Spotify']['client_secret']
spotify_redirect_uri = config['Spotify']['redirect_uri']
spotify_scope = config['Spotify']['scope']

# Spotify API Configuration
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    redirect_uri=spotify_redirect_uri,
    scope=spotify_scope
))

# OSC Configuration
vrchat_ip = "127.0.0.1"  # Beispiel-IP-Adresse
vrchat_port = 9000  # Beispiel-Port
osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)

class SpotifyInfoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Spotify Info App")
        self.root.geometry("600x400")
        self.root.configure(bg="#282c35")
        self.root.overrideredirect(True)  # Entfernen Sie die Taskleiste oben

        self.close_button = tk.Button(self.root, text="X", command=self.quit_app, bg="red", fg="white", font=("Helvetica", 12))
        self.close_button.place(x=570, y=10)  # Positionieren Sie die Schaltfläche zum Schließen oben rechts

        self.user_label = tk.Label(self.root, text="", fg="white", bg="#282c35", font=("Helvetica", 12))
        self.user_label.pack(pady=(20, 0))

        self.track_label = tk.Label(self.root, text="", fg="white", bg="#282c35", font=("Helvetica", 14))
        self.track_label.pack(pady=(20, 0))

        self.start_button = tk.Button(self.root, text="Start", command=self.toggle_update, fg="white", bg="#485063", font=("Helvetica", 12))
        self.start_button.pack(pady=(20, 0))

        self.debug_console = scrolledtext.ScrolledText(self.root, width=50, height=10, wrap=tk.WORD, fg="white", bg="#1e1e1e", font=("Helvetica", 10))
        self.debug_console.pack(padx=20, pady=20)
        self.debug_console.configure(state=tk.DISABLED)  # Deaktivieren Sie die Bearbeitung der Konsole

        self.update_running = False
        self.logged_in = False
        self.spotify_username = ""

        # Event-Handler für das Verschieben des Fensters per Drag & Drop
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False  # Verfolgen Sie, ob das Verschieben aktiv ist
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag_window)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)

        # Event-Handler für den Mauszeiger über dem Button
        self.start_button.bind("<Enter>", self.mouse_over_button)
        self.start_button.bind("<Leave>", self.mouse_leave_button)

        # Event-Handler für den Mauszeiger über der Konsole
        self.debug_console.bind("<Enter>", self.mouse_over_console)
        self.debug_console.bind("<Leave>", self.mouse_leave_console)

    def toggle_update(self):
        if not self.update_running:
            self.start_button.config(text="Stop")
            self.update_running = True
            self.debug_console.config(state=tk.NORMAL)  # Aktivieren Sie die Bearbeitung der Konsole
            self.debug_console.insert(tk.END, "Updating...\n")
            self.debug_console.update_idletasks()
            self.update_thread = threading.Thread(target=self.update_info_thread)
            self.update_thread.start()
        else:
            self.start_button.config(text="Start")
            self.update_running = False
            self.debug_console.insert(tk.END, "Update stopped\n")
            self.debug_console.config(state=tk.DISABLED)  # Deaktivieren Sie die Bearbeitung der Konsole

    def quit_app(self):
        self.root.quit()

    def update_info_thread(self):
        try:
            # Holen Sie zuerst den Spotify-Benutzernamen
            user_info = sp.me()
            if user_info:
                user_display_name = user_info.get('display_name', 'Unknown User')
                self.spotify_username = user_display_name
                user_id = user_info.get('id', 'Unknown User ID')
                self.user_label.config(text=f"Name: {self.spotify_username} | ID: {user_id}")

            if not self.logged_in:
                # Sende den Login einmalig, falls noch nicht geschehen
                self.send_login_info()
                self.logged_in = True
                time.sleep(7)  # Verzögerung von 7 Sekunden nach der Login-Nachricht

            while self.update_running:
                current_track_info, _ = self.get_current_track_info()
                self.track_label.config(text=current_track_info)

                # Konstruieren Sie die OSC-Nachricht
                osc_message = [current_track_info, True, True]
                osc_address = "/chatbox/input"

                try:
                    osc_client.send_message(osc_address, osc_message)
                    self.debug_console.config(state=tk.NORMAL)  # Aktivieren Sie die Bearbeitung der Konsole
                    self.debug_console.insert(tk.END, f"OSC message sent successfully: {current_track_info}\n")
                    self.debug_console.config(state=tk.DISABLED)  # Deaktivieren Sie die Bearbeitung der Konsole
                except Exception as e:
                    self.debug_console.config(state=tk.NORMAL)  # Aktivieren Sie die Bearbeitung der Konsole
                    self.debug_console.insert(tk.END, f"Error sending OSC message: {str(e)}\n")
                    self.debug_console.config(state=tk.DISABLED)  # Deaktivieren Sie die Bearbeitung der Konsole

                self.debug_console.update_idletasks()
                time.sleep(2)
        finally:
            self.update_running = False

    def send_login_info(self):
        # Sende den Login einmalig
        login_message = f"Logged in as: {self.spotify_username}"
        osc_message = [login_message, True, True]
        osc_address = "/chatbox/input"
        try:
            osc_client.send_message(osc_address, osc_message)
            self.debug_console.config(state=tk.NORMAL)  # Aktivieren Sie die Bearbeitung der Konsole
            self.debug_console.insert(tk.END, f"Login info sent successfully: {login_message}\n")
            self.debug_console.config(state=tk.DISABLED)  # Deaktivieren Sie die Bearbeitung der Konsole
        except Exception as e:
            self.debug_console.config(state=tk.NORMAL)  # Aktivieren Sie die Bearbeitung der Konsole
            self.debug_console.insert(tk.END, f"Error sending login info: {str(e)}\n")
            self.debug_console.config(state=tk.DISABLED)  # Deaktivieren Sie die Bearbeitung der Konsole

    def get_current_track_info(self):
        try:
            current_track = sp.current_playback()
            if current_track is not None and 'item' in current_track:
                track_name = current_track['item']['name']
                artist_name = current_track['item']['artists'][0]['name']
                return f"Title: {track_name} | Artist: {artist_name}", None
        except Exception as e:
            self.debug_console.config(state=tk.NORMAL)  # Aktivieren Sie die Bearbeitung der Konsole
            self.debug_console.insert(tk.END, f"Error retrieving current track title and artist: {str(e)}\n")
            self.debug_console.config(state=tk.DISABLED)  # Deaktivieren Sie die Bearbeitung der Konsole
        return None, None

    def start_drag(self, event):
        if not self.is_over_button(event) and not self.is_over_console(event):
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.is_dragging = True

    def drag_window(self, event):
        if self.is_dragging:
            x = self.root.winfo_x() + (event.x - self.drag_start_x)
            y = self.root.winfo_y() + (event.y - self.drag_start_y)
            self.root.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        self.is_dragging = False

    def is_over_button(self, event):
        x, y = event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y()
        return (
            self.start_button.winfo_rootx() <= x <= self.start_button.winfo_rootx() + self.start_button.winfo_width() and
            self.start_button.winfo_rooty() <= y <= self.start_button.winfo_rooty() + self.start_button.winfo_height()
        )

    def is_over_console(self, event):
        x, y = event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y()
        return (
            self.debug_console.winfo_rootx() <= x <= self.debug_console.winfo_rootx() + self.debug_console.winfo_width() and
            self.debug_console.winfo_rooty() <= y <= self.debug_console.winfo_rooty() + self.debug_console.winfo_height()
        )

    def mouse_over_button(self, event):
        if self.is_dragging:
            return
        self.start_button.config(bg="#607080")

    def mouse_leave_button(self, event):
        self.start_button.config(bg="#485063")

    def mouse_over_console(self, event):
        self.debug_console.bind("<MouseWheel>", self.scroll_console)

    def mouse_leave_console(self, event):
        self.debug_console.unbind("<MouseWheel>")

    def scroll_console(self, event):
        self.debug_console.yview_scroll(int(-1 * (event.delta / 120)), "units")

if __name__ == "__main__":
    app = SpotifyInfoApp()
    app.root.mainloop()
