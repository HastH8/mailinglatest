import os
import csv
import requests
from flask import Flask, render_template, request, session, redirect, url_for, make_response

app = Flask(__name__)
app.secret_key = "sshhh"

def convert_to_grams(mass, unit):
    conversion_factors = {
        "grams": 1,
        "kilograms": 1000,
        "ounces": 28.3495,
        "pounds": 453.592
    }
    return mass * conversion_factors.get(unit, 1)

def calculate_mail_cost(mass):
    breakdown = []
    if mass <= 30:
        cost = 40
        breakdown.append((f"{mass} grams at base cost", 40))
    elif mass <= 50:
        cost = 55
        breakdown.append((f"{mass} grams at base cost", 55))
    elif mass <= 100:
        cost = 70
        breakdown.append((f"{mass} grams at base cost", 70))
    else:
        base_cost = 70
        breakdown.append(("First 100 grams at base cost", base_cost))
        extra_weight = mass - 100
        additional_cost = ((extra_weight + 49) // 50) * 25
        cost = base_cost + additional_cost
        breakdown.append((f"{extra_weight} grams extra at additional cost", additional_cost))
    return cost, breakdown

def convert_currency(amount, target_currency):
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/TRY")
        data = response.json()
        exchange_rate = data['rates'].get(target_currency.upper(), 1)
        return round(amount * exchange_rate, 2), exchange_rate
    except:
        return "Conversion error. Please try again."

@app.route("/", methods=["GET", "POST"])
def index():
    cost = None
    message = None
    breakdown_detail = []
    currency = "TRY"
    converted_breakdown = [] 

    if "history" not in session:
        session["history"] = []

    if request.method == "POST":
        try:
            mass = float(request.form.get("mass"))
            unit = request.form.get("unit", "grams")
            currency = request.form.get("currency", "TRY")

            if mass <= 0 or mass > 10000:
                message = "Please enter a weight between 1 and 10,000 grams."
            else:
                mass_in_grams = convert_to_grams(mass, unit)
                cost_in_try, breakdown_detail = calculate_mail_cost(mass_in_grams)
                
                # Convert cost and each breakdown item to the selected currency
                converted_cost, exchange_rate = convert_currency(cost_in_try, currency)
                converted_breakdown = [
                    (item[0], round(item[1] * exchange_rate, 2)) for item in breakdown_detail
                ]
                
                # Store converted cost and breakdown in session history
                cost = f"The cost to mail a {mass} {unit} package is {converted_cost} {currency.upper()}."
                history_entry = {
                    "weight": f"{mass} {unit}",
                    "cost": f"{converted_cost} {currency.upper()}",
                    "breakdown": converted_breakdown
                }
                session["history"].append(history_entry)
                session.modified = True
        except ValueError:
            message = "Invalid input. Please enter a numeric value for weight."

    return render_template("index.html", cost=cost, message=message, history=session.get("history"), breakdown=converted_breakdown, currency=currency)

@app.route("/clear_history", methods=["POST"])
def clear_history():
    session["history"] = []
    session.modified = True
    return redirect(url_for("index"))

@app.route("/export_csv")
def export_csv():
    if "history" not in session or not session["history"]:
        return redirect(url_for("index"))

    output = []
    output.append(["Weight", "Cost", "Breakdown"])  

    for entry in session["history"]:
        breakdown_text = "; ".join([f"{item[0]}: {item[1]} {entry['cost'].split()[-1]}" for item in entry["breakdown"]])
        output.append([entry["weight"], entry["cost"], breakdown_text])

    response = make_response("\n".join([",".join(row) for row in output]))
    response.headers["Content-Disposition"] = "attachment; filename=calculation_history.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 808))
    app.run(host="0.0.0.0", port=port)
