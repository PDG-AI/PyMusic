"""
Servidor HTTP para la integración de Streamlabs
Sirve el HTML del overlay y proporciona un endpoint JSON con la información de la canción actual
"""
import http.server
import socketserver
import json
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STREAMLABS_DIR = os.path.dirname(os.path.abspath(__file__))

class StreamlabsHandler(http.server.SimpleHTTPRequestHandler):
    """Manejador HTTP personalizado para servir el overlay de Streamlabs"""
    
    def __init__(self, *args, music_player=None, **kwargs):
        self.music_player = music_player
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Maneja las peticiones GET"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Endpoint para obtener información de la canción actual
        if path == '/api/current-song':
            self.send_song_info()
        # Servir el HTML del overlay
        elif path == '/' or path == '/index.html':
            self.serve_overlay()
        # Servir archivos estáticos (CSS, JS, imágenes)
        elif path.startswith('/assets/'):
            self.serve_static_file(path)
        else:
            self.send_error(404, "File not found")
    
    def send_song_info(self):
        """Envía la información de la canción actual en formato JSON"""
        try:
            if self.music_player:
                song_info = {
                    "song_name": self.music_player.current_song_title or "No hay canción reproduciéndose",
                    "duration": self.music_player.current_song_duration,
                    "playlist_name": self.music_player.current_playlist_name or "Reproducción individual",
                    "is_playing": self.music_player.is_playing and not self.music_player.is_paused
                }
            else:
                song_info = {
                    "song_name": "No hay información disponible",
                    "duration": 0,
                    "playlist_name": "N/A",
                    "is_playing": False
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(song_info, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
    
    def serve_overlay(self):
        """Sirve el archivo HTML del overlay"""
        overlay_path = os.path.join(STREAMLABS_DIR, 'overlay.html')
        try:
            with open(overlay_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "Overlay file not found")
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
    
    def serve_static_file(self, path):
        """Sirve archivos estáticos desde la carpeta assets"""
        # Remover el /assets/ del path
        filename = path.replace('/assets/', '')
        file_path = os.path.join(STREAMLABS_DIR, 'assets', filename)
        
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # Determinar el tipo de contenido
                content_type = 'application/octet-stream'
                if filename.endswith('.png'):
                    content_type = 'image/png'
                elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif filename.endswith('.css'):
                    content_type = 'text/css'
                elif filename.endswith('.js'):
                    content_type = 'application/javascript'
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
    
    def log_message(self, format, *args):
        """Suprime los mensajes de log del servidor"""
        pass


def create_handler_class(music_player):
    """Crea una clase de manejador con el music_player inyectado"""
    class Handler(StreamlabsHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, music_player=music_player, **kwargs)
    return Handler


def start_server(music_player, port=8765):
    """Inicia el servidor HTTP para Streamlabs"""
    handler_class = create_handler_class(music_player)
    
    try:
        with socketserver.TCPServer(("", port), handler_class) as httpd:
            print(f"Servidor Streamlabs iniciado en http://localhost:{port}")
            print(f"Accede al overlay en: http://localhost:{port}/")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: El puerto {port} ya está en uso. Intenta con otro puerto.")
        else:
            print(f"Error al iniciar el servidor: {e}")
    except KeyboardInterrupt:
        print("\nServidor detenido")

