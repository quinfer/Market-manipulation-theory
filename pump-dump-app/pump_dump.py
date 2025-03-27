import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

def simulate_pump_and_dump(num_traders, num_manipulators, pump_duration, dump_duration, 
                         pump_strength, dump_strength, noise_trader_ratio=0.7,
                         show_details=True):
    prices = [100]
    returns = []
    manipulator_activity = []
    volumes = []
    spreads = []
    volatilities = [0.01 * (1 + noise_trader_ratio * 2)]  # Initial volatility
    regimes = [0]  # 0: normal, 1: high volatility, 2: crash
    market_stress = 0
    momentum = 0
    order_imbalance = 0
    
    # Calculate trader composition
    num_noise_traders = int((num_traders - num_manipulators) * noise_trader_ratio)
    num_informed_traders = num_traders - num_manipulators - num_noise_traders
    
    # Only show details if requested
    if show_details:
        st.markdown(f"""
        ### Simulation Details
        Running enhanced simulation with:
        - {num_noise_traders} noise traders ({noise_trader_ratio*100:.1f}%)
        - {num_informed_traders} informed traders ({(1-noise_trader_ratio)*100:.1f}%)
        - {num_manipulators} manipulators
        - GARCH volatility model
        - Regime-switching dynamics
        - Jump diffusion process
        - Fat-tailed return distributions
        """)
    
    # GARCH parameters
    garch_omega = 0.000001
    garch_alpha = 0.1
    garch_beta = 0.85
    
    # Regime transition matrices - probability of moving from current regime to next
    regime_transition_matrices = {
        'pump': [
            [0.95, 0.04, 0.01],  # Normal -> Normal, High Vol, Crash
            [0.15, 0.80, 0.05],  # High Vol -> Normal, High Vol, Crash
            [0.30, 0.50, 0.20]   # Crash -> Normal, High Vol, Crash
        ],
        'dump': [
            [0.80, 0.15, 0.05],  # More likely to transition in dump phase
            [0.10, 0.70, 0.20],
            [0.15, 0.35, 0.50]
        ]
    }
    
    # Helper functions
    def t_dist_random(mean, scale, df):
        """Generate Student's t-distributed random variable"""
        # Standard t-distribution
        t = np.random.standard_t(df)
        # Scale and shift
        return mean + scale * t
    
    def poisson_jump(intensity, jump_size_mean, jump_size_std):
        """Generate price jumps based on Poisson process"""
        # Determine if jump occurs
        jump_occurs = np.random.random() < intensity
        if jump_occurs:
            # Generate jump size
            return np.random.normal(jump_size_mean, jump_size_std)
        return 0
    
    def update_garch_volatility(prev_volatility, prev_return, omega, alpha, beta):
        """Update volatility using GARCH(1,1) model with numerical safety"""
        # Clip previous return to prevent extreme values
        safe_return = np.clip(prev_return, -0.25, 0.25)
        safe_volatility = np.clip(prev_volatility, 0.001, 0.5)
        
        # Calculate GARCH value with bounds
        garch_value = omega + alpha * np.power(safe_return, 2) + beta * np.power(safe_volatility, 2)
        # Ensure result is positive and not too extreme
        return np.sqrt(np.clip(garch_value, 0.00001, 0.25))
    
    def regime_switching_model(current_regime, transition_matrix):
        """Determine next market regime based on transition probabilities"""
        rand_value = np.random.random()
        transition_probs = transition_matrix[current_regime]
        cumulative_prob = 0
        
        for i, prob in enumerate(transition_probs):
            cumulative_prob += prob
            if rand_value < cumulative_prob:
                return i
        
        return len(transition_probs) - 1
    
    def calculate_liquidity(base_volume, prev_volatility, order_imb, mkt_stress):
        """Model market liquidity based on conditions with numerical stability"""
        # Ensure all inputs are within safe ranges
        safe_vol = min(2.0, max(0.0001, prev_volatility))
        safe_imb = min(1.0, max(-1.0, order_imb))
        safe_stress = min(1.0, max(0.0, mkt_stress))
        
        # Capped calculation to prevent extreme values
        liquidity_factor = max(0.1, min(2.0, 1 - 0.3 * safe_vol - 0.2 * abs(safe_imb) - 0.1 * safe_stress))
        return max(1.0, base_volume * liquidity_factor)
    
    def calculate_price_impact(volume, liquidity, volatility, order_imb):
        """Enhanced price impact model with nonlinear effects and numerical stability"""
        nonlinearity = 0.5  # Square root model
        impact_factor = 0.1
        
        # Safely handle inputs
        safe_volume = max(0.1, volume)
        safe_liquidity = max(1.0, liquidity)
        safe_volatility = min(1.0, max(0.001, volatility))
        safe_imb = min(1.0, max(-1.0, order_imb))
        
        # Safer adjustments with upper bounds
        vol_adj = min(3.0, 1 + safe_volatility * 2)
        imbalance_adj = min(1.5, 1 + abs(safe_imb) * 0.5)
        
        # Prevent division by zero and cap the result
        impact_ratio = min(10.0, safe_volume / safe_liquidity)
        
        return min(0.1, impact_factor * np.power(impact_ratio, nonlinearity) * vol_adj * imbalance_adj)
    
    def calculate_spread(volume, volatility, market_stress, order_imb):
        """Dynamic spread calculation based on market conditions with bounds"""
        base_spread = 0.02
        
        # Safe input values
        safe_vol = np.clip(volatility, 0.001, 0.3)
        safe_stress = np.clip(market_stress, 0, 1)
        safe_imb = np.clip(abs(order_imb), 0, 1)
        safe_volume = max(1.0, volume)
        
        # Bounded component calculations
        vol_component = min(1.0, safe_vol * 4)
        stress_component = safe_stress * 0.05
        imbalance_component = safe_imb * 0.03
        volume_component = min(0.5, 0.1 / np.sqrt(safe_volume))
        
        # Calculate with upper bound
        spread = base_spread * (1 + vol_component + stress_component + imbalance_component) * volume_component
        return min(0.1, max(0.001, spread))  # Keep spread in reasonable range
    
    def update_momentum(prev_momentum, current_return, decay=0.85):
        """Update price momentum with decay"""
        return decay * prev_momentum + (1 - decay) * current_return
    
    def calculate_noise_trader_sentiment(price_momentum, volatility, market_stress, order_imb):
        """Model complex noise trader sentiment with behavioral biases and numerical safety"""
        # Clip inputs to prevent extreme values
        safe_momentum = np.clip(price_momentum, -0.1, 0.1)
        safe_volatility = np.clip(volatility, 0.001, 0.3)
        safe_stress = np.clip(market_stress, 0, 1)
        safe_imb = np.clip(order_imb, -1, 1)
        
        # Calculate components with bounded outputs
        trend_following = 1.5 * safe_momentum  # Reduced coefficient for stability
        fear_component = -1.0 * safe_volatility * (1 + safe_stress)
        herding = 1.0 * safe_imb  # Reduced coefficient
        recency_bias = np.random.normal(0, 0.05 * noise_trader_ratio)
        
        # Safer overreaction calculation
        if abs(safe_momentum) < 0.001:
            overreaction = 0
        else:
            overreaction = 0.3 * np.sign(safe_momentum) * min(0.2, np.power(abs(safe_momentum), 1.5))
        
        # Clip final sentiment to reasonable bounds
        sentiment = trend_following + fear_component + herding + recency_bias + overreaction
        return np.clip(sentiment, -0.5, 0.5)
    
    for t in range(1, pump_duration + dump_duration + 1):
        current_price = prices[-1]
        current_volatility = volatilities[-1]
        prev_return = returns[-1] if returns else 0
        
        # Determine phase
        phase = 'pump' if t <= pump_duration else 'dump'
        time_left = pump_duration - t if phase == 'pump' else dump_duration - (t - pump_duration)
        
        # Update regime based on transition probabilities
        current_regime = regimes[-1]
        new_regime = regime_switching_model(current_regime, regime_transition_matrices[phase])
        regimes.append(new_regime)
        
        # Regime-specific parameters
        regime_settings = [
            {'vol_multiplier': 1.0, 'jump_intensity': 0.01, 'jump_mean': 0, 'jump_std': 0.01},  # Normal
            {'vol_multiplier': 2.5, 'jump_intensity': 0.05, 'jump_mean': 0, 'jump_std': 0.02},  # High volatility
            {'vol_multiplier': 4.0, 'jump_intensity': 0.15, 'jump_mean': -0.02, 'jump_std': 0.03}  # Crash
        ][new_regime]
        
        # Update market stress based on regime and other factors, with safety
        regime_stress = new_regime / 2.0  # Normalized regime stress
        
        # Safely calculate return-based stress
        if current_volatility < 0.001 or np.isnan(current_volatility):
            return_stress = 0.05  # Default value if volatility is too low
        else:
            # Limit the volatility-normalized return to prevent extreme values
            normalized_return = min(5.0, abs(prev_return) / current_volatility)
            return_stress = 0.1 * normalized_return
            
        # Smooth update with bounds
        market_stress = 0.8 * market_stress + 0.2 * regime_stress + min(0.2, return_stress)
        market_stress = min(1.0, max(0.0, market_stress))
        
        # Update momentum
        momentum = update_momentum(momentum, prev_return)
        
        # Calculate noise trader sentiment with more complex dynamics
        noise_sentiment = calculate_noise_trader_sentiment(momentum, current_volatility, market_stress, order_imbalance)
        
        # Calculate strategic manipulation effect with variability
        if phase == 'pump':
            # More variable pump strategy
            manipulation_strategy = pump_strength * (1 + 0.5 * np.sin(np.pi * t / pump_duration) + 0.3 * np.random.random())
        else:
            # Adaptive dump strategy
            panic_factor = 0.3 * (1 - t/pump_duration + dump_duration) + 0.2 * market_stress
            manipulation_strategy = -dump_strength * (1 + panic_factor + 0.2 * np.random.random())
        
        # Number of active traders varies based on market conditions
        participation_rate_informed = 0.7 + 0.3 * np.random.random() - 0.2 * market_stress
        participation_rate_noise = 0.5 + 0.5 * (0.5 + 0.5 * abs(momentum) + 0.3 * market_stress)
        
        active_informed_traders = int(num_informed_traders * max(0.1, min(1.0, participation_rate_informed)))
        active_noise_traders = int(num_noise_traders * max(0.1, min(1.0, participation_rate_noise)))
        
        # Generate volumes with more realistic distributions
        if phase == 'pump':
            # Informed traders - more stable but varies with conditions
            informed_shape = 2.0 - 0.5 * market_stress
            informed_scale = 2.0 + 1.0 * (1 - market_stress)
            informed_volume = np.random.gamma(informed_shape, informed_scale, size=active_informed_traders)
            
            # Noise traders - much more volatile
            noise_shape = 3.0 + 1.0 * abs(noise_sentiment) 
            noise_scale = 2.0 + 2.0 * abs(noise_sentiment)
            noise_volume = np.random.gamma(noise_shape, noise_scale, size=active_noise_traders)
        else:
            # Informed traders - more cautious during dump
            informed_shape = 1.5 - 0.5 * market_stress
            informed_scale = 1.5 * (1.0 - 0.3 * market_stress)
            informed_volume = np.random.gamma(informed_shape, informed_scale, size=active_informed_traders)
            
            # Noise traders - panic response during dump
            noise_shape = 4.0 + 2.0 * market_stress + 1.0 * abs(noise_sentiment)
            noise_scale = 2.0 + 3.0 * market_stress + 2.0 * abs(noise_sentiment)
            noise_volume = np.random.gamma(noise_shape, noise_scale, size=active_noise_traders)
        
        # Manipulator volume with strategic variations
        manipulation_volume = num_manipulators * (
            (pump_strength if phase == 'pump' else dump_strength) * 
            100 * (0.8 + 0.4 * np.random.random())
        )
        
        # Total trading volume
        total_volume = np.sum(informed_volume) + np.sum(noise_volume) + manipulation_volume
        volumes.append(total_volume)
        
        # Calculate order imbalance (between -1 and 1)
        # Positive means more buy orders, negative means more sell orders
        manip_imbalance = 0.8 if phase == 'pump' else -0.8
        
        if phase == 'pump':
            informed_imbalance = 0.1 - 0.4 * market_stress
            # Informed traders might detect manipulation late in pump
            if t > pump_duration * 0.7:
                informed_imbalance -= 0.2 * (t - pump_duration * 0.7) / (pump_duration * 0.3)
        else:
            informed_imbalance = -0.3 - 0.3 * market_stress
            
        noise_imbalance = 0.7 * noise_sentiment
        
        order_imbalance = (
            (manip_imbalance * manipulation_volume + 
             informed_imbalance * np.sum(informed_volume) + 
             noise_imbalance * np.sum(noise_volume))
            / total_volume if total_volume > 0 else 0
        )
        
        # Calculate liquidity
        liquidity = calculate_liquidity(total_volume, current_volatility, order_imbalance, market_stress)
        
        # Generate returns for different trader types with fat tails
        # Degrees of freedom for t-distribution (lower = fatter tails)
        # With safety bounds to prevent numerical issues
        informed_df = max(3.0, 5 - 2 * market_stress)  # Range: 3-5
        noise_df = max(2.0, 3 - 1.5 * market_stress)   # Range: 2-3
        
        # Informed trader returns
        if phase == 'pump':
            informed_mean = 0.001 - 0.002 * market_stress
            informed_scale = current_volatility * 0.3
        else:
            informed_mean = -0.002 - 0.003 * market_stress
            informed_scale = current_volatility * 0.4
            
        informed_returns = t_dist_random(informed_mean, informed_scale, informed_df)
        
        # Noise trader returns
        noise_mean = noise_sentiment * (0.01 if phase == 'pump' else 0.02)
        noise_scale = current_volatility * regime_settings['vol_multiplier'] * 3
        noise_returns = t_dist_random(noise_mean, noise_scale, noise_df)
        
        # Price impact from manipulation
        manip_effect = manipulation_strategy * calculate_price_impact(
            manipulation_volume,
            liquidity,
            current_volatility,
            order_imbalance
        )
        manipulator_activity.append(manip_effect)
        
        # Add jump component
        jump = poisson_jump(
            regime_settings['jump_intensity'],
            regime_settings['jump_mean'],
            regime_settings['jump_std']
        )
        
        # Combine returns with more complex weighting
        informed_weight = max(0.2, min(0.8, (1 - noise_trader_ratio) * (1 + 0.5 * np.random.random())))
        noise_weight = 1 - informed_weight
        
        # Final return calculation with all components and bounds
        combined_return = (
            informed_weight * informed_returns +
            noise_weight * noise_returns +
            manip_effect +
            jump +
            np.random.normal(0, 0.001 * (1 + market_stress))  # Microstructure noise
        )
        
        # Clip returns to prevent extreme values
        return_t = np.clip(combined_return, -0.15, 0.15)
        returns.append(return_t)
        
        # Calculate bid-ask spread based on volatility, volume and market stress
        spread = calculate_spread(total_volume, current_volatility, market_stress, order_imbalance)
        spreads.append(spread)
        
        # Update price with spread effect and liquidity premium, with safety
        if total_volume < 0.1 or liquidity < 0.1:
            liquidity_premium = 0.001 * market_stress  # Default if volumes/liquidity are too low
        else:
            liquidity_ratio = min(10.0, liquidity / total_volume)
            liquidity_premium = min(0.01, 0.0005 * market_stress / liquidity_ratio)
            
        # Calculate new price with bounds to prevent overflow
        price_factor = 1 + return_t + spread/2 * np.sign(order_imbalance) + liquidity_premium
        price_factor = np.clip(price_factor, 0.8, 1.2)  # Limit single-period price change
        price_t = current_price * price_factor
        prices.append(price_t)
        
        # Update volatility using GARCH model with safety factors
        base_vol = update_garch_volatility(
            current_volatility, return_t, garch_omega, garch_alpha, garch_beta
        )
        
        # Apply regime and stress multipliers with upper bound
        stress_factor = min(1.5, 1 + 0.2 * market_stress)
        regime_factor = min(3.0, regime_settings['vol_multiplier'])
        
        # Final volatility with upper bound to prevent extreme values
        new_vol = min(0.25, base_vol * stress_factor * regime_factor)
        
        volatilities.append(new_vol)
    
    return prices, returns, manipulator_activity, volumes, spreads, volatilities, regimes

st.title("Advanced Pump and Dump Manipulation Simulation")

st.markdown("""
## About This Enhanced Simulation
This application simulates realistic market microstructure dynamics during a pump and dump manipulation scheme with enhanced stochastic elements, including:

1. **Fat-tailed return distributions** - Student's t-distribution for more realistic extreme events
2. **Volatility clustering** - GARCH(1,1) model for time-varying volatility
3. **Regime-switching** - Markov chain model for market state transitions
4. **Jump diffusion process** - Poisson jumps for sudden price movements
5. **Liquidity dynamics** - State-dependent liquidity conditions
6. **Order flow imbalance** - Strategic and behavioral imbalances
7. **Market stress feedback loops** - Complex interactions between variables

The simulation produces more realistic price paths with:
- **Natural market noise** - Stochastic processes beyond simple random walks
- **Heterogeneous traders** - Different behavior models across trader types
- **Strategic adaptation** - Manipulators respond to market conditions
- **Emergent properties** - Complex system interactions create realistic patterns
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
The enhanced simulation incorporates several key market microstructure elements:
- **Fat-Tailed Distributions**: More realistic extreme price movements
- **Volatility Clustering**: Similar volatility tends to cluster together in time
- **Regime Switching**: Market can transition between normal, volatile, and crash states
- **Liquidity Dynamics**: Liquidity varies with market conditions
- **Order Flow Imbalance**: Strategic positioning of trades
- **Market Stress Feedback**: Interactions between volatility, sentiment and liquidity
""")

if st.button("Simulate"):
    with st.spinner("Running advanced simulation..."):
        # Main simulation - show details
        prices, returns, manipulator_activity, volumes, spreads, volatilities, regimes = simulate_pump_and_dump(
            num_traders, num_manipulators, pump_duration, dump_duration, 
            pump_strength, dump_strength, noise_trader_ratio, show_details=True)

        # Create subplots with 7 rows and 1 column
        fig = make_subplots(rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            subplot_titles=("Price", "Return", "Volatility", "Manipulator Activity", 
                                           "Trading Volume", "Bid-Ask Spread", "Market Regime"))

        # Add traces for each subplot
        fig.add_trace(go.Scatter(x=list(range(len(prices))), y=prices, mode='lines', name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(returns) + 1)), y=returns, mode='lines', name='Return'), row=2, col=1)
        fig.add_trace(go.Scatter(x=list(range(len(volatilities))), y=volatilities, mode='lines', name='Volatility'), row=3, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(manipulator_activity) + 1)), y=manipulator_activity, mode='lines', name='Manipulator Activity'), row=4, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(volumes) + 1)), y=volumes, mode='lines', name='Volume'), row=5, col=1)
        fig.add_trace(go.Scatter(x=list(range(1, len(spreads) + 1)), y=spreads, mode='lines', name='Spread'), row=6, col=1)
        
        # Regime plot
        regime_labels = ["Normal", "High Volatility", "Crisis"]
        fig.add_trace(go.Scatter(x=list(range(len(regimes))), y=regimes, mode='lines', 
                                name='Market Regime', line=dict(shape='hv')), row=7, col=1)

        # Update layout
        fig.update_layout(
            height=1400,  # Increase overall height
            title="Enhanced Market Microstructure During Pump and Dump",
            xaxis=dict(title="Time"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # Update y-axis titles
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Return", row=2, col=1)
        fig.update_yaxes(title_text="Volatility", row=3, col=1)
        fig.update_yaxes(title_text="Manipulator Activity", row=4, col=1)
        fig.update_yaxes(title_text="Volume", row=5, col=1)
        fig.update_yaxes(title_text="Spread", row=6, col=1)
        fig.update_yaxes(title_text="Regime", row=7, col=1, tickvals=[0, 1, 2], ticktext=regime_labels)

        st.plotly_chart(fig)

        st.markdown("""
        ## Enhanced Interpretation Guide
        
        ### Price Pattern Analysis
        - **Realistic Noise**: Price paths now show natural market noise rather than smooth trends
        - **Regime-Dependent Behavior**: Notice how behavior changes across market regimes
        - **Discontinuities**: Jump processes create occasional price gaps
        - **Emergent Patterns**: Complex price behaviors emerge from simple interaction rules
        
        ### Volatility Dynamics
        - **Clustering Effect**: Periods of high volatility tend to cluster together
        - **Regime Transitions**: Volatility spikes often coincide with regime shifts
        - **GARCH Effects**: Volatility has a persistent component that creates realistic patterns
        
        ### Trading Volume Interpretation
        - **Heterogeneous Response**: Different trader types respond differently to conditions
        - **Participation Rate Variations**: Trader activity varies with market conditions
        - **Volume-Volatility Relationship**: Note the relationship between these variables
        
        ### Manipulator Effectiveness Analysis
        - **Variable Impact**: Manipulation effectiveness varies with market conditions
        - **Strategic Adaptation**: Manipulators adjust strategies based on market response
        - **Detection Threshold**: High activity periods may trigger detection by informed traders
        """)

        # Run multiple simulations for comparison
        st.subheader("Comparative Simulation Analysis")
        
        fig_comparative = go.Figure()
        
        for i in range(5):
            sim_prices, _, _, _, _, _, _ = simulate_pump_and_dump(
                num_traders, 
                num_manipulators, 
                pump_duration, 
                dump_duration, 
                pump_strength, 
                dump_strength,
                noise_trader_ratio,
                show_details=False
            )
            fig_comparative.add_trace(go.Scatter(
                x=list(range(len(sim_prices))), 
                y=sim_prices, 
                mode='lines', 
                name=f"Simulation Run {i+1}"
            ))

        fig_comparative.update_layout(
            title="Multiple Simulation Runs with Identical Parameters - Note the Variance",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Price"),
            legend=dict(x=1.0, y=1.0, orientation="v"),
        )

        st.plotly_chart(fig_comparative)
        
        st.markdown("""
        ## Understanding the Enhanced Model
        
        The comparative visualization demonstrates an important improvement: **path diversity**. 
        Even with identical parameters, each simulation produces a unique price path - just like real markets.
        
        ### Key Enhancements
        
        1. **Fat-Tailed Returns**: Student's t-distribution generates more realistic extreme events
        2. **Regime-Switching**: Markov model creates distinct market phases
        3. **GARCH Volatility**: Time-varying volatility with realistic persistence
        4. **Jump Process**: Occasional discontinuous price movements
        5. **Strategic Adaptation**: Manipulators respond to evolving conditions
        6. **Behavioral Elements**: Realistic trader psychology and biases
        7. **Liquidity Dynamics**: Market depth varies with conditions
        8. **Multi-Agent Interaction**: Complex emergent behaviors from simple rules
        
        These enhancements create much more realistic market behavior during manipulation events.
        """)
        
        # Add market regime analysis
        st.subheader("Market Regime Analysis")
        
        # Count occurrences of each regime
        regime_counts = [regimes.count(0), regimes.count(1), regimes.count(2)]
        regime_colors = ['rgba(99, 110, 250, 0.7)', 'rgba(239, 85, 59, 0.7)', 'rgba(0, 0, 0, 0.7)']
        
        fig_regimes = go.Figure()
        fig_regimes.add_trace(go.Bar(
            x=["Normal", "High Volatility", "Crisis"],
            y=regime_counts,
            marker_color=regime_colors
        ))
        
        fig_regimes.update_layout(
            title="Distribution of Market Regimes During Simulation",
            xaxis=dict(title="Regime Type"),
            yaxis=dict(title="Time Periods"),
        )
        
        st.plotly_chart(fig_regimes)
        
        st.markdown("""
        ## Application to Real Market Analysis
        
        The regime distribution provides insight into the stability of the market during the manipulation period. 
        Real pump and dump schemes often coincide with increased market instability and regime transitions.
        
        ### Implications for Detection
        
        1. **Regime Transitions**: Unusual transitions between market states can signal manipulation
        2. **Volatility Patterns**: GARCH-type volatility patterns differ during manipulation
        3. **Volume-Price Relationships**: Abnormal relationships can indicate manipulative activity
        4. **Order Flow Analysis**: Strategic order placement reveals manipulator footprints
        5. **Trader Composition Effects**: Market composition amplifies manipulation impact
        
        These advanced simulation elements provide a more robust framework for understanding 
        how market manipulation manifests in real financial markets with natural noise and complexity.
        """)