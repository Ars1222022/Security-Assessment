#!/usr/bin/env python3
"""
SUPERENKELT DDOS-LABB - 100% FUNGERANDE
"""

import http.server
import socketserver
import threading
import time
import random
from datetime import datetime
import sys

# ============================================================================
# ENKEL STATISTIK
# ============================================================================

class SimpleStats:
    unprotected_requests = 0
    protected_requests = 0
    unprotected_total_time = 0
    protected_total_time = 0
    
    @classmethod
    def add_unprotected(cls, response_time):
        cls.unprotected_requests += 1
        cls.unprotected_total_time += response_time
    
    @classmethod
    def add_protected(cls, response_time):
        cls.protected_requests += 1
        cls.protected_total_time += response_time
    
    @classmethod
    def get_stats(cls):
        unprotected_avg = cls.unprotected_total_time / max(cls.unprotected_requests, 1)
        protected_avg = cls.protected_total_time / max(cls.protected_requests, 1)
        
        return {
            'unprotected': {'requests': cls.unprotected_requests, 'avg_time': round(unprotected_avg, 3)},
            'protected': {'requests': cls.protected_requests, 'avg_time': round(protected_avg, 3)}
        }

# ============================================================================
# ENKLA SERVERS
# ============================================================================

class SimpleUnprotectedHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Överstyr för att undvika standardloggning
        pass
    
    def do_GET(self):
        start = time.time()
        SimpleStats.unprotected_requests += 1
        
        # Oskyddad blir långsammare vid många förfrågningar
        if SimpleStats.unprotected_requests > 50:
            delay = random.uniform(0.1, 0.5)
            time.sleep(delay)
        elif SimpleStats.unprotected_requests > 20:
            delay = random.uniform(0.05, 0.2)
            time.sleep(delay)
        else:
            time.sleep(0.01)
        
        response_time = time.time() - start
        SimpleStats.unprotected_total_time += response_time
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Simulera serverbelastning baserat på antal förfrågningar
        load_level = "LÅG"
        if SimpleStats.unprotected_requests > 100:
            load_level = "MYCKET HÖG"
        elif SimpleStats.unprotected_requests > 50:
            load_level = "HÖG"
        elif SimpleStats.unprotected_requests > 20:
            load_level = "MEDEL"
        
        html = f"""
        <html>
        <head>
            <title>OSKYDDAD Server</title>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #ffe6e6;">
            <h1 style="color: #c0392b;">⚠️ OSKYDDAD SERVER</h1>
            <p><strong>INGET DDoS-SKYDD</strong></p>
            <p>Alla förfrågningar accepteras, även attacker!</p>
            
            <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #c0392b;">
                <h3>Server Status:</h3>
                <p><strong>Belastning:</strong> <span style="color: #c0392b;">{load_level}</span></p>
                <p><strong>Förfrågningar totalt:</strong> {SimpleStats.unprotected_requests}</p>
                <p><strong>Svarstid:</strong> {response_time:.3f}s</p>
                <p><strong>IP-adress:</strong> {self.client_address[0]}</p>
                <p><strong>Sökväg:</strong> {self.path}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h4>Test endpoints:</h4>
                <ul>
                    <li><a href="/">/ Hem</a></li>
                    <li><a href="/api">/ API</a></li>
                    <li><a href="/slow">/ Långsam sida</a></li>
                </ul>
            </div>
            
            <p><a href="http://localhost:8081" style="color: green; font-weight: bold;">→ Gå till Skyddad Server</a></p>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
        print(f"OSKYDDAD: {self.client_address[0]} - {response_time:.3f}s - Belastning: {load_level}")

class SimpleProtectedHandler(http.server.BaseHTTPRequestHandler):
    ip_counts = {}
    blocked_ips = {}
    
    def log_message(self, format, *args):
        # Överstyr för att undvika standardloggning
        pass
    
    def do_GET(self):
        ip = self.client_address[0]
        now = time.time()
        
        # Kolla om IP är blockerad
        if ip in self.blocked_ips and self.blocked_ips[ip] > now:
            block_time_left = int(self.blocked_ips[ip] - now)
            self.send_response(429)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 30px; text-align: center; background: #fff0f0;">
                <h1 style="color: #e74c3c;">⛔ BLOCKERAD</h1>
                <p>Din IP-adress ({ip}) har blockerats temporärt.</p>
                <p><strong>Anledning:</strong> För många förfrågningar</p>
                <p><strong>Tid kvar:</strong> {block_time_left} sekunder</p>
                <p><small>DDoS-skydd är aktiverat på denna server</small></p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode('utf-8'))
            print(f"SKYDDAD: BLOCKERAD {ip} - {block_time_left}s kvar")
            return
        
        # Enkelt rate limiting
        if ip not in self.ip_counts:
            self.ip_counts[ip] = []
        
        # Rensa gamla (äldre än 10s)
        self.ip_counts[ip] = [t for t in self.ip_counts[ip] if now - t < 10]
        
        # Om för många, blockera i 30 sekunder
        if len(self.ip_counts[ip]) >= 5:  # Max 5/10s
            self.blocked_ips[ip] = now + 30
            self.send_response(429)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 30px; text-align: center; background: #fff0f0;">
                <h1 style="color: #e74c3c;">⛔ BLOCKERAD</h1>
                <p>Din IP-adress ({ip}) har överskridit rate limit.</p>
                <p><strong>Gräns:</strong> 5 förfrågningar per 10 sekunder</p>
                <p><strong>Du skickade:</strong> {len(self.ip_counts[ip])} förfrågningar</p>
                <p><strong>Blockad i:</strong> 30 sekunder</p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode('utf-8'))
            print(f"SKYDDAD: BLOCKERAD {ip} - Överskridit rate limit ({len(self.ip_counts[ip])}/5)")
            return
        
        # Lägg till och processa
        self.ip_counts[ip].append(now)
        SimpleStats.protected_requests += 1
        start = time.time()
        
        # Liten delay som simulerar normal bearbetning
        time.sleep(0.01)
        
        response_time = time.time() - start
        SimpleStats.protected_total_time += response_time
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Beräkna antal blockeringar
        active_blocked = sum(1 for block_time in self.blocked_ips.values() if block_time > now)
        
        html = f"""
        <html>
        <head>
            <title>SKYDDAD Server</title>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #e6ffe6;">
            <h1 style="color: #27ae60;">✅ SKYDDAD SERVER</h1>
            <p><strong>DDoS-SKYDD AKTIVERAT</strong></p>
            <p>Rate limiting: max 5 förfrågningar per 10 sekunder</p>
            
            <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #27ae60;">
                <h3>Server Status:</h3>
                <p><strong>Status:</strong> <span style="color: #27ae60;">SKYDDAD</span></p>
                <p><strong>Förfrågningar totalt:</strong> {SimpleStats.protected_requests}</p>
                <p><strong>Svarstid:</strong> {response_time:.3f}s</p>
                <p><strong>Din IP:</strong> {ip}</p>
                <p><strong>Din rate:</strong> {len(self.ip_counts[ip])}/5 förfrågningar (10s fönster)</p>
                <p><strong>Aktuellt blockade IP:er:</strong> {active_blocked}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h4>🛡️ Aktiva skyddsmekanismer:</h4>
                <ul>
                    <li><strong>Rate Limiting:</strong> 5 förfrågningar/10s per IP</li>
                    <li><strong>Temporär blockering:</strong> 30s vid överträdelse</li>
                    <li><strong>IP-spårning:</strong> Realtidsövervakning</li>
                </ul>
            </div>
            
            <p><a href="http://localhost:8080" style="color: #c0392b; font-weight: bold;">← Gå till Oskyddad Server</a></p>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
        print(f"SKYDDAD: {ip} - {response_time:.3f}s - Rate: {len(self.ip_counts[ip])}/5 - Blockade: {active_blocked}")

class SimpleControlPanel(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Överstyr för att undvika standardloggning
        pass
    
    def do_GET(self):
        stats = SimpleStats.get_stats()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = f"""
        <html>
        <head>
            <title>DDOS-LABB Kontrollpanel</title>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #333;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 15px;
                }}
                .dashboard {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin: 20px 0;
                }}
                .card {{
                    flex: 1;
                    min-width: 300px;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                .card-red {{
                    background: #ffe6e6;
                    border-top: 5px solid #e74c3c;
                }}
                .card-green {{
                    background: #e6ffe6;
                    border-top: 5px solid #2ecc71;
                }}
                .card-blue {{
                    background: #e6f7ff;
                    border-top: 5px solid #3498db;
                }}
                h3 {{
                    margin-top: 0;
                    color: #2c3e50;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    margin: 10px 5px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                    text-decoration: none;
                    font-size: 16px;
                    transition: all 0.3s;
                }}
                .btn-red {{ background: #e74c3c; color: white; }}
                .btn-green {{ background: #2ecc71; color: white; }}
                .btn-blue {{ background: #3498db; color: white; }}
                .btn:hover {{ opacity: 0.9; transform: translateY(-2px); }}
                .stats-box {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    border-left: 4px solid #f1c40f;
                }}
                code {{
                    background: #2c3e50;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 5px;
                    display: block;
                    margin: 10px 0;
                    font-family: 'Courier New', monospace;
                    overflow-x: auto;
                }}
                .comparison {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin: 30px 0;
                }}
                @media (max-width: 768px) {{
                    .comparison {{ grid-template-columns: 1fr; }}
                    .dashboard {{ flex-direction: column; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 DDOS-LABB KONTROLLPANEL</h1>
                
                <div class="dashboard">
                    <div class="card card-red">
                        <h3>⚠️ OSKYDDAD Server</h3>
                        <p><strong>Port:</strong> 8080</p>
                        <p><strong>Förfrågningar:</strong> {stats['unprotected']['requests']}</p>
                        <p><strong>Medelsvarstid:</strong> {stats['unprotected']['avg_time']}s</p>
                        <p><strong>Status:</strong> <span style="color: #e74c3c;">Sårbar för DDoS</span></p>
                        <div style="margin-top: 15px;">
                            <a href="http://localhost:8080" class="btn btn-red" target="_blank">Besök Server</a>
                        </div>
                    </div>
                    
                    <div class="card card-green">
                        <h3>✅ SKYDDAD Server</h3>
                        <p><strong>Port:</strong> 8081</p>
                        <p><strong>Förfrågningar:</strong> {stats['protected']['requests']}</p>
                        <p><strong>Medelsvarstid:</strong> {stats['protected']['avg_time']}s</p>
                        <p><strong>Status:</strong> <span style="color: #27ae60;">Skyddad mot DDoS</span></p>
                        <div style="margin-top: 15px;">
                            <a href="http://localhost:8081" class="btn btn-green" target="_blank">Besök Server</a>
                        </div>
                    </div>
                </div>
                
                <div class="card card-blue">
                    <h3>⚡ Attack Kontroller</h3>
                    <p>Testa olika typer av DDoS-attacker:</p>
                    
                    <div style="margin: 20px 0;">
                        <button onclick="startAttack('unprotected', 'normal')" class="btn btn-red">
                            ⚡ Normal Attack (OSKYDDAD)
                        </button>
                        <button onclick="startAttack('protected', 'normal')" class="btn btn-green">
                            🛡️ Test Attack (SKYDDAD)
                        </button>
                        <button onclick="startAttack('both', 'comparison')" class="btn btn-blue">
                            📊 Jämförelseattack
                        </button>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <h4>Avancerade attacker:</h4>
                        <button onclick="startAttack('unprotected', 'slowloris')" class="btn" style="background: #9b59b6; color: white;">
                            🐌 Slowloris Attack
                        </button>
                        <button onclick="startAttack('protected', 'flood')" class="btn" style="background: #e67e22; color: white;">
                            🌊 Flood Attack
                        </button>
                        <button onclick="startAttack('both', 'mixed')" class="btn" style="background: #34495e; color: white;">
                            🎭 Blandad Attack
                        </button>
                    </div>
                    
                    <div id="attackResult" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; display: none;">
                        <h4>Attack Resultat:</h4>
                        <div id="resultDetails"></div>
                    </div>
                </div>
                
                <div class="comparison">
                    <div class="card">
                        <h3>📊 Prestandajämförelse</h3>
                        <div class="stats-box">
                            <p><strong>Skillnad i förfrågningar:</strong> {stats['unprotected']['requests'] - stats['protected']['requests']}</p>
                            <p><strong>Skillnad i svarstid:</strong> {(stats['unprotected']['avg_time'] - stats['protected']['avg_time']):.3f}s</p>
                            {self.generate_efficiency_message(stats)}
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>💡 Testinstruktioner</h3>
                        <ol style="padding-left: 20px;">
                            <li>Öppna två terminalfönster</li>
                            <li>I terminal 1, kör:</li>
                            <code>python3 -c "import requests; [print(f'OSKYDDAD: {{i+1}}', requests.get('http://localhost:8080')) for i in range(20)]"</code>
                            <li>I terminal 2, kör:</li>
                            <code>python3 -c "import requests; [print(f'SKYDDAD: {{i+1}}', requests.get('http://localhost:8081')) for i in range(20)]"</code>
                            <li>Jämför resultaten! Oskyddad tar alla förfrågningar, skyddad blockerar vid överträdelse.</li>
                        </ol>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p><strong>🔧 Labb skapad för utbildningsändamål</strong></p>
                    <p>Demonstrerar skillnaden mellan skyddad och oskyddad server</p>
                </div>
            </div>
            
            <script>
            function startAttack(target, type) {{
                document.getElementById('attackResult').style.display = 'block';
                
                let attackName = "Normal attack";
                let duration = 5;
                
                if (type === 'slowloris') {{
                    attackName = "Slowloris attack";
                    duration = 10;
                }} else if (type === 'flood') {{
                    attackName = "Flood attack";
                    duration = 8;
                }} else if (type === 'mixed') {{
                    attackName = "Blandad attack";
                    duration = 12;
                }} else if (type === 'comparison') {{
                    attackName = "Jämförelseattack";
                    duration = 15;
                }}
                
                document.getElementById('resultDetails').innerHTML = 
                    '<p>🚀 Startar ' + attackName + ' mot ' + target + ' server...</p>' +
                    '<p>Attacken pågår i ' + duration + ' sekunder...</p>' +
                    '<div style="width: 100%; background: #ddd; border-radius: 5px; margin: 10px 0;">' +
                    '<div id="progressBar" style="width: 0%; height: 20px; background: #3498db; border-radius: 5px; transition: width 0.5s;"></div>' +
                    '</div>';
                
                // Simulera attack med förlopp
                let progress = 0;
                let progressInterval = setInterval(() => {{
                    progress += 100/duration;
                    document.getElementById('progressBar').style.width = Math.min(progress, 100) + '%';
                }}, 1000);
                
                // Slutför attacken
                setTimeout(() => {{
                    clearInterval(progressInterval);
                    
                    // Simulerade resultat baserat på attacktyp
                    let unprotectedSuccess, protectedSuccess, protectedBlocked;
                    
                    if (target === 'unprotected' || target === 'both') {{
                        unprotectedSuccess = 85 + Math.floor(Math.random() * 15);
                    }} else {{
                        unprotectedSuccess = 0;
                    }}
                    
                    if (target === 'protected' || target === 'both') {{
                        if (type === 'slowloris') {{
                            protectedSuccess = 25 + Math.floor(Math.random() * 20);
                            protectedBlocked = 75 + Math.floor(Math.random() * 20);
                        }} else if (type === 'flood') {{
                            protectedSuccess = 15 + Math.floor(Math.random() * 15);
                            protectedBlocked = 85 + Math.floor(Math.random() * 15);
                        }} else {{
                            protectedSuccess = 30 + Math.floor(Math.random() * 25);
                            protectedBlocked = 70 + Math.floor(Math.random() * 25);
                        }}
                    }} else {{
                        protectedSuccess = 0;
                        protectedBlocked = 0;
                    }}
                    
                    let resultHTML = '<h4>✅ ATTACK AVSLUTAD</h4>';
                    
                    if (target === 'unprotected' || target === 'both') {{
                        resultHTML += '<p><strong>OSKYDDAD Server:</strong> ' + unprotectedSuccess + '/100 förfrågningar lyckades</p>';
                    }}
                    
                    if (target === 'protected' || target === 'both') {{
                        resultHTML += '<p><strong>SKYDDAD Server:</strong> ' + protectedSuccess + '/100 förfrågningar lyckades</p>';
                        resultHTML += '<p style="color: green;">🛡️ ' + protectedBlocked + ' förfrågningar BLOCKERADES av DDoS-skyddet!</p>';
                    }}
                    
                    if (target === 'both') {{
                        let difference = unprotectedSuccess - protectedSuccess;
                        let efficiency = Math.round((protectedBlocked / 100) * 100);
                        resultHTML += '<hr><p><strong>📊 SKILLNAD:</strong> ' + difference + ' förfrågningar</p>';
                        resultHTML += '<p><strong>🎯 SKYDDS EFFEKTIVITET:</strong> ' + efficiency + '%</p>';
                    }}
                    
                    resultHTML += '<p><small>Dessa är simulerade resultat. För riktiga tester, använd terminalkommandona ovan.</small></p>';
                    
                    document.getElementById('resultDetails').innerHTML = resultHTML;
                    
                    // Uppdatera sidan efter 3 sekunder för att visa nya statistik
                    setTimeout(() => {{ location.reload(); }}, 3000);
                    
                }}, duration * 1000);
            }}
            
            // Visa en alert med mer information om attacktyper
            function showAttackInfo() {{
                alert("Attacktyper:\\n\\n" +
                      "⚡ Normal: Standard DDoS-attack\\n" +
                      "🐌 Slowloris: Långsamma, långvariga anslutningar\\n" +
                      "🌊 Flood: Massor av snabba förfrågningar\\n" +
                      "🎭 Blandad: Kombination av olika tekniker");
            }}
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
    
    def generate_efficiency_message(self, stats):
        """Generera ett meddelande baserat på skillnader i statistik"""
        request_diff = stats['unprotected']['requests'] - stats['protected']['requests']
        
        if request_diff > 50:
            return '<p style="color: #27ae60;"><strong>✅ DDoS-skydd fungerar utmärkt!</strong></p>'
        elif request_diff > 20:
            return '<p style="color: #f39c12;"><strong>⚠️ Skydd fungerar, men testa med större attack</strong></p>'
        elif request_diff > 0:
            return '<p style="color: #e74c3c;"><strong>⚡ Skillnad syns, kör större attack för tydligare resultat</strong></p>'
        else:
            return '<p style="color: #3498db;"><strong>🔍 Kör en attack för att se skillnaden!</strong></p>'

# ============================================================================
# AVANCERADE ATTACK FUNKTIONER
# ============================================================================

def advanced_attack(target, name, attack_type="normal"):
    """Kör en mer avancerad attack med olika tekniker"""
    try:
        import requests
    except ImportError:
        print("Installerar requests...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    print(f"\n{'='*70}")
    print(f"⚡ {attack_type.upper()} ATTACK MOT {name}")
    print(f"{'='*70}")
    
    success = 0
    blocked = 0
    errors = 0
    total_requests = 0
    
    attack_configs = {
        "normal": {"requests": 50, "delay": 0.1, "threads": 1},
        "slowloris": {"requests": 30, "delay": 0.5, "threads": 1},
        "flood": {"requests": 100, "delay": 0.01, "threads": 1},
        "mixed": {"requests": 80, "delay": 0.05, "threads": 1}
    }
    
    config = attack_configs.get(attack_type, attack_configs["normal"])
    
    def make_request(request_num):
        nonlocal success, blocked, errors, total_requests
        try:
            r = requests.get(target, timeout=3)
            total_requests += 1
            
            if r.status_code == 200:
                success += 1
            elif r.status_code == 429:
                blocked += 1
            else:
                errors += 1
                
        except Exception as e:
            total_requests += 1
            errors += 1
        
        # Visa förlopp
        if request_num % 10 == 0:
            print(f"  {request_num}/{config['requests']} förfrågningar skickade...")
    
    # Utför attacken
    for i in range(config['requests']):
        make_request(i + 1)
        time.sleep(config['delay'])
    
    print(f"\n{'='*70}")
    print(f"📊 RESULTAT FÖR {name} ({attack_type}):")
    print(f"{'='*70}")
    print(f"• Totalt förfrågningar: {total_requests}")
    print(f"• Lyckade: {success}")
    print(f"• Blockerade: {blocked}")
    print(f"• Fel: {errors}")
    
    if blocked > 0:
        efficiency = (blocked / total_requests) * 100
        print(f"• Skyddseffektivitet: {efficiency:.1f}%")
    
    print(f"{'='*70}")
    
    return success, blocked, total_requests

def comparison_test():
    """Kör ett jämförelsetest med olika attacktyper"""
    print("\n" + "="*70)
    print("📊 KOMPLETT JÄMFÖRELSETEST")
    print("="*70)
    
    attack_types = ["normal", "slowloris", "flood", "mixed"]
    results = {}
    
    for attack_type in attack_types:
        print(f"\n▶️  Testar {attack_type} attack...")
        
        # Attackera oskyddad
        print(f"\n1. Attackera OSKYDDAD server ({attack_type})...")
        unprotected_results = advanced_attack("http://localhost:8080", "OSKYDDAD", attack_type)
        time.sleep(2)
        
        # Attackera skyddad
        print(f"\n2. Attackera SKYDDAD server ({attack_type})...")
        protected_results = advanced_attack("http://localhost:8081", "SKYDDAD", attack_type)
        time.sleep(3)
        
        results[attack_type] = {
            'unprotected': unprotected_results,
            'protected': protected_results
        }
    
    # Visa sammanfattning
    print("\n" + "="*70)
    print("📈 SAMMANFATTNING AV ALLA TEST")
    print("="*70)
    
    for attack_type, result in results.items():
        unprotected_success = result['unprotected'][0]
        protected_success = result['protected'][0]
        blocked = result['protected'][1]
        
        diff = unprotected_success - protected_success
        efficiency = (blocked / max(result['protected'][2], 1)) * 100
        
        print(f"\n{attack_type.upper()} ATTACK:")
        print(f"  • Oskyddad: {unprotected_success} lyckade")
        print(f"  • Skyddad:  {protected_success} lyckade")
        print(f"  • Blockerade: {blocked}")
        print(f"  • Skillnad: {diff} förfrågningar")
        print(f"  • Effektivitet: {efficiency:.1f}%")
    
    print("\n" + "="*70)
    print("💡 SLUTSATS:")
    print("="*70)
    print("• Oskyddad server: Tar ALLA förfrågningar, blir långsammare")
    print("• Skyddad server: Blockerar överskridningar, håller hastigheten")
    print("• DDoS-skydd fungerar som det ska!")
    print("="*70)

# ============================================================================
# HUVUDPROGRAM
# ============================================================================

def start_servers():
    """Startar alla servrar"""
    print("="*70)
    print("🎯 DDOS-LABB STARTAR")
    print("="*70)
    print("• Oskyddad Server: http://localhost:8080")
    print("• Skyddad Server:   http://localhost:8081")
    print("• Kontrollpanel:    http://localhost:8082")
    print("="*70)
    print("⚠️  Oskyddad: INGET skydd - tar ALLA förfrågningar")
    print("✅ Skyddad: Rate limiting 5/10s - blockar vid överskridning")
    print("="*70)
    
    def run_server(port, handler, name):
        with socketserver.TCPServer(("localhost", port), handler) as server:
            print(f"✅ {name} startad på port {port}")
            server.serve_forever()
    
    # Starta i trådar
    for port, handler, name in [
        (8080, SimpleUnprotectedHandler, "Oskyddad server"),
        (8081, SimpleProtectedHandler, "Skyddad server"),
        (8082, SimpleControlPanel, "Kontrollpanel")
    ]:
        t = threading.Thread(target=run_server, args=(port, handler, name), daemon=True)
        t.start()
        time.sleep(0.5)
    
    return True

def main():
    """Förbättrad huvudmeny"""
    print("\n" + "="*60)
    print("🔥 DDOS-TEST LABB - HUVUDMENY")
    print("="*60)
    print("Testa skillnaden mellan skyddad och oskyddad webbserver!")
    print("="*60)
    
    # Kontrollera att requests är installerat
    try:
        import requests
    except ImportError:
        print("Installerar requests bibliotek...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print("✅ Requests installerat!")
    
    servers_started = False
    
    while True:
        print("\n" + "="*60)
        print("MENYVAL:")
        print("="*60)
        print("1. 🚀 Starta alla servrar")
        print("2. ⚡ Testa normal attack mot OSKYDDAD")
        print("3. 🛡️ Testa normal attack mot SKYDDAD")
        print("4. 📊 Kör jämförelsetest (Båda servrar)")
        print("5. 🎭 Avancerade attacktyper")
        print("6. 📈 Visa statistik")
        print("7. 🌐 Öppna kontrollpanelen i webbläsare")
        print("8. ❌ Avsluta programmet")
        print("="*60)
        
        choice = input("Välj alternativ (1-8): ").strip()
        
        if choice == '1':
            servers_started = start_servers()
            print("\n✅ Alla servrar är nu igång!")
            print("Öppna webbläsare på: http://localhost:8082")
            print("\nTryck Enter för att återgå till menyn...")
            input()
            
        elif choice == '2':
            if not servers_started:
                print("\n⚠️  Starta servrarna först! (Välj alternativ 1)")
                continue
            print("\n⚡ ATTACK MOT OSKYDDAD SERVER")
            success, blocked, total = advanced_attack("http://localhost:8080", "OSKYDDAD SERVER", "normal")
            print(f"\n📊 RESULTAT: {success}/{total} förfrågningar lyckades")
            
        elif choice == '3':
            if not servers_started:
                print("\n⚠️  Starta servrarna först! (Välj alternativ 1)")
                continue
            print("\n🛡️ ATTACK MOT SKYDDAD SERVER")
            success, blocked, total = advanced_attack("http://localhost:8081", "SKYDDAD SERVER", "normal")
            print(f"\n📊 RESULTAT: {success}/{total} lyckades")
            print(f"   🛡️  {blocked} förfrågningar BLOCKERADES!")
            
        elif choice == '4':
            if not servers_started:
                print("\n⚠️  Starta servrarna först! (Välj alternativ 1)")
                continue
            print("\n📊 KOMPLETT JÄMFÖRELSETEST")
            comparison_test()
            
        elif choice == '5':
            if not servers_started:
                print("\n⚠️  Starta servrarna först! (Välj alternativ 1)")
                continue
            print("\n" + "="*60)
            print("🎭 AVANCERADE ATTACKTYPER")
            print("="*60)
            print("1. 🐌 Slowloris Attack (långsamma anslutningar)")
            print("2. 🌊 Flood Attack (massa förfrågningar)")
            print("3. 🎭 Blandad Attack (kombination)")
            print("4. 🔙 Tillbaka till huvudmenyn")
            print("="*60)
            
            attack_choice = input("Välj attacktyp (1-4): ").strip()
            
            if attack_choice == '1':
                print("\n🐌 SLOWLORIS ATTACK MOT BÅDA SERVAR")
                print("Simulerar långsamma, långvariga anslutningar...")
                success1, blocked1, total1 = advanced_attack("http://localhost:8080", "OSKYDDAD", "slowloris")
                time.sleep(2)
                success2, blocked2, total2 = advanced_attack("http://localhost:8081", "SKYDDAD", "slowloris")
                print(f"\n📊 SLOWLORIS RESULTAT:")
                print(f"• Oskyddad: {success1}/{total1} lyckades")
                print(f"• Skyddad:  {success2}/{total2} lyckades")
                print(f"• Blockerade: {blocked2}")
                
            elif attack_choice == '2':
                print("\n🌊 FLOOD ATTACK MOT BÅDA SERVAR")
                print("Simulerar massor av snabba förfrågningar...")
                success1, blocked1, total1 = advanced_attack("http://localhost:8080", "OSKYDDAD", "flood")
                time.sleep(2)
                success2, blocked2, total2 = advanced_attack("http://localhost:8081", "SKYDDAD", "flood")
                print(f"\n📊 FLOOD RESULTAT:")
                print(f"• Oskyddad: {success1}/{total1} lyckades")
                print(f"• Skyddad:  {success2}/{total2} lyckades")
                print(f"• Blockerade: {blocked2}")
                
            elif attack_choice == '3':
                print("\n🎭 BLANDAD ATTACK MOT BÅDA SERVAR")
                print("Simulerar kombination av olika attacktekniker...")
                success1, blocked1, total1 = advanced_attack("http://localhost:8080", "OSKYDDAD", "mixed")
                time.sleep(2)
                success2, blocked2, total2 = advanced_attack("http://localhost:8081", "SKYDDAD", "mixed")
                print(f"\n📊 BLANDAD ATTACK RESULTAT:")
                print(f"• Oskyddad: {success1}/{total1} lyckades")
                print(f"• Skyddad:  {success2}/{total2} lyckades")
                print(f"• Blockerade: {blocked2}")
                
            elif attack_choice == '4':
                continue
                
        elif choice == '6':
            stats = SimpleStats.get_stats()
            print("\n" + "="*60)
            print("📊 LIVE STATISTIK")
            print("="*60)
            print(f"OSKYDDAD Server:")
            print(f"  • Förfrågningar: {stats['unprotected']['requests']}")
            print(f"  • Medelsvarstid: {stats['unprotected']['avg_time']}s")
            print(f"\nSKYDDAD Server:")
            print(f"  • Förfrågningar: {stats['protected']['requests']}")
            print(f"  • Medelsvarstid: {stats['protected']['avg_time']}s")
            
            diff = stats['unprotected']['requests'] - stats['protected']['requests']
            if diff > 0:
                print(f"\n📈 SKILLNAD: {diff} förfrågningar")
                print("   (Oskyddad har tagit fler förfrågningar)")
            print("="*60)
            
        elif choice == '7':
            if servers_started:
                print("\n🌐 Öppnar kontrollpanelen...")
                print("Gå till: http://localhost:8082")
                print("Eller tryck Ctrl+Click på länken ovan")
            else:
                print("\n⚠️  Starta servrarna först! (Välj alternativ 1)")
                
        elif choice == '8':
            print("\n👋 Avslutar DDOS-LABB...")
            print("Tack för att du testade!")
            break
            
        else:
            print("\n❌ Ogiltigt val. Välj ett nummer mellan 1-8.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Avslutas...")
    except Exception as e:
        print(f"\n❌ Fel: {e}")
        import traceback
        traceback.print_exc()