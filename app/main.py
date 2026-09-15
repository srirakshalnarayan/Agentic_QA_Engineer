from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "testuser":
        return "Login successful"

    return "Invalid username or password"


if __name__ == "__main__":
    app.run(debug=True)