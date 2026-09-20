import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src import config
from plotly.subplots import make_subplots
import base64
import requests
import re
from typing import Dict, List, Any, Optional

# --- HELPER: GET DRIVER TEAM COLOR ---
def get_driver_color(driver: str, results_df: Optional[pd.DataFrame] = None) -> str:
    """
    Resolves driver abbreviation to official FIA team color with high contrast.
    """
    if results_df is not None and not results_df.empty:
        drv_row = results_df[results_df['Abbreviation'] == driver]
        if not drv_row.empty:
            color = drv_row.iloc[0].get('TeamColor')
            if pd.notna(color) and color != '':
                color = str(color).strip()
                if not color.startswith('#'):
                    return f"#{color}"
                return color
                
    # Fallbacks for key drivers if results dataframe doesn't resolve color
    fallbacks = {
        'VER': '#3671C6', 'PER': '#3671C6',
        'HAM': '#27F4D2', 'RUS': '#27F4D2',
        'LEC': '#E80020', 'SAI': '#E80020',
        'NOR': '#FF8000', 'PIA': '#FF8000',
        'ALO': '#229971', 'STR': '#229971',
        'GAS': '#0093CC', 'OCO': '#0093CC',
        'ALB': '#37BEDD', 'SAR': '#37BEDD',
        'TSU': '#52697F', 'RIC': '#52697F',
        'BOT': '#C92D4B', 'ZHO': '#C92D4B',
        'MAG': '#B6BABD', 'HUL': '#B6BABD'
    }
    return fallbacks.get(driver, '#4A90E2')

# --- 1. FUEL-CORRECTED PACE MATH ENGINE & SMOOTHING ---
def calculate_fuel_corrected_pace(laps_df: pd.DataFrame, fuel_burn_delta: float = 0.03) -> pd.DataFrame:
    """
    Applies linear mass reduction adjustment to raw lap times.
    Formula: t_corrected = t_raw - (L_total - L_current) * delta_t_fuel
    """
    df = laps_df.dropna(subset=['LapTime']).copy()
    if df.empty:
        return df
        
    df['LapTime_s'] = df['LapTime'].dt.total_seconds()
    
    # Calculate L_total dynamically per driver to handle DNFs cleanly
    df['L_total'] = df.groupby('Driver')['LapNumber'].transform('max')
    
    # Apply LaTeX pace correction formula
    df['FuelCorrected_s'] = df['LapTime_s'] - (df['L_total'] - df['LapNumber']) * fuel_burn_delta
    return df

def apply_tyre_smoothing(laps_df: pd.DataFrame, alpha: float = 0.3, fuel_burn_delta: float = 0.03) -> pd.DataFrame:
    """
    Applies Exponential Moving Average (EMA) smoothing stint-by-stint to filter out traffic noise.
    Formula: s_t = alpha * x_t + (1 - alpha) * s_{t-1}
    """
    df = calculate_fuel_corrected_pace(laps_df, fuel_burn_delta)
    if df.empty:
        return df
        
    smoothed_list = []
    for (driver, stint), group in df.groupby(['Driver', 'Stint']):
        group = group.sort_values('LapNumber')
        # ewm implements recursive EMA. adjust=False matches the mathematical recurrence exactly
        group['FuelCorrected_s'] = group['FuelCorrected_s'].ewm(alpha=alpha, adjust=False).mean()
        smoothed_list.append(group)
        
    if smoothed_list:
        return pd.concat(smoothed_list).sort_index()
    return df

def generate_fuel_pace_chart(laps_df: pd.DataFrame, results_df: pd.DataFrame, selected_drivers: List[str], fuel_burn_delta: float = 0.03, apply_ema: bool = False, ema_alpha: float = 0.3) -> go.Figure:
    """
    Renders Plotly comparison chart between raw, fuel-corrected, and EMA smoothed lap times.
    """
    fig = go.Figure()
    
    if apply_ema:
        corrected_df = apply_tyre_smoothing(laps_df, ema_alpha, fuel_burn_delta)
    else:
        corrected_df = calculate_fuel_corrected_pace(laps_df, fuel_burn_delta)
        
    if corrected_df.empty or not selected_drivers:
        return fig
        
    for drv in selected_drivers:
        drv_data = corrected_df[corrected_df['Driver'] == drv].sort_values('LapNumber')
        if drv_data.empty:
            continue
            
        color = get_driver_color(drv, results_df)
        
        # Raw Lap Time Trace
        fig.add_trace(go.Scatter(
            x=drv_data['LapNumber'],
            y=drv_data['LapTime_s'],
            mode='lines+markers',
            name=f"{drv} (Raw)",
            line=dict(color=color, width=1.5, dash='dot'),
            marker=dict(size=4),
            hovertemplate="Driver: %{text}<br>Lap: %{x}<br>Raw Time: %{y:.3f}s<extra></extra>",
            text=[drv] * len(drv_data)
        ))
        
        # Fuel-Corrected Pace Trace
        col_y = 'FuelCorrected_s'
        trace_label = "Fuel Corrected"
        if apply_ema:
            trace_label = "Fuel Corrected + EMA"
            
        fig.add_trace(go.Scatter(
            x=drv_data['LapNumber'],
            y=drv_data[col_y],
            mode='lines+markers',
            name=f"{drv} ({trace_label})",
            line=dict(color=color, width=3),
            marker=dict(size=5),
            hovertemplate=f"Driver: %{{text}}<br>Lap: %{{x}}<br>{trace_label} Time: %{{y:.3f}}s<extra></extra>",
            text=[drv] * len(drv_data)
        ))
        
    fig.update_layout(
        title=dict(text="FUEL-CORRECTED PACE EVOLUTION", font=dict(family="Share Tech Mono")),
        xaxis=dict(title="Lap Number", gridcolor="#1E293B"),
        yaxis=dict(title="Lap Time (Seconds)", gridcolor="#1E293B"),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


# --- 2. 25-ZONE DOMINANCE SPATIAL MAPPING ---
def generate_25_zone_map(raw_session: Any, results_df: pd.DataFrame) -> go.Figure:
    """
    Segments the track GPS coordinates into 25 micro-sectors, computes
    the fastest driver in each zone, and displays the dominant team colors.
    """
    fig = go.Figure()
    try:
        fastest_lap = raw_session.laps.pick_fastest()
        ref_tel = fastest_lap.get_telemetry().add_distance()
        
        if ref_tel.empty or 'X' not in ref_tel.columns:
            return fig
            
        D = ref_tel['Distance'].max()
        zone_boundaries = np.linspace(0, D, 26)
        
        # Determine dominance using top 10 competitive drivers
        drivers = results_df.head(10)['Abbreviation'].tolist()
        driver_telemetries = {}
        for d in drivers:
            try:
                if hasattr(raw_session.laps, 'pick_drivers'):
                    d_laps = raw_session.laps.pick_drivers(d)
                else:
                    d_laps = raw_session.laps[raw_session.laps['Driver'] == d]
                if not d_laps.empty:
                    d_lap = d_laps.pick_fastest()
                    d_tel = d_lap.get_telemetry().add_distance()
                    if not d_tel.empty:
                        driver_telemetries[d] = d_tel
            except Exception:
                pass
                
        if not driver_telemetries:
            return fig
            
        zone_winners = []
        for i in range(25):
            z_start = zone_boundaries[i]
            z_end = zone_boundaries[i+1]
            z_mid = (z_start + z_end) / 2.0
            
            best_speed = -1.0
            winner = None
            
            for d, d_tel in driver_telemetries.items():
                speed_at_mid = np.interp(z_mid, d_tel['Distance'], d_tel['Speed'])
                if speed_at_mid > best_speed:
                    best_speed = speed_at_mid
                    winner = d
            
            zone_winners.append(winner)
            
        plotted_drivers = set()
        for i in range(25):
            z_start = zone_boundaries[i]
            z_end = zone_boundaries[i+1]
            
            zone_mask = (ref_tel['Distance'] >= z_start) & (ref_tel['Distance'] <= z_end)
            zone_data = ref_tel[zone_mask]
            
            if zone_data.empty:
                continue
                
            if len(zone_data) < 2:
                idx = (ref_tel['Distance'] - z_mid).abs().idxmin()
                start_idx = max(0, idx - 1)
                end_idx = min(len(ref_tel) - 1, idx + 1)
                zone_data = ref_tel.iloc[start_idx:end_idx+1]
                
            winner = zone_winners[i]
            color = get_driver_color(winner, results_df)
            
            show_legend = winner not in plotted_drivers
            plotted_drivers.add(winner)
            
            fig.add_trace(go.Scatter(
                x=zone_data['X'],
                y=zone_data['Y'],
                mode='lines',
                line=dict(color=color, width=5),
                name=f"Zone {i+1} Dominant: {winner}",
                legendgroup=winner,
                showlegend=show_legend,
                hovertemplate=f"Zone {i+1}<br>Dominant: {winner}<extra></extra>"
            ))
            
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=40, b=10),
            title=dict(text="25-ZONE TRACK DOMINANCE SPATIAL MATRIX", font=dict(family="Share Tech Mono")),
            xaxis=dict(visible=False, constrain="domain"),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
            height=600,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        
    except Exception as e:
        st.error(f"Failed to generate Dominance Spatial Map: {e}")
        
    return fig


# --- 3. RACE TRACE ENGINE (CUMULATIVE DELTA & SHADOWS) ---
def generate_race_trace(laps_df: pd.DataFrame, results_df: pd.DataFrame, reference_driver: str) -> go.Figure:
    """
    Renders lap-by-lap cumulative gap delta curves with a dynamic lapped traffic bottom shadow.
    """
    fig = go.Figure()
    
    valid_laps = laps_df.dropna(subset=['Time']).copy()
    if valid_laps.empty:
        return fig
        
    valid_laps['SessionTime_s'] = valid_laps['Time'].dt.total_seconds()
    
    # Pivot session times
    time_pivot = valid_laps.pivot(index='LapNumber', columns='Driver', values='SessionTime_s')
    
    if reference_driver not in time_pivot.columns:
        return fig
        
    ref_times = time_pivot[reference_driver]
    gap_df = time_pivot.sub(ref_times, axis=0)
    
    # Add dynamic lapped traffic shadow region (bottom shadow)
    median_lap_time = 90.0
    ref_laps = laps_df[laps_df['Driver'] == reference_driver]
    if not ref_laps.empty:
        median_lap_time = ref_laps['LapTime'].dt.total_seconds().median()
        
    # Standard F1 race traces invert Y axis: 0 is at top, positive gaps (behind) go down.
    # We color the lapped zone at the bottom of the chart
    y_max_bound = max(gap_df.max().max(), median_lap_time + 60.0) if not gap_df.empty else 180.0
    fig.add_hrect(
        y0=median_lap_time,
        y1=y_max_bound,
        fillcolor="rgba(255, 0, 85, 0.08)", # Antigravity neon pink
        line_width=0,
        annotation_text="LAPPED TRAFFIC ZONE (BLUE FLAG SHADOW)",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color="#EF4444", family="Share Tech Mono")
    )
    
    for drv in gap_df.columns:
        drv_gaps = gap_df[drv].dropna()
        if drv_gaps.empty:
            continue
            
        color = get_driver_color(drv, results_df)
        
        # Base Gap Trace
        fig.add_trace(go.Scatter(
            x=drv_gaps.index,
            y=drv_gaps.values,
            mode='lines',
            name=drv,
            line=dict(color=color, width=2),
            hovertemplate="Driver: %{text}<br>Lap: %{x}<br>Delta vs Ref: %{y:.3f}s<extra></extra>",
            text=[drv] * len(drv_gaps)
        ))
        
        # Pitstop overlay
        drv_laps = valid_laps[valid_laps['Driver'] == drv]
        pit_laps = drv_laps[drv_laps['PitOutTime'].notna() | drv_laps['PitInTime'].notna()]
        pit_laps = pit_laps[pit_laps['LapNumber'].isin(drv_gaps.index)]
        if not pit_laps.empty:
            pit_gaps = drv_gaps.loc[pit_laps['LapNumber']]
            fig.add_trace(go.Scatter(
                x=pit_gaps.index,
                y=pit_gaps.values,
                mode='markers',
                marker=dict(color='#FF8000', size=8, symbol='circle', line=dict(color='#05080F', width=1)),
                name=f"{drv} Pitstop",
                legendgroup=drv,
                showlegend=False,
                hovertemplate="Driver: %{text}<br>Lap: %{x}<br>PIT STOP ACTION<extra></extra>",
                text=[drv] * len(pit_gaps)
            ))
            
        # Track limits overlay
        if 'Deleted' in drv_laps.columns:
            limit_laps = drv_laps[drv_laps['Deleted'] == True]
            limit_laps = limit_laps[limit_laps['LapNumber'].isin(drv_gaps.index)]
            if not limit_laps.empty:
                limit_gaps = drv_gaps.loc[limit_laps['LapNumber']]
                fig.add_trace(go.Scatter(
                    x=limit_gaps.index,
                    y=limit_gaps.values,
                    mode='markers',
                    marker=dict(color='#EF4444', size=8, symbol='triangle-up', line=dict(color='#05080F', width=1)),
                    name=f"{drv} Track Limits",
                    legendgroup=drv,
                    showlegend=False,
                    hovertemplate="Driver: %{text}<br>Lap: %{x}<br>TRACK LIMIT VIOLATION<extra></extra>",
                    text=[drv] * len(limit_gaps)
                ))
                
    fig.update_layout(
        title=dict(text=f"RACE TRACE (CUMULATIVE GAP IN SECONDS VS {reference_driver})", font=dict(family="Share Tech Mono")),
        xaxis=dict(title="Lap Number", gridcolor="#1E293B"),
        yaxis=dict(title="Gap to Reference (Seconds) [Inverted]", gridcolor="#1E293B", autorange="reversed"),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


# --- 4. LAP TIME HEATMAPS ---
def generate_pace_heatmap(laps_df: pd.DataFrame, selected_drivers: List[str]) -> go.Figure:
    """
    Generates thermal matrix grid showing absolute pace variations.
    """
    fig = go.Figure()
    if not selected_drivers:
        return fig
        
    df = laps_df.dropna(subset=['LapTime']).copy()
    if df.empty:
        return fig
        
    df['LapTime_s'] = df['LapTime'].dt.total_seconds()
    
    # Clip pit stops to prevent distortion
    min_lap = df['LapTime_s'].min()
    upper_threshold = min_lap * 1.15
    df['Pace_Clipped'] = df['LapTime_s'].clip(upper=upper_threshold)
    
    matrix = df[df['Driver'].isin(selected_drivers)].pivot(index='Driver', columns='LapNumber', values='Pace_Clipped')
    matrix_raw = df[df['Driver'].isin(selected_drivers)].pivot(index='Driver', columns='LapNumber', values='LapTime_s')
    
    if matrix.empty:
        return fig
        
    matrix = matrix.reindex(selected_drivers)
    matrix_raw = matrix_raw.reindex(selected_drivers)
    
    fig.add_trace(go.Heatmap(
        z=matrix.values,
        x=matrix.columns,
        y=matrix.index,
        colorscale=[[0, '#4A90E2'], [0.5, '#FFEA00'], [1, '#EF4444']],
        colorbar=dict(title="Clipped Pace (s)"),
        hoverongaps=False,
        text=matrix_raw.values,
        hovertemplate="Driver: %{y}<br>Lap: %{x}<br>Actual Pace: %{text:.3f}s<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text="GRID PACING THERMAL CLIFF MATRIX", font=dict(family="Share Tech Mono")),
        xaxis=dict(title="Lap Number"),
        yaxis=dict(title="Driver", categoryorder="array", categoryarray=selected_drivers[::-1]),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


# --- 5. DISTANCE-BASED CORNERING KINEMATICS ---
CIRCUIT_CORNERS = {
    "Spanish Grand Prix": [
        {"name": "T1 (Apex)", "distance": 620},
        {"name": "T3 (Apex)", "distance": 1050},
        {"name": "T4 (Apex)", "distance": 1420},
        {"name": "T5 (Apex)", "distance": 1720},
        {"name": "T7 (Apex)", "distance": 2150},
        {"name": "T9 (Apex)", "distance": 2580},
        {"name": "T10 (Apex)", "distance": 2900},
        {"name": "T12 (Apex)", "distance": 3320},
        {"name": "T13 (Apex)", "distance": 3600},
        {"name": "T14 (Apex)", "distance": 3900}
    ],
    "Monaco Grand Prix": [
        {"name": "T1 (Sainte Devote)", "distance": 280},
        {"name": "T3 (Massenet)", "distance": 800},
        {"name": "T4 (Casino)", "distance": 950},
        {"name": "T5 (Mirabeau)", "distance": 1250},
        {"name": "T6 (Grand Hotel)", "distance": 1400},
        {"name": "T8 (Portier)", "distance": 1600},
        {"name": "T9 (Tunnel)", "distance": 1850},
        {"name": "T10 (Chicane)", "distance": 2150},
        {"name": "T12 (Tabac)", "distance": 2500},
        {"name": "T13 (Swimming Pool)", "distance": 2750},
        {"name": "T18 (Rascasse)", "distance": 3150}
    ],
    "Silverstone Grand Prix": [
        {"name": "T1 (Abbey)", "distance": 320},
        {"name": "T3 (Loop)", "distance": 850},
        {"name": "T6 (Brooklands)", "distance": 2000},
        {"name": "T9 (Copse)", "distance": 2950},
        {"name": "T11 (Maggotts)", "distance": 3500},
        {"name": "T12 (Becketts)", "distance": 3750},
        {"name": "T15 (Stowe)", "distance": 4750},
        {"name": "T18 (Club)", "distance": 5600}
    ]
}

def detect_corners_from_speed(distance: np.ndarray, speed: np.ndarray) -> List[Dict[str, Any]]:
    """
    Finds corner apexes by identifying local minima in reference velocity profile.
    """
    corners = []
    s_speed = pd.Series(speed).rolling(window=15, center=True, min_periods=1).mean().values
    
    # Peak/Valley identifier
    for i in range(15, len(s_speed) - 15):
        if s_speed[i] < 190.0 and all(s_speed[i] <= s_speed[i+j] for j in range(-15, 16) if j != 0):
            # Check proximity to other turns to avoid duplicates
            if not corners or (distance[i] - corners[-1]['distance']) > 150:
                corners.append({
                    "name": f"T{len(corners)+1} (Apex)",
                    "distance": float(distance[i])
                })
    return corners

def generate_cornering_kinematics(raw_session: Any, results_df: pd.DataFrame, selected_drivers: List[str], gp_name: str) -> go.Figure:
    """
    Plots a 4-panel telemetry overlay mapped strictly against distance in meters.
    Includes vertical corner markers at turn apexes.
    """
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=("SPEED (km/h)", "THROTTLE (%)", "BRAKE", "GEAR")
    )
    
    if not selected_drivers:
        return fig
        
    line_colors = ['#4A90E2', '#EF4444', '#27F4D2', '#FFEA00', '#A020F0', '#FFFFFF']
    ref_tel = None
    
    for idx, drv in enumerate(selected_drivers):
        try:
            if hasattr(raw_session.laps, 'pick_drivers'):
                drv_laps = raw_session.laps.pick_drivers(drv)
            else:
                drv_laps = raw_session.laps[raw_session.laps['Driver'] == drv]
            if drv_laps.empty:
                continue
            drv_lap = drv_laps.pick_fastest()
            tel = drv_lap.get_telemetry().add_distance()
            if tel.empty:
                continue
                
            color = config.TEAM_COLORS.get(drv, line_colors[idx % len(line_colors)])
            if ref_tel is None:
                ref_tel = tel
                
            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Speed'], name=drv, line=dict(color=color, width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Throttle'], showlegend=False, line=dict(color=color, width=2)), row=2, col=1)
            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Brake'], showlegend=False, line=dict(color=color, width=2)), row=3, col=1)
            fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['nGear'], showlegend=False, line=dict(color=color, width=2, shape='hv')), row=4, col=1)
        except Exception:
            pass
            
    if ref_tel is None or ref_tel.empty:
        return fig
        
    # Add vertical apex indicators
    corners = None
    for key in CIRCUIT_CORNERS:
        if key.lower() in gp_name.lower():
            corners = CIRCUIT_CORNERS[key]
            break
            
    if not corners:
        corners = detect_corners_from_speed(ref_tel['Distance'].values, ref_tel['Speed'].values)
        
    for turn in corners:
        dist = turn['distance']
        name = turn['name']
        
        # Add line to all subplots
        for r in range(1, 5):
            fig.add_vline(x=dist, line=dict(color="rgba(148, 163, 184, 0.35)", width=1, dash="dash"), row=r, col=1)
            
        fig.add_annotation(
            x=dist,
            y=ref_tel['Speed'].max(),
            text=name,
            showarrow=False,
            font=dict(size=8, color="#94A3B8", family="Share Tech Mono"),
            textangle=-90,
            xshift=-5,
            yshift=-20,
            row=1, col=1
        )
        
    fig.update_layout(
        height=800,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        margin=dict(l=10, r=10, t=30, b=10)
    )
    fig.update_yaxes(range=[0, 105], row=2, col=1)
    fig.update_yaxes(range=[0, 9], row=4, col=1)
    return fig


# --- 6. Z-AXIS SYNCHRONIZATION VALIDATION ---
def validate_z_axis(raw_session: Any, driver_code: str, tolerance: float = 2.0) -> Dict[str, Any]:
    """
    Validates Z-Axis coordinates against smoothed reference track profiles.
    Drops corrupted packets.
    """
    try:
        ref_lap = raw_session.laps.pick_fastest()
        ref_tel = ref_lap.get_telemetry().add_distance()
        ref_tel['Z_smoothed'] = ref_tel['Z'].rolling(window=15, center=True, min_periods=1).mean()
        
        if hasattr(raw_session.laps, 'pick_drivers'):
            d_laps = raw_session.laps.pick_drivers(driver_code)
        else:
            d_laps = raw_session.laps[raw_session.laps['Driver'] == driver_code]
            
        if d_laps.empty:
            return {"success": False, "error": f"No telemetry for driver {driver_code}"}
            
        driver_lap = d_laps.pick_fastest()
        tel = driver_lap.get_telemetry().add_distance()
        
        if tel.empty or ref_tel.empty:
            return {"success": False, "error": "Missing telemetry streams"}
            
        tel['Z_ref'] = np.interp(tel['Distance'], ref_tel['Distance'], ref_tel['Z_smoothed'])
        tel['Z_delta'] = (tel['Z'] - tel['Z_ref']).abs()
        tel['Corrupted'] = tel['Z_delta'] > tolerance
        
        total_packets = len(tel)
        corrupted_packets = tel['Corrupted'].sum()
        drop_rate = (corrupted_packets / total_packets) * 100.0 if total_packets > 0 else 0.0
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=ref_tel['Distance'],
            y=ref_tel['Z_smoothed'],
            mode='lines',
            line=dict(color='#64748B', width=1.5, dash='dash'),
            name="Reference (Smoothed)"
        ))
        
        valid_tel = tel[~tel['Corrupted']]
        fig.add_trace(go.Scatter(
            x=valid_tel['Distance'],
            y=valid_tel['Z'],
            mode='lines',
            line=dict(color='#4A90E2', width=2),
            name="Uplink Verified"
        ))
        
        corrupt_tel = tel[tel['Corrupted']]
        if not corrupt_tel.empty:
            fig.add_trace(go.Scatter(
                x=corrupt_tel['Distance'],
                y=corrupt_tel['Z'],
                mode='markers',
                marker=dict(color='#EF4444', size=6, symbol='x'),
                name="Dropped Packet"
            ))
            
        fig.update_layout(
            title=dict(text=f"Z-AXIS TELEMETRY CORRELATION: {driver_code}", font=dict(family="Share Tech Mono")),
            xaxis=dict(title="Track Distance (meters)", gridcolor="#1E293B"),
            yaxis=dict(title="Elevation (meters)", gridcolor="#1E293B"),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        return {
            "success": True,
            "fig": fig,
            "total_packets": total_packets,
            "corrupted_packets": corrupted_packets,
            "drop_rate": drop_rate
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- 7. OPENF1 INGESTION & TEAM RADIO TIMELINE ---
def fetch_openf1_intervals(session_key: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Ingests live gap timings from OpenF1 API. Returns empty list if offline.
    """
    if not session_key:
        return []
        
    try:
        url = "https://api.openf1.org/v1/intervals"
        params = {'session_key': session_key}
        r = requests.get(url, params=params, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def fetch_openf1_radio(session_key: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetches team radio audio calls from OpenF1 endpoint. Returns empty list if offline.
    """
    if not session_key:
        return []

    try:
        url = "https://api.openf1.org/v1/team_radio"
        params = {'session_key': session_key}
        r = requests.get(url, params=params, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def map_radio_to_laps(laps_df: pd.DataFrame, radio_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Maps UTC team radio transcripts directly onto driver lap numbers.
    """
    mapped_radio = []
    
    date_col = 'LapStartDate' if 'LapStartDate' in laps_df.columns else 'Date'
    if date_col not in laps_df.columns:
        return mapped_radio
        
    df = laps_df.dropna(subset=[date_col, 'LapTime']).copy()
    if df.empty or not radio_data:
        return mapped_radio
        
    df['LapStartUtc'] = df[date_col] - df['LapTime']
    
    for msg in radio_data:
        try:
            msg_num = str(msg.get('driver_number'))
            msg_text = msg.get('transcript', '')
            msg_time_str = msg.get('date')
            if not msg_time_str:
                continue
                
            msg_time = pd.to_datetime(msg_time_str)
            
            drv_laps = df[df['DriverNumber'].astype(str) == msg_num]
            if drv_laps.empty:
                continue
                
            lap_match = drv_laps[(drv_laps['LapStartUtc'] <= msg_time) & (msg_time <= drv_laps[date_col])]
            if not lap_match.empty:
                lap_num = lap_match.iloc[0]['LapNumber']
                driver = lap_match.iloc[0]['Driver']
                mapped_radio.append({
                    "driver": driver,
                    "lap": int(lap_num),
                    "transcript": msg_text,
                    "timestamp": msg_time_str
                })
        except Exception:
            pass
            
    return mapped_radio

def generate_radio_timeline(laps_df: pd.DataFrame, results_df: pd.DataFrame, radio_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Renders timeline scatter map representing team radio tooltip markers.
    """
    fig = go.Figure()
    
    mapped_radio = map_radio_to_laps(laps_df, radio_data)
    if not mapped_radio:
        return fig
        
    radio_df = pd.DataFrame(mapped_radio)
    
    for drv in radio_df['driver'].unique():
        drv_radio = radio_df[radio_df['driver'] == drv]
        color = get_driver_color(drv, results_df)
        
        fig.add_trace(go.Scatter(
            x=drv_radio['lap'],
            y=drv_radio['driver'],
            mode='markers+text',
            name=drv,
            marker=dict(color=color, size=14, symbol='diamond', line=dict(color='#05080F', width=1.5)),
            text=drv_radio['lap'],
            textposition="top center",
            hovertext=drv_radio['transcript'],
            hovertemplate="Driver: %{y}<br>Lap: %{x}<br>Transcript: %{hovertext}<extra></extra>"
        ))
        
    fig.update_layout(
        title=dict(text="TEAM RADIO TIMELINE TOOLTIP OVERLAY", font=dict(family="Share Tech Mono")),
        xaxis=dict(title="Lap Number", gridcolor="#1E293B", dtick=1),
        yaxis=dict(title="Driver", gridcolor="#1E293B"),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=50, b=10),
        height=320
    )
    return fig


# --- 8. FIA DOCUMENT SCRAPER & VIEWER ---
FIA_YEAR_IDS = {
    2026: "2268",
    2025: "2268",
    2024: "2043",
    2023: "2037",
    2022: "2007",
    2021: "1798"
}

def fetch_fia_documents(year: int, event_name: str) -> List[Dict[str, str]]:
    """
    Scrapes the official FIA decision matrix index page for PDF files.
    Currently returns an empty list as real data is not yet available.
    """
    return []

def render_pdf_viewer(pdf_base64: str) -> None:
    """
    Renders the raw base64 encoded PDF document natively in an HTML iframe.
    """
    if not pdf_base64:
        st.warning("DOCUMENT DATA UNAVAILABLE.")
        return
    pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="500" type="application/pdf" style="border:1px solid #1E293B; border-radius:4px;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


