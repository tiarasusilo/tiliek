from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/telusur")
def telusur():
    return render_template("home.html")


@app.route("/peta-isu")
def peta_isu():
    return render_template("home.html")


@app.route("/chatbot")
def chatbot():
    return render_template("home.html")


@app.route("/tentang")
def tentang():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True)