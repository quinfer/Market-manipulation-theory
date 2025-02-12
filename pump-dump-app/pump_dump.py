import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def simulate_pump_and_dump(num_traders, num_manipulators, pump_duration, dump_duration, 
                         pump_strength, dump_strength, noise_trader_ratio=0.7,
                         show_details=True):
    prices = [100]
    returns = []
    manipulator_activity = []
    volumes = []
    spreads = []
    volatility = 0.01 * (1 + noise_trader_ratio * 2)  # Double the noise trader impact on base volatility
    base_spread = 0.02
    momentum = 0
    
    # Calculate trader composition
    num_noise_traders = int((num_traders - num_manipulators) * noise_trader_ratio)
    num_informed_traders = num_traders - num_manipulators - num_noise_traders
    
    # Only show details if requested
    if show_details:
        st.markdown(f"""
        ### Simulation Details
        Running simulation with:
        - {num_noise_traders} noise traders ({noise_trader_ratio*100:.1f}%)
        - {num_informed_traders} informed traders ({(1-noise_trader_ratio)*100:.1f}%)
        - {num_manipulators} manipulators
        """)
    
    def calculate_price_impact(volume, current_price):
        # Square root price impact model
        impact_factor = 0.1
        return impact_factor * np.sqrt(volume) * current_price
    
    def update_volatility(current_return):
        nonlocal volatility
        # More persistent volatility with noise traders
        volatility = 0.8 * volatility + 0.2 * abs(current_return) * (1 + noise_trader_ratio * 2)
        return max(0.005, min(0.15, volatility))  # Increased max volatility
    
    def calculate_spread(volume, volatility):
        # Spread widens with volatility and narrows with volume
        return base_spread * (1 + volatility * 2) * (1 / np.sqrt(volume + 1))

    def calculate_noise_trader_sentiment(price_momentum, volatility):
        # More extreme sentiment swings
        sentiment_sensitivity = 3.0  # Increased from 2.0
        volatility_aversion = 1.5
        # Larger random component
        random_sentiment = np.random.normal(0, 0.05 * noise_trader_ratio)  # Scales with noise ratio
        return (price_momentum * sentiment_sensitivity) - (volatility * volatility_aversion) + random_sentiment
    
    def update_momentum(current_return):
        # Exponential moving average of returns
        decay = 0.85
        return decay * momentum + (1 - decay) * current_return

    def calculate_strategic_advantage(current_price, phase, time_left):
        # Manipulators' information advantage and strategic positioning
        base_advantage = 0.02  # Base information advantage
        phase_multiplier = 1.5 if phase == 'pump' else 2.0  # Higher advantage during dump
        time_decay = np.exp(-0.1 * time_left)  # Advantage decreases as event approaches
        return base_advantage * phase_multiplier * (1 - time_decay)
    
    def calculate_manipulator_strategy(phase, current_price, time_left, volatility):
        # Strategic trading based on phase and market conditions
        if phase == 'pump':
            # Gradual accumulation and price support
            base_volume = pump_strength * 100
            stealth_factor = 1 - (time_left / pump_duration)  # Increase visibility over time
            volume_adjustment = 1 + stealth_factor
            
            # Price support when needed
            if volatility > 0.02:  # High volatility threshold
                volume_adjustment *= 1.2  # Increase support
                
            return base_volume * volume_adjustment
        else:
            # Strategic distribution during dump
            base_volume = dump_strength * 200
            urgency_factor = (dump_duration - time_left) / dump_duration
            volume_adjustment = 1 + urgency_factor
            
            # Adapt to market conditions
            if volatility > 0.03:  # Market stress threshold
                volume_adjustment *= 1.5  # Accelerate distribution
                
            return base_volume * volume_adjustment

    for t in range(1, pump_duration + dump_duration + 1):
        current_price = prices[-1]
        phase = 'pump' if t <= pump_duration else 'dump'
        time_left = pump_duration - t if phase == 'pump' else dump_duration - (t - pump_duration)
        
        if phase == 'pump':
            # Informed traders - more stable
            informed_volume = np.random.gamma(2, 2, size=num_informed_traders)
            informed_returns = np.random.normal(0.001, volatility * 0.3, 
                                             size=num_informed_traders)
            
            # Noise traders - much more volatile
            noise_sentiment = calculate_noise_trader_sentiment(momentum, volatility)
            noise_volume = np.random.gamma(3, 2, size=num_noise_traders)
            # Significantly increased volatility for noise traders
            noise_returns = np.random.normal(noise_sentiment, volatility * 4.0, 
                                          size=num_noise_traders)
            
        else:
            # Informed traders - more cautious during dump
            informed_volume = np.random.gamma(1.5, 1.5, size=num_informed_traders)
            informed_returns = np.random.normal(-0.002, volatility * 0.4, 
                                             size=num_informed_traders)
            
            # Noise traders - panic response
            noise_sentiment = calculate_noise_trader_sentiment(momentum, volatility) * 4  # More extreme
            noise_volume = np.random.gamma(4, 2, size=num_noise_traders)
            # Even more volatile during dump
            noise_returns = np.random.normal(noise_sentiment, volatility * 5.0, 
                                          size=num_noise_traders)
        
        # Manipulation effect
        manipulation_volume = num_manipulators * (pump_strength if phase == 'pump' else dump_strength) * 100
        manipulation_effect = (1 if phase == 'pump' else -1) * calculate_price_impact(manipulation_volume, current_price) / current_price

        # Add high-frequency noise based on noise trader ratio
        micro_noise = np.random.normal(0, volatility * noise_trader_ratio * 1.0)
        
        # Combine returns with stronger weighting by trader type
        total_volume = (np.sum(informed_volume) + np.sum(noise_volume) + manipulation_volume)
        volumes.append(total_volume)
        
        # Weight returns more extremely based on trader composition
        returns_t = np.concatenate((
            informed_returns * (1 - noise_trader_ratio) ** 2,  # Square the weight to amplify difference
            noise_returns * noise_trader_ratio ** 2,  # Square the weight to amplify difference
            [manipulation_effect],
            [micro_noise]
        ))
        return_t = np.mean(returns_t)
        
        # Update market state
        volatility = update_volatility(return_t)
        momentum = update_momentum(return_t)
        spread = calculate_spread(total_volume, volatility)
        spreads.append(spread)
        
        # Add more microstructure noise to price updates
        price_t = current_price * (1 + return_t + spread/2 + np.random.normal(0, 0.001 * noise_trader_ratio))
        prices.append(price_t)
        returns.append(return_t)
        manipulator_activity.append(manipulation_effect)

    return prices, returns, manipulator_activity, volumes, spreads

st.title("Pump and Dump Manipulation Simulation")

st.markdown("""
## About This Simulation
This application simulates market microstructure dynamics during a pump and dump manipulation scheme. 

### Trader Types
1. **Strategic Informed Traders (Manipulators)**:
   - Execute the pump and dump scheme
   - Have superior information about their own trading intentions
   - Trade strategically to maximize impact

2. **Regular Informed Traders**:
   - Trade based on fundamental information
   - Gradually detect manipulation
   - More sophisticated than noise traders
   
3. **Noise Traders**:
   - React to price movements and market sentiment
   - Display behavioral biases (herding, momentum following)
   - More susceptible to manipulation

The balance between these trader types significantly affects market efficiency and manipulation success.
""")

st.markdown("---")
st.subheader("Simulation Parameters")

# Market Participant Configuration
st.markdown("""
### Market Participants
Configure the number and composition of market participants. The trader mix affects:
- Market efficiency
- Information diffusion speed
- Manipulation effectiveness
- Price discovery process
""")

num_traders = st.slider(
    "Total Number of Traders", 
    min_value=10, 
    max_value=1000, 
    value=500, 
    step=10,
    help="Total number of traders in the market. A larger number creates more liquid markets but may dilute manipulation effects."
)

num_manipulators = st.slider(
    "Number of Manipulators", 
    min_value=1, 
    max_value=100, 
    value=10, 
    step=1,
    help="Number of strategic informed traders executing the pump and dump scheme. More manipulators increase scheme effectiveness but may also increase detection risk."
)

# New control for trader composition
noise_trader_ratio = st.slider(
    "Noise Trader Ratio", 
    min_value=0.0, 
    max_value=1.0, 
    value=0.7, 
    step=0.1,
    help="Proportion of non-manipulator traders that are noise traders. Higher ratios make the market more susceptible to manipulation but potentially more profitable for manipulators."
)

st.markdown(f"""
### Current Trader Composition
Based on your settings:
- Total Traders: {num_traders}
- Manipulators: {num_manipulators}
- Noise Traders: {int((num_traders - num_manipulators) * noise_trader_ratio)}
- Informed Traders: {int((num_traders - num_manipulators) * (1 - noise_trader_ratio))}

**Market Composition Effects:**
- Higher noise trader ratio → More volatile markets, stronger momentum effects
- Higher informed trader ratio → Better price discovery, harder to manipulate
- Current noise/informed ratio: {noise_trader_ratio:.1f}/{(1-noise_trader_ratio):.1f}
""")

st.markdown("""
### Timing Parameters
Define the duration of manipulation phases:
""")

pump_duration = st.slider(
    "Pump Duration", 
    min_value=1, 
    max_value=100, 
    value=30, 
    step=1,
    help="Number of periods for the pump phase. Longer pump duration may build more momentum but increases execution costs."
)

dump_duration = st.slider(
    "Dump Duration", 
    min_value=1, 
    max_value=100, 
    value=10, 
    step=1,
    help="Number of periods for the dump phase. Shorter dump duration may prevent price collapse but risks incomplete distribution."
)

st.markdown("""
### Manipulation Intensity
Set the strength of manipulation activities:
""")

pump_strength = st.slider(
    "Pump Strength", 
    min_value=0.001, 
    max_value=0.1, 
    value=0.01, 
    step=0.001,
    help="Intensity of buying during pump phase. Higher values create stronger price movements but increase visibility."
)

dump_strength = st.slider(
    "Dump Strength", 
    min_value=0.001, 
    max_value=0.1, 
    value=0.05, 
    step=0.001,
    help="Intensity of selling during dump phase. Higher values enable faster distribution but may cause sharper price drops."
)

st.markdown("""
### Market Microstructure Effects
The simulation incorporates several key market microstructure elements:
- **Price Impact**: Larger trades move prices more (square root impact model)
- **Volatility**: Updates dynamically based on trading activity (GARCH-like process)
- **Bid-Ask Spread**: Widens with volatility and narrows with volume
- **Information Diffusion**: Regular traders gradually detect manipulation
""")

if st.button("Simulate"):
    with st.spinner("Running simulation..."):
        # Main simulation - show details
        prices, returns, manipulator_activity, volumes, spreads = simulate_pump_and_dump(
            num_traders, num_manipulators, pump_duration, dump_duration, 
            pump_strength, dump_strength, noise_trader_ratio, show_details=True)

        # Create subplots with 5 rows and 1 column
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            subplot_titles=("Price", "Return", "Manipulator Activity", "Trading Volume", "Bid-Ask Spread"))

        # Add traces for each subplot
        fig.add_trace(go.Scatter(x=list(range(len(prices))), y=prices, mode='lines', name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(returns) + 1)), y=returns, mode='lines', name='Return'), row=2, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(manipulator_activity) + 1)), y=manipulator_activity, mode='lines', name='Manipulator Activity'), row=3, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(volumes) + 1)), y=volumes, mode='lines', name='Volume'), row=4, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(spreads) + 1)), y=spreads, mode='lines', name='Spread'), row=5, col=1)

        # Update layout
        fig.update_layout(
            height=1200,  # Increase overall height
            title="Market Microstructure During Pump and Dump",
            xaxis=dict(title="Time"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # Update y-axis titles
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Return", row=2, col=1)
        fig.update_yaxes(title_text="Manipulator Activity", row=3, col=1)
        fig.update_yaxes(title_text="Volume", row=4, col=1)
        fig.update_yaxes(title_text="Spread", row=5, col=1)

        st.plotly_chart(fig)

        st.markdown("""
        ## Interpretation Guide
        
        ### Price Pattern
        - The pump phase shows gradually increasing prices as manipulators accumulate positions
        - The dump phase exhibits a sharp price decline as positions are distributed
        
        ### Returns
        - More volatile during manipulation periods
        - Asymmetric patterns between pump and dump phases
        
        ### Manipulator Activity
        - Initially subtle during accumulation
        - More aggressive during distribution
        
        ### Trading Volume
        - Typically increases during both phases
        - Highest during the dump phase due to panic selling
        
        ### Bid-Ask Spread
        - Widens with increased volatility
        - Reflects market maker uncertainty
        """)

        st.subheader("Comparative Illustration")
        pump_strengths = [0.001, 0.005, 0.01, 0.05, 0.1]
        dump_strengths = [0.001, 0.005, 0.01, 0.05, 0.1]

        fig_comparative = go.Figure()

        for pump_strength, dump_strength in zip(pump_strengths, dump_strengths):
            # Comparative simulations - don't show details
            prices, _, _, _, _ = simulate_pump_and_dump(
                num_traders, 
                num_manipulators, 
                pump_duration, 
                dump_duration, 
                pump_strength, 
                dump_strength,
                noise_trader_ratio,
                show_details=False  # Don't show details for comparative runs
            )
            fig_comparative.add_trace(go.Scatter(
                x=list(range(len(prices))), 
                y=prices, 
                mode='lines', 
                name=f"Pump: {pump_strength}, Dump: {dump_strength}"
            ))

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

        st.markdown("""
        ## Market Composition Effects on Results
        
        ### Price Formation
        - **High Noise Trader Ratio**: Prices more volatile, stronger momentum effects
        - **High Informed Ratio**: More efficient price discovery, resistance to manipulation
        
        ### Volume Patterns
        - Noise traders tend to trade more frequently
        - Informed traders more selective in timing
        - Volume spikes often indicate noise trader herding
        
        ### Spread Behavior
        - Wider spreads when noise traders dominate
        - Tighter spreads with more informed trading
        - Spread patterns signal market maker confidence
        
        ### Manipulation Effectiveness
        - More successful with higher noise trader ratio
        - Harder to execute with more informed traders
        - Trade-off between profit potential and detection risk
        """)

        # Add comparison of different noise trader ratios
        st.subheader("Impact of Noise Trader Ratio")
        noise_ratios = [0.2, 0.5, 0.8]
        fig_noise = go.Figure()

        for ratio in noise_ratios:
            prices_n, _, _, _, _ = simulate_pump_and_dump(
                num_traders, num_manipulators, pump_duration, dump_duration,
                pump_strength, dump_strength, ratio, show_details=False
            )
            fig_noise.add_trace(go.Scatter(
                x=list(range(len(prices_n))),
                y=prices_n,
                mode='lines',
                name=f"Noise Ratio: {ratio:.1f}"
            ))

        fig_noise.update_layout(
            title="Price Paths with Different Noise Trader Ratios",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Price"),
            legend=dict(x=1.0, y=1.0, orientation="v"),
        )

        st.plotly_chart(fig_noise)