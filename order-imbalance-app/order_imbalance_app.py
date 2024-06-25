import streamlit as st
import random
import numpy as np
import plotly.graph_objects as go

def simulate_order_imbalance(num_rounds, initial_bid_ask_spread, order_imbalance_factor):
    prices = [100]
    bid_ask_spreads = [initial_bid_ask_spread]
    
    for _ in range(num_rounds - 1):
        order_imbalance = random.uniform(-1, 1) * order_imbalance_factor
        
        if order_imbalance > 0:
            # Positive order imbalance (more buy orders)
            price_change = order_imbalance * bid_ask_spreads[-1] / 2
            new_price = prices[-1] + price_change
            new_bid_ask_spread = bid_ask_spreads[-1] * (1 - order_imbalance)
        else:
            # Negative order imbalance (more sell orders)
            price_change = order_imbalance * bid_ask_spreads[-1] / 2
            new_price = prices[-1] + price_change
            new_bid_ask_spread = bid_ask_spreads[-1] * (1 + abs(order_imbalance))
        
        prices.append(new_price)
        bid_ask_spreads.append(new_bid_ask_spread)
    
    return prices, bid_ask_spreads

st.title("Order Imbalance and Bid-Ask Spread")

num_rounds = st.slider("Number of Rounds", min_value=10, max_value=1000, value=100, step=10)
initial_bid_ask_spread = st.slider("Initial Bid-Ask Spread", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
order_imbalance_factor = st.slider("Order Imbalance Factor", min_value=0.1, max_value=1.0, value=0.5, step=0.1)

if st.button("Simulate"):
    prices, bid_ask_spreads = simulate_order_imbalance(num_rounds, initial_bid_ask_spread, order_imbalance_factor)
    
    fig_prices = go.Figure()
    fig_prices.add_trace(go.Scatter(x=list(range(num_rounds)), y=prices, mode='lines+markers', name='Price'))
    fig_prices.update_layout(title="Price Series", xaxis_title="Round", yaxis_title="Price")
    st.plotly_chart(fig_prices)
    
    fig_spreads = go.Figure()
    fig_spreads.add_trace(go.Scatter(x=list(range(num_rounds)), y=bid_ask_spreads, mode='lines+markers', name='Bid-Ask Spread'))
    fig_spreads.update_layout(title="Bid-Ask Spread Series", xaxis_title="Round", yaxis_title="Spread")
    st.plotly_chart(fig_spreads)
    
    st.write("This simulation demonstrates how order imbalance can affect bid-ask spreads and future price movements. When there is a positive order imbalance (more buy orders), the bid-ask spread tends to narrow, and prices are likely to increase in the future. Conversely, when there is a negative order imbalance (more sell orders), the bid-ask spread tends to widen, and prices are likely to decrease.")
    
    st.write("The Order Imbalance Factor determines the magnitude of the impact of order imbalance on spreads and prices. A higher factor means that order imbalance has a stronger influence on the market dynamics.")
    
    st.write("By observing the order imbalance and changes in bid-ask spreads, market participants can gain insights into the likely direction of future price movements. This information can be valuable for making trading decisions and predicting short-term market trends.")