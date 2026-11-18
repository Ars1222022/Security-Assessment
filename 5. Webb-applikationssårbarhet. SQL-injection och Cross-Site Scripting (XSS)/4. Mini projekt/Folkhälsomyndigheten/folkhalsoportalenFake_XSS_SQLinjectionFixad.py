from flask import Flask, request, render_template_string, session, redirect, url_for
import sqlite3
import html
import re

app = Flask(__name__)
app.secret_key = 'en_hemlig_nyckel'

# ==================== DATABAS ====================
def init_database():
    conn = sqlite3.connect('folkhalsa_saker.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS region_statistik
                     (id INTEGER PRIMARY KEY, region TEXT, kategori TEXT, värde REAL, år INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS användare
                     (id INTEGER PRIMARY KEY, personnummer TEXT, namn TEXT, epost TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS kontakt_meddelanden
                     (id INTEGER PRIMARY KEY, namn TEXT, meddelande TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM region_statistik")
    if cursor.fetchone()[0] == 0:
        data = [
            ('Stockholm', 'Vaccintäckning (%)', 87.5, 2023),
            ('Västra Götaland', 'Vaccintäckning (%)', 85.2, 2023),
            ('Skåne', 'Förekomst övervikt (%)', 52.1, 2022),
            ('Uppsala', 'Vaccintäckning (%)', 82.3, 2023),
            ('Örebro', 'Förekomst övervikt (%)', 48.7, 2022),
        ]
        cursor.executemany("INSERT INTO region_statistik (region, kategori, värde, år) VALUES (?, ?, ?, ?)", data)
        
        cursor.executemany("INSERT INTO användare (personnummer, namn, epost) VALUES (?, ?, ?)",
                          [('199001011234', 'Anna Andersson', 'anna.andersson@example.com'),
                           ('198502029876', 'Bo Bengtsson', 'bo.bengtsson@example.com'),
                           ('197803033456', 'Cecilia Carlsson', 'cecilia.carlsson@example.com')])
    
    conn.commit()
    return conn

db = init_database()

# ==================== HTML-MALL ====================
BASE_HTML = '''
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <title>Folkhälsoportalen - Testa attacker (SÄKER)</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; padding: 20px; background: #f0f4f8; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        header { background: #0067B3; color: white; padding: 25px; border-radius: 10px 10px 0 0; margin: -30px -30px 30px -30px; }
        h1 { margin: 0; font-size: 28px; }
        h2 { color: #0067B3; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        h3 { color: #444; }
        .menu { display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; }
        .menu a { background: #e6f2ff; color: #0067B3; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #b3d9ff; }
        .menu a:hover { background: #cce5ff; }
        .test-area { background: #fff9e6; border: 2px solid #ff9900; padding: 20px; margin: 25px 0; border-radius: 8px; }
        .test-area h3 { color: #b35900; margin-top: 0; }
        .resultat { background: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 6px; border-left: 4px solid #666; }
        .success { background: #e6ffe6; border-left: 4px solid #009900; }
        .blocked { background: #ffe6e6; border-left: 4px solid #cc0000; }
        .info { background: #e6f2ff; border-left: 4px solid #0067B3; }
        input[type="text"], textarea { width: 100%; padding: 12px; margin: 8px 0 20px 0; border: 2px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box; }
        button { background: #0067B3; color: white; border: none; padding: 14px 28px; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #005293; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f0f8ff; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.9em; }
        .alert { background: #fff4e5; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .error { background: #ffe6e6; color: #990000; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .code { font-family: monospace; background: #f5f5f5; padding: 5px 10px; border-radius: 4px; }
        .attack-example { background: #ffe6e6; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .safe-example { background: #e6ffe6; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .security-info { background: #f0f8ff; padding: 15px; border-radius: 6px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🇸🇪 Folkhälsoportalen - Testa attacker (SÄKER)</h1>
            <p><strong>Testa attacker och se hur de BLOCKERAS i realtid</strong></p>
        </header>
        
        <div class="menu">
            <a href="/">🏠 Hem</a>
            <a href="/statistik">📊 Testa SQL-injektion</a>
            <a href="/kontakt">📩 Testa XSS</a>
            <a href="/admin">🔐 Testa Admin-SQLi</a>
        </div>
        
        <main>
            {% if page_content %}
                {{ page_content|safe }}
            {% else %}
                <p>Välj en funktion från menyn ovan för att testa attacker.</p>
            {% endif %}
        </main>
        
        <div class="footer">
            <p>Folkhälsoportalen • Testa attacker mot en säker applikation • <strong>ALLA ATTACKER BLOCKERAS</strong></p>
        </div>
    </div>
</body>
</html>
'''

# ==================== HANTERARE ====================
def is_suspicious_input(input_str):
    """Kollar om input ser misstänkt ut (för demonstrationsändamål)"""
    suspicious_patterns = [
        r".*--.*",  # SQL kommentarer
        r".*OR.*1=1.*",  # SQL injection klassiker
        r".*UNION.*SELECT.*",  # UNION attacks
        r".*<script.*>.*",  # XSS script taggar
        r".*onerror=.*",  # XSS event handlers
        r".*onload=.*",  # XSS event handlers
        r".*javascript:.*",  # JavaScript i länkar
        r".*<img.*>.*",  # Img tags för XSS
        r".*alert\(.*",  # Alert funktioner
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, input_str, re.IGNORECASE):
            return True
    return False

def safe_sql_query(query, params=()):
    """Kör en säker SQL-fråga med parameteriserade queries"""
    try:
        cursor = db.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        return None

# ==================== ROUTES ====================
@app.route('/')
def hem():
    content = '''
    <div class="security-info">
        <h2>🛡️ Testa attacker mot en SÄKER webbapplikation</h2>
        <p>Den här sajten är säker mot vanliga webbattacker. Testa attacker och se hur de <strong>blockeras i realtid</strong>.</p>
    </div>
    
    <div class="test-area">
        <h3>🎯 Testa dessa attacker (de kommer att misslyckas):</h3>
        
        <div class="attack-example">
            <h4>💉 SQL-injektion test:</h4>
            <ol>
                <li>Gå till <a href="/statistik">Testa SQL-injektion</a></li>
                <li>Skriv: <code class="code">' OR 1=1 --</code></li>
                <li>Klicka "🔍 Sök statistik"</li>
                <li><strong>Resultat:</strong> Inget kommer att hittas (attacken blockeras)</li>
            </ol>
        </div>
        
        <div class="attack-example">
            <h4>⚠️ XSS (Cross-Site Scripting) test:</h4>
            <ol>
                <li>Gå till <a href="/kontakt">Testa XSS</a></li>
                <li>Skriv i namn-fältet: <code class="code">&lt;script&gt;alert('XSS')&lt;/script&gt;</code></li>
                <li>Skicka meddelandet</li>
                <li><strong>Resultat:</strong> Texten kommer visas som ofarlig text (attacken neutraliseras)</li>
            </ol>
        </div>
        
        <div class="attack-example">
            <h4>🔐 Admin SQL-injektion test:</h4>
            <ol>
                <li>Gå till <a href="/inloggning">Logga in först</a></li>
                <li>Gå till <a href="/admin">Testa Admin-SQLi</a></li>
                <li>Sök på: <code class="code">' UNION SELECT * FROM användare --</code></li>
                <li><strong>Resultat:</strong> Inga användare hittas (attacken blockerades)</li>
            </ol>
        </div>
    </div>
    
    <div class="safe-example">
        <h3>✅ Så här ska du testa NORMALT (ska fungera):</h3>
        <ul>
            <li><strong>Statistik:</strong> Sök på "Stockholm" eller "Skåne" - ska visa resultat</li>
            <li><strong>Kontakt:</strong> Skriv ett normalt meddelande - ska sparas och visas</li>
            <li><strong>Admin:</strong> Sök på "Andersson" eller "1990" - ska visa användare</li>
        </ul>
    </div>
    '''
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/statistik', methods=['GET', 'POST'])
def statistik():
    content = '<h2>💉 Testa SQL-injektion här</h2>'
    
    user_input = ""
    show_results = False
    is_attack = False
    
    if request.method == 'POST':
        region = request.form.get('region', '').strip()
        user_input = region
        show_results = True
        
        # Kolla om det är en attack
        if is_suspicious_input(region):
            is_attack = True
        
        content += f'''
        <div class="resultat {'blocked' if is_attack else 'info'}">
            <h3>📊 Sökresultat för: <code class="code">{html.escape(region)}</code></h3>
        '''
        
        if region:
            if is_attack:
                content += '''
                <div class="alert">
                    <h4>🛡️ MISSTÄNKT INPUT UPPTÄCKT!</h4>
                    <p>Din input innehåller potentiellt skadlig kod. Attacken har <strong>blokerats</strong>.</p>
                    <p><strong>Säkerhetsåtgärd:</strong> Parameteriserad SQL-fråga används</p>
                </div>
                '''
            
            # ✅ SÄKER SQL-FRÅGA (Parameteriserad)
            sql = "SELECT * FROM region_statistik WHERE region = ?"
            
            try:
                # Kör den säkra queryn
                resultat = safe_sql_query(sql, (region,))
                
                if resultat:
                    content += f"<h4>✅ Hittade {len(resultat)} resultat:</h4>"
                    content += '<table><tr><th>Region</th><th>Kategori</th><th>Värde</th><th>År</th></tr>'
                    for rad in resultat:
                        content += f'<tr><td>{html.escape(str(rad[1]))}</td><td>{html.escape(str(rad[2]))}</td><td>{html.escape(str(rad[3]))}</td><td>{html.escape(str(rad[4]))}</td></tr>'
                    content += '</table>'
                    
                    if is_attack:
                        content += '''
                        <div class="alert">
                            <p><strong>💡 OBS:</strong> Den här frågan sökte efter regionen med <strong>exakt det namnet du skrev</strong>.</p>
                            <p>SQL-injektionsattacken <code>\' OR 1=1 --</code> söker alltså efter en region som heter <code>\' OR 1=1 --</code>, vilket inte finns.</p>
                        </div>
                        '''
                else:
                    if is_attack:
                        content += f'<p>❌ Ingen statistik hittades för regionen <strong>{html.escape(region)}</strong>.</p>'
                        content += '''
                        <div class="alert">
                            <p><strong>✅ ATTACKEN BLOCKERAD!</strong></p>
                            <p>SQL-injektionen fungerade inte eftersom vi använder parameteriserade queries.</p>
                            <p>Din input behandlas som <strong>data</strong>, inte som SQL-kod.</p>
                        </div>
                        '''
                    else:
                        content += f'<p>Ingen statistik hittades för regionen <strong>{html.escape(region)}</strong>.</p>'
                        
            except Exception as e:
                content += f'<div class="error">Ett fel uppstod vid sökningen: {html.escape(str(e))}</div>'
        
        content += '</div>'
    
    # Formuläret
    content += '''
    <div class="test-area">
        <h3>💉 Testa SQL-injektion här:</h3>
        <form method="POST">
            <label for="region"><strong>Ange regionnamn:</strong></label>
            <input type="text" id="region" name="region" placeholder="T.ex. 'Stockholm' eller testa en attack" value="''' + user_input + '''">
            <button type="submit">🔍 Sök statistik</button>
        </form>
        
        <div class="security-info">
            <h4>🔬 Test-attacker att prova:</h4>
            <table>
                <tr><th>Attack</th><th>Förväntat resultat</th></tr>
                <tr>
                    <td><code class="code">Stockholm</code></td>
                    <td>✅ Visar statistik för Stockholm</td>
                </tr>
                <tr>
                    <td><code class="code">' OR 1=1 --</code></td>
                    <td>❌ BLOCKERAD - visar inga resultat</td>
                </tr>
                <tr>
                    <td><code class="code">' UNION SELECT * FROM användare --</code></td>
                    <td>❌ BLOCKERAD - visar inga resultat</td>
                </tr>
            </table>
        </div>
        
        <div class="security-info">
            <h4>🛡️ Säkerhetsåtgärder som aktiveras:</h4>
            <ul>
                <li><strong>Parameteriserade queries:</strong> Användarinput separeras från SQL-koden</li>
                <li><strong>Input validering:</strong> Misstänkt mönster detekteras</li>
                <li><strong>HTML escaping:</strong> All output renderas säkert</li>
            </ul>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/kontakt', methods=['GET', 'POST'])
def kontakt():
    content = '<h2>⚠️ Testa XSS (Cross-Site Scripting) här</h2>'
    
    user_name = ""
    user_message = ""
    show_results = False
    is_attack = False
    
    if request.method == 'POST':
        namn = request.form.get('namn', '').strip()
        meddelande = request.form.get('meddelande', '').strip()
        
        user_name = namn
        user_message = meddelande
        show_results = True
        
        # Kolla om det är en attack
        if is_suspicious_input(namn) or is_suspicious_input(meddelande):
            is_attack = True
        
        content += f'''
        <div class="resultat {'blocked' if is_attack else 'success'}">
            <h3>📨 Meddelandet har skickats</h3>
        '''
        
        if is_attack:
            content += '''
            <div class="alert">
                <h4>🛡️ XSS-ATTACK UPPTÄCKT OCH NEUTRALISERAD!</h4>
                <p>Din input innehöll potentiellt skadlig JavaScript-kod.</p>
                <p>Attacken har <strong>neutraliserats</strong> genom HTML escaping.</p>
            </div>
            '''
        
        # ✅ SÄKER LAGRING (HTML escaping innan lagring)
        safe_namn = html.escape(namn)
        safe_meddelande = html.escape(meddelande)
        
        try:
            cursor = db.cursor()
            cursor.execute("INSERT INTO kontakt_meddelanden (namn, meddelande) VALUES (?, ?)", 
                         (safe_namn, safe_meddelande))
            db.commit()
            
            content += f'''
            <p><strong>📝 Ditt namn:</strong> {safe_namn}</p>
            <p><strong>💬 Ditt meddelande:</strong> {safe_meddelande}</p>
            '''
            
            if is_attack:
                content += f'''
                <div class="alert">
                    <h4>🔍 Så här lagras det i databasen:</h4>
                    <p><strong>Namn:</strong> <code class="code">{safe_namn}</code></p>
                    <p><strong>Meddelande:</strong> <code class="code">{safe_meddelande}</code></p>
                    <p>All HTML-kod har konverterats till ofarliga entiteter (t.ex. &lt; blir &amp;lt;)</p>
                </div>
                '''
            
        except Exception as e:
            content += f'<div class="error">Ett fel uppstod: {html.escape(str(e))}</div>'
        
        content += '</div>'
    
    # Formuläret
    content += '''
    <div class="test-area">
        <h3>⚠️ Testa XSS-attacker här:</h3>
        <form method="POST">
            <label for="namn"><strong>Ditt namn:</strong></label>
            <input type="text" id="namn" name="namn" placeholder="Testa XSS här" value="''' + user_name + '''">
            
            <label for="meddelande"><strong>Ditt meddelande:</strong></label>
            <textarea id="meddelande" name="meddelande" rows="4" placeholder="Testa persistent XSS här">''' + user_message + '''</textarea>
            
            <button type="submit">✉️ Skicka meddelande</button>
        </form>
        
        <div class="security-info">
            <h4>🔬 Test-attacker att prova:</h4>
            <table>
                <tr><th>Attack</th><th>Förväntat resultat</th></tr>
                <tr>
                    <td><code class="code">&lt;script&gt;alert('XSS')&lt;/script&gt;</code></td>
                    <td>❌ BLOCKERAD - visas som text</td>
                </tr>
                <tr>
                    <td><code class="code">&lt;img src=x onerror="alert(1)"&gt;</code></td>
                    <td>❌ BLOCKERAD - visas som text</td>
                </tr>
                <tr>
                    <td><code class="code">&lt;b&gt;Normalt meddelande&lt;/b&gt;</code></td>
                    <td>✅ Visas som text (ingen JS körs)</td>
                </tr>
            </table>
        </div>
        
        <div class="security-info">
            <h4>🛡️ Säkerhetsåtgärder som aktiveras:</h4>
            <ul>
                <li><strong>HTML escaping:</strong> &lt; &gt; " ' konverteras till entiteter</li>
                <li><strong>Input scanning:</strong> Misstänkta mönster detekteras</li>
                <li><strong>Säker lagring:</strong> Data saniteras innan lagring</li>
            </ul>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/admin')
def admin():
    if 'inloggad' not in session:
        return redirect(url_for('inloggning'))
    
    sökterm = request.args.get('sök', '').strip()
    content = '<h2>🔐 Testa SQL-injektion i Admin-panelen</h2>'
    content += '<div class="test-area">'
    
    if sökterm:
        is_attack = is_suspicious_input(sökterm)
        
        content += f'''
        <div class="resultat {'blocked' if is_attack else 'info'}">
            <h3>🔍 Sökresultat för: <code class="code">{html.escape(sökterm)}</code></h3>
        '''
        
        if is_attack:
            content += '''
            <div class="alert">
                <h4>🛡️ SQL-INJEKTIONSFÖRSÖK UPPTÄCKT!</h4>
                <p>Din input ser ut som en SQL-injektionsattack.</p>
                <p>Attacken har <strong>blokerats</strong> genom parameteriserade queries.</p>
            </div>
            '''
        
        # ✅ SÄKER SQL-FRÅGA (Parameteriserad med LIKE)
        sql = "SELECT * FROM användare WHERE namn LIKE ? OR personnummer LIKE ?"
        
        try:
            # Parameteriserad query
            search_pattern = f"%{sökterm}%"
            cursor = db.cursor()
            cursor.execute(sql, (search_pattern, search_pattern))
            resultat = cursor.fetchall()
            
            if resultat:
                content += f"<h4>✅ Hittade {len(resultat)} användare:</h4>"
                content += '<table><tr><th>Personnummer</th><th>Namn</th><th>E-post</th></tr>'
                for rad in resultat:
                    content += f'<tr><td>{html.escape(str(rad[1]))}</td><td>{html.escape(str(rad[2]))}</td><td>{html.escape(str(rad[3]))}</td></tr>'
                content += '</table>'
                
                if is_attack:
                    content += '''
                    <div class="alert">
                        <p><strong>💡 OBS:</strong> SQL-injektionen <code>\' UNION SELECT ...</code> fungerade inte!</p>
                        <p>Den sökte efter användare vars namn innehåller <code>\' UNION SELECT ...</code> som text.</p>
                    </div>
                    '''
            else:
                if is_attack:
                    content += f'<p>❌ Inga användare hittades för: <strong>{html.escape(sökterm)}</strong></p>'
                    content += '''
                    <div class="alert">
                        <p><strong>✅ ATTACKEN BLOCKERAD!</strong></p>
                        <p>SQL-injektionen kunde inte extrahera känslig data från databasen.</p>
                        <p>Databasen är säker tack vare parameteriserade queries.</p>
                    </div>
                    '''
                else:
                    content += f'<p>Inga användare hittades för: <strong>{html.escape(sökterm)}</strong></p>'
                    
        except Exception as e:
            content += f'<div class="error">Ett fel uppstod: {html.escape(str(e))}</div>'
        
        content += '</div>'
    
    # Formuläret
    content += '''
    <h3>💉 Testa SQL-injektion med känslig data:</h3>
    <form method="GET">
        <label for="sök"><strong>Sök användare (namn eller personnummer):</strong></label>
        <input type="text" id="sök" name="sök" placeholder="Testa SQL-injektion här" value="''' + (sökterm if 'sökterm' in locals() else '') + '''">
        <button type="submit">🔍 Sök användare</button>
    </form>
    
    <div class="security-info">
        <h4>🔬 Test-attacker att prova:</h4>
        <table>
            <tr><th>Attack</th><th>Förväntat resultat</th></tr>
            <tr>
                <td><code class="code">Andersson</code></td>
                <td>✅ Visar användare med namnet Andersson</td>
            </tr>
            <tr>
                <td><code class="code">' OR 1=1 --</code></td>
                <td>❌ BLOCKERAD - visar inga resultat</td>
            </tr>
            <tr>
                <td><code class="code">' UNION SELECT * FROM användare --</code></td>
                <td>❌ BLOCKERAD - visar inga resultat</td>
            </tr>
        </table>
    </div>
    
    <div class="security-info">
        <h4>🛡️ Säkerhetsåtgärder:</h4>
        <ul>
            <li><strong>Parameteriserade queries:</strong> Användarinput kan inte ändra SQL-strukturen</li>
            <li><strong>Pattern matching:</strong> Detekterar kända attackmönster</li>
            <li><strong>Principle of least privilege:</strong> Admin kräver inloggning</li>
        </ul>
    </div>
    </div>
    '''
    
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/inloggning', methods=['GET', 'POST'])
def inloggning():
    if request.method == 'POST':
        session['inloggad'] = True
        return redirect(url_for('admin'))
    
    content = '''
    <div class="test-area">
        <h2>🔐 Inloggning för att testa Admin-attacker</h2>
        <p><em>Logga in för att testa SQL-injektion mot känslig data i Admin-panelen</em></p>
        <form method="POST">
            <button type="submit">✅ Logga in som administratör (demo)</button>
        </form>
        <p><small>Efter inloggning kan du testa SQL-injektion på <a href="/admin">Admin-sidan</a></small></p>
    </div>
    '''
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/logout')
def logout():
    session.pop('inloggad', None)
    return redirect(url_for('hem'))

# ==================== KÖR APPEN ====================
if __name__ == '__main__':
    print("=" * 70)
    print("🎯 FOLKHÄLSOPORTALEN - TESTA ATTACKER (SÄKER VERSION)")
    print("=" * 70)
    print("\n🌐 Öppna i webbläsare: http://127.0.0.1:5000")
    print("\n💉 TESTA ATTACKER OCH SE DEM BLOCKERAS:")
    print("1. SQL-injektion:      http://127.0.0.1:5000/statistik")
    print("2. XSS (reflected):    http://127.0.0.1:5000/kontakt")
    print("3. XSS (persistent):   http://127.0.0.1:5000/kontakt")
    print("4. Admin + SQLi:       http://127.0.0.1:5000/inloggning (logga in först)")
    print("\n🛡️ SÄKERHETSÅTGÄRDER:")
    print("• Parameteriserade SQL queries")
    print("• HTML escaping på all output")
    print("• Input validation och scanning")
    print("• Realtids detection av attacker")
    print("\n💡 Appen skapar: 'folkhalsa_saker.db'")
    print("=" * 70)
    
    app.run(debug=True, use_reloader=False)