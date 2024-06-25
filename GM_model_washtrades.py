import streamlit as st
import random
import numpy as np
import plotly.graph_objects as go

def simulate_wash_trading(num_traders, num_insiders, num_wash_traders, wash_trade_probability, num_rounds):
    prices = [100]
    bid_ask_spreads = [2]
    wash_trade_volume = [0]
    total_volume = [0]

    for _ in range(num_rounds - 1):
        # Generate informed and uninformed trades
        insider_trades = np.random.choice([-1, 1], size=num_insiders, p=[0.5, 0.5])
        uninformed_trades = np.random.choice([-1, 1], size=num_traders - num_insiders - num_wash_traders, p=[0.5, 0.5])
        
        # Generate wash trades
        wash_trades = np.random.choice([-1, 1], size=num_wash_traders, p=[0.5, 0.5])
        wash_trade_mask = np.random.choice([0, 1], size=num_wash_traders, p=[1 - wash_trade_probability, wash_trade_probability])
        wash_trades = wash_trades * wash_trade_mask
        
        trades = np.concatenate((insider_trades, uninformed_trades, wash_trades))

        # Calculate net order imbalance
        net_order_imbalance = np.sum(trades)

        # Update price based on net order imbalance
        price_change = net_order_imbalance * bid_ask_spreads[-1] / num_traders
        new_price = prices[-1] + price_change
        prices.append(new_price)

        # Update bid-ask spread based on fraction of informed traders
        new_bid_ask_spread = 2 * (1 + 2 * num_insiders / num_traders)
        bid_ask_spreads.append(new_bid_ask_spread)

        # Update wash trade volume and total volume
        wash_trade_volume.append(np.sum(np.abs(wash_trades)))
        total_volume.append(np.sum(np.abs(trades)))

    return prices, bid_ask_spreads, wash_trade_volume, total_volume

st.title("Glosten-Milgrom Model - Wash Trading")

num_traders = st.slider("Number of Traders", min_value=10, max_value=1000, value=100, step=10)
num_insiders = st.slider("Number of Insiders", min_value=0, max_value=num_traders, value=10, step=1)
num_wash_traders = st.slider("Number of Wash Traders", min_value=0, max_value=num_traders - num_insiders, value=10, step=1)
wash_trade_probability = st.slider("Wash Trade Probability", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
num_rounds = st.slider("Number of Rounds", min_value=10, max_value=1000, value=100, step=10)

if st.button("Simulate"):
    prices, bid_ask_spreads, wash_trade_volume, total_volume = simulate_wash_trading(num_traders, num_insiders, num_wash_traders, wash_trade_probability, num_rounds)

    fig_prices = go.Figure()
    fig_prices.add_trace(go.Scatter(x=list(range(num_rounds)), y=prices, mode='lines+markers', name='Price'))
    fig_prices.update_layout(title="Price Series", xaxis_title="Round", yaxis_title="Price")
    st.plotly_chart(fig_prices)

    fig_spreads = go.Figure()
    fig_spreads.add_trace(go.Scatter(x=list(range(num_rounds)), y=bid_ask_spreads, mode='lines+markers', name='Bid-Ask Spread'))
    fig_spreads.update_layout(title="Bid-Ask Spread Series", xaxis_title="Round", yaxis_title="Spread")
    st.plotly_chart(fig_spreads)

    fig_volume = go.Figure()
    fig_volume.add_trace(go.Scatter(x=list(range(1, num_rounds)), y=wash_trade_volume, mode='lines+markers', name='Wash Trade Volume'))
    fig_volume.add_trace(go.Scatter(x=list(range(1, num_rounds)), y=total_volume, mode='lines+markers', name='Total Volume'))
    fig_volume.update_layout(title="Volume Series", xaxis_title="Round", yaxis_title="Volume")
    st.plotly_chart(fig_volume)

    st.write("This app demonstrates the impact of wash trading on market dynamics using a modified Glosten-Milgrom model. Wash trading refers to the manipulative practice of simultaneously buying and selling the same asset to create artificial trading activity and mislead other market participants.")

    st.write("In this simulation, a specified number of wash traders engage in wash trades with a given probability in each round. Wash trades are generated as pairs of offsetting buy and sell orders, which do not contribute to the net order imbalance but inflate the trading volume.")

    st.write("The app shows the effect of wash trading on price series, bid-ask spread series, and volume series. The price and bid-ask spread dynamics are influenced by the net order imbalance, which excludes wash trades. However, the volume series displays both the wash trade volume and the total volume, highlighting the artificial inflation of trading activity.")

    st.write("By adjusting the number of wash traders and the probability of wash trades, users can observe how different levels of wash trading affect market liquidity, price discovery, and trading volume. This simulation helps illustrate the potential distortions caused by wash trading and emphasizes the importance of detecting and preventing such manipulative practices.")