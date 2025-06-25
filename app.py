from flask import Flask, request, jsonify, render_template, session

app = Flask(__name__)
app.secret_key = 'auction-multiuser-secret'

auction_data = {}      # ongoing products
sold_products = {}      # finished auctions
active_product = None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    global active_product
    user_input = request.json.get("query", "").lower().strip()

    if "reset" in user_input:
        auction_data.clear()
        sold_products.clear()
        session.clear()
        return jsonify(reply="🔄 Auction has been reset. Say 'start' to begin a new one.")

    if "start" in user_input:
        session.clear()
        session['state'] = 'awaiting_product'
        return jsonify(reply="🎯 Auction started! Please say the product name.")

    if "leaderboard" in user_input:
        if not auction_data and not sold_products:
            return jsonify(reply="🏁 No auctions or bids yet!")
        leaderboard = "🏆 Leaderboard:\n"
        for product, data in sold_products.items():
            leaderboard += f"✅ SOLD: {product.title()} – ₹{data['highest_bid']} by {data['bidder']}\n"
        for product, data in auction_data.items():
            leaderboard += f"📦 LIVE: {product.title()} – ₹{data['highest_bid']} by {data['bidder']}\n"
        return jsonify(reply=leaderboard.strip())

    if session.get('state') == 'awaiting_product':
        # prevent duplicate names by checking sold list
        for sold_name in sold_products:
            if user_input in sold_name or sold_name in user_input:
                sold = sold_products[sold_name]
                return jsonify(reply=f"❌ {sold_name.title()} has already been sold to {sold['bidder']} for ₹{sold['highest_bid']}.")

        session['product'] = user_input
        active_product = user_input
        session['state'] = 'awaiting_price'
        return jsonify(reply=f"📦 Got it! {user_input.title()} selected. What is the starting bid?")

    if session.get('state') == 'awaiting_price':
        digits = ''.join(filter(str.isdigit, user_input))
        if digits:
            price = int(digits)
            auction_data[active_product] = {'highest_bid': price, 'bidder': ''}
            session['bid'] = price
            session['state'] = 'awaiting_name'
            return jsonify(reply="🙋 Please say your name.")
        else:
            return jsonify(reply="❌ Please say a valid price like ₹45000.")

    if session.get('state') == 'awaiting_name':
        bidder = user_input.title()
        auction_data[active_product]['bidder'] = bidder
        session['state'] = 'bidding'
        return jsonify(reply=f"✅ {bidder} placed ₹{session['bid']} on {active_product.title()}!")

    if session.get('state') == 'bidding':
        if any(char.isdigit() for char in user_input):
            bid = int(''.join(filter(str.isdigit, user_input)))
            session['bid'] = bid
            session['state'] = 'awaiting_new_bidder'
            return jsonify(reply="🧑 What's your name?")
        elif "end auction" in user_input:
            sold_products[active_product] = auction_data.pop(active_product)
            session.clear()
            return jsonify(reply=f"🔔 Auction ended. {sold_products[active_product]['bidder']} won {active_product.title()} for ₹{sold_products[active_product]['highest_bid']}.")
        else:
            return jsonify(reply="💬 Please say your bid like ₹50000")

    if session.get('state') == 'awaiting_new_bidder':
        bidder = user_input.title()
        current = auction_data[active_product]
        if session['bid'] > current['highest_bid']:
            auction_data[active_product] = {'highest_bid': session['bid'], 'bidder': bidder}
            session['state'] = 'bidding'
            return jsonify(reply=f"🎉 {bidder} is now the highest bidder with ₹{session['bid']}!")
        else:
            session['state'] = 'bidding'
            return jsonify(reply=f"❌ {bidder}, ₹{session['bid']} is too low. Current highest is ₹{current['highest_bid']} by {current['bidder']}.")

    return jsonify(reply="Say 'start' to begin an auction, 'leaderboard' to see top bids, or 'reset' to clear auction data.")

if __name__ == "__main__":
    app.run(debug=True)
