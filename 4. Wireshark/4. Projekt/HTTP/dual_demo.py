#!/usr/bin/env python3
"""
DUAL HTTP/HTTPS DEMO - Visa både krypterad och okrypterad trafik
Skapa två servrar: HTTP (8080) och HTTPS (8443) från samma kod
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import ssl
import subprocess
import os
import sys
import threading
import time
import shutil
import tempfile

# Port definitions
HTTP_PORT = 8080
HTTPS_PORT = 8443

class DualHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Visa samma sida för både HTTP och HTTPS"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Check if this is HTTPS or HTTP
        is_https = hasattr(self, 'is_https') and self.is_https
        
        if is_https:
            protocol = "https"
            port = HTTPS_PORT
            title = "🔒 SÄKER HTTPS DEMO"
            color = "green"
            bg_color = "#d4edda"
            button_color = "#28a745"
            status = "✅ KRYPTERAD"
        else:
            protocol = "http"
            port = HTTP_PORT
            title = "⚠️ OSÄKER HTTP DEMO"
            color = "red"
            bg_color = "#f8d7da"
            button_color = "#dc3545"
            status = "❌ OKRYPTERAD"
        
        tls_view = """Frame X: TLSv1.2 Record Layer: Application Data
    Content Type: Application Data (23)
    Version: TLS 1.2
    Length: 342 bytes
    Encrypted Application Data: 8a3f5c... [KRYPTERAT!]
"""
        http_view = """Frame X: HTTP
    POST / HTTP/1.1
    Content-Type: application/x-www-form-urlencoded
    Content-Length: 189

    username=anna.andersson&
    password=mittHemligaLösen123&
    email=anna.andersson@example.com&
    creditcard=4111111111111111&
    personnummer=850101-1234&
    message=Min+bankkod+är+9876...
"""
        username = "anna.andersson"   # exempelvärde i GET-vyn (POST fyller i riktiga värden)
        seen_block = tls_view if is_https else http_view
        preview_user = "" if is_https else "    " + chr(10) + "    username=" + str(username) + "&"
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; }}
        .protocol-box {{ 
            background: {bg_color}; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 5px solid {color};
        }}
        .comparison {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 5px; 
            margin: 20px 0;
            border: 2px solid #dee2e6;
        }}
        form {{ background: #e9ecef; padding: 25px; border-radius: 5px; }}
        input, textarea {{ 
            width: 100%; 
            padding: 12px; 
            margin: 8px 0 20px 0; 
            border: 2px solid #ced4da;
            border-radius: 4px;
            font-size: 16px;
        }}
        button {{ 
            background: {button_color}; 
            color: white; 
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            width: 100%;
        }}
        button:hover {{ opacity: 0.9; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
            background: white;
        }}
        th, td {{ 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #dee2e6;
        }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .demo-info {{ 
            background: #fff3cd; 
            padding: 15px; 
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #ffc107;
        }}
        .wireshark-instructions {{ 
            background: #d1ecf1; 
            padding: 15px; 
            border-radius: 5px;
            font-family: monospace;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="protocol-box">
        <h2>Status: {status}</h2>
        <p><strong>Protokoll:</strong> <code>{protocol.upper()}</code></p>
        <p><strong>URL:</strong> <code>{protocol}://localhost:{port}</code></p>
        <p><strong>Wireshark filter:</strong> <code>{"tcp.port == " + str(port) if is_https else "http"}</code></p>
    </div>
    
    <div class="comparison">
        <h3>📊 Vad du kommer se i Wireshark:</h3>
        <table>
            <tr>
                <th>Data</th>
                <th style="color: red;">HTTP (Osäkert)</th>
                <th style="color: green;">HTTPS (Säkert)</th>
            </tr>
            <tr>
                <td><strong>Lösenord</strong></td>
                <td style="color: red;">✅ SYNES i klartext</td>
                <td style="color: green;">❌ Bara krypterat</td>
            </tr>
            <tr>
                <td><strong>Kreditkort</strong></td>
                <td style="color: red;">✅ SYNES i klartext</td>
                <td style="color: green;">❌ Bara krypterat</td>
            </tr>
            <tr>
                <td><strong>All annan data</strong></td>
                <td style="color: red;">✅ SYNES i klartext</td>
                <td style="color: green;">❌ Bara krypterat</td>
            </tr>
            <tr>
                <td><strong>Vad Wireshark visar</strong></td>
                <td style="color: red;"><code>pass=secret123</code></td>
                <td style="color: green;"><code>Application Data</code></td>
            </tr>
        </table>
    </div>
    
    <h2>Testa {protocol.upper()} inloggning:</h2>
    <form method="POST">
        <label><strong>👤 Användarnamn:</strong></label>
        <input type="text" name="username" value="anna.andersson" required>
        
        <label><strong>🔑 Lösenord:</strong></label>
        <input type="password" name="password" value="mittHemligaLösen123" required>
        
        <label><strong>📧 E-postadress:</strong></label>
        <input type="email" name="email" value="anna.andersson@example.com">
        
        <label><strong>💳 Kreditkortsnummer:</strong></label>
        <input type="text" name="creditcard" value="4111 1111 1111 1111">
        
        <label><strong>🔢 Personnummer:</strong></label>
        <input type="text" name="personnummer" value="850101-1234">
        
        <label><strong>💬 Känsligt meddelande:</strong></label>
        <textarea name="message" rows="3">Min bankkod är 9876 och mitt födelsedatum är 1985-01-01</textarea>
        
        <br><br>
        <button type="submit">
            {'🔒 SKICKA KRYPTERAT' if is_https else '⚠️ SKICKA OKRYPTERAT'}
        </button>
    </form>
    
    <div class="demo-info">
        <h3>🔍 Så här testar du:</h3>
        <ol>
            <li><strong>Starta Wireshark</strong> och fånga på <code>enp0s3</code></li>
            <li><strong>Använd filter:</strong> <code>{"tcp.port == " + str(port) if is_https else "http"}</code></li>
            <li><strong>Skicka formuläret</strong> här ovan</li>
            <li><strong>Letar i Wireshark</strong> efter dina data</li>
        </ol>
    </div>
    
    <div class="wireshark-instructions">
        <h3>🎯 Exakt vad du ska se i Wireshark:</h3>
        <p><strong>{'HTTPS (Krypterat):' if is_https else 'HTTP (Okrypterat):'}</strong></p>
        <pre>
{seen_block}
        </pre>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding: 15px; background: #e9ecef; border-radius: 5px;">
        <h3>🔄 Jämför båda versionerna:</h3>
        <p>
            <a href="http://localhost:{HTTP_PORT}" style="color: #dc3545; font-weight: bold; margin-right: 20px;">
                ← Testa OSÄKER HTTP
            </a>
            <a href="https://localhost:{HTTPS_PORT}" style="color: #28a745; font-weight: bold;">
                Testa SÄKER HTTPS →
            </a>
        </p>
        <p><em>Skicka samma data på båda och jämför i Wireshark!</em></p>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        """Hantera POST för både HTTP och HTTPS"""
        is_https = hasattr(self, 'is_https') and self.is_https
        
        # Läs datan
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        # Extrahera värden
        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        email = params.get('email', [''])[0]
        creditcard = params.get('creditcard', [''])[0]
        personnummer = params.get('personnummer', [''])[0]
        message = params.get('message', [''])[0]
        
        # Skicka respons
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        if is_https:
            color = "#28a745"
            title = "✅ DATA KRYPTERAD OCH SKICKAD!"
            security_status = "KRYPTERAD"
            wireshark_view = "Application Data (krypterat)"
        else:
            color = "#dc3545"
            title = "⚠️ DATA SKICKAD OKRYPTERAD!"
            security_status = "OKRYPTERAD"
            wireshark_view = "Klartext data"
        
        html = f"""<!DOCTYPE html>
<html>
<head><title>{title}</title>
<style>
body {{ font-family: Arial; max-width: 700px; margin: 40px auto; padding: 20px; }}
.result-box {{ 
    background: {color}; 
    color: white;
    padding: 25px;
    border-radius: 8px;
    margin: 25px 0;
}}
.data-item {{ 
    background: rgba(255,255,255,0.15);
    padding: 12px;
    margin: 10px 0;
    border-radius: 4px;
    border-left: 4px solid rgba(255,255,255,0.3);
}}
.wireshark-preview {{ 
    background: #212529; 
    color: #20c997; 
    padding: 20px;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
    margin: 20px 0;
    overflow-x: auto;
}}
.protocol-info {{ 
    background: #6c757d; 
    color: white;
    padding: 15px;
    border-radius: 5px;
    margin: 15px 0;
}}
</style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="protocol-info">
        <h3>Protokoll: <code>{'HTTPS' if is_https else 'HTTP'}</code></h3>
        <p>Status: <strong>{security_status}</strong></p>
        <p>I Wireshark ser du: <strong>{wireshark_view}</strong></p>
    </div>
    
    <div class="result-box">
        <h2>📋 Data som skickades:</h2>
        
        <div class="data-item">
            <strong>👤 Användarnamn:</strong><br>
            <code>{username}</code>
        </div>
        
        <div class="data-item">
            <strong>🔑 Lösenord:</strong><br>
            <code>{'[KRYPTERAT - syns inte i Wireshark]' if is_https else password}</code>
        </div>
        
        <div class="data-item">
            <strong>📧 E-post:</strong><br>
            <code>{email}</code>
        </div>
        
        <div class="data-item">
            <strong>💳 Kreditkort:</strong><br>
            <code>{creditcard}</code>
        </div>
        
        <div class="data-item">
            <strong>🔢 Personnummer:</strong><br>
            <code>{personnummer}</code>
        </div>
        
        <div class="data-item">
            <strong>💬 Meddelande:</strong><br>
            <code>{message}</code>
        </div>
    </div>
    
    <div class="wireshark-preview">
        <h3>🔍 Så här ser det ut i Wireshark:</h3>
        <pre>
{'TLSv1.2 Record Layer: Application Data' if is_https else 'HTTP/1.1 200 OK'}
{'    Content Type: Application Data (23)' if is_https else '    Content-Type: application/x-www-form-urlencoded'}
{'    Version: TLS 1.2 (0x0303)' if is_https else '    Content-Length: ' + str(len(post_data))}
{'    Length: 256' if is_https else ''}
{'    Encrypted Application Data: 3a5f8c9b...' if is_https else ''}
 {preview_user}
{'' if is_https else f'    password={password}&'}
{'' if is_https else f'    email={email}&'}
{'' if is_https else f'    creditcard={creditcard}&'}
{'' if is_https else '    ... [ALL DATA IN CLEAR TEXT]'}
        </pre>
    </div>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <h3>💡 Säkerhetslärdom:</h3>
        <p><strong>{'✅ BRA:' if is_https else '❌ DÅLIGT:'}</strong> 
        {'All data är krypterad. Ingen kan läsa ditt lösenord eller kreditkortsinformation.' 
         if is_https else 
         'All data skickas i klartext. Vem som helst på samma nätverk kan stjäla dina uppgifter.'}</p>
        
        <p><strong>Verkliga konsekvenser:</strong></p>
        <ul>
            <li>{'På ett café-WiFi: Dina uppgifter är säkra' if is_https else 'På ett café-WiFi: Andra gäster kan stjäla dina uppgifter'}</li>
            <li>{'I ett företagsnätverk: Administratören kan inte läsa din data' if is_https else 'I ett företagsnätverk: IT-avdelningen kan se all din data'}</li>
            <li>{'Med en Man-in-the-Middle attack: Mycket svårt att avlyssna' if is_https else 'Med en Man-in-the-Middle attack: Lätt att avlyssna'}</li>
        </ul>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="/" style="background: {color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
            ← Testa igen
        </a>
        <a href="{'http://localhost:' + str(HTTP_PORT) if is_https else 'https://localhost:' + str(HTTPS_PORT)}" 
           style="background: #6c757d; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
            {'← Jämför med HTTP' if is_https else 'Jämför med HTTPS →'}
        </a>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
        
        # Skriv till terminalen
        protocol = "HTTPS" if is_https else "HTTP"
        print(f"\n{'='*70}")
        print(f"{'🔒' if is_https else '🔓'} {protocol} - DATA {'KRYPTERAD' if is_https else 'OKRYPTERAD'}")
        print("="*70)
        print(f"👤 Användarnamn: {username}")
        print(f"🔑 Lösenord:     {'[KRYPTERAT]' if is_https else password}")
        print(f"📧 E-post:       {email}")
        print(f"💳 Kreditkort:   {creditcard}")
        print(f"🔢 Personnummer: {personnummer}")
        print("="*70)
        print(f"🎯 Wireshark filter: {'tcp.port == ' + str(HTTPS_PORT) if is_https else 'http'}")
        print(f"   Ser: {'Application Data (krypterat)' if is_https else 'Klartext data'}\n")

def create_certificate():
    """Skapa självsignerat certifikat för HTTPS"""
    key_file = os.path.join(tempfile.gettempdir(), "demo_https.key")
    cert_file = os.path.join(tempfile.gettempdir(), "demo_https.crt")
    
    # Ta bort gamla filer
    for f in [key_file, cert_file]:
        if os.path.exists(f):
            os.remove(f)
    
    # Skapa certifikat med openssl
    print("📝 Genererar självsignerat certifikat för HTTPS...")
    result = subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", key_file, "-out", cert_file,
        "-days", "365", "-nodes",
        "-subj", "/C=SE/CN=localhost"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Certifikat skapat!")
        return key_file, cert_file
    else:
        print(f"❌ Certifikatfel: {result.stderr}")
        return None, None

def start_http_server():
    """Starta HTTP-servern (okrypterad)"""
    print(f"\n🚀 Startar OSÄKER HTTP-server på port {HTTP_PORT}...")
    
    # Skapa custom handler för HTTP
    class HTTPHandler(DualHandler):
        is_https = False
    
    httpd = HTTPServer(('0.0.0.0', HTTP_PORT), HTTPHandler)
    
    print(f"✅ HTTP-server startad!")
    print(f"🌐 Öppna: http://localhost:{HTTP_PORT}")
    print(f"🎯 Wireshark filter: http eller tcp.port == {HTTP_PORT}")
    print("   Kommer visa: LÖSENORD I KLARTEXT\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 HTTP-server stoppad.")

def start_https_server():
    """Starta HTTPS-servern (krypterad)"""
    print(f"\n🚀 Startar SÄKER HTTPS-server på port {HTTPS_PORT}...")
    
    # Skapa certifikat först
    key_file, cert_file = create_certificate()
    if not key_file:
        print("❌ Kan inte starta HTTPS utan certifikat")
        return
    
    # Skapa custom handler för HTTPS
    class HTTPSHandler(DualHandler):
        is_https = True
    
    # Skapa och konfigurera HTTPS-server
    httpsd = HTTPServer(('0.0.0.0', HTTPS_PORT), HTTPSHandler)
    
    # Lägg till SSL/TLS
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    httpsd.socket = context.wrap_socket(httpsd.socket, server_side=True)
    
    print(f"✅ HTTPS-server startad!")
    print(f"🌐 Öppna: https://localhost:{HTTPS_PORT}")
    print("⚠️  Webbläsaren kommer varna om certifikat")
    print("   Klicka: 'Advanced' → 'Proceed to localhost (unsafe)'")
    print(f"🎯 Wireshark filter: tcp.port == {HTTPS_PORT}")
    print("   Kommer visa: APPLICATION DATA (krypterat)\n")
    
    try:
        httpsd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 HTTPS-server stoppad.")

def start_dual_servers():
    """Starta båda servrarna i separata trådar"""
    print("\n" + "="*70)
    print("🔓🔒 DUAL HTTP/HTTPS DEMO - Startar båda servrarna")
    print("="*70)
    
    # Starta HTTP-server i separat tråd
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Vänta lite
    time.sleep(2)
    
    # Starta HTTPS-server i separat tråd
    https_thread = threading.Thread(target=start_https_server, daemon=True)
    https_thread.start()
    
    print("\n📊 DEMONSTRATIONSINSTRUKTIONER:")
    print("-"*40)
    print("1. Öppna två webbläsarflikar/fönster")
    print(f"   → Flik 1: http://localhost:{HTTP_PORT}  (OSÄKER)")
    print(f"   → Flik 2: https://localhost:{HTTPS_PORT} (SÄKER)")
    print("")
    print("2. Starta Wireshark:")
    print("   → sudo wireshark")
    print("   → Välj 'enp0s3'")
    print("   → Starta capture (blå hajfena)")
    print("")
    print("3. Jämförelsetest:")
    print("   a) Skicka formuläret på HTTP-sidan")
    print("   b) Filter: http")
    print("   c) Se: Lösenord i klartext")
    print("")
    print("   d) Skicka SAMMA formulär på HTTPS-sidan")
    print("   e) Filter: tcp.port == 8443")
    print("   f) Se: 'Application Data' (krypterat)")
    print("")
    print("="*70)
    print("Tryck Ctrl+C för att stoppa båda servrarna")
    print("="*70)
    
    try:
        # Håll programmet körande
        http_thread.join()
        https_thread.join()
    except KeyboardInterrupt:
        print("\n\n👋 Båda servrarna stoppas...")
        print("✅ Demo klar! Förhoppningsvis såg du skillnaden mellan HTTP och HTTPS!")
        sys.exit(0)

if __name__ == '__main__':
    # Kontrollera att openssl är installerat
    if shutil.which("openssl") is None:
        print("❌ OpenSSL saknas! Installera med:")
        print("   sudo apt update && sudo apt install openssl -y")
        sys.exit(1)
    
    # Starta båda servrarna
    start_dual_servers()