import streamlit as st
import random
import numpy as np
import plotly.graph_objects as go

def simulate_libor_manipulation(num_traders, num_insiders, num_honest_banks, num_manipulated_banks, num_rounds, manipulation_mean, manipulation_std):
    prices = [100]
    bid_ask_spreads = [2]
    libor_rates = [3]

    for _ in range(num_rounds - 1):
        # Generate informed and uninformed trades
        insider_trades = np.random.choice([-1, 1], size=num_insiders, p=[0.5, 0.5])
        uninformed_trades = np.random.choice([-1, 1], size=num_traders - num_insiders, p=[0.5, 0.5])
        trades = np.concatenate((insider_trades, uninformed_trades))

        # Calculate net order imbalance
        net_order_imbalance = np.sum(trades)

        # Update price based on net order imbalance
        price_change = net_order_imbalance * bid_ask_spreads[-1] / num_traders
        new_price = prices[-1] + price_change
        prices.append(new_price)

        # Update bid-ask spread based on fraction of informed traders
        new_bid_ask_spread = 2 * (1 + 2 * num_insiders / num_traders)
        bid_ask_spreads.append(new_bid_ask_spread)

        # Generate honest Libor submissions
        honest_libor_submissions = np.random.normal(loc=3, scale=0.1, size=num_honest_banks)

        # Generate manipulated Libor submissions
        manipulated_libor_submissions = np.random.normal(loc=manipulation_mean, scale=manipulation_std, size=num_manipulated_banks)

        # Combine honest and manipulated Libor submissions
        libor_submissions = np.concatenate((honest_libor_submissions, manipulated_libor_submissions))

        # Calculate Libor rate as the trimmed mean of submissions
        trimmed_submissions = np.sort(libor_submissions)[1:-1]
        libor_rate = np.mean(trimmed_submissions)
        libor_rates.append(libor_rate)

    return prices, bid_ask_spreads, libor_rates

st.title("Glosten-Milgrom Model - Libor Scandal")

num_traders = st.slider("Number of Traders", min_value=10, max_value=1000, value=100, step=10)
num_insiders = st.slider("Number of Insiders", min_value=0, max_value=num_traders, value=10, step=1)
num_honest_banks = st.slider("Number of Honest Banks", min_value=1, max_value=20, value=10, step=1)
num_manipulated_banks = st.slider("Number of Manipulated Banks", min_value=0, max_value=10, value=3, step=1)
num_rounds = st.slider("Number of Rounds", min_value=10, max_value=1000, value=100, step=10)
manipulation_mean = st.slider("Manipulation Mean", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
manipulation_std = st.slider("Manipulation Standard Deviation", min_value=0.1, max_value=2.0, value=0.5, step=0.1)

if st.button("Simulate"):
    prices, bid_ask_spreads, libor_rates = simulate_libor_manipulation(num_traders, num_insiders, num_honest_banks, num_manipulated_banks, num_rounds, manipulation_mean, manipulation_std)

    fig_prices = go.Figure()
    fig_prices.add_trace(go.Scatter(x=list(range(num_rounds)), y=prices, mode='lines+markers', name='Price'))
    fig_prices.update_layout(title="Price Series", xaxis_title="Round", yaxis_title="Price")
    st.plotly_chart(fig_prices)

    fig_spreads = go.Figure()
    fig_spreads.add_trace(go.Scatter(x=list(range(num_rounds)), y=bid_ask_spreads, mode='lines+markers', name='Bid-Ask Spread'))
    fig_spreads.update_layout(title="Bid-Ask Spread Series", xaxis_title="Round", yaxis_title="Spread")
    st.plotly_chart(fig_spreads)

    fig_libor = go.Figure()
    fig_libor.add_trace(go.Scatter(x=list(range(num_rounds)), y=libor_rates, mode='lines+markers', name='Libor Rate'))
    fig_libor.update_layout(title="Libor Rate Series", xaxis_title="Round", yaxis_title="Libor Rate")
    st.plotly_chart(fig_libor)

    st.write("This app demonstrates the impact of Libor manipulation on market prices and bid-ask spreads, using a modified Glosten-Milgrom model. The app simulates a market with a given number of traders, including insiders, and a panel of banks submitting Libor rates, some of which are manipulated.")

    st.write("In each round, the app generates informed and uninformed trades, updates the market price based on the net order imbalance, and adjusts the bid-ask spread based on the fraction of informed traders. Simultaneously, honest and manipulated Libor submissions are generated, and the Libor rate is calculated as the trimmed mean of the submissions.")

    st.write("The manipulation of Libor rates is modeled by specifying the mean and standard deviation of the manipulated submissions, which can differ from the honest submissions. The impact of the manipulation on market prices and bid-ask spreads can be observed in the plotted series.")

    st.write("By adjusting the parameters, such as the number of manipulated banks and the manipulation mean and standard deviation, users can explore how different levels of Libor manipulation affect market dynamics. This app provides insights into how the Libor scandal, where banks submitted false rates for their own benefit, could have distorted market prices and liquidity.")