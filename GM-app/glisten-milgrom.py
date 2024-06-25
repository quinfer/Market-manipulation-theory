import streamlit as st
import random
import plotly.graph_objects as go

def simulate(num_traders, num_insiders, num_rounds):
    prices = []
    bid_ask_spreads = []
    
    for _ in range(num_rounds):
        insider_orders = ["buy" if random.random() < 0.7 else "sell" for _ in range(num_insiders)]
        noise_orders = ["buy" if random.random() < 0.5 else "sell" for _ in range(num_traders - num_insiders)]
        orders = insider_orders + noise_orders
        
        buy_orders = orders.count("buy")
        sell_orders = orders.count("sell")
        
        bid_price = 100 - (1 + 2 * num_insiders / num_traders)
        ask_price = 100 + (1 + 2 * num_insiders / num_traders)
        
        if buy_orders > sell_orders:
            price = ask_price
        else:
            price = bid_price
        
        prices.append(price)
        bid_ask_spreads.append(ask_price - bid_price)
    
    return prices, bid_ask_spreads

st.title("Glosten-Milgrom Model Simulation")

num_traders = st.slider("Number of Traders", min_value=1, max_value=1000, value=100, step=1)
num_insiders = st.slider("Number of Insiders", min_value=0, max_value=num_traders, value=10, step=1)
num_rounds = st.slider("Number of Rounds", min_value=1, max_value=1000, value=50, step=1)

if st.button("Simulate"):
    prices, bid_ask_spreads = simulate(num_traders, num_insiders, num_rounds)
    
    fig_prices = go.Figure()
    fig_prices.add_trace(go.Scatter(x=list(range(1, num_rounds + 1)), y=prices, mode='lines+markers', name='Price'))
    fig_prices.update_layout(title="Price Series", xaxis_title="Round", yaxis_title="Price")
    st.plotly_chart(fig_prices)
    
    fig_spreads = go.Figure()
    fig_spreads.add_trace(go.Scatter(x=list(range(1, num_rounds + 1)), y=bid_ask_spreads, mode='lines+markers', name='Bid-Ask Spread'))
    fig_spreads.update_layout(title="Bid-Ask Spread Series", xaxis_title="Round", yaxis_title="Spread")
    st.plotly_chart(fig_spreads)

    st.subheader("Effect of Reducing Informed Traders")
    num_insiders_reduced = st.slider("Reduced Number of Insiders", min_value=0, max_value=num_insiders, value=num_insiders // 2, step=1)
    
    prices_reduced, bid_ask_spreads_reduced = simulate(num_traders, num_insiders_reduced, num_rounds)
    
    fig_comparison = go.Figure()
    fig_comparison.add_trace(go.Scatter(x=list(range(1, num_rounds + 1)), y=prices, mode='lines+markers', name='Original Price'))
    fig_comparison.add_trace(go.Scatter(x=list(range(1, num_rounds + 1)), y=prices_reduced, mode='lines+markers', name='Reduced Insiders Price'))
    fig_comparison.update_layout(title="Price Comparison", xaxis_title="Round", yaxis_title="Price")
    st.plotly_chart(fig_comparison)
    
    st.write("As the number of informed traders (insiders) decreases, the bid-ask spread narrows, and the price series becomes less volatile. This is because with fewer informed traders, there is less information asymmetry in the market, and market makers face less adverse selection risk. Consequently, they can quote tighter spreads, and prices are less sensitive to the trading activity of the remaining informed traders.")