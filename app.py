import os
from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-qualquer-123'
# Usando um banco local simples. O Render vai deixar criar se não tiver caminho absoluto.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo do Banco
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50))
    image = db.Column(db.String(500))
    text = db.Column(db.Text)

# HTML Simples para o Feed
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8"><title>Connectify</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-5">
    <div class="max-w-xl mx-auto">
        <h1 class="text-3xl font-bold text-indigo-600 mb-5">Connectify</h1>
        
        {% if not session.get('user') %}
            <form method="POST" action="/login" class="bg-white p-5 rounded shadow">
                <input name="user" placeholder="Seu nome" class="w-full border p-2 mb-2 rounded" required>
                <input name="pass" type="password" placeholder="Senha (só para admin)" class="w-full border p-2 mb-2 rounded">
                <button class="w-full bg-indigo-600 text-white p-2 rounded">Entrar</button>
            </form>
        {% else %}
            <div class="mb-5 flex justify-between items-center">
                <span>Logado como: <b>{{ session['user'] }}</b></span>
                <a href="/logout" class="text-red-500">Sair</a>
            </div>
            <form method="POST" action="/post" class="bg-white p-5 rounded shadow mb-10">
                <input name="img" placeholder="URL da Foto" class="w-full border p-2 mb-2 rounded text-sm">
                <textarea name="txt" placeholder="O que está pensando?" class="w-full border p-2 rounded" required></textarea>
                <button class="w-full bg-indigo-600 text-white p-2 mt-2 rounded">Publicar</button>
            </form>
            {% for post in posts %}
                <div class="bg-white rounded shadow-md mb-5 overflow-hidden">
                    <div class="p-3 border-b flex justify-between bg-gray-50">
                        <span class="font-bold">@{{ post.author }}</span>
                        {% if session.get('is_admin') %}
                            <a href="/del/{{ post.id }}" class="text-red-500 font-bold text-xs uppercase">Deletar</a>
                        {% endif %}
                    </div>
                    {% if post.image %}<img src="{{ post.image }}" class="w-full">{% endif %}
                    <p class="p-4 text-gray-800">{{ post.text }}</p>
                </div>
            {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    try:
        posts = Post.query.order_by(Post.id.desc()).all()
        return render_template_string(HTML, posts=posts)
    except Exception as e:
        return f"Erro no banco: {str(e)}"

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    password = request.form.get('pass')
    session['user'] = user
    # Defina sua senha aqui
    if user.lower() == 'admin' and password == '12345':
        session['is_admin'] = True
    else:
        session['is_admin'] = False
    return redirect('/')

@app.route('/post', methods=['POST'])
def post():
    if not session.get('user'): return redirect('/')
    new_post = Post(author=session['user'], image=request.form.get('img'), text=request.form.get('txt'))
    db.session.add(new_post)
    db.session.commit()
    return redirect('/')

@app.route('/del/<int:id>')
def delete(id):
    if not session.get('is_admin'): return "Sem permissão", 403
    post_to_del = Post.query.get(id)
    db.session.delete(post_to_del)
    db.session.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ESSA PARTE É VITAL PARA O RENDER
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
