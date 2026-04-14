import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_ultra_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectify_v3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    bio = db.Column(db.String(150), default="Explorando o Connectify!")
    is_verified = db.Column(db.Boolean, default=False)

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

# --- INTERFACE ---
HTML = """
<!DOCTYPE html>
<html lang="pt-br" :class="darkMode ? 'dark' : ''" x-data="{ darkMode: false }">
<head>
    <meta charset="UTF-8">
    <title>Connectify Ultra</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script>
        tailwind.config = { darkMode: 'class' }
    </script>
</head>
<body class="bg-gray-50 dark:bg-gray-900 transition-colors duration-300 min-h-screen">
    <nav class="bg-white dark:bg-gray-800 p-4 shadow-sm sticky top-0 z-50 border-b dark:border-gray-700">
        <div class="max-w-4xl mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-black text-indigo-600 tracking-tighter">CONNECTIFY</h1>
            <div class="flex items-center gap-4">
                <button @click="darkMode = !darkMode" class="text-gray-500 dark:text-gray-400">
                    <i :class="darkMode ? 'fa-solid fa-sun' : 'fa-solid fa-moon'"></i>
                </button>
                {% if session.get('user') %}
                    <span class="font-bold text-gray-700 dark:text-gray-200">@{{ session['user'] }}</span>
                    <a href="/logout" class="text-red-500 text-xs font-bold">SAIR</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 p-4">
        <div class="hidden md:block space-y-4">
            {% if session.get('user') %}
            <div class="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border dark:border-gray-700">
                <p class="font-bold dark:text-white">Seu Perfil</p>
                <p class="text-xs text-gray-500 mb-2 italic">"{{ user_info.bio }}"</p>
                <form action="/update_bio" method="POST">
                    <input name="new_bio" placeholder="Nova bio..." class="text-xs w-full p-2 border rounded dark:bg-gray-700 dark:text-white dark:border-gray-600">
                </form>
            </div>
            {% endif %}
            <div class="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border dark:border-gray-700">
                <p class="font-bold mb-3 dark:text-white text-sm">🔥 Influencers</p>
                {% for inf in influencers %}
                    <div class="flex justify-between text-xs mb-2 dark:text-gray-300">
                        <span>@{{ inf[0] }}</span>
                        <span class="font-bold text-indigo-500">{{ inf[1] }} ❤️</span>
                    </div>
                {% endfor %}
            </div>
        </div>

        <div class="md:col-span-2 space-y-6">
            {% if not session.get('user') %}
                <div class="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-lg border dark:border-gray-700">
                    <form method="POST" action="/login" class="space-y-4">
                        <input name="user" placeholder="Usuário" class="w-full border p-3 rounded-xl dark:bg-gray-700 dark:text-white dark:border-gray-600" required>
                        <input name="pass" type="password" placeholder="Senha (Admin)" class="w-full border p-3 rounded-xl dark:bg-gray-700 dark:text-white dark:border-gray-600">
                        <button class="w-full bg-indigo-600 text-white py-3 rounded-xl font-bold">Entrar</button>
                    </form>
                </div>
            {% else %}
                <div class="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border dark:border-gray-700">
                    <form method="POST" action="/post">
                        <textarea name="txt" placeholder="O que tem de novo?" class="w-full border-none focus:ring-0 dark:bg-gray-800 dark:text-white" required></textarea>
                        <input name="img" placeholder="URL da imagem..." class="w-full bg-gray-50 dark:bg-gray-700 border p-2 rounded-lg text-xs mb-4 dark:text-white dark:border-gray-600">
                        <button class="w-full bg-indigo-600 text-white py-2 rounded-full font-bold">Publicar</button>
                    </form>
                </div>

                {% for post in posts %}
                <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border dark:border-gray-700 overflow-hidden">
                    <div class="p-4 flex justify-between items-center">
                        <div class="flex items-center gap-1">
                            <span class="font-bold text-indigo-600">@{{ post.author }}</span>
                            {% if post.is_verified %}<i class="fa-solid fa-circle-check text-blue-400 text-[10px]"></i>{% endif %}
                        </div>
                        <div class="flex gap-2">
                            {% if session.get('is_admin') %}
                                <a href="/verify/{{ post.author }}" class="text-blue-500 text-[10px] font-bold">VERIFICAR</a>
                                <a href="/del/{{ post.id }}" class="text-red-400 text-[10px] font-bold">DELETAR</a>
                            {% endif %}
                        </div>
                    </div>
                    {% if post.image %}<img src="{{ post.image }}" class="w-full border-y dark:border-gray-700">{% endif %}
                    <div class="p-4">
                        <p class="text-gray-800 dark:text-gray-200 mb-4">{{ post.text }}</p>
                        <div class="flex items-center gap-4 text-gray-500 text-xs mb-4">
                            <a href="/like/{{ post.id }}" class="hover:text-red-500 flex items-center gap-1">
                                <i class="fa-solid fa-heart text-red-400"></i> {{ post.likes }}
                            </a>
                            <span><i class="fa-regular fa-comment"></i> {{ post.comments|length }}</span>
                            <span class="text-[10px]">{{ post.date_posted.strftime('%d/%m %H:%M') }}</span>
                        </div>
                        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3 space-y-2">
                            {% for com in post.comments %}
                                <p class="text-[10px] dark:text-gray-300"><span class="font-bold text-indigo-500">@{{ com.author }}:</span> {{ com.text }}</p>
                            {% endfor %}
                            <form method="POST" action="/comment/{{ post.id }}" class="mt-2 flex gap-2">
                                <input name="com_txt" placeholder="Responder..." class="flex-1 bg-white dark:bg-gray-800 border-none text-[10px] p-2 rounded-lg dark:text-white" required>
                                <button class="text-indigo-600 font-bold text-[10px]">OK</button>
                            </form>
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- LOGICA ---

@app.route('/')
def home():
    posts_data = Post.query.order_by(Post.id.desc()).all()
    # Adiciona flag de verificado manualmente para o template
    for p in posts_data:
        u = User.query.filter_by(username=p.author).first()
        p.is_verified = u.is_verified if u else False
    
    # Ranking
    influencers = db.session.query(Post.author, db.func.sum(Post.likes)).group_by(Post.author).order_by(db.func.sum(Post.likes).desc()).limit(5).all()
    
    user_info = None
    if session.get('user'):
        user_info = User.query.filter_by(username=session['user']).first()
        if not user_info:
            user_info = User(username=session['user'])
            db.session.add(user_info)
            db.session.commit()

    return render_template_string(HTML, posts=posts_data, influencers=influencers, user_info=user_info)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user').strip().lower()
    password = request.form.get('pass')
    session['user'] = user
    session['is_admin'] = (user == 'admin' and password == 'batima') # <--- SENHA AQUI
    if not User.query.filter_by(username=user).first():
        db.session.add(User(username=user))
        db.session.commit()
    return redirect('/')

@app.route('/post', methods=['POST'])
def post():
    if not session.get('user'): return redirect('/')
    txt = request.form.get('txt')
    # Lógica simples de Hashtag: apenas visual aqui, mas dá pra expandir
    new = Post(author=session['user'], image=request.form.get('img'), text=txt)
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
    new_com = Comment(text=request.form.get('com_txt'), author=session['user'], post_id=id)
    db.session.add(new_com)
    db.session.commit()
    return redirect('/')

@app.route('/verify/<username>')
def verify(username):
    if not session.get('is_admin'): return "Negado", 403
    u = User.query.filter_by(username=username).first()
    if u:
        u.is_verified = not u.is_verified
        db.session.commit()
    return redirect('/')

@app.route('/update_bio', methods=['POST'])
def update_bio():
    if not session.get('user'): return redirect('/')
    u = User.query.filter_by(username=session['user']).first()
    u.bio = request.form.get('new_bio')
    db.session.commit()
    return redirect('/')

@app.route('/del/<int:id>')
def delete(id):
    if session.get('is_admin'):
        db.session.delete(Post.query.get(id))
        db.session.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
