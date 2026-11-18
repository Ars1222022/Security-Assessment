#!/usr/bin/env python3
"""
ENKEL DDOS-LABB SOM FUNGERAR - Utan JavaScript problem
"""

import http.server
import socketserver
import threading
import time
import json
import sqlite3
from datetime import datetime
import random
import string

# ============================================================================
# ENKEL DATABAS
# ============================================================================

class SimpleDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('simple_ddos.db')
        self.c = self.conn.cursor()
        self.setup_database()
    
    def setup_database(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ip TEXT,
                server TEXT,
                response_time REAL,
                status INTEGER
            )
        ''')
        self.conn.commit()
    
    def log_request(self, ip, server, response_time, status=200):
        self.c.execute('''
            INSERT INTO requests (timestamp, ip, server, response_time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), ip, server, response_time, status))
        self.conn.commit()
    
    def get_stats(self, server):
        self.c.execute('''
            SELECT COUNT(*), AVG(response_time), MAX(response_time)
            FROM requests WHERE server = ?
        ''', (server,))
        return self.c.fetchone()

# ============================================================================
# ENKLA SERVERS
# ============================================================================

class SimpleUnprotectedHandler(http.server.BaseHTTPRequestHandler):
    count = 0
    
    def do_GET(self):
        start = time.time()
        SimpleUnprotectedHandler.count += 1
        
        # Simulera arbete
        time.sleep(random.uniform(0.01, 0.05))
        
        response_time = time.time() - start
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <html>
        <body style="font-family: Arial; padding: 20px; background: #ffe6e6;">
            <h1>⚠️ OSKYDDAD SERVER</h1>
            <p><strong>Inget DDoS-skydd!</strong></p>
            <p>Förfrågningar: {SimpleUnprotectedHandler.count}</p>
            <p>Svarstid: {response_time:.3f}s</p>
            <p>IP: {self.client_address[0]}</p>
            <hr>
            <p><a href="http://localhost:8081">Skyddad server</a></p>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
        print(f"OSKYDDAD: {self.client_address[0]} - {response_time:.3f}s")

class SimpleProtectedHandler(http.server.BaseHTTPRequestHandler):
    count = 0
    ip_requests = {}
    
    def do_GET(self):
        ip = self.client_address[0]
        now = time.time()
        
        # Enkelt rate limiting
        if ip not in self.ip_requests:
            self.ip_requests[ip] = []
        
        # Rensa gamla (äldre än 10s)
        self.ip_requests[ip] = [t for t in self.ip_requests[ip] if now - t < 10]
        
        # Om för många, blockera
        if len(self.ip_requests[ip]) > 10:  # Max 10/10s
            self.send_response(429)
            self.end_headers()
            self.wfile.write(b"<h1>BLOCKERAD - For manga forfragningar</h1>")
            print(f"SKYDDAD: BLOCKERAD {ip}")
            return
        
        # Lägg till förfrågan
        self.ip_requests[ip].append(now)
        SimpleProtectedHandler.count += 1
        start = time.time()
        
        time.sleep(random.uniform(0.01, 0.03))
        response_time = time.time() - start
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <html>
        <body style="font-family: Arial; padding: 20px; background: #e6ffe6;">
            <h1>✅ SKYDDAD SERVER</h1>
            <p><strong>DDoS-skydd aktiverat!</strong></p>
            <p>Förfrågningar: {SimpleProtectedHandler.count}</p>
            <p>Svarstid: {response_time:.3f}s</p>
            <p>IP: {ip} (har skickat {len(self.ip_requests[ip])}/10s)</p>
            <hr>
            <p><a href="http://localhost:8080">Oskyddad server</a></p>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
        print(f"SKYDDAD: {ip} - {response_time:.3f}s - Rate: {len(self.ip_requests[ip])}/10")

# ============================================================================
# ENKEL ATTACK FUNKTION
# ============================================================================

def run_attack(target, name, count=500):
    """Kör en enkel attack"""
    import requests
    
    print(f"\n{'='*60}")
    print(f"⚡ ATTACK MOT {name}")
    print(f"{'='*60}")
    
    success = 0
    blocked = 0
    start_time = time.time()
    
    for i in range(count):
        try:
            r = requests.get(target, timeout=2)
            if r.status_code == 200:
                success += 1
            elif r.status_code == 429:
                blocked += 1
        except:
            pass
        
        if i % 100 == 0:
            print(f"  {i}/{count}...")
    
    total_time = time.time() - start_time
    
    print(f"\n📊 RESULTAT:")
    print(f"• Lyckade: {success}/{count}")
    print(f"• Blockerade: {blocked}")
    print(f"• Tid: {total_time:.1f}s")
    print(f"• Förfrågningar/sekund: {count/total_time:.1f}")
    print(f"{'='*60}")
    
    return success, blocked

# ============================================================================
# HUVUDPROGRAM
# ============================================================================

def start_servers():
    """Startar båda servrarna"""
    print("="*60)
    print("🎯 ENKELT DDOS-LABB")
    print("="*60)
    print("Oskyddad: http://localhost:8080")
    print("Skyddad:  http://localhost:8081")
    print("="*60)
    
    def run_unprotected():
        with socketserver.TCPServer(("localhost", 8080), SimpleUnprotectedHandler) as server:
            print("✅ Oskyddad server startad")
            server.serve_forever()
    
    def run_protected():
        with socketserver.TCPServer(("localhost", 8081), SimpleProtectedHandler) as server:
            print("✅ Skyddad server startad")
            server.serve_forever()
    
    t1 = threading.Thread(target=run_unprotected, daemon=True)
    t2 = threading.Thread(target=run_protected, daemon=True)
    
    t1.start()
    t2.start()
    
    return t1, t2

def main():
    """Huvudprogram"""
    print("ENKELT DDOS-TESTLABB")
    print("Testa skillnaden mellan skyddad och oskyddad server!")
    
    # Starta servrar
    print("\nStartar servrar...")
    start_servers()
    time.sleep(2)
    
    while True:
        print("\n" + "="*60)
        print("MENY:")
        print("1. Testa att besöka båda servrarna")
        print("2. Attackera OSKYDDAD server")
        print("3. Attackera SKYDDAD server")
        print("4. Kör jämförelsetest")
        print("5. Avsluta")
        print("="*60)
        
        choice = input("Välj: ").strip()
        
        if choice == '1':
            print("\nBesöker servrarna...")
            
            import requests
            
            # Testa oskyddad
            start = time.time()
            r = requests.get("http://localhost:8080")
            time1 = time.time() - start
            
            # Testa skyddad
            start = time.time()
            r = requests.get("http://localhost:8081")
            time2 = time.time() - start
            
            print(f"\n📊 TEST RESULTAT:")
            print(f"Oskyddad: {time1:.3f}s")
            print(f"Skyddad:  {time2:.3f}s")
            
        elif choice == '2':
            print("\n⚡ Attackera oskyddad server (500 förfrågningar)")
            success, blocked = run_attack("http://localhost:8080", "OSKYDDAD SERVER", 500)
            print(f"\n✅ {success} lyckades, {blocked} blockerade")
            
        elif choice == '3':
            print("\n🛡️ Attackera skyddad server (500 förfrågningar)")
            success, blocked = run_attack("http://localhost:8081", "SKYDDAD SERVER", 500)
            print(f"\n✅ {success} lyckades, {blocked} blockerade")
            
        elif choice == '4':
            print("\n📊 JÄMFÖRELSE TEST")
            print("\n1. Attackera oskyddad...")
            success1, blocked1 = run_attack("http://localhost:8080", "OSKYDDAD", 300)
            
            time.sleep(3)
            
            print("\n2. Attackera skyddad...")
            success2, blocked2 = run_attack("http://localhost:8081", "SKYDDAD", 300)
            
            print(f"\n{'='*60}")
            print("📈 SLUTRESULTAT")
            print(f"{'='*60}")
            print(f"OSKYDDAD: {success1}/300 lyckades")
            print(f"SKYDDAD:  {success2}/300 lyckades ({blocked2} blockerade!)")
            print(f"SKILLNAD: {success1 - success2} förfrågningar")
            print(f"SKYDDS EFFEKTIVITET: {(blocked2/300*100):.1f}%")
            print(f"{'='*60}")
            
        elif choice == '5':
            print("\n👋 Avslutar...")
            break
            
        else:
            print("Ogiltigt val")

if __name__ == '__main__':
    try:
        # Installera requests om det behövs
        try:
            import requests
        except ImportError:
            print("Installerar requests...")
            import subprocess
            subprocess.check_call(['pip3', 'install', 'requests'])
            import requests
        
        main()
    except KeyboardInterrupt:
        print("\n\nAvslutas...")
    except Exception as e:
        print(f"\nFel: {e}")