#!/usr/bin/env python3
"""
WIRESHARK DEMO - Visa hur lätt det är att stjäla lösenord via HTTP
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import socket
import sys

class DemoHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Överstyr logging för att visa i terminalen"""
        print(f"[HTTP] {self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Visa inloggningssidan"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Hämta serverns IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                server_ip = s.getsockname()[0]
                s.close()
            except:
                server_ip = "localhost"
            
            html = '''<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <title>🔓 HTTP Säkerhetsdemo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
        .warning { 
            background: #fff3cd; 
            border: 2px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .danger { 
            background: #f8d7da;
            border: 2px solid #dc3545;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
        }
        form { background: #f8f9fa; padding: 20px; border-radius: 5px; }
        input, textarea { 
            width: 100%; 
            padding: 10px; 
            margin: 8px 0; 
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button { 
            background: #dc3545; 
            color: white; 
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        button:hover { background: #c82333; }
        .stolen { 
            background: #e9ecef;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #6c757d;
        }
        pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>🔐 Wireshark Demo: Avlyssning av HTTP-trafik</h1>
    
    <div class="warning">
        <h3>⚠️ VARNING: Denna sida använder HTTP (inte HTTPS)</h3>
        <p>All data du skickar här kan läsas av vem som helst på samma nätverk!</p>
    </div>
    
    <h2>Testa att "logga in":</h2>
    <form method="POST" action="/login">
        <label><strong>👤 Användarnamn:</strong></label>
        <input type="text" name="username" value="anna.andersson" required>
        
        <label><strong>🔑 Lösenord:</strong></label>
        <input type="password" name="password" value="mittHemligaLösen123" required>
        
        <label><strong>📧 E-post:</strong></label>
        <input type="email" name="email" value="anna.andersson@example.com">
        
        <label><strong>🔎 Vad söker du på Google?</strong></label>
        <input type="text" name="search" value="hur byter jag lösenord på banken">
        
        <label><strong>💬 Meddelande:</strong></label>
        <textarea name="message" rows="3">Min bankkod är 1234 och mitt personnummer är 850101-1234</textarea>
        
        <br><br>
        <button type="submit">🚨 SKICKA OKRYPTERAT (Farligt!)</button>
    </form>
    
    <div class="danger">
        <h3>🎯 Vad du kommer se i Wireshark:</h3>
        <ol>
            <li>Starta Wireshark och börja fånga trafik</li>
            <li>Använd filtret: <code>http</code></li>
            <li>Skicka formuläret här ovan</li>
            <li>Hitta POST-paketet i listan</li>
            <li>Högerklicka → Follow → TCP Stream</li>
            <li><strong>VOILÀ! All data syns i klartext!</strong></li>
        </ol>
    </div>
    
    <hr>
    <p><strong>Server IP:</strong> ''' + server_ip + ''':8080</p>
    <p><strong>Local URL:</strong> http://localhost:8080</p>
    <p><strong>Wireshark filter:</strong> <code>tcp.port == 8080</code></p>
    
    <div class="stolen">
        <h3>📡 Exempel på vad som kan stjälas:</h3>
        <ul>
            <li>Lösenord och användarnamn</li>
            <li>Personnummer och bankuppgifter</li>
            <li>Sökhistorik och intressen</li>
            <li>Cookies för att kapra sessioner</li>
            <li>All form-data från alla formulär</li>
        </ul>
    </div>
</body>
</html>'''
            self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        """Hantera inloggning - visa stulen data"""
        if self.path == '/login':
            # Läs POST-datan
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parsa parametrarna
            params = parse_qs(post_data)
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            email = params.get('email', [''])[0]
            search = params.get('search', [''])[0]
            message = params.get('message', [''])[0]
            
            # Visa stulen data
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            post_data_display = post_data.replace('&', '&\n')
            
            html = f'''<!DOCTYPE html>
<html>
<head><title>Data Stulen! 🎯</title>
    <style>
        body {{ font-family: Arial; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .stolen-box {{ 
            background: #dc3545; 
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .data-item {{ 
            background: rgba(255,255,255,0.2);
            padding: 10px;
            margin: 10px 0;
            border-radius: 3px;
        }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>🎯 DATA HAR STULITS!</h1>
    
    <div class="stolen-box">
        <h2>📡 All denna information är nu stulen:</h2>
        
        <div class="data-item">
            <strong>👤 Användarnamn:</strong><br>
            <code>{username}</code>
        </div>
        
        <div class="data-item">
            <strong>🔑 Lösenord:</strong><br>
            <code>{password}</code>
        </div>
        
        <div class="data-item">
            <strong>📧 E-post:</strong><br>
            <code>{email}</code>
        </div>
        
        <div class="data-item">
            <strong>🔎 Sökterm:</strong><br>
            <code>{search}</code>
        </div>
        
        <div class="data-item">
            <strong>💬 Meddelande:</strong><br>
            <code>{message}</code>
        </div>
    </div>
    
    <h3>🔍 Så här ser det ut i Wireshark:</h3>
    <pre>
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: {len(post_data)}

{post_data_display}
    </pre>
    
    <h3>💡 Lärdom:</h3>
    <ul>
        <li><strong>HTTP skickar allt i KLARTEXT</strong></li>
        <li>På ett café-WiFi kan alla se detta</li>
        <li>Enda lösningen: <strong>ALLTID använda HTTPS (🔒)</strong></li>
        <li>Använd VPN på opålitliga nätverk</li>
    </ul>
    
    <p><a href="/">← Testa igen</a></p>
    
    <hr>
    <p><em>Denna demo körs i en säker VM. I verkligheten skulle detta vara ett allvarligt brott.</em></p>
</body>
</html>'''
            self.wfile.write(html.encode('utf-8'))
            
            # Skriv ut i terminalen också
            print("\n" + "="*70)
            print("🚨 WIRESHARK DEMO - FÅNGAD DATA I KLARTEXT:")
            print("="*70)
            print(f"👤 Användarnamn: {username}")
            print(f"🔑 Lösenord:     {password}")
            print(f"📧 E-post:       {email}")
            print(f"🔎 Sökterm:      {search}")
            print(f"💬 Meddelande:   {message}")
            print("="*70)
            print("\n🎯 Visa detta i Wireshark med filtret: http")
            print("   eller: tcp.port == 8080\n")

def run_server():
    """Starta HTTP-servern"""
    PORT = 8080
    
    try:
        server = HTTPServer(('0.0.0.0', PORT), DemoHandler)
        
        print("\n" + "="*70)
        print("🔓 WIRESHARK HTTP DEMO - STARTAD!")
        print("="*70)
        print("\n🌐 ÖPPNA I WEBBLÄSARE:")
        print(f"   → http://localhost:{PORT}")
        
        print("\n🎯 WIRESHARK FILTER:")
        print("   http")
        print("   tcp.port == 8080")
        
        print("\n📝 INSTRUKTIONER:")
        print("   1. Starta Wireshark i VM")
        print("   2. Börja fånga på 'ens33' eller 'eth0'")
        print("   3. Använd filtret 'http'")
        print("   4. Fyll i formuläret på webbsidan")
        print("   5. Leta efter POST /login i Wireshark")
        print("   6. Följ TCP-stream för att se lösenordet!")
        
        print("\n" + "="*70)
        print("Tryck Ctrl+C för att stoppa servern")
        print("="*70 + "\n")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n👋 Servern stoppad. Demo klar!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Prova med en annan port:")
        print("   Ändra PORT = 8080 till PORT = 9999")
        print("\n💡 Eller kolla om porten är upptagen:")
        print("   sudo lsof -i :8080")
        sys.exit(1)

if __name__ == '__main__':
    run_server()
