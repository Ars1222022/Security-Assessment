from flask import Flask, request, render_template_string
import sqlite3
import html

app = Flask(__name__)

# HTML-mall - OBS: Använder enkla måsvingar {%%} och {{}}
BASE_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Sårbar Demo App</title>
<style>
    body { font-family: sans-serif; margin: 40px; }
    .result { background: #f0f0f0; padding: 15px; margin-top: 20px; }
    .error { color: red; }
    pre { background: #eee; padding: 10px; }
    .menu { margin-bottom: 30px; }
    .menu a { margin-right: 15px; }
</style>
</head>
<body>
    <div class="menu">
        <a href="/">Hem</a> | 
        <a href="/search?q=">Sök (SQLi)</a> | 
        <a href="/safe_search?q=">Säker Sök</a> | 
        <a href="/feedback">Feedback (XSS)</a>
    </div>
    
    <h1>🛒 Demo Webbshop (Sårbar)</h1>
    
    <!-- Dynamiskt innehåll kommer här -->
    {% if page_content %}
        {{ page_content|safe }}
    {% else %}
        <p>Välj en funktion från menyn ovan.</p>
    {% endif %}
</body>
</html>
'''

def init_database():
    """Skapar en databas med exempeldata."""
    conn = sqlite3.connect('demo.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Skapa tabeller
    cursor.execute('''CREATE TABLE IF NOT EXISTS products
                     (id INTEGER PRIMARY KEY, name TEXT, price REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback
                     (id INTEGER PRIMARY KEY, text TEXT)''')
    
    # Lägg till exempeldata om tabellerna är tomma
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products = [('Äpple', 12.50), ('Banan', 8.95), ('Mjölk', 15.75), ('Bröd', 28.90)]
        cursor.executemany("INSERT INTO products (name, price) VALUES (?, ?)", products)
        
        users = [('admin', 'superhemligt123'), ('alice', 'qwerty'), ('bob', 'password')]
        cursor.executemany("INSERT INTO users (username, password) VALUES (?, ?)", users)
    
    conn.commit()
    return conn

# Initiera databasen
db_connection = init_database()

@app.route('/')
def home():
    """Hemsida med instruktioner."""
    content = """
    <h2>Välkommen till säkerhetsdemo!</h2>
    
    <h3>1. Testa SQL Injection</h3>
    <p>Gå till <strong>Sök (SQLi)</strong> och prova:</p>
    <ul>
        <li><code>' OR 1=1--</code> - Visar alla produkter</li>
        <li><code>' UNION SELECT username, password FROM users--</code> - Stjäl användardata</li>
    </ul>
    
    <h3>2. Testa XSS (Cross-Site Scripting)</h3>
    <p>Gå till <strong>Feedback (XSS)</strong> och prova:</p>
    <ul>
        <li><code>&lt;script&gt;alert('XSS')&lt;/script&gt;</code></li>
        <li><code>&lt;img src=x onerror=alert('Hackad')&gt;</code></li>
    </ul>
    
    <h3>3. Jämför med säker sökning</h3>
    <p>Prova samma attacker i <strong>Säker Sök</strong> - de kommer inte fungera!</p>
    """
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/search')
def search():
    """SÅRBAR för SQL-injektion."""
    query = request.args.get('q', '')
    content = "<h2>🔓 Sårbar Sökning (SQL Injection Test)</h2>"
    
    if query:
        # ⚠️ KRITISKT SÅRBART: Direkt strängkonkatenering
        sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
        content += f"<p><strong>Kör SQL:</strong> <code>{html.escape(sql)}</code></p>"
        
        try:
            cursor = db_connection.cursor()
            cursor.execute(sql)  # ⚠️ Sårbar rad!
            results = cursor.fetchall()
            
            if results:
                content += "<h3>Resultat:</h3><ul>"
                for row in results:
                    content += f"<li><strong>{html.escape(str(row[1]))}</strong> - {row[2]} kr (ID: {row[0]})</li>"
                content += "</ul>"
            else:
                content += "<p>Inga produkter hittades.</p>"
        except Exception as e:
            content += f'<p class="error">Database fel: {html.escape(str(e))}</p>'
    else:
        content += """
        <form action="/search" method="GET">
            <input type="text" name="q" placeholder="Sök produkt..." size="40">
            <button type="submit">Sök</button>
        </form>
        <p><small>Testa: <code>' OR 1=1--</code> eller <code>apple' UNION SELECT username, password FROM users--</code></small></p>
        """
    
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """SÅRBAR för XSS."""
    content = "<h2>📝 Feedback (XSS Test)</h2>"
    
    if request.method == 'POST':
        text = request.form.get('text', '')
        
        if text:
            # Spara i databas (säker pga parameteriserad fråga)
            cursor = db_connection.cursor()
            cursor.execute("INSERT INTO feedback (text) VALUES (?)", (text,))
            db_connection.commit()
            
            # ⚠️ SÅRBART: Visar utan escaping
            content += f"<p><strong>Tack för din feedback!</strong></p>"
            content += f"<p>Du skrev: <blockquote>{text}</blockquote></p>"
            
            # Visa all feedback (också sårbar)
            cursor.execute("SELECT text FROM feedback ORDER BY id DESC")
            all_feedback = cursor.fetchall()
            
            if all_feedback:
                content += "<h4>All feedback:</h4><ul>"
                for fb in all_feedback:
                    content += f"<li>{fb[0]}</li>"  # ⚠️ XSS här!
                content += "</ul>"
    
    # Visa formuläret
    content += """
    <form method="POST">
        <textarea name="text" rows="4" cols="50" placeholder="Skriv din feedback här..."></textarea><br>
        <button type="submit">Skicka</button>
    </form>
    <p><small>Testa XSS: <code>&lt;script&gt;alert('XSS')&lt;/script&gt;</code></small></p>
    """
    
    return render_template_string(BASE_HTML, page_content=content)

@app.route('/safe_search')
def safe_search():
    """SÄKER version - parameteriserad fråga."""
    query = request.args.get('q', '')
    content = "<h2>✅ Säker Sökning</h2>"
    
    if query:
        # ✅ SÄKERT: Parameteriserad fråga
        sql = "SELECT * FROM products WHERE name LIKE ?"
        content += f"<p><strong>Kör SQL:</strong> <code>{html.escape(sql)}</code></p>"
        content += f"<p><strong>Söker efter:</strong> <code>%{html.escape(query)}%</code></p>"
        
        try:
            cursor = db_connection.cursor()
            cursor.execute(sql, (f'%{query}%',))  # ✅ Säker!
            results = cursor.fetchall()
            
            if results:
                content += "<h3>Resultat:</h3><ul>"
                for row in results:
                    content += f"<li><strong>{html.escape(str(row[1]))}</strong> - {row[2]} kr (ID: {row[0]})</li>"
                content += "</ul>"
            else:
                content += "<p>Inga produkter hittades.</p>"
        except Exception as e:
            content += f'<p class="error">Database fel: {html.escape(str(e))}</p>'
    else:
        content += """
        <form action="/safe_search" method="GET">
            <input type="text" name="q" placeholder="Sök produkt..." size="40">
            <button type="submit">Sök</button>
        </form>
        <p><small>Denna sida är säker - SQL injection kommer inte fungera här!</small></p>
        """
    
    return render_template_string(BASE_HTML, page_content=content)

if __name__ == '__main__':
    print("=" * 60)
    print("✅ Sårbar applikation startar...")
    print("🌐 Öppna: http://127.0.0.1:5000")
    print("=" * 60)
    print("\nTesta dessa attacker:")
    print("1. SQL Injection:  http://127.0.0.1:5000/search?q=' OR 1=1--")
    print("2. XSS:            Gå till /feedback och skriv <script>alert('XSS')</script>")
    print("3. Säker jämförelse: http://127.0.0.1:5000/safe_search?q=apple")
    print("\nDatabasfil: 'demo.db' skapas automatiskt")
    print("=" * 60)
    
    app.run(debug=True, use_reloader=False)