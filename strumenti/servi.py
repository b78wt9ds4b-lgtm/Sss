"""Il sito di docs/ sul computer, servito come lo servirà l'hosting.

    python3 strumenti/servi.py           # http://localhost:8000
    python3 strumenti/servi.py 8080      # su un'altra porta

Fa quello che fanno GitHub Pages e gli altri hosting statici, così quello che provi qui è
quello che vedranno i clienti:
- un indirizzo che non esiste riceve la pagina 404.html, con il codice 404;
- una cartella senza la barra finale (/negozio) viene reindirizzata a /negozio/;
- HTML, CSS, JavaScript, XML e SVG viaggiano compressi (gzip).
Risponde solo da questo computer (127.0.0.1). Serve solo la libreria standard di Python.
"""
import gzip
import http.server
import io
import os
import sys
from functools import partial
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
COMPRIMIBILI = {"text/html", "text/css", "text/javascript", "application/javascript", "application/xml",
                "text/xml", "image/svg+xml", "text/plain", "application/json"}


class Gestore(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # connessioni persistenti, come un hosting vero
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".webp": "image/webp", ".woff2": "font/woff2", ".xml": "application/xml",
                      ".js": "text/javascript"}

    def send_head(self):
        percorso = self.translate_path(self.path)
        if os.path.isdir(percorso) and not self.path.split("?", 1)[0].endswith("/"):
            return super().send_head()  # la classe di base risponde 301 verso la cartella con la barra
        if os.path.isdir(percorso):
            percorso = os.path.join(percorso, "index.html")
        if not os.path.isfile(percorso):
            return self.manda(DOCS / "404.html", 404)
        if self.guess_type(percorso) in COMPRIMIBILI:
            return self.manda(Path(percorso), 200)
        return super().send_head()

    def log_message(self, formato, *argomenti):
        # una riga per richiesta, sull'uscita normale: lo standard error resta per gli errori veri
        print(f"{self.address_string()} {formato % argomenti}", flush=True)

    def manda(self, file, codice):
        """Intestazioni e contenuto (compresso, se il browser lo accetta) di un file di testo."""
        dati = file.read_bytes()
        tipo = self.guess_type(str(file))
        self.send_response(codice)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        if "gzip" in self.headers.get("Accept-Encoding", ""):
            dati = gzip.compress(dati, 6)
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        return io.BytesIO(dati)


class Server(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # il browser ha chiuso la connessione a metà (una foto non più necessaria, una pagina
        # lasciata prima della fine): succede anche sull'hosting vero, non è un errore del sito
        if not isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            super().handle_error(request, client_address)


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = Server(("127.0.0.1", porta), partial(Gestore, directory=str(DOCS)))
    print(f"Il sito è su http://localhost:{porta}  (Ctrl+C per fermarlo)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
