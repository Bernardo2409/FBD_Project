from flask import Flask, render_template, request, make_response, render_template_string
from persistence.session import create_connection

app = Flask(__name__)

@app.route("/")
def base():
    # Conectar ao banco de dados
    conn = create_connection()
    cursor = conn.cursor()

    return render_template("hello_world.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
