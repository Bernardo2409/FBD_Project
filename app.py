from flask import Flask

app = Flask(__name__)

@app.route("/")
def main():
    return "<p><h1>Hello, World!<h1></p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0")