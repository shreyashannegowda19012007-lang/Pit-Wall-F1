import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import textwrap
import bayesian_tyre_model

def render_jarvis_deck(raw_session, target_driver, laps, results, info):
    """
    Renders the AI tactical directive panel for a specific driver using the authoritative AIEngineerService.
    """
    header_html = textwrap.dedent(f"""
    <div class="hud-panel-header">
        <span class="hud-panel-title">TACTICAL QUERY SYSTEM</span>
        <span class="hud-status-badge active">{target_driver} DIRECTIVE</span>
    </div>
    """).strip()
    st.markdown(header_html, unsafe_allow_html=True)
    
    try:
        from ai_engineer_service import AIEngineerService
        from universal_session_engine import EventSessionInfo
        
        jarvis = AIEngineerService()
        
        query = st.text_input("TACTICAL QUERY", placeholder="e.g. Why are we losing time? or Should we pit?", key="jarvis_query", label_visibility="collapsed")
        
        # Determine comparison driver (just default to someone else for now or let UI pass it)
        comp_driver = st.session_state.get('comp_drv', 'HAM') if st.session_state.get('comp_drv') != target_driver else 'VER'
        
        if query:
            with st.spinner("Analyzing telemetry & strategy vectors..."):
                mc_outcomes = st.session_state.get('mc_outcomes', None)
                race_state = st.session_state.get('race_state', None)
                current_lap = int(laps['LapNumber'].max()) if not laps.empty and 'LapNumber' in laps.columns else 1
                
                resp = jarvis.process_query(
                    query=query,
                    primary_driver=target_driver,
                    ref_driver=comp_driver,
                    session=raw_session,
                    laps_df=laps,
                    race_state=race_state,
                    mc_outcomes=mc_outcomes,
                    current_lap=current_lap,
                    mode="REPLAY"
                )
                
                status_color = "#00CC64" if resp.get("data_status") == "SUCCESS" else "#FFB800"
                status_header = textwrap.dedent(f"""
                <div style="background: #0E1015; border: 1px solid #1E2129; border-left: 3px solid {status_color}; padding: 10px 14px; border-radius: 6px; margin-top: 10px; font-family: 'Inter', sans-serif;">
                    <div style="font-size: 10px; color: {status_color}; font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: 1px;">
                        STATUS: {resp.get('data_status', 'SUCCESS')}
                    </div>
                </div>
                """).strip()
                st.markdown(status_header, unsafe_allow_html=True)
                
                # Render answer markdown cleanly without enclosing indented HTML code block
                st.markdown(resp.get('answer_markdown', resp.get('answer', '')))
                
                # Render Evidence Citations if any
                if resp.get("evidence_citations"):
                    ev_header = textwrap.dedent("""
                    <div style="font-family: 'Inter', sans-serif; font-size: 10px; color: #8FB4D4; margin-top: 10px; letter-spacing: 1px;">
                        EVIDENCE CITATIONS
                    </div>
                    """).strip()
                    st.markdown(ev_header, unsafe_allow_html=True)
                    for cit in resp["evidence_citations"]:
                        st.caption(f"- [{cit.get('source_classification', cit.get('source', 'UNKNOWN'))}] {cit.get('metric', cit.get('parameter_name', 'Metric'))}: {cit.get('value')} (Source: {cit.get('tool_name', cit.get('source', 'System'))})")

    except Exception as e:
        st.error(f"Logic Engine Error: {e}")

def render_strategy_timeline(laps):
    """
    Visualizes the entire grid's compound history using a horizontal stacked Gantt chart.
    """
    st.markdown("### GRID-WIDE STRATEGY TIMELINE")
    
    try:
        # Group laps into stints: [Driver, Stint, Compound, LapCount]
        # We aggregate based on the unique combination of Driver and Stint
        stint_data = laps.groupby(['Driver', 'Stint', 'Compound']).agg({
            'LapNumber': 'count'
        }).reset_index()
        
        stint_data.columns = ['Driver', 'Stint', 'Compound', 'LapsCount']
        
        # Exact FIA Compound Color Mapping
        color_map = {
            'SOFT': '#FF3333',
            'MEDIUM': '#EAE210',
            'HARD': '#FFFFFF',
            'INTERMEDIATE': '#39B54A',
            'WET': '#00AEEF',
            'UNKNOWN': '#64748B'
        }

        fig = go.Figure()

        # Get unique drivers
        drivers = stint_data['Driver'].unique()

        for compound in stint_data['Compound'].unique():
            comp_df = stint_data[stint_data['Compound'] == compound]
            
            fig.add_trace(go.Bar(
                name=str(compound),
                y=comp_df['Driver'],
                x=comp_df['LapsCount'],
                orientation='h',
                marker=dict(
                    color=color_map.get(str(compound).upper(), '#64748B'),
                    line=dict(color='#05080F', width=1)
                ),
                customdata=comp_df['Stint'],
                hovertemplate="Driver: %{y}<br>Compound: " + str(compound) + "<br>Stint: %{customdata}<br>Laps: %{x}<extra></extra>"
            ))

        fig.update_layout(
            barmode='stack',
            height=max(400, len(drivers) * 25),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(
                title="Race Distance (Laps)",
                gridcolor='#1E293B',
                zeroline=False
            ),
            yaxis=dict(
                title=None,
                gridcolor='#1E293B',
                categoryorder='total descending'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Strategy Timeline Error: {e}")
