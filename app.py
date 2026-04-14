import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Em produção, o GitHub pede que segredos fiquem em variáveis de ambiente
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave_super_secreta_99')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectify.db'
db = SQLAlchemy(app)

# Senha do ADM (Mude aqui!)
ADMIN_PASSWORD = "Mudar123" 

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50))
    image = db.Column(db.String(500))
    text = db.Column(db.Text)

# --- TEMPLATE ÚNICO ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Connectify</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-white p-4 shadow-sm mb-6">
        <div class="max-w-2xl mx-auto flex justify-between">
            <h1 class="font-bold text-indigo-600">CONNECTIFY</h1>
            {% if session.get('user') %}
                <span>Olá, {{ session['user'] }} <a href="/logout" class="text-red-500 ml-2">Sair</a></span>
            {% endif %}
        </div>
    </nav>
    <div class="max-w-xl mx-auto p-4">
        {% if not session.get('user') %}
            <form method="POST" action="/login" class="bg-white p-6 rounded shadow">
                <input name="user" placeholder="Usuário" class="w-full border p-2 mb-2 rounded">
                <input name="pass" type="password" placeholder="Senha (apenas para admin)" class="w-full border p-2 mb-4 rounded">
                <button class="w-full bg-indigo-600 text-white p-2 rounded">Entrar</button>
            </form>
        {% else %}
            <form method="POST" action="/post" class="bg-white p-4 rounded shadow mb-6">
                <input name="img" placeholder="URL da Imagem" class="w-full border p-2 mb-2 text-sm">
                <textarea name="txt" placeholder="O que novo?" class="w-full border p-2 rounded"></textarea>
                <button class="w-full bg-indigo-600 text-white p-2 mt-2 rounded">Postar</button>
            </form>
            {% for post in posts %}
                <div class="bg-white rounded shadow mb-4 overflow-hidden">
                    <div class="p-3 font-bold border-b flex justify-between">
                        @{{ post.author }}
                        {% if session.get('is_admin') %}
                            <a href="/del/{{ post.id }}" class="text-red-500 text-xs">APAGAR</a>
                        {% endif %}
                    </div>
                    {% if post.image %}<img src="{{ post.image }}" class="w-full">{% endif %}
                    <p class="p-4">{{ post.text }}</p>
                </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template_string(HTML, posts=posts)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    password = request.form.get('pass')
    
    if user.lower() == 'admin':
        if password == ADMIN_PASSWORD:
            session['user'] = 'Admin'
            session['is_admin'] = True
        else:
            return "Senha de Admin incorreta!", 403
    else:
        session['user'] = user
        session['is_admin'] = False
    return redirect('/')

@app.route('/post', methods=['POST'])
def post():
    if not session.get('user'): return redirect('/')
    new = Post(author=session['user'], image=request.form.get('img'), text=request.form.get('txt'))
    db.session.add(new)
    db.session.commit()
    return redirect('/')

@app.route('/del/<int:id>')
def delete(id):
    if not session.get('is_admin'): return "Negado", 403
    p = Post.query.get(id)
    db.session.delete(p)
    db.session.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)