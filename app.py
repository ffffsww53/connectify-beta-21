import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'connectify_secret_99')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE DADOS ATUALIZADOS ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50))
    image = db.Column(db.String(500))
    text = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    author = db.Column(db.String(50))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

with app.app_context():
    db.create_all()

# --- INTERFACE (HTML) ---
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connectify v2.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-50 min-h-screen pb-10">
    <nav class="bg-white p-4 shadow-sm sticky top-0 z-50">
        <div class="max-w-2xl mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-black text-indigo-600 tracking-tighter">CONNECTIFY</h1>
            {% if session.get('user') %}
                <div class="flex items-center gap-4">
                    <span class="font-bold text-gray-600">@{{ session['user'] }}</span>
                    <a href="/logout" class="text-red-500 text-xs font-bold">SAIR</a>
                </div>
            {% endif %}
        </div>
    </nav>

    <div class="max-w-xl mx-auto px-4 mt-6">
        {% if not session.get('user') %}
            <div class="bg-white p-8 rounded-2xl shadow border text-center">
                <h2 class="text-xl font-bold mb-4">Bem-vindo de volta!</h2>
                <form method="POST" action="/login" class="space-y-4">
                    <input name="user" placeholder="Usuário" class="w-full border p-3 rounded-xl outline-none focus:ring-2 ring-indigo-500" required>
                    <input name="pass" type="password" placeholder="Senha (Admin)" class="w-full border p-3 rounded-xl outline-none focus:ring-2 ring-indigo-500">
                    <button class="w-full bg-indigo-600 text-white py-3 rounded-xl font-bold">Entrar</button>
                </form>
            </div>
        {% else %}
            <div class="bg-white p-4 rounded-2xl shadow-sm border mb-8">
                <form method="POST" action="/post">
                    <textarea name="txt" placeholder="O que você está pensando?" class="w-full border-none focus:ring-0 text-lg" required></textarea>
                    <input name="img" placeholder="URL da foto (opcional)" class="w-full bg-gray-50 border p-2 rounded-lg text-xs mb-4 outline-none">
                    <button class="w-full bg-indigo-600 text-white py-2 rounded-full font-bold">Publicar</button>
                </form>
            </div>

            {% for post in posts %}
            <div class="bg-white rounded-2xl shadow-sm border mb-6 overflow-hidden">
                <div class="p-4 flex justify-between">
                    <span class="font-bold text-indigo-600">@{{ post.author }}</span>
                    {% if session.get('is_admin') %}
                        <a href="/del/{{ post.id }}" class="text-red-400 text-xs font-bold">DELETAR</a>
                    {% endif %}
                </div>
                
                {% if post.image %}<img src="{{ post.image }}" class="w-full border-y">{% endif %}
                
                <div class="p-4">
                    <p class="text-gray-800 mb-4">{{ post.text }}</p>
                    
                    <div class="flex items-center gap-4 text-gray-500 text-sm mb-4">
                        <a href="/like/{{ post.id }}" class="hover:text-red-500 flex items-center gap-1">
                            <i class="fa-solid fa-heart text-red-400"></i> {{ post.likes }}
                        </a>
                        <span class="flex items-center gap-1"><i class="fa-regular fa-comment"></i> {{ post.comments|length }}</span>
                    </div>

                    <div class="bg-gray-50 rounded-xl p-3 space-y-2">
                        {% for com in post.comments %}
                            <div class="text-xs">
                                <span class="font-bold text-gray-700">{{ com.author }}:</span> {{ com.text }}
                            </div>
                        {% endfor %}
                        <form method="POST" action="/comment/{{ post.id }}" class="mt-2 flex gap-2">
                            <input name="com_txt" placeholder="Comentar..." class="flex-1 bg-white border-none text-xs p-2 rounded-lg outline-none focus:ring-1 ring-indigo-400" required>
                            <button class="text-indigo-600 font-bold text-xs">Enviar</button>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROTAS ---

@app.route('/')
def home():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template_string(HTML, posts=posts)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user').strip()
    password = request.form.get('pass')
    session['user'] = user
    session['is_admin'] = (user.lower() == 'admin' and password == 'batima')
    return redirect('/')

@app.route('/post', methods=['POST'])
def post():
    if not session.get('user'): return redirect('/')
    new = Post(author=session['user'], image=request.form.get('img'), text=request.form.get('txt'))
    db.session.add(new)
    db.session.commit()
    return redirect('/')

@app.route('/like/<int:id>')
def like(id):
    post = Post.query.get(id)
    if post:
        post.likes += 1
        db.session.commit()
    return redirect('/')

@app.route('/comment/<int:id>', methods=['POST'])
def comment(id):
    if not session.get('user'): return redirect('/')
    txt = request.form.get('com_txt')
    if txt:
        new_com = Comment(text=txt, author=session['user'], post_id=id)
        db.session.add(new_com)
        db.session.commit()
    return redirect('/')

@app.route('/del/<int:id>')
def delete(id):
    if session.get('is_admin'):
        post = Post.query.get(id)
        db.session.delete(post)
        db.session.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
