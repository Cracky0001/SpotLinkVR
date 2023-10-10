import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pythonosc import udp_client
import configparser

print(f"Do not close this window! \nYou need it to run SpotLinkVR.exe")
# Lese Konfigurationswerte aus der INI-Datei
config = configparser.ConfigParser()
config.read('config.ini')

# Hole die Spotify-API-Konfigurationswerte aus der INI-Datei
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
        self.root.title("SpotLinkVR")
        self.root.geometry("600x400")
        self.root.configure(bg="#282c35")
        
        # Favicon als Symbol für Fenster und Taskleiste festlegen
        favicon_path = "./recs/favicon.ico"
        try:
            self.root.iconbitmap(favicon_path)
        except tk.TclError:
            print(f"Warning: The favicon '{favicon_path}' could not be loaded")
        
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
            # Hole den Spotify-Benutzernamen
            user_info = sp.me()
            if user_info:
                user_display_name = user_info.get('display_name', 'Unknown User')
                self.spotify_username = user_display_name
                user_id = user_info.get('id', 'Unknown User ID')
                self.user_label.config(text=f"Name: {self.spotify_username} | ID: {user_id}")

            if not self.logged_in:
                # Sende den Login 
                self.send_login_info()
                self.logged_in = True
                time.sleep(7)  

            while self.update_running:
                current_track_info, _ = self.get_current_track_info()
                self.track_label.config(text=current_track_info)

                # Konstruiere die OSC-Nachricht
                osc_message = [current_track_info, True, True]
                osc_address = "/chatbox/input"

                try:
                    osc_client.send_message(osc_address, osc_message)
                    self.debug_console.config(state=tk.NORMAL)  
                    self.debug_console.insert(tk.END, f"OSC message sent successfully: {current_track_info}\n")
                    self.debug_console.see(tk.END)  
                    self.debug_console.config(state=tk.DISABLED)  
                except Exception as e:
                    self.debug_console.config(state=tk.NORMAL)
                    self.debug_console.insert(tk.END, f"Error sending OSC message: {str(e)}\n")
                    self.debug_console.see(tk.END)  
                    self.debug_console.config(state=tk.DISABLED)  

                self.debug_console.update_idletasks()
                time.sleep(2)
        finally:
            self.update_running = False

    def send_login_info(self):
        # Sende den Login
        login_message = f"Logged in as: {self.spotify_username}"
        osc_message = [login_message, True, True]
        osc_address = "/chatbox/input"
        try:
            osc_client.send_message(osc_address, osc_message)
            self.debug_console.config(state=tk.NORMAL)  
            self.debug_console.insert(tk.END, f"Login info sent successfully: {login_message}\n")
            self.debug_console.see(tk.END) 
            self.debug_console.config(state=tk.DISABLED)
        except Exception as e:
            self.debug_console.config(state=tk.NORMAL) 
            self.debug_console.insert(tk.END, f"Error sending login info: {str(e)}\n")
            self.debug_console.see(tk.END) 
            self.debug_console.config(state=tk.DISABLED)  

    def get_current_track_info(self):
        try:
            current_track = sp.current_playback()
            if current_track is not None and 'item' in current_track:
                track_name = current_track['item']['name']
                artist_name = current_track['item']['artists'][0]['name']
                return f"Title: {track_name} | Artist: {artist_name}", None
        except Exception as e:
            self.debug_console.config(state=tk.NORMAL)  #
            self.debug_console.insert(tk.END, f"Error retrieving current track title and artist: {str(e)}\n")
            self.debug_console.see(tk.END) 
            self.debug_console.config(state=tk.DISABLED)  
        return None, None

    def start_drag(self, event):
        if not self.is_over_button(event) and not self.is_over_console(event):
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.is_dragging = True

if __name__ == "__main__":
    app = SpotifyInfoApp()
    app.root.mainloop()
