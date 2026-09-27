import streamlit as st

def inject_custom_css():
    """
    Injects the minimal, flat, professional F1 engineering workstation CSS.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

        /* ============================================================
           GLOBAL CANVAS THEME
        ============================================================ */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #0A0B0D !important;
            color: #E0E2E5 !important;
            font-family: 'Inter', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
        }

        /* HIDE STREAMLIT CHROME */
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stHeaderActionElements"] { display: none !important; }
        footer { visibility: hidden !important; }
        .stAppViewMainBlockContainer { padding-top: 1rem !important; padding-bottom: 2rem !important; }

        /* ============================================================
           SIDEBAR & INPUTS
        ============================================================ */
        [data-testid="stSidebar"] {
            background: #111317 !important;
            border-right: 1px solid #1E2129 !important;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stSelectbox > label,
        [data-testid="stWidgetLabel"] {
            font-family: 'Inter', sans-serif !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            color: #9BA2AE !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            margin-bottom: 4px !important;
        }

        /* Selectbox */
        div[data-baseweb="select"] > div {
            background: #181A20 !important;
            border: 1px solid #2B303B !important;
            border-radius: 4px !important;
            color: #FFFFFF !important;
            font-size: 13px !important;
        }

        div[data-baseweb="select"] > div:hover {
            border-color: #4A90E2 !important;
        }

        div[data-baseweb="popover"] ul {
            background: #181A20 !important;
            border: 1px solid #2B303B !important;
            border-radius: 4px !important;
        }

        div[data-baseweb="popover"] li {
            color: #FFFFFF !important;
            font-size: 13px !important;
        }

        div[data-baseweb="popover"] li:hover {
            background: #252830 !important;
        }

        /* Radio buttons */
        div[data-testid="stRadio"] div[role="radiogroup"] > label {
            background: #181A20 !important;
            border: 1px solid #2B303B !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            margin-bottom: 4px !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
            border-color: #4A90E2 !important;
            background: #1C2028 !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
            border-color: #4A90E2 !important;
            background: #1F2A38 !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] > label p {
            color: #D1D5DB !important;
            font-size: 13px !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] p {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Button */
        div.stButton > button {
            background: #1A1D24 !important;
            color: #FFFFFF !important;
            border: 1px solid #333842 !important;
            border-radius: 4px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            width: 100%;
        }

        div.stButton > button:hover {

        /* Base alert reset */
        div[data-testid="stAlert"] {
            border-radius: 6px !important;
            padding: 10px 14px !important;
            font-family: 'Inter', 'Inter', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        /* INFO   Cyan/teal theme */
        div[data-testid="stAlert"][data-baseweb="notification"][kind="info"],
        div[data-testid="stNotification"][kind="info"] {
            background: #333842 !important;
            border: 1px solid #333842 !important;
            border-left: 4px solid #4A90E2 !important;
            color: #A8D4F0 !important;
        }

        /* WARNING   Amber theme */
        div[data-testid="stAlert"][data-baseweb="notification"][kind="warning"],
        div[data-testid="stNotification"][kind="warning"] {
            background: rgba(255, 180, 0, 0.07) !important;
            border: 1px solid rgba(255, 180, 0, 0.3) !important;
            border-left: 4px solid #FFB400 !important;
            color: #FFD580 !important;
        }

        /* ERROR   Red theme */
        div[data-testid="stAlert"][data-baseweb="notification"][kind="error"],
        div[data-testid="stNotification"][kind="error"] {
            background: rgba(255, 0, 85, 0.08) !important;
            border: 1px solid rgba(255, 0, 85, 0.3) !important;
            border-left: 4px solid #EF4444 !important;
            color: #FF9AB8 !important;
        }

        /* SUCCESS   Green theme */
        div[data-testid="stAlert"][data-baseweb="notification"][kind="success"],
        div[data-testid="stNotification"][kind="success"] {
            background: rgba(0, 204, 100, 0.07) !important;
            border: 1px solid rgba(0, 204, 100, 0.3) !important;
            border-left: 4px solid #00CC64 !important;
            color: #80E8B8 !important;
        }

        /* Alert text */
        div[data-testid="stAlert"] p,
        div[data-testid="stNotification"] p {
            color: inherit !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        /* Alert icons */
        div[data-testid="stAlert"] svg, div[data-testid="stNotification"] svg {
            flex-shrink: 0 !important;
        }

        /* ============================================================
           TABS STYLING (NEON SEGMENTED CONTROLS)
        ============================================================ */
        div[data-testid="stTabs"] div[role="tablist"],
        div[role="tablist"] {
            display: flex !important;
            border-bottom: 2px solid #16243A !important;
            gap: 6px !important;
            padding-bottom: 0 !important;
            overflow: visible !important;
        }
        div[data-testid="stTabs"] button,
        div[data-testid="stTabs"] button[role="tab"],
        div[data-testid="stTabs"] [data-baseweb="tab"],
        button[data-baseweb="tab"] {
            background-color: rgba(8, 16, 30, 0.75) !important;
            color: #7A98B8 !important;
            border: 1px solid #16243A !important;
            border-bottom: none !important;
            border-radius: 6px 6px 0 0 !important;
            padding: 8px 14px !important;
            font-family: 'Inter', monospace !important;
            text-transform: uppercase !important;
            font-size: 10.5px !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            flex-grow: 1 !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        div[data-testid="stTabs"] button[aria-selected="true"],
        div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #4A90E2 !important;
            border-color: #4A90E2 !important;
            border-bottom: 2px solid #4A90E2 !important;

            background: linear-gradient(180deg, rgba(0,240,255,0.15) 0%, rgba(8,16,30,0.98) 100%) !important;
        }

        div[data-testid="stTabs"] button:hover,
        button[data-baseweb="tab"]:hover {
            color: #FFFFFF !important;
            border-color: #333842 !important;
            background-color: #333842 !important;
        }

        /* ============================================================
           METRIC CARDS - Fix truncation and improve contrast
        ============================================================ */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(8,14,24,0.9) 0%, rgba(3,6,12,0.95) 100%) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid #101B2B !important;
            border-top: 2px solid #4A90E2 !important;
            padding: 12px 14px !important;
            border-radius: 8px !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5) !important;
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease !important;
            overflow: visible !important;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-2px) !important;
            border-top-color: #EF4444 !important;
            box-shadow: 0 12px 30px #333842 !important;
        }

        /* Metric VALUE - large number/text */
        [data-testid="stMetricValue"] {
            color: #4A90E2 !important;
            font-size: 22px !important;
            font-weight: 900 !important;
            font-family: 'Share Tech Mono', monospace !important;

            white-space: normal !important;
            word-break: break-word !important;
        }

        /* Metric LABEL */
        [data-testid="stMetricLabel"] {
            color: #8FB4D4 !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            font-family: 'Inter', sans-serif !important;
            margin-bottom: 4px !important;
            white-space: normal !important;
            word-wrap: break-word !important;
        }

        /* Metric delta */
        [data-testid="stMetricDelta"] {
            font-size: 11px !important;
            font-weight: 600 !important;
        }

        /* ============================================================
           STATUS BAR ELEMENTS
        ============================================================ */
        .status-bar-label {
            color: #8FB4D4 !important;
            font-size: 11px !important;
            letter-spacing: 1.5px !important;
        }

        /* ============================================================
           SLIDERS
        ============================================================ */
        [data-testid="stSlider"] label,
        [data-testid="stSlider"] label p {
            color: #4A90E2 !important;
            font-size: 12px !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: 1.5px !important;
        }

        /* ============================================================
           DATA TABLE / DATAFRAME
        ============================================================ */
        div[data-testid="stDataFrame"] {
            border: 1px solid #101B2B !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }

        /* ============================================================
           COMMAND CENTER CARD SYSTEM (hud-card)
        ============================================================ */
        .hud-card {
            background: linear-gradient(135deg, rgba(8,14,24,0.95) 0%, rgba(3,6,12,0.98) 100%);
            backdrop-filter: blur(15px);
            border: 1px solid #333842;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.6);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .hud-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 100%; height: 3px;
            background: linear-gradient(90deg, #4A90E2, #333842, transparent);
        }

        .hud-card:hover {
            border-color: #333842;
            box-shadow: 0 12px 32px #333842, inset 0 0 15px #333842;
            transform: translateY(-2px);
        }

        /* Tactical HUD Card & Headers */
        .hud-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: rgba(10, 20, 36, 0.85);
            border-bottom: 1px solid #333842;
            margin-bottom: 10px;
            border-radius: 6px 6px 0 0;
        }
        .hud-panel-title {
            font-family: 'Inter', sans-serif;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #4A90E2;
            display: flex;
            align-items: center;
            gap: 7px;
            margin: 0;
        }
        .hud-status-badge {
            font-family: 'Share Tech Mono', monospace;
            font-size: 9.5px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 2px 7px;
            border-radius: 3px;
        }
        .hud-status-badge.active {
            background: #333842;
            border: 1px solid #4A90E2;
            color: #4A90E2;
        }
        .hud-status-badge.rec {
            background: rgba(255, 0, 85, 0.18);
            border: 1px solid #EF4444;
            color: #EF4444;
        }
        .hud-status-badge.info {
            background: rgba(255, 234, 0, 0.15);
            border: 1px solid #FFEA00;
            color: #FFEA00;
        }

        /* ============================================================
           TYRE RING BADGES
        ============================================================ */
        .tyre-ring {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid;
            font-size: 9.5px;
            font-weight: 900;
            font-family: 'Share Tech Mono', monospace;
        }

        /* Tyre Pills for Timing Tower & Stints */
        .tyre-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 17px;
            height: 17px;
            border-radius: 50%;
            font-size: 9px;
            font-weight: 900;
            font-family: 'Inter', monospace;
            margin-right: 4px;
            line-height: 1;
        }
        .tyre-s { background: #FF2B4D; color: #FFF; box-shadow: 0 0 5px rgba(255,43,77,0.6); }
        .tyre-m { background: #FFD21E; color: #000; box-shadow: 0 0 5px rgba(255,210,30,0.6); }
        .tyre-h { background: #F0F4F8; color: #000; box-shadow: 0 0 5px rgba(240,244,248,0.5); }
        .tyre-i { background: #00D06C; color: #000; }
        .tyre-w { background: #00A3FF; color: #FFF; }
        .tyre-u { background: #475569; color: #FFF; }

        /* ============================================================
           SECTOR TIMING BADGES
        ============================================================ */
        .sector-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 800;
            font-size: 10px;
            font-family: 'Share Tech Mono', monospace;
            display: inline-block;
        }

        .purple { background-color: #A020F0; color: white; box-shadow: 0 0 8px rgba(160,32,240,0.55); }
        .green  { background-color: #00CC64; color: #03060B; font-weight: 900; box-shadow: 0 0 8px rgba(0,204,100,0.55); }
        .yellow { background-color: #FFEA00; color: #03060B; font-weight: 900; box-shadow: 0 0 8px rgba(255,234,0,0.55); }
        .gray   { color: #4A6480; }

        /* ============================================================
           TIMING TABLE & SCROLLABLE CONTAINER
        ============================================================ */
        .timing-container {
            max-height: 520px;
            overflow-y: auto;
            overflow-x: hidden;
            border: 1px solid #1E2129;
            border-radius: 6px;
            background: #0E1015;
        }

        .timing-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            table-layout: fixed;
        }

        .timing-table th {
            position: sticky;
            top: 0;
            z-index: 5;
            background: #111317;
            color: #4A90E2;
            padding: 8px 6px;
            border-bottom: 2px solid #1E2129;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            white-space: nowrap;
            font-size: 10px;
        }

        .timing-table td {
            padding: 6px 6px;
            border-bottom: 1px solid #1E2129;
            white-space: nowrap;
            color: #C8D8E8;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 11px;
        }

        .timing-table tr:hover td {
            background: #333842;
        }

        .timing-table tr.primary-row td {
            background: #1a1215 !important;
            border-left: 3px solid #EF4444;
        }

        .timing-table tr.comp-row td {
            background: #333842 !important;
            border-left: 3px solid #4A90E2;
        }

        /* ============================================================
           SPINNERS AND LOADING STATES
        ============================================================ */
        [data-testid="stSpinner"] p {
            color: #8FB4D4 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
            letter-spacing: 1px !important;
        }

        /* ============================================================
           INFO / WARNING / ERROR BOXES
        ============================================================ */
        [data-testid="stAlert"] {
            border-radius: 6px !important;
        }

        /* ============================================================
           CHECKBOX
        ============================================================ */
        [data-testid="stSidebar"] [data-testid="stCheckbox"] label,
        [data-testid="stSidebar"] [data-testid="stCheckbox"] label p {
            color: #A8C4E0 !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        /* ============================================================
           SCROLLBAR STYLING
        ============================================================ */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
        ::-webkit-scrollbar-thumb { background: #1A3050; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #4A90E2; }

        /* ============================================================
           CAPTION & SMALL TYPOGRAPHY
        ============================================================ */
        [data-testid="stCaptionContainer"] p {
            color: #6B8BAA !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 11px !important;
            letter-spacing: 0.8px !important;
        }

        /* ============================================================
           DIVIDER LINE STYLING
        ============================================================ */
        [data-testid="stDivider"] {
            border-color: #333842 !important;
            margin: 16px 0 !important;
        }

        /* ============================================================
           CODE BLOCKS
        ============================================================ */
        code, pre {
            background: rgba(6, 14, 26, 0.92) !important;
            color: #4A90E2 !important;
            border: 1px solid #1A2E45 !important;
            border-radius: 4px !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 12px !important;
            padding: 2px 6px !important;
        }

        pre {
            padding: 12px 16px !important;
            color: #A8C4E0 !important;
        }

        /* ============================================================
           PROGRESS BARS
        ============================================================ */
        [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #4A90E2, #0088FF) !important;
            border-radius: 2px !important;
        }
        [data-testid="stProgressBar"] > div {
            background: rgba(10, 20, 36, 0.8) !important;
            border: 1px solid #1A2E45 !important;
            border-radius: 2px !important;
        }

        /* ============================================================
           MARKDOWN CODE BLOCK THEMING
        ============================================================ */
        .stMarkdown pre {
            background: rgba(6, 12, 22, 0.95) !important;
            border: 1px solid #333842 !important;
            border-radius: 6px !important;
            color: #A8D4F0 !important;
        }

        .stMarkdown code {
            background: #333842 !important;
            border: 1px solid #333842 !important;
            color: #4A90E2 !important;
            border-radius: 3px !important;
        }

        /* ============================================================
           DATAFRAME & TABLE ENHANCEMENTS
        ============================================================ */
        div[data-testid="stDataFrame"] {
            border: 1px solid #333842 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }

        /* Glassine panel backdrop for sections */
        div[data-testid="stVerticalBlock"] > div[data-testid="element-container"]:first-child {
            padding-top: 0 !important;
        }

        /* ============================================================
           CHECKBOX AND TOGGLE
        ============================================================ */
        [data-testid="stCheckbox"] label span[data-testid="stMarkdownContainer"] p {
            color: #A8C4E0 !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        /* ============================================================
           TEXT INPUT FIELDS
        ============================================================ */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            background: rgba(10, 18, 32, 0.95) !important;
            border: 1px solid #1E3050 !important;
            border-radius: 6px !important;
            color: #E8EDF5 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: #333842 !important;
            box-shadow: 0 0 10px #333842 !important;
            outline: none !important;
        }

        [data-testid="stTextInput"] label,
        [data-testid="stTextArea"] label {
            color: #8FB4D4 !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }

        /* ============================================================
           MAIN CONTENT AREA BACKGROUND - Layer 2
        ============================================================ */
        [data-testid="stAppViewBlockContainer"] {
            background: transparent !important;
        }

        /* Top Gradient Fade */
        [data-testid="stAppViewContainer"]::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 200px;
            background: linear-gradient(180deg, #333842 0%, transparent 100%);
            pointer-events: none;
            z-index: 0;
        }

        /* ============================================================
           RESPONSIVE ADJUSTMENTS
        ============================================================ */
        @media (max-width: 1440px) {
            [data-testid="stMetricValue"] {
                font-size: 20px !important;
            }
        }

        @media (max-width: 1366px) {
            [data-testid="stMetricValue"] {
                font-size: 17px !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 10px !important;
            }
            .hud-panel-title {
                font-size: 10px !important;
            }
        }

        @media (max-width: 1024px) {
            [data-testid="stMetricValue"] {
                font-size: 14px !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 9.5px !important;
            }
        }

    </style>
    """, unsafe_allow_html=True)


def render_standby_screen():
    """
    Displays the initial system state before data is synchronized.
    """
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; background: #111317; border: 1px solid #1E2129; padding: 10px 20px; border-radius: 4px; margin-bottom: 25px; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: #FFFFFF; letter-spacing: 1px; text-transform: uppercase;">ENGINEERING WORKSTATION</span>
            </div>
            <div style="display: flex; gap: 20px; align-items: center;">
                <span style="color: #9BA2AE; letter-spacing: 1px;">STATUS: <strong style="color: #EF4444; padding: 2px 8px; border: 1px solid #EF4444; border-radius: 3px; background: rgba(239,68,68,0.1);">OFFLINE</strong></span>
                <span style="color: #9BA2AE; letter-spacing: 1px;">LAST SYNC: <strong style="color: #D1D5DB;">--:--:--</strong></span>
                <span style="color: #9BA2AE; letter-spacing: 1px;">ENGINE: <strong style="color: #F59E0B;">STANDBY</strong></span>
            </div>
        </div>

    """, unsafe_allow_html=True)

    # Hero Title Banner
    st.markdown("""
        <div style="text-align: center; margin-bottom: 35px;">
            <h1 style="color: #4A90E2; font-family: 'Inter', sans-serif; font-weight: 900; font-size: 32px; letter-spacing: 6px;  margin: 0;">
                J.A.R.V.I.S. // ANTIGRAVITY ENGINE
            </h1>
            <p style="color: #8FB4D4; font-family: 'Inter', sans-serif; font-size: 12px; letter-spacing: 4px; margin-top: 10px;">
                TACTICAL F1 RACE INFERENCE CORE
            </p>
            <div style="width: 120px; height: 3px; background: linear-gradient(90deg, #4A90E2, #EF4444); margin: 15px auto 0 auto; border-radius: 2px; box-shadow: 0 0 10px #4A90E2;"></div>
        </div>
    """, unsafe_allow_html=True)

    # 6 Command Telemetry Metrics Strip
    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    with col_m1:
        st.metric("System Status", "OFFLINE")
    with col_m2:
        st.metric("Uplink", "IDLE")
    with col_m3:
        st.metric("Data Stream", "NO SIGNAL")
    with col_m4:
        st.metric("Engine Load", "0%")
    with col_m5:
        st.metric("Memory", "0%")
    with col_m6:
        st.metric("Uptime", "00:00:00")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3 High-Density Command Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="hud-card" style="border-left: 4px solid #4A90E2;">
            <div style="display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #142236; padding-bottom: 12px; margin-bottom: 15px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4A90E2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.9 19.1C1.9 16.1 1.9 11.4 4.9 8.5"/><path d="M7.8 16.2c-1.6-1.6-1.6-4.1 0-5.7"/><circle cx="12" cy="12" r="2"/><path d="M16.2 7.8c1.6 1.6 1.6 4.1 0 5.7"/><path d="M19.1 4.9c3 3 3 7.7 0 10.6"/></svg>
                <h4 style="color: #4A90E2; margin: 0; font-size: 14px; letter-spacing: 2px;">COMMUNICATIONS</h4>
            </div>
            <div style="font-size: 13px; color: #8FB4D4; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #C0D4E8;">TELEMETRY UPLINK</span>
                <span style="color: #4A90E2; font-weight: 700; font-family: 'Share Tech Mono', monospace;">[ IDLE ]</span>
            </div>
            <div style="font-size: 13px; color: #8FB4D4; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #C0D4E8;">GEOMETRY ENGINE</span>
                <span style="color: #EF4444; font-weight: 700; font-family: 'Share Tech Mono', monospace;">[ OFF ]</span>
            </div>
            <div style="text-align: right;">
                <span style="color: #4A90E2; font-size: 11px; font-weight: 700; font-family: 'Inter', sans-serif; cursor: pointer; letter-spacing: 1px;">VIEW DETAILS &gt;</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="hud-card" style="border-left: 4px solid #FFEA00;">
            <div style="display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #142236; padding-bottom: 12px; margin-bottom: 15px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFEA00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="m9 9 6 6"/><path d="m15 9-6 6"/></svg>
                <h4 style="color: #FFEA00; margin: 0; font-size: 14px; letter-spacing: 2px;">PROCESSING CORE</h4>
            </div>
            <div style="font-size: 13px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #C0D4E8;">JARVIS INFERENCE</span>
                <span style="color: #FFEA00; font-weight: 700; font-family: 'Share Tech Mono', monospace;">[ SLEEP ]</span>
            </div>
            <div style="font-size: 13px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #C0D4E8;">RACE CONTROL LOG</span>
                <span style="color: #EF4444; font-weight: 700; font-family: 'Share Tech Mono', monospace;">[ CLOSED ]</span>
            </div>
            <div style="text-align: right;">
                <span style="color: #FFEA00; font-size: 11px; font-weight: 700; font-family: 'Inter', sans-serif; cursor: pointer; letter-spacing: 1px;">VIEW DETAILS &gt;</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="hud-card" style="border-left: 4px solid #27F4D2;">
            <div style="display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #142236; padding-bottom: 12px; margin-bottom: 15px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#27F4D2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
                <h4 style="color: #27F4D2; margin: 0; font-size: 14px; letter-spacing: 2px;">PREDICTIVE MODELS</h4>
            </div>
            <div style="font-size: 13px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #C0D4E8;">PHYSICS SOLVER</span>
                <span style="color: #EF4444; font-weight: 700; font-family: 'Share Tech Mono', monospace;">[ PAUSED ]</span>
            </div>
            <div style="font-size: 13px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #C0D4E8;">DEGRADATION MODEL</span>
                <span style="color: #4A6480; font-weight: 700; font-family: 'Share Tech Mono', monospace;">[ N/A ]</span>
            </div>
            <div style="text-align: right;">
                <span style="color: #27F4D2; font-size: 11px; font-weight: 700; font-family: 'Inter', sans-serif; cursor: pointer; letter-spacing: 1px;">VIEW DETAILS &gt;</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Radar & System Notification Box
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(8, 14, 24, 0.92) 0%, rgba(4, 7, 14, 0.97) 100%); border: 1px solid #1A2E45; border-radius: 10px; padding: 25px; margin-top: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <div style="display: flex; align-items: center; gap: 25px;">
                <div style="flex-shrink: 0; width: 60px; height: 60px; border-radius: 50%; border: 2px solid #4A90E2; display: flex; align-items: center; justify-content: center; position: relative; box-shadow: 0 0 15px rgba(0,240,255,0.25);">
                    <div style="width: 40px; height: 40px; border-radius: 50%; border: 1px dashed rgba(0,240,255,0.4);"></div>
                    <div style="width: 6px; height: 6px; background: #EF4444; border-radius: 50%; position: absolute; top: 15px; right: 18px; box-shadow: 0 0 6px #EF4444;"></div>
                </div>
                <div>
                    <h5 style="color: #4A90E2; font-family: 'Inter', sans-serif; margin: 0 0 6px 0; letter-spacing: 2px; font-size: 12px;">SYSTEM MESSAGE</h5>
                    <p style="color: #C8D8E8; font-family: 'Share Tech Mono', monospace; margin: 0; font-size: 13px; letter-spacing: 0.8px; line-height: 1.5;">
                        AWAITING SYNCHRONIZATION PULSE. CONFIGURE SESSION PARAMETERS IN THE SIDEBAR AND INITIALIZE UPLINK.
                    </p>
                </div>
            </div>
            <div style="border-top: 1px solid #101B2B; margin-top: 20px; padding-top: 15px; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #4A6480; font-family: 'Inter', sans-serif; letter-spacing: 1.5px;">
                <span>ENGINEERED FOR PRECISION. BUILT FOR PERFORMANCE.</span>
                <span style="color: #EF4444; font-weight: 700;">FORMULA 1 // RACING INTELLIGENCE DIVISION</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_live_track_map(location_df):
    """
    Renders an animated, high-performance Plotly scatter map of live driver locations.
    Uses OpenF1 X/Y coordinates.
    """
    import plotly.graph_objects as go

    if location_df.empty or 'x' not in location_df.columns or 'y' not in location_df.columns:
        st.warning("Insufficient OpenF1 location data for track map rendering.")
        return

    latest_loc = location_df.groupby('driver_number').last().reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=latest_loc['x'],
        y=latest_loc['y'],
        mode='markers+text',
        marker=dict(
            size=14,
            color='#4A90E2',
            line=dict(width=2, color='white')
        ),
        text=latest_loc['driver_number'].astype(str),
        textposition="top center",
        textfont=dict(color="white", family='Inter', size=12),
        name="Drivers"
    ))

    fig.update_layout(
        plot_bgcolor='rgba(8, 14, 24, 0.9)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        title=dict(text="LIVE GPS TELEMETRY", font=dict(color="#4A90E2", family='Inter', size=18)),
        showlegend=False,
        dragmode='pan',
        hovermode='closest'
    )

    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def inject_hotkeys():
    import streamlit.components.v1 as components
    components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'textarea') return;

        let tabToClick = null;
        if (e.key === '1') tabToClick = "TIMING TOWER";
        if (e.key === '2') tabToClick = "TELEMETRY & PERFORMANCE";
        if (e.key === '3') tabToClick = "TYRE STRATEGY";
        if (e.key === '4') tabToClick = "TRACK";

        if (tabToClick) {
            const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
            for (let i = 0; i < tabs.length; i++) {
                if (tabs[i].innerText.includes(tabToClick)) {
                    tabs[i].click();
                    break;
                }
            }
        }
    });
    </script>
    """, height=0)
