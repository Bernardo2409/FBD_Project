import os
import secrets

from flask import Flask, render_template, request, redirect, jsonify, session, url_for

from persistence.equipa import adicionar_jogador_equipa, criar_equipa, obter_equipa_por_utilizador, obter_jogadores_equipa, remover_jogador_equipa, verificar_limites_equipa
from persistence.players import list_all, list_paginated, read
from persistence.clubs import list_all_clubs, list_paginated_clubs, read_club
from persistence.users import create_user, login_user, get_users

import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'chave-temporaria-para-desenvolvimento'  # ← ADIC


@app.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_submit():
    email = request.form.get("email")
    password = request.form.get("password")

    user = login_user(email, password)

    if user:
        # user é um dicionário, usar colchetes
        session['user_id'] = user["id"]  # ← CORREÇÃO AQUI
        session['user_name'] = user["first"]
        return redirect("/index")

    return render_template("login.html", error="Email ou palavra-passe incorretos")

@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup_submit():
    first = request.form.get("first")
    last = request.form.get("last")
    email = request.form.get("email")
    password = request.form.get("password")
    country = request.form.get("country")
    nationality = request.form.get("nationality")
    birthdate = request.form.get("birthdate")

    create_user(first, last, email, password, country, nationality, birthdate)

    return redirect("/")

@app.route("/logout")
def logout():
    # Limpar a sessão
    session.clear()
    return redirect("/")

@app.route("/index")
def index():
    
    user_has_team = False
    if 'user_id' in session:
        user_id = session['user_id']
        equipa_user = obter_equipa_por_utilizador(user_id)
        user_has_team = equipa_user is not None
        return render_template("index.html", user_has_team=user_has_team)
    else:
        return redirect("/")

@app.route("/players")
def players_list():
    page = int(request.args.get("page", 1))
    per_page = 10

    jogadores, total = list_paginated(page, per_page)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "players.html",
        jogadores=jogadores,
        page=page,
        total_pages=total_pages
    )

@app.route("/players/<j_id>")
def player_details(j_id):
    jogador = read(j_id)

    if jogador:
        return render_template("player_details.html", jogador=jogador)
    else:
        return "Jogador não encontrado", 404


@app.route("/clubs")
def clubs_list():
    page = int(request.args.get("page", 1))
    per_page = 10

    clubes, total = list_paginated_clubs(page, per_page)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "clubs.html",
        clubes=clubes,
        page=page,
        total_pages=total_pages
    )


@app.route("/clubs/<c_id>")
def club_details(c_id):
    clube = read_club(c_id)     # função que vais criar

    if clube:
        return render_template("club_details.html", clube=clube)
    else:
        return "Clube não encontrado", 404
    

    
POSICOES = {
    "POS01": "Goalkeeper",
    "POS02": "Defender",
    "POS03": "Midfielder",
    "POS04": "Forward"
}

@app.route("/equipa")
def equipa():
    # Verificar se utilizador está logado (simulação - ajustar conforme tua auth)
    if 'user_id' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    
    # Verificar se utilizador já tem equipa
    equipa_user = obter_equipa_por_utilizador(user_id)
    
    if not equipa_user:
        # Se não tem equipa, redirecionar para criar
        return redirect("/criar-equipa")
    
    # Obter jogadores da equipa
    jogadores_equipa = obter_jogadores_equipa(equipa_user.id)
    
    # Separar por posições
    guarda_redes = [j for j in jogadores_equipa if j['posicao'] == "Goalkeeper"]
    defesas = [j for j in jogadores_equipa if j['posicao'] == "Defender"]
    medios = [j for j in jogadores_equipa if j['posicao'] == "Midfielder"]
    avancados = [j for j in jogadores_equipa if j['posicao'] == "Forward"]
    
    # Obter todos os jogadores disponíveis (para as dropdowns)
    todos_jogadores = list_all()
    todos_avancados = [j for j in todos_jogadores if j.posicao == "Forward"]
    todos_medios = [j for j in todos_jogadores if j.posicao == "Midfielder"]
    todos_defesas = [j for j in todos_jogadores if j.posicao == "Defender"]
    todos_gr = [j for j in todos_jogadores if j.posicao == "Goalkeeper"]
    
    return render_template("equipa.html", 
                         equipa={
                             'gr': guarda_redes,
                             'defesas': defesas,
                             'medios': medios,
                             'avancados': avancados,
                             'info': equipa_user
                         },
                         todos_jogadores={
                             'Goalkeeper': todos_gr,
                             'Defender': todos_defesas,
                             'Midfielder': todos_medios,
                             'Forward': todos_avancados
                         })


@app.route("/criar-equipa", methods=['GET', 'POST'])
def criar_equipa_route():
    if 'user_id' not in session:
        return redirect("/")
    
    if request.method == 'POST':
        nome_equipa = request.form.get('nome_equipa')
        user_id = session['user_id']
        
        if nome_equipa:
            # Criar equipa
            equipa_id = criar_equipa(nome_equipa, user_id)
            return redirect("/equipa")
    
    return render_template("criar_equipa.html")

@app.route("/equipa/adicionar/<posicao>/<jogador_id>")
def adicionar_jogador_equipa_route(posicao, jogador_id):
    if 'user_id' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)
    
    if equipa_user:
        try:
            # Verificar limites antes de adicionar
            limites = verificar_limites_equipa(equipa_user.id)
            
            # Verificar se pode adicionar mais jogadores nesta posição
            if posicao == 'gr' and not limites['pode_adicionar_gr']:
                session['error'] = "Já tens 2 guarda-redes! Remove um primeiro."
            elif posicao == 'defesas' and not limites['pode_adicionar_defesa']:
                session['error'] = "Já tens 5 defesas! Remove um primeiro."
            elif posicao == 'medios' and not limites['pode_adicionar_medio']:
                session['error'] = "Já tens 5 médios! Remove um primeiro."
            elif posicao == 'avancados' and not limites['pode_adicionar_avancado']:
                session['error'] = "Já tens 3 avançados! Remove um primeiro."
            else:
                adicionar_jogador_equipa(equipa_user.id, jogador_id)
                session['message'] = "Jogador adicionado com sucesso!"
                
        except Exception as e:
            session['error'] = str(e)
    
    return redirect("/equipa")

@app.route("/equipa/remover/<jogador_id>")
def remover_jogador_equipa_route(jogador_id):
    if 'user_id' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)
    
    if equipa_user:
        try:
            remover_jogador_equipa(equipa_user.id, jogador_id)
            session['message'] = "Jogador removido com sucesso!"
        except Exception as e:
            session['error'] = f"Erro ao remover jogador: {str(e)}"
    
    return redirect("/equipa")



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
