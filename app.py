import os
from flask import Flask, render_template, request

app = Flask(__name__)


def calculate_mail_cost(mass):
    if mass <= 30:
        return 40
    elif mass <= 50:
        return 55
    elif mass <= 100:
        return 70
    else:
        # For mass over 100 grams:
        extra_weight = mass - 100
        additional_cost = ((extra_weight + 49) // 50) * 25
        return 70 + additional_cost

@app.route("/", methods=["GET", "POST"])
def index():
    cost = None
    if request.method == "POST":
        try:
            mass = float(request.form.get("mass"))
            if mass < 0:
                cost = "Invalid mass. Please enter a non-negative value."
            else:
                cost = calculate_mail_cost(mass)
                cost = f"The cost to mail a letter weighing {mass} grams is {cost} sinas."
        except ValueError:
            cost = "Please enter a valid numeric value for the mass."

    return render_template("index.html", cost=cost)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
