from flask import Flask, request, render_template_string, session, redirect, url_for
import sqlite3
import html

app = Flask(__name__)
app.secret_key = 'en_hemlig_nyckel'

# ==================== DATABAS ====================
def init_database():
    conn = sqlite3.connect('folkhalsa.db', check_same_thread=False)
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
        ]
        cursor.executemany("INSERT INTO region_statistik (region, kategori, värde, år) VALUES (?, ?, ?, ?)", data)
        
        cursor.executemany("INSERT INTO användare (personnummer, namn, epost) VALUES (?, ?, ?)",
                          [('199001011234', 'Anna Andersson', 'anna.andersson@example.com'),
                           ('198502029876', 'Bo Bengtsson', 'bo.bengtsson@example.com')])
    
    conn.commit()
    return conn

db = init_database()

# ==================== HTML-MALL (ENKLARE & TYDLIGARE) ====================
BASE_HTML = '''
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <title>Folkhälsoportalen - Demo</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; padding: 20px; background: #f0f4f8; color: #333; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        header { background: #0067B3; color: white; padding: 25px; border-radius: 10px 10px 0 0; margin: -30px -30px 30px -30px; }
        h1 { margin: 0; font-size: 28px; }
        h2 { color: #0067B3; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        h3 { color: #444; }
        .menu { display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; }
        .menu a { background: #e6f2ff; color: #0067B3; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #b3d9ff; }
        .menu a:hover { background: #cce5ff; }
        .test-area { background: #fff9e6; border-left: 4px solid #ff9900; padding: 20px; margin: 25px 0; border-radius: 4px; }
        .test-area h3 { color: #b35900; margin-top: 0; }
        .danger { background: #ffe6e6; border-left: 4px solid #cc0000; }
        .danger h3 { color: #990000; }
        .safe { background: #e6ffe6; border-left: 4px solid #009900; }
        input[type="text"], textarea { width: 100%; padding: 12px; margin: 8px 0 20px 0; border: 2px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box; }
        button { background: #0067B3; color: white; border: none; padding: 14px 28px; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #005293; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f0f8ff; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.9em; }
        .alert { background: #fff4e5; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .error { background: #ffe6e6; color: #990000; padding: 15px; border-radius: 6px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🇸🇪 Folkhälsoportalen - Säkerhetsdemo</h1>
            <p><strong>Offentlig statistik och information för Sveriges invånare</strong></p>
        </header>
        
        <div class="menu">
            <a href="/">🏠 Hem</a>
            <a href="/statistik">📊 Sök statistik</a>
            <a href="/kontakt">📩 Kontakta oss</a>
            <a href="/admin">🔐 Admin (intern)</a>
        </div>
        
        <main>
            {% if page_content %}
                {{ page_content|safe }}
            {% else %}
                <p>Välj en funktion från menyn ovan.</p>
            {% endif %}
        </main>
        
        <div class="footer">
            <p>Folkhälsoportalen • En säkerhetsdemo för utbildning • <strong>INNEHÅLLER AVSIKTLIGA SÄKERHETSHÅL</strong></p>
        </div>
    </div>
</body>
</html>
'''

# ==================== ROUTES ====================
@app.route('/')
def hem():
    content = '''
    <h2>Välkommen till säkerhetsdemosajten</h2>
    <p>Den här sajten simulerar en offentlig portal med <strong>avsiktliga säkerhetshål</strong>.</p>
    
    <div class="test-area">
        <h3>🎯 Testa dessa attacker:</h3>
        <ol>
            <li><strong>SQL-injektion:</strong> Gå till <a href="/statistik">Sök statistik</a> och skriv: <code>' OR 1=1 --</code></li>
            <li><strong>XSS (Reflected):</strong> Gå till <a href="/kontakt">Kontakta oss</a> och skriv: <code>&lt;script&gt;alert('XSS')&lt;/script&gt;</code> i namn-fältet</li>
            <li><strong>XSS (Persistent):</strong> Gå till <a href="/kontakt">Kontakta oss</a> och skriv: <code>&lt;img src=x onerror="alert('Stored')"&gt;</code> i meddelande-fältet</li>
            <li><strong>SQL-injektion (känslig data):</strong> Logga in på <a href="/admin">Admin</a> och sök: <code>' UNION SELECT * FROM användare --</code></li>
        </ol>
    </div>
    '''
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/statistik', methods=['GET', 'POST'])
def statistik():
    content = '<h2>📊 Sök i folkhälsostatistik</h2>'
    
    if request.method == 'POST':
        region = request.form.get('region', '')
        
        if region:
            content += f'<div class="test-area danger">'
            content += f'<h3>⚡ Testområde (Sårbart)</h3>'
            
            # ⚠️ SÅRBAR SQL-INJEKTION
            sql = f"SELECT * FROM region_statistik WHERE region = '{region}'"
            content += f"<p><strong>SQL-fråga som körs:</strong><br><code>{html.escape(sql)}</code></p>"
            
            try:
                cursor = db.cursor()
                cursor.execute(sql)  # ⚠️ Sårbar rad!
                resultat = cursor.fetchall()
                
                if resultat:
                    content += f"<h4>Hittade {len(resultat)} resultat:</h4>"
                    content += '<table><tr><th>Region</th><th>Kategori</th><th>Värde</th><th>År</th></tr>'
                    for rad in resultat:
                        content += f'<tr><td>{rad[1]}</td><td>{rad[2]}</td><td>{rad[3]}</td><td>{rad[4]}</td></tr>'
                    content += '</table>'
                else:
                    content += '<p>Ingen statistik hittades.</p>'
                    
            except Exception as e:
                content += f'<div class="error">Databasfel: {html.escape(str(e))}</div>'
            
            content += '</div>'
    
    content += '''
    <div class="test-area">
        <h3>Testa SQL-injektion här:</h3>
        <form method="POST">
            <label for="region"><strong>Ange regionnamn:</strong></label>
            <input type="text" id="region" name="region" placeholder="T.ex. 'Stockholm' eller 'Skåne'" value="Stockholm">
            <button type="submit">🔍 Sök statistik</button>
        </form>
        <p><strong>Test-exempel att kopiera:</strong></p>
        <ul>
            <li><code>Stockholm</code> - Normal sökning</li>
            <li><code>' OR 1=1 --</code> - Visa ALL statistik</li>
            <li><code>' UNION SELECT id, personnummer, namn, epost FROM användare --</code> - Stjäl användardata</li>
        </ul>
    </div>
    '''
    
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/kontakt', methods=['GET', 'POST'])
def kontakt():
    content = '<h2>📩 Kontakta oss</h2>'
    
    if request.method == 'POST':
        namn = request.form.get('namn', '')
        meddelande = request.form.get('meddelande', '')
        
        if namn and meddelande:
            cursor = db.cursor()
            cursor.execute("INSERT INTO kontakt_meddelanden (namn, meddelande) VALUES (?, ?)", (namn, meddelande))
            db.commit()
            
            # ⚠️ SÅRBAR XSS (Reflected)
            content += f'''
            <div class="test-area danger">
                <h3>⚡ Testresultat (Sårbart för XSS)</h3>
                <p><strong>Tack för ditt meddelande, {namn}!</strong></p>
                <p>Du skrev: "{meddelande}"</p>
                <p><em>OBS: Om du skrev skript-kod (t.ex. &lt;script&gt;...) visas den inte här, men den KÖRS i webbläsaren!</em></p>
            </div>
            '''
    
    content += '''
    <div class="test-area">
        <h3>Testa XSS (Cross-Site Scripting) här:</h3>
        <form method="POST">
            <label for="namn"><strong>Ditt namn:</strong></label>
            <input type="text" id="namn" name="namn" placeholder="Ange namn här" value="Testanvändare">
            
            <label for="meddelande"><strong>Ditt meddelande:</strong></label>
            <textarea id="meddelande" name="meddelande" rows="4" placeholder="Skriv ditt meddelande här">Det här är ett testmeddelande.</textarea>
            
            <button type="submit">✉️ Skicka meddelande</button>
        </form>
        
        <p><strong>Test-exempel att kopiera:</strong></p>
        <ul>
            <li>För Reflected XSS (i namn-fältet):<br>
                <code>&lt;script&gt;alert("Hackad!")&lt;/script&gt;</code></li>
            <li>För Persistent XSS (i meddelande-fältet):<br>
                <code>&lt;img src=x onerror="alert('Lagrad XSS!')"&gt;</code></li>
        </ul>
    </div>
    '''
    
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/admin')
def admin():
    if 'inloggad' not in session:
        return redirect(url_for('inloggning'))
    
    sökterm = request.args.get('sök', '')
    content = '<h2>🔐 Administrativ sökning (intern)</h2>'
    content += '<div class="test-area danger">'
    content += '<h3>⚡ Sårbar för SQL-injektion med känslig data</h3>'
    
    if sökterm:
        # ⚠️ SÅRBAR SQL-INJEKTION (med känslig data)
        sql = f"SELECT * FROM användare WHERE namn LIKE '%{sökterm}%' OR personnummer LIKE '%{sökterm}%'"
        content += f"<p><strong>SQL-fråga som körs:</strong><br><code>{html.escape(sql)}</code></p>"
        
        try:
            cursor = db.cursor()
            cursor.execute(sql)  # ⚠️ Sårbar rad!
            resultat = cursor.fetchall()
            
            if resultat:
                content += f"<h4>Hittade {len(resultat)} användare:</h4>"
                content += '<table><tr><th>Personnummer</th><th>Namn</th><th>E-post</th></tr>'
                for rad in resultat:
                    content += f'<tr><td>{rad[1]}</td><td>{rad[2]}</td><td>{rad[3]}</td></tr>'
                content += '</table>'
            else:
                content += '<p>Inga användare hittades.</p>'
                
        except Exception as e:
            content += f'<div class="error">Databasfel: {html.escape(str(e))}</div>'
    
    content += '''
    <form method="GET">
        <label for="sök"><strong>Sök användare (namn eller personnummer):</strong></label>
        <input type="text" id="sök" name="sök" placeholder="T.ex. 'Andersson' eller '19900101'">
        <button type="submit">🔍 Sök</button>
    </form>
    <p><strong>Test-exempel:</strong> <code>' UNION SELECT * FROM användare --</code></p>
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
        <h2>🔐 Inloggning för administratörer</h2>
        <p><em>För denna demo: logga in genom att klicka på knappen nedan</em></p>
        <form method="POST">
            <button type="submit">✅ Logga in som administratör</button>
        </form>
        <p><small>Efter inloggning kan du gå till <a href="/admin">Admin-sidan</a> för att testa SQL-injektion med känslig data.</small></p>
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
    print("🚨 FOLKHÄLSOPORTALEN STARTAR (TYDLIGARE VERSION)")
    print("=" * 70)
    print("\n🌐 Öppna i webbläsare: http://127.0.0.1:5000")
    print("\n🎯 TESTVÄGAR:")
    print("1. SQL-injektion:      http://127.0.0.1:5000/statistik")
    print("2. XSS (reflected):    http://127.0.0.1:5000/kontakt")
    print("3. XSS (persistent):   http://127.0.0.1:5000/kontakt")
    print("4. Admin + SQLi:       http://127.0.0.1:5000/admin (logga in först)")
    print("\n💡 Appen skapar automatiskt: 'folkhalsa.db'")
    print("=" * 70)
    
    app.run(debug=True, use_reloader=False)