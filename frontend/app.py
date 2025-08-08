from flask import Flask, render_template
from frontend.blueprints.travel_plan import plan_bp
from frontend.blueprints.settings import settings_bp

app = Flask(__name__)
app.register_blueprint(plan_bp)
app.register_blueprint(settings_bp)


@app.route("/")
def index():
    return render_template("base.html")

@app.route("/login")
def login():
    ...

@app.route("/logout")
def logout():
    ...


if __name__ == "__main__":
    app.run(debug=True)