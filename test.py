def calculate_postage_cost(mass):
    if mass <= 30:
        return 40
    elif mass <= 50:
        return 55
    elif mass <= 100:
        return 70
    else:
        additional_cost = 25 * ((mass - 100 + 49) // 50) 
        return 70 + additional_cost

mass = float(input("Enter the mass of the letter in grams: "))
cost = calculate_postage_cost(mass)

print(f"The cost to mail a letter weighing {mass} grams is {cost} sinas.")
