from flask import Flask, render_template, request, redirect, jsonify, url_for

from persistence.players import list_all, list_paginated, read
from persistence.clubs import list_all_clubs, list_paginated_clubs, read_club
from persistence.users import create_user, login_user, get_users

import random

app = Flask(__name__)

@app.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_submit():
    email = request.form.get("email")
    password = request.form.get("password")

    user = login_user(email, password)

    if user:
        # Se login tiver sucesso → ir para index
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

@app.route("/index")
def index():
    return render_template("index.html")

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
    jogadores = list_all()

    # separar as posições
    guarda_redes = [j for j in jogadores if j.posicao == "Goalkeeper"]
    defesas      = [j for j in jogadores if j.posicao == "Defender"]
    medios       = [j for j in jogadores if j.posicao == "Midfielder"]
    avancados    = [j for j in jogadores if j.posicao == "Forward"]

    # validar quantidade
    if len(guarda_redes) < 2 or len(defesas) < 5 or len(medios) < 5 or len(avancados) < 3:
        print([j.posicao for j in jogadores])
        return "Jogadores insuficientes para criar equipa automaticamente", 500

    equipa_auto = {
        "gr": random.sample(guarda_redes, 2),
        "defesas": random.sample(defesas, 5),
        "medios": random.sample(medios, 5),
        "avancados": random.sample(avancados, 3)
    }

    return render_template("equipa.html", equipa=equipa_auto)






if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
