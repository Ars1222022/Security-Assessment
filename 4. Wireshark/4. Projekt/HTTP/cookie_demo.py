#!/usr/bin/env python3
"""
COOKIE SESSION HIJACKING DEMO - Visa hur cookies kan stjälas
HTTP (8080) vs HTTPS (8443) med session cookie-stöld demonstration
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import ssl
import subprocess
import os
import sys
import threading
import time
import secrets
import hashlib
from datetime import datetime

# Port definitions
HTTP_PORT = 8080
HTTPS_PORT = 8443

# Simulera en databas med användare och sessioner
users_db = {
    "anna.andersson": {"password": "mittHemligaLösen123", "fullname": "Anna Andersson"},
    "admin": {"password": "admin123", "fullname": "Systemadministratör"}
}

sessions_db = {}  # {session_id: username}
stolen_cookies = []  # Lagra stulna cookies för demonstration

class CookieHandler(BaseHTTPRequestHandler):
    def parse_cookies(self):
        """Parse cookies från request headers"""
        cookies = {}
        if 'cookie' in self.headers:
            cookie_header = self.headers['cookie']
            for cookie in cookie_header.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key] = value
        return cookies
    
    def get_current_user(self):
        """Hämta användaren baserat på session cookie"""
        cookies = self.parse_cookies()
        session_id = cookies.get('sessionid')
        
        if session_id in sessions_db:
            return sessions_db[session_id]
        return None
    
    def do_GET(self):
        """Hantera GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Kolla om det är HTTPS eller HTTP
        is_https = hasattr(self, 'is_https') and self.is_https
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        
        # Lägg till säkerhetsheaders för HTTPS
        if is_https:
            self.send_header('Set-Cookie', 'visited=true; Path=/')
        
        self.end_headers()
        
        # Hämta aktuell användare
        current_user = self.get_current_user()
        
        # ROUTING
        if path == '/':
            self.show_login_page(is_https, current_user)
        elif path == '/dashboard':
            self.show_dashboard(is_https, current_user)
        elif path == '/private':
            self.show_private_page(is_https, current_user)
        elif path == '/steal-cookie':
            self.show_cookie_theft_page(is_https, current_user)
        elif path == '/use-stolen-cookie':
            self.show_use_stolen_cookie(is_https)
        else:
            self.show_404()
    
    def do_POST(self):
        """Hantera POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        is_https = hasattr(self, 'is_https') and self.is_https
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        if path == '/login':
            self.handle_login(params, is_https)
        elif path == '/steal-cookie-action':
            self.handle_cookie_theft(params, is_https)
        elif path == '/logout':
            self.handle_logout(is_https)
    
    def show_login_page(self, is_https, current_user):
        """Visa inloggningssidan"""
        if current_user:
            # Redan inloggad, redirecta till dashboard
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            self.end_headers()
            return
        
        protocol = "https" if is_https else "http"
        port = HTTPS_PORT if is_https else HTTP_PORT
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🍪 Cookie Demo - {'HTTPS' if is_https else 'HTTP'}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .protocol-box {{ 
            background: {'#d4edda' if is_https else '#f8d7da'}; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 5px solid {'#28a745' if is_https else '#dc3545'};
        }}
        .info-box {{ 
            background: #fff3cd; 
            padding: 15px; 
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #ffc107;
        }}
        .danger-box {{ 
            background: #f8d7da; 
            padding: 15px; 
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #dc3545;
        }}
        form {{ background: #e9ecef; padding: 25px; border-radius: 5px; }}
        input {{ 
            width: 100%; 
            padding: 12px; 
            margin: 8px 0 20px 0; 
            border: 2px solid #ced4da;
            border-radius: 4px;
            font-size: 16px;
        }}
        button {{ 
            background: {'#28a745' if is_https else '#dc3545'}; 
            color: white; 
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }}
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
        .cookie-display {{ 
            background: #212529; 
            color: #20c997; 
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            margin: 10px 0;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <h1>🍪 Cookie & Session Demo - {'HTTPS (SÄKER)' if is_https else 'HTTP (OSÄKER)'}</h1>
    
    <div class="protocol-box">
        <h2>{'🔒 SÄKERT: Cookies är skyddade' if is_https else '⚠️ OSÄKERT: Cookies kan stjälas'}</h2>
        <p><strong>Protokoll:</strong> <code>{protocol.upper()}</code></p>
        <p><strong>URL:</strong> <code>{protocol}://localhost:{port}</code></p>
        <p><strong>Wireshark filter:</strong> <code>{"tcp.port == " + str(port) if is_https else "http"}</code></p>
    </div>
    
    <div class="info-box">
        <h3>📖 Vad är cookies?</h3>
        <p>Cookies är små textfiler som webbsidor sparar i din webbläsare för att:</p>
        <ul>
            <li>Hålla dig inloggad (session cookies)</li>
            <li>Komma ihåg dina inställningar</li>
            <li>Spara varukorgsinnehåll</li>
            <li>Spåra användarbeteende (analytics)</li>
        </ul>
    </div>
    
    <div class="danger-box">
        <h3>🎯 Vad vi ska testa:</h3>
        <ol>
            <li><strong>Logga in</strong> för att få en session cookie</li>
            <li><strong>Se i Wireshark</strong> hur cookien skickas med varje request</li>
            <li><strong>Stjäl cookien</strong> från HTTP-trafiken</li>
            <li><strong>Använd den stulna cookien</strong> för att bli inloggad som någon annan</li>
            <li><strong>Jämför</strong> hur HTTPS skyddar cookies</li>
        </ol>
    </div>
    
    <h2>Steg 1: Logga in för att få en cookie</h2>
    <form method="POST" action="/login">
        <label><strong>👤 Användarnamn:</strong></label>
        <input type="text" name="username" value="anna.andersson" required>
        
        <label><strong>🔑 Lösenord:</strong></label>
        <input type="password" name="password" value="mittHemligaLösen123" required>
        
        <br><br>
        <button type="submit">
            {'🔒 LOGGA IN (Säkert)' if is_https else '⚠️ LOGGA IN (Osäkert)'}
        </button>
    </form>
    
    <div style="margin-top: 30px; padding: 15px; background: #e9ecef; border-radius: 5px;">
        <h3>🔗 Gå direkt till:</h3>
        <p>
            <a href="/steal-cookie" style="color: #dc3545; font-weight: bold; margin-right: 20px;">
                🎯 Steg 2: Visa hur cookies stjäls
            </a>
            <a href="/dashboard" style="color: #6c757d; font-weight: bold;">
                📊 Dashboard (kräver inloggning)
            </a>
        </p>
        <p style="text-align: center; margin-top: 15px;">
            <a href="{'http://localhost:' + str(HTTP_PORT) if is_https else 'https://localhost:' + str(HTTPS_PORT)}" 
               style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                {'← Jämför med HTTP' if is_https else 'Jämför med HTTPS →'}
            </a>
        </p>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    
    def handle_login(self, params, is_https):
        """Hantera inloggning och sätt cookie"""
        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        
        # Validera användare
        if username in users_db and users_db[username]['password'] == password:
            # Skapa session
            session_id = secrets.token_urlsafe(32)
            sessions_db[session_id] = username
            
            # Skicka response med cookie
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            
            # Sätt cookie med olika säkerhetsinställningar beroende på protokoll
            if is_https:
                # Säkra inställningar för HTTPS
                cookie_str = f'sessionid={session_id}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=3600'
            else:
                # Osäkra inställningar för HTTP
                cookie_str = f'sessionid={session_id}; Path=/; Max-Age=3600'
            
            self.send_header('Set-Cookie', cookie_str)
            self.end_headers()
            
            print(f"\n{'🔒' if is_https else '🔓'} {'HTTPS' if is_https else 'HTTP'}:")
            print(f"   👤 {username} loggade in")
            print(f"   🍪 Session cookie: {session_id[:16]}...")
            print(f"   🛡️  Cookie säkerhet: {'Secure + HttpOnly + SameSite' if is_https else 'Ingen säkerhet'}")
            
        else:
            # Felaktiga uppgifter
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
    
    def show_dashboard(self, is_https, current_user):
        """Visa dashboard för inloggad användare"""
        if not current_user:
            # Ej inloggad, redirecta till login
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            return
        
        user_info = users_db[current_user]
        cookies = self.parse_cookies()
        session_id = cookies.get('sessionid', 'Ingen cookie')
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dashboard - {current_user}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .success-box {{ 
            background: #d4edda; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 5px solid #28a745;
        }}
        .cookie-box {{ 
            background: #fff3cd; 
            padding: 20px; 
            border-radius: 5px;
            margin: 20px 0;
        }}
        .cookie-display {{ 
            background: #212529; 
            color: #20c997; 
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            margin: 15px 0;
            word-break: break-all;
        }}
        .danger {{ color: #dc3545; font-weight: bold; }}
        .safe {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>📊 Välkommen {user_info['fullname']}!</h1>
    
    <div class="success-box">
        <h2>✅ Du är inloggad!</h2>
        <p>Din session cookie håller dig inloggad utan att du behöver skriva lösenordet igen.</p>
    </div>
    
    <div class="cookie-box">
        <h3>🍪 Din session cookie:</h3>
        <div class="cookie-display">
            sessionid={session_id}
        </div>
        <p><strong>Denna cookie skickas med VARJE request du gör till denna sida!</strong></p>
        
        <h3>🔍 Så här ser det ut i Wireshark:</h3>
        <div class="cookie-display">
GET /dashboard HTTP/1.1<br>
Host: localhost:{HTTPS_PORT if is_https else HTTP_PORT}<br>
Cookie: sessionid={session_id[:32]}...<br>
User-Agent: ...
        </div>
        
        <p><span class="{'danger' if not is_https else 'safe'}">
            {'⚠️ OSÄKERT: Denna cookie kan läsas av alla på samma nätverk!' if not is_https else '✅ SÄKERT: Denna cookie är krypterad med HTTPS!'}
        </span></p>
    </div>
    
    <h3>🔐 Privat information:</h3>
    <ul>
        <li><strong>Användarnamn:</strong> {current_user}</li>
        <li><strong>Fullständigt namn:</strong> {user_info['fullname']}</li>
        <li><strong>Senaste inloggning:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        <li><strong>Session giltig i:</strong> 60 minuter till</li>
    </ul>
    
    <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 5px;">
        <h3>🎯 Demo fortsättning:</h3>
        <p>
            <a href="/steal-cookie" style="background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                🎯 Visa hur cookies stjäls
            </a>
            <a href="/private" style="background: #17a2b8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                🔐 Privat sida
            </a>
            <form method="POST" action="/logout" style="display: inline;">
                <button type="submit" style="background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                    🚪 Logga ut
                </button>
            </form>
        </p>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="{'http://localhost:' + str(HTTP_PORT) if is_https else 'https://localhost:' + str(HTTPS_PORT)}" 
           style="color: #6c757d; text-decoration: none;">
            {'← Testa samma sak på HTTP (osäkert)' if is_https else 'Testa samma sak på HTTPS (säkert) →'}
        </a>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    
    def show_cookie_theft_page(self, is_https, current_user):
        """Visa sida för cookie-stöld demonstration"""
        global stolen_cookies
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🍪 Cookie Stöld Demo</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }}
        .demo-box {{ 
            background: #f8f9fa; 
            padding: 25px; 
            border-radius: 8px; 
            margin: 20px 0;
            border: 2px solid #dee2e6;
        }}
        .step {{ 
            background: white; 
            padding: 20px; 
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #17a2b8;
        }}
        .code-display {{ 
            background: #212529; 
            color: #20c997; 
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            margin: 15px 0;
            overflow-x: auto;
        }}
        .stolen-cookie {{ 
            background: #dc3545; 
            color: white; 
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
        }}
        .comparison-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
        }}
        th, td {{ 
            padding: 12px; 
            text-align: left; 
            border: 1px solid #dee2e6;
        }}
        th {{ background: #f8f9fa; }}
        .http {{ background: #f8d7da; }}
        .https {{ background: #d4edda; }}
    </style>
</head>
<body>
    <h1>🎯 Cookie Session Hijacking Demo</h1>
    
    <div class="demo-box">
        <h2>🍪 Vad är Session Hijacking?</h2>
        <p>Session hijacking innebär att en angripare stjäl din session cookie och använder den för att bli inloggad som DIG.</p>
        
        <h3>📊 Cookie-stöld jämförelse:</h3>
        <table class="comparison-table">
            <tr>
                <th>Säkerhetsaspekt</th>
                <th class="http">HTTP (Osäkert)</th>
                <th class="https">HTTPS (Säkert)</th>
            </tr>
            <tr>
                <td><strong>Cookie synlighet</strong></td>
                <td class="http">✅ Syns i klartext i Wireshark</td>
                <td class="https">❌ Krypterad - syns inte</td>
            </tr>
            <tr>
                <td><strong>Stöldrisk</strong></td>
                <td class="http">✅ Mycket hög - vem som helst kan stjäla</td>
                <td class="https">❌ Mycket låg - kräver privat nyckel</td>
            </tr>
            <tr>
                <td><strong>Man-in-the-Middle</strong></td>
                <td class="http">✅ Lätt att avlyssna cookies</td>
                <td class="https">❌ Mycket svårt</td>
            </tr>
            <tr>
                <td><strong>Säkra cookie-attribut</strong></td>
                <td class="http">❌ Fungerar inte utan HTTPS</td>
                <td class="https">✅ Secure-flaggan skyddar</td>
            </tr>
        </table>
    </div>
    
    <div class="step">
        <h3>🎯 Steg 1: Se din cookie i Wireshark</h3>
        <p>Om du är inloggad, skickas din cookie med varje request:</p>
        <div class="code-display">
# Wireshark filter för att hitta cookies:<br>
http.cookie                    # Alla cookies<br>
http contains "sessionid"      # Cookies med sessionid<br>
<br>
# Expandera ett GET-paket och leta efter:<br>
GET /dashboard HTTP/1.1<br>
Host: localhost:{HTTPS_PORT if is_https else HTTP_PORT}<br>
<strong>Cookie: sessionid=abc123def456...</strong>
        </div>
    </div>
    
    <div class="step">
        <h3>🎯 Steg 2: Simulera cookie-stöld</h3>
        <p>Testa att "stjäla" en cookie (detta är bara en simulation):</p>
        
        <form method="POST" action="/steal-cookie-action">
            <label><strong>Klistra in en stulen cookie här:</strong></label>
            <input type="text" name="stolen_cookie" placeholder="sessionid=abc123..." style="width: 100%; padding: 10px;">
            <button type="submit" style="background: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin-top: 10px; cursor: pointer;">
                🎯 SIMULERA COOKIE-STÖLD
            </button>
        </form>
        
        {'<div class="stolen-cookie"><strong>VARNING:</strong> På riktigt HTTP skulle denna cookie vara synlig i Wireshark!</div>' if not is_https else ''}
    </div>
    
    <div class="step">
        <h3>🎯 Steg 3: Använd en stulen cookie</h3>
        <p>Testa att använda en cookie som har "stulits":</p>
        <div style="text-align: center;">
            <a href="/use-stolen-cookie" style="background: #17a2b8; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                🔓 TESTA MED STULEN COOKIE
            </a>
        </div>
        {'<p><strong>På HTTP:</strong> Du kan kopiera en cookie från Wireshark och använda den här!</p>' if not is_https else ''}
    </div>
    
    <div class="step">
        <h3>🛡️ Så här skyddar du cookies:</h3>
        <div class="code-display">
// SÄKRA COOKIE-INSTÄLLNINGAR (kräver HTTPS):<br>
Set-Cookie: sessionid=abc123; <strong>Secure</strong>; <strong>HttpOnly</strong>; <strong>SameSite=Strict</strong><br>
<br>
<strong>Secure:</strong> Skickas bara över HTTPS<br>
<strong>HttpOnly:</strong> Kan inte läsas av JavaScript (skyddar mot XSS)<br>
<strong>SameSite:</strong> Skickas inte till andra domäner<br>
<strong>Max-Age:</strong> Begränsar giltighetstid
        </div>
    </div>
    
    <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 5px;">
        <h3>🔗 Fortsätt demonstrationen:</h3>
        <p>
            <a href="/dashboard" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                ← Tillbaka till Dashboard
            </a>
            <a href="/" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                🏠 Startsida
            </a>
        </p>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    
    def handle_cookie_theft(self, params, is_https):
        """Hantera cookie-stöld simulation"""
        stolen_cookie = params.get('stolen_cookie', [''])[0]
        
        if stolen_cookie:
            # Extrahera session ID från cookien
            if 'sessionid=' in stolen_cookie:
                session_id = stolen_cookie.split('sessionid=')[1].split(';')[0].strip()
                stolen_cookies.append({
                    'cookie': session_id,
                    'protocol': 'HTTPS' if is_https else 'HTTP',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
                
                print(f"\n🎯 {'HTTPS' if is_https else 'HTTP'} - COOKIE STÖLD SIMULATION:")
                print(f"   🍪 Stulen cookie: {session_id[:16]}...")
                print(f"   ⚠️  På {'HTTPS skulle detta vara krypterat' if is_https else 'HTTP kan detta faktiskt stjälas!'}")
        
        self.send_response(302)
        self.send_header('Location', '/steal-cookie')
        self.end_headers()
    
    def show_use_stolen_cookie(self, is_https):
        """Visa sida för att använda stulna cookies"""
        global stolen_cookies
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Använd Stulen Cookie</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .demo-box {{ 
            background: {'#d4edda' if is_https else '#f8d7da'}; 
            padding: 25px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 5px solid {'#28a745' if is_https else '#dc3545'};
        }}
        .cookie-list {{ 
            background: white; 
            padding: 20px; 
            border-radius: 5px;
            margin: 15px 0;
        }}
        .cookie-item {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #6c757d;
        }}
        .danger {{ color: #dc3545; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🔓 Använda Stulna Cookies</h1>
    
    <div class="demo-box">
        <h2>{'🔒 HTTPS: Cookies är skyddade' if is_https else '⚠️ HTTP: Cookies kan stjälas'}</h2>
        <p>
            {'På HTTPS är cookies krypterade och kan inte stjälas via nätverksavlyssning.' if is_https 
            else 'På HTTP syns cookies i klartext i Wireshark. Någon på samma WiFi kan:'}
        </p>
        
        <ul>
            {'<li>Se alla dina cookies i Wireshark</li>' if not is_https else ''}
            {'<li>Kopiera din session cookie</li>' if not is_https else ''}
            {'<li>Klistra in den i sin egen webbläsare</li>' if not is_https else ''}
            {'<li>Blir inloggad som DIG utan lösenord</li>' if not is_https else ''}
            <li>Få åtkomst till dina privata sidor</li>
            <li>Göra ändringar i ditt namn</li>
            <li>Se din personliga information</li>
        </ul>
        
        {'<p class="danger">⚠️ PÅ HTTP: Detta är inte en simulation - det kan faktiskt hända på riktigt!</p>' if not is_https else ''}
    </div>
    
    <div class="cookie-list">
        <h3>📋 Stulna cookies i denna demo:</h3>
        {self.generate_stolen_cookies_list()}
    </div>
    
    <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 5px;">
        <h3>🛡️ Skyddsåtgärder:</h3>
        <ol>
            <li><strong>Använd ALLTID HTTPS</strong> - krypterar alla cookies</li>
            <li><strong>Secure-flagga</strong> på cookies (fungerar bara med HTTPS)</li>
            <li><strong>HttpOnly-flagga</strong> - förhindrar JavaScript-åtkomst</li>
            <li><strong>SameSite=Strict</strong> - skickas inte till andra sidor</li>
            <li><strong>Korta sessioner</strong> - begränsa giltighetstid</li>
            <li><strong>Undvik publika WiFi</strong> för känsliga ärenden</li>
            <li><strong>Använd VPN</strong> på opålitliga nätverk</li>
        </ol>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="/steal-cookie" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
            ← Tillbaka till cookie-stöld
        </a>
        <a href="/" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            🏠 Startsida
        </a>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    
    def generate_stolen_cookies_list(self):
        """Generera HTML-lista med stulna cookies"""
        global stolen_cookies
        
        if not stolen_cookies:
            return '<p>Inga cookies har "stulits" ännu. Testa att "stjäla" en på föregående sida.</p>'
        
        items = []
        for i, cookie_data in enumerate(stolen_cookies[-5:]):  # Visa senaste 5
            items.append(f'''
            <div class="cookie-item">
                <strong>Cookie #{i+1}:</strong> {cookie_data['cookie'][:32]}...<br>
                <small>Protokoll: {cookie_data['protocol']} | Tid: {cookie_data['timestamp']}</small>
            </div>
            ''')
        
        return '\n'.join(items)
    
    def show_private_page(self, is_https, current_user):
        """Visa en privat sida som kräver inloggning"""
        if not current_user:
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            return
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Privat Sida - {current_user}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .private-box {{ 
            background: #e9ecef; 
            padding: 30px; 
            border-radius: 8px; 
            margin: 20px 0;
            border: 3px solid #6c757d;
        }}
        .warning {{ 
            background: #fff3cd; 
            padding: 15px; 
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #ffc107;
        }}
    </style>
</head>
<body>
    <h1>🔐 Privat Sida</h1>
    
    <div class="warning">
        <h3>⚠️ DENNA SIDA KRÄVER INLOGGNING</h3>
        <p>Du kommer hit automatiskt om du har en giltig session cookie.</p>
    </div>
    
    <div class="private-box">
        <h2>Hej {current_user}!</h2>
        <p>Denna sida är skyddad av din session cookie. Om någon stjäl din cookie kan de komma hit utan ditt lösenord.</p>
        
        <h3>📋 Din privata information:</h3>
        <ul>
            <li><strong>Användarprofil:</strong> {users_db[current_user]['fullname']}</li>
            <li><strong>Personnummer:</strong> 850101-1234</li>
            <li><strong>Bankkonton:</strong> Swedbank: 123-4567 | Nordea: 890-1234</li>
            <li><strong>Kreditkort:</strong> Visa **** **** **** 1234</li>
            <li><strong>Adress:</strong> Exempelgatan 1, 123 45 Stockholm</li>
            <li><strong>Telefon:</strong> 070-123 45 67</li>
        </ul>
        
        <p><strong>Så här kom du hit:</strong> Din webbläsare skickade automatiskt din session cookie, och servern verifierade att den var giltig.</p>
    </div>
    
    <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
        <h3>🎯 Demo poäng:</h3>
        <p><strong>Med en stulen cookie kan en angripare:</strong></p>
        <ul>
            <li>Komma till denna sida utan lösenord</li>
            <li>Se all din privata information</li>
            <li>Göra ändringar i ditt konto</li>
            <li>Skicka meddelanden i ditt namn</li>
        </ul>
        <p><strong>Lösning:</strong> HTTPS + Secure cookies + HttpOnly + SameSite</p>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="/dashboard" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            ← Tillbaka till Dashboard
        </a>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    
    def handle_logout(self, is_https):
        """Hantera utloggning"""
        cookies = self.parse_cookies()
        session_id = cookies.get('sessionid')
        
        if session_id in sessions_db:
            del sessions_db[session_id]
        
        # Skicka response som tar bort cookien
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'sessionid=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()
    
    def show_404(self):
        """Visa 404 sida"""
        html = """<!DOCTYPE html>
<html>
<head><title>404 - Sidan finns inte</title></head>
<body>
    <h1>404 - Sidan finns inte</h1>
    <p><a href="/">← Tillbaka till startsidan</a></p>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))

# Resten av koden (create_certificate, start_http_server, start_https_server, start_dual_servers) 
# är identisk med den du redan har, men byt ut DualHandler mot CookieHandler

def create_certificate():
    """Skapa självsignerat certifikat för HTTPS"""
    key_file = "/tmp/demo_https.key"
    cert_file = "/tmp/demo_https.crt"
    
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
    class HTTPHandler(CookieHandler):
        is_https = False
    
    httpd = HTTPServer(('0.0.0.0', HTTP_PORT), HTTPHandler)
    
    print(f"✅ HTTP-server startad!")
    print(f"🌐 Öppna: http://localhost:{HTTP_PORT}")
    print(f"🎯 Wireshark filter: http eller tcp.port == {HTTP_PORT}")
    print("   Kommer visa: COOKIES I KLARTEXT!\n")
    
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
    class HTTPSHandler(CookieHandler):
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
    print("   Kommer visa: COOKIES KRYPTERADE!\n")
    
    try:
        httpsd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 HTTPS-server stoppad.")

def start_dual_servers():
    """Starta båda servrarna i separata trådar"""
    print("\n" + "="*70)
    print("🍪 COOKIE SESSION HIJACKING DEMO")
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
    print("2. Följ dessa steg på BÅDA sidorna:")
    print("   a) Logga in (får en session cookie)")
    print("   b) Gå till Dashboard")
    print("   c) Klicka på 'Visa hur cookies stjäls'")
    print("   d) Se skillnaden i Wireshark")
    print("")
    print("3. Wireshark filter för cookies:")
    print("   → HTTP: http.cookie")
    print("   → HTTPS: tcp.port == 8443")
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
        print("✅ Demo klar! Förhoppningsvis såg du hur cookies kan stjälas!")
        sys.exit(0)

if __name__ == '__main__':
    # Kontrollera att openssl är installerat
    if subprocess.run(["which", "openssl"], capture_output=True).returncode != 0:
        print("❌ OpenSSL saknas! Installera med:")
        print("   sudo apt update && sudo apt install openssl -y")
        sys.exit(1)
    
    # Starta båda servrarna
    start_dual_servers()