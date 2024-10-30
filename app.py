import os
import requests  
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def convert_to_grams(mass, unit):
    conversion_factors = {
        "grams": 1,
        "kilograms": 1000,
        "ounces": 28.3495,
        "pounds": 453.592
    }
    return mass * conversion_factors.get(unit, 1)

def calculate_mail_cost(mass):
    if mass <= 30:
        return 40
    elif mass <= 50:
        return 55
    elif mass <= 100:
        return 70
    else:
        extra_weight = mass - 100
        additional_cost = ((extra_weight + 49) // 50) * 25
        return 70 + additional_cost

def convert_currency(cost, target_currency):
    try:
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/TRY")
        data = response.json()
        exchange_rate = data['rates'].get(target_currency.upper(), 1)
        return round(cost * exchange_rate, 2)
    except:
        return "Conversion error. Please try again."

@app.route("/", methods=["GET", "POST"])
def index():
    cost = None
    message = None
    if request.method == "POST":
        try:
            mass = float(request.form.get("mass"))
            unit = request.form.get("unit", "grams")
            currency = request.form.get("currency", "TRY")

            if mass <= 0 or mass > 10000:
                message = "Please enter a weight between 1 and 10,000 grams."
            else:
                mass_in_grams = convert_to_grams(mass, unit)
                cost_in_try = calculate_mail_cost(mass_in_grams)
                converted_cost = convert_currency(cost_in_try, currency)
                cost = f"The mailing cost is {converted_cost} {currency.upper()}"
        except ValueError:
            message = "Invalid input. Please enter a numeric value for weight."

    return render_template("index.html", cost=cost, message=message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
