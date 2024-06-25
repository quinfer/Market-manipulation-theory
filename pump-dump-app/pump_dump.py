import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def simulate_pump_and_dump(num_traders, num_manipulators, pump_duration, dump_duration, pump_strength, dump_strength):
    prices = [100]
    returns = []
    manipulator_activity = []

    for t in range(1, pump_duration + dump_duration + 1):
        if t <= pump_duration:
            # Pump phase
            manipulation_effect = pump_strength * num_manipulators
            organic_returns = np.random.normal(0, 0.01, size=num_traders - num_manipulators)
        else:
            # Dump phase
            manipulation_effect = -dump_strength * num_manipulators
            organic_returns = np.random.normal(0, 0.01, size=num_traders)

        returns_t = np.concatenate((organic_returns, [manipulation_effect]))
        return_t = np.mean(returns_t)
        price_t = prices[-1] * (1 + return_t)
        prices.append(price_t)
        returns.append(return_t)
        manipulator_activity.append(manipulation_effect)

    return prices, returns, manipulator_activity

st.title("Pump and Dump Manipulation Simulation")

num_traders = st.slider("Number of Traders", min_value=10, max_value=1000, value=500, step=10)
num_manipulators = st.slider("Number of Manipulators", min_value=1, max_value=100, value=10, step=1)
pump_duration = st.slider("Pump Duration", min_value=1, max_value=100, value=30, step=1)
dump_duration = st.slider("Dump Duration", min_value=1, max_value=100, value=10, step=1)
pump_strength = st.slider("Pump Strength", min_value=0.001, max_value=0.1, value=0.01, step=0.001)
dump_strength = st.slider("Dump Strength", min_value=0.001, max_value=0.1, value=0.05, step=0.001)

if st.button("Simulate"):
    prices, returns, manipulator_activity = simulate_pump_and_dump(num_traders, num_manipulators, pump_duration, dump_duration, pump_strength, dump_strength)

    # Create subplots with 3 rows and 1 column
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=("Price", "Return", "Manipulator Activity"))

    # Add traces for each subplot
    fig.add_trace(go.Scatter(x=list(range(len(prices))), y=prices, mode='lines', name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=list(range(1, len(returns) + 1)), y=returns, mode='lines', name='Return'), row=2, col=1)
    fig.add_trace(go.Scatter(x=list(range(1, len(manipulator_activity) + 1)), y=manipulator_activity, mode='lines', name='Manipulator Activity'), row=3, col=1)

    # Update layout
    fig.update_layout(
        height=800,  # Increase overall height
        title="Pump and Dump Manipulation",
        xaxis=dict(title="Time"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Update y-axis titles
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Return", row=2, col=1)
    fig.update_yaxes(title_text="Manipulator Activity", row=3, col=1)

    st.plotly_chart(fig)


    st.subheader("Comparative Illustration")

    pump_strengths = [0.001, 0.005, 0.01, 0.05, 0.1]
    dump_strengths = [0.001, 0.005, 0.01, 0.05, 0.1]

    fig_comparative = go.Figure()

    for pump_strength, dump_strength in zip(pump_strengths, dump_strengths):
        prices, _, _ = simulate_pump_and_dump(num_traders, num_manipulators, pump_duration, dump_duration, pump_strength, dump_strength)
        fig_comparative.add_trace(go.Scatter(x=list(range(len(prices))), y=prices, mode='lines', name=f"Pump: {pump_strength}, Dump: {dump_strength}"))

        fig_comparative.update_layout(
            title="Impact of Pump and Dump Intensity on Market Function",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Price"),
            legend=dict(x=1.0, y=1.0, orientation="v"),
        )

    st.plotly_chart(fig_comparative)

    st.write("The comparative illustration demonstrates the impact of different pump and dump intensities on market function. By varying the pump and dump strengths, we can observe how the severity of the manipulation affects the price trajectory and the overall market dynamics.")

    st.write("As the pump and dump strengths increase, the price distortion becomes more pronounced, with steeper price increases during the pump phase and sharper declines during the dump phase. This highlights the potential for more severe market disruptions when manipulators employ more aggressive tactics.")

    st.write("The comparative illustration also reveals the sensitivity of the market to manipulation intensity. Even small changes in pump and dump strengths can lead to noticeable differences in price patterns, underscoring the importance of detecting and mitigating manipulative activities early on.")

    st.write("By providing this comparative view, the app helps users develop a deeper understanding of how the intensity of pump and dump manipulation can impact market function and stability. It emphasises the need for robust surveillance and regulatory measures to prevent and counteract such manipulative practices.")