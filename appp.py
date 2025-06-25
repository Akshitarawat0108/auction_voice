from flask import Flask, request, jsonify, render_template
import re

app = Flask(__name__)

# Dummy product data
products = {
    "Laptop": {"highest_bid": 30000},
    "iPhone": {"highest_bid": 45000},
    "Camera": {"highest_bid": 20000},
}

# ✅ Serve the HTML frontend
@app.route("/")
def index():
    return render_template("index.html")

# ✅ Webhook logic
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    command = data.get("command", "").strip().lower()

    if not command:
        return jsonify({"response": "Please type something!"})

    # 🎯 Understand "list products"
    if any(word in command for word in ["show", "list", "available", "products"]):
        product_names = ", ".join(products.keys())
        return jsonify({"response": f"Here are the available products: {product_names}"})

    # 🎯 Understand "highest bid on"
    if "highest bid" in command:
        for product in products:
            if product.lower() in command:
                bid = products[product]["highest_bid"]
                return jsonify({"response": f"The highest bid on {product} is ₹{bid}."})
        return jsonify({"response": "Please mention a valid product name to check its bid."})

    # 🎯 Understand "place ₹ amount bid on product"
    if any(word in command for word in ["place", "add", "submit", "bid"]):
        match = re.search(r"₹?(\d+)[^\d]*(?:bid\s*(?:on|for)?\s*)?(\w+)?", command)
        if match:
            amount = int(match.group(1))
            product = match.group(2).capitalize() if match.group(2) else None

            if product and product in products:
                if amount > products[product]["highest_bid"]:
                    products[product]["highest_bid"] = amount
                    return jsonify({"response": f"✅ ₹{amount} bid placed successfully on {product}!"})
                else:
                    return jsonify({"response": f"❌ Bid too low. Current highest bid on {product} is ₹{products[product]['highest_bid']}."})
            else:
                return jsonify({"response": "Please specify a valid product to place bid."})
        else:
            return jsonify({"response": "Please provide both bid amount and product name."})

    # 🎯 Help command
    if "help" in command or "what can i do" in command:
        return jsonify({
            "response": "You can say things like:\n• show all products\n• place ₹50000 bid on Laptop\n• what's the highest bid on iPhone"
        })

    # ❓ Fallback for unknown input
    return jsonify({
        "response": f"I'm not sure how to respond to that. Try asking about products, placing bids, or typing 'help'."
    })


if __name__ == "__main__":
    app.run(debug=True)
