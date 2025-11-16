from flask import Flask, render_template
from persistence.session import create_connection
from persistence.players import list_all, read
from persistence.clubs import list_all_clubs, read_club   # <-- quando criares

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/players")
def players_list():
    jogadores = list_all()
    return render_template("players.html", jogadores=jogadores)


@app.route("/players/<j_id>")
def player_view(j_id):
    jogador = read(j_id)

    if jogador:
        return render_template("player_view.html", jogador=jogador)
    else:
        return "Jogador não encontrado", 404


@app.route("/clubs")
def clubs_list():
    clubes = list_all_clubs()   # função que vais criar
    return render_template("clubs.html", clubes=clubes)


@app.route("/clubs/<c_id>")
def club_view(c_id):
    clube = read_club(c_id)     # função que vais criar

    if clube:
        return render_template("club_view.html", clube=clube)
    else:
        return "Clube não encontrado", 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
