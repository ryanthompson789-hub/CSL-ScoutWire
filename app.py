import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="CSL Scoutwire", layout="wide")
st.title("🏀 CSL ScoutWire")

# --- SESSION STATE INITIALIZATION ---
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None

# Function to handle clicking a player name
def select_player(name):
    st.session_state.selected_player = name

# --- AESTHETIC LEAGUE LANDING PAGE (CLEAN FLOW) ---
st.markdown("""
    <style>
    /* Background and Global Font */
    .stApp { 
        background-color: #F8FAFC; 
    }
    /* Typography Styling */
    .league-title {
        color: #1E293B;
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0px;
        text-align: center;
    }
    .league-subtitle {
        color: #D4AF37;
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-bottom: 20px;
        text-align: center;
    }
    .instruction {
        color: #64748B;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 30px;
    }
    /* Custom Trophy Circle */
    .trophy-icon {
        font-size: 50px;
        background: white;
        border: 4px solid #D4AF37;
        width: 100px;
        height: 100px;
        line-height: 90px;
        border-radius: 50%;
        margin: 0 auto 30px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 1. League Branding Header
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Header Section
    st.markdown("<h1 class='league-title'>CHAMPION SIM LEAGUE</h1>", unsafe_allow_html=True)
    st.markdown("<p class='league-subtitle'>CSL Scouting Tool</p>", unsafe_allow_html=True)
    
    # Visual Separator
    st.markdown("<hr style='border: 2px solid #D4AF37; width: 40%; margin: 20px auto;'>", unsafe_allow_html=True)
    
    # 2. Icon and Instruction
    st.markdown('<div class="trophy-icon">🏆</div>', unsafe_allow_html=True)
    st.markdown("<p class='instruction'>Please upload league-standard scouting CSVs from CSLO to populate your draft data.</p>", unsafe_allow_html=True)

    # 3. The File Uploader (Centered via the column)
    uploaded_files = st.file_uploader("", accept_multiple_files=True, type=['csv'])

    # 4. Footer info
    st.markdown("<p style='color: #94A3B8; font-size: 0.8rem; text-align: center; margin-top: 40px; font-weight: bold;'>VERSION 1.0</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #CBD5E1; font-size: 0.7rem; text-align: center;'>Internal data for CSL GMs only.</p>", unsafe_allow_html=True)

# 5. Stop execution until files are uploaded
if not uploaded_files:
    st.stop()
    
# --- DATA PROCESSING ---
try:
    # 1. Combine all uploaded CSVs into one dataframe
    df_list = [pd.read_csv(file) for file in uploaded_files]
    df = pd.concat(df_list)
    
    # 2. THE SANITY FILTER
    if 'DRFL' in df.columns:
        df = df[df['DRFL'] <= 25]

    # 3. Define the Full Name
    df['Full_Name'] = df['First'].astype(str) + " " + df['Last'].astype(str)
    
    # 4. Standardize Column Names
    rename_map = {
        'POS': 'Pos', 'Pos': 'Pos',
        'AGE': 'AGE', 'Age': 'AGE',
        'HT': 'HT', 'Ht': 'HT', 'Height': 'HT',
        'WT': 'WT', 'Wt': 'WT', 'Weight': 'WT',
        'FROM': 'FROM', 'From': 'FROM', 'School': 'FROM'
    }
    df = df.rename(columns=rename_map)
    
    year_col = 'YEAR' 
    bio_cols = ['Pos', 'AGE', 'HT', 'WT', 'FROM']

    # --- CONVERT NUMERIC POSITIONS TO TEXT ---
    pos_map = {
        '1': 'PG', '2': 'SG', '3': 'SF', '4': 'PF', '5': 'C',
        1: 'PG', 2: 'SG', 3: 'SF', 4: 'PF', 5: 'C',
        1.0: 'PG', 2.0: 'SG', 3.0: 'SF', 4.0: 'PF', 5.0: 'C'
    }
    if 'Pos' in df.columns:
        df['Pos'] = df['Pos'].map(pos_map).fillna(df['Pos'])
        
    # 1. Stats used for GRAPHING
    core_stats = ['SCR', 'PAS', 'HDL', 'ORB', 'DRB', 'BLK', 'STL', 'DEF', 'DIS', 'IQ', 'DRFL']
    
    # 2. Stats used for CALCULATING Ratings
    calc_stats = ['SCR', 'PAS', 'HDL', 'ORB', 'DRB', 'BLK', 'STL', 'DEF', 'IQ']
    
    # Generate potential versions
    pot_stats = [s + '_POT' for s in core_stats]
    calc_pot = [s + '_POT' for s in calc_stats]
    
    shoot_stats = ['FG_RA', 'FG_ITP', 'FG_MID', 'FG_COR', 'FG_ATB', 'FT']
    shoot_pot = [s + '_POT' for s in shoot_stats]
    
    all_numeric_stats = core_stats + pot_stats + shoot_stats + shoot_pot + ["DriveKick", "DriveShot", "PostUp", "PullUp", "CS", "PASS", "LocATB", "LocCorner", "LodMid", "LocPaint", "DUNK RATE", "RIM AREA RATE"]
    
    existing_numeric = [s for s in all_numeric_stats if s in df.columns]
    existing_bio = [col for col in bio_cols if col in df.columns]
    if year_col in df.columns:
        existing_bio.append(year_col)

    player_stats = df.groupby('Full_Name').agg({
        **{stat: 'mean' for stat in existing_numeric},
        **{bio: 'first' for bio in existing_bio}
    }).reset_index()
    
    if year_col in player_stats.columns:
        player_stats[year_col] = player_stats[year_col].astype(str).str.replace('.0', '', regex=False)
    
    # --- THE KEY CALCULATIONS ---
    player_stats['Current_Rating'] = player_stats[calc_stats].mean(axis=1)
    player_stats['Overall_Pot'] = player_stats[calc_pot].mean(axis=1)
    player_stats['Growth_Score'] = player_stats['Overall_Pot'] - player_stats['Current_Rating']

except Exception as e:
    st.error(f"⚠️ Error processing data: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("🔍 Database Filters")
if year_col in player_stats.columns:
    available_years = sorted(player_stats[year_col].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Select Draft Year", available_years)
    filtered_stats = player_stats[player_stats[year_col] == selected_year]
else:
    filtered_stats = player_stats
    selected_year = "All"

all_positions = sorted(filtered_stats['Pos'].unique())
    
st.sidebar.header(f"🚀 Top Growth ({selected_year})")
project_board = filtered_stats.sort_values(by='Growth_Score', ascending=False).head(5)

for i, row in project_board.iterrows():
    if st.sidebar.button(f"{row['Full_Name']} (+{row['Growth_Score']:.1f})", key=f"side_{row['Full_Name']}"):
        st.session_state.selected_player = row['Full_Name']

tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Individual Prospect Scout", 
    "🎯 Advanced Player Finder", 
    "📋 Draft War Room", 
    "📈 Strategy & Analysis"
])
    
with tab1:
    player_list = list(filtered_stats['Full_Name'].unique())
    
    # 1. Sync session state with the list
    if 'selected_player' not in st.session_state or st.session_state.selected_player not in player_list:
        st.session_state.selected_player = player_list[0]
    
    # 2. Get the row number for the dropdown
    default_index = player_list.index(st.session_state.selected_player)

    # 3. The Dropdown Menu
    selected_player = st.selectbox(
        "Select Primary Prospect", 
        player_list, 
        index=default_index
    )
    
    # Update state if the user manually clicks the dropdown
    st.session_state.selected_player = selected_player

    # --- CRITICAL FIX: DEFINE p_data HERE ---
    p_data = filtered_stats[filtered_stats['Full_Name'] == selected_player].iloc[0]

    # --- ADVANCED SCOUTING REPORT FUNCTION ---
    def generate_scout_report(player, df_context):
        # We use a try/except here just in case a numeric column is missing
        try:
            avg = df_context.mean(numeric_only=True)
            high_traits = [stat for stat in ['SCR', 'DEF', 'PAS', 'IQ', 'BLK', 'STL', 'ORB'] 
                           if stat in player and player[stat] > avg[stat] + 8]
            
            archetype = "Well-Rounded Prospect"
            if player.get('SCR', 0) >= 65 and player.get('FG_ATB', 0) > 38:
                archetype = "Dynamic Perimeter Scorer"
            elif player.get('DEF', 0) >= 65 and (player.get('BLK', 0) > 55 or player.get('STL', 0) > 60):
                archetype = "High-Impact Defensive Specialist"
            elif player.get('PAS', 0) >= 70 and player.get('IQ', 0) >= 70:
                archetype = "High-IQ Playmaker"
            elif player.get('ORB', 0) >= 70 or player.get('BLK', 0) >= 55:
                archetype = "Interior Anchor"

            if player.get('SCR', 0) >= 70 and player.get('DEF', 0) >= 70:
                archetype = "Elite Two-Way Threat"

            habits = []
            if player.get('DriveKick', 0) > 7: habits.append("attacking the paint to collapse defenses and find the open man")
            if player.get('CS', 0) > 10: habits.append("finding space as a catch-and-shoot threat")
            if player.get('PostUp', 0) > 8: habits.append("using their size in the low post")
            if player.get('DriveShot', 0) > 8: habits.append("attacking the paint looking to finish at the rim")
            
            habit_str = f" often seen {habits[0]}" if habits else " playing within the flow of the offense"

            shot_note = ""
            if player.get('FG_COR', 0) > 38:
                shot_note = "He is particularly dangerous from the corners,"
            elif player.get('FG_RA', 0) > 60:
                shot_note = "He is an elite finisher at the rim,"
            elif player.get('FG_ATB', 0) > 38:
                shot_note = "He is an above average shooter from above the break,"
            elif player.get('FT', 0) > 80:
                shot_note = "He has been shooting over 80% from the free throw line in college,"
            
            growth_diff = player['Growth_Score'] - avg['Growth_Score']
            if growth_diff > 5:
                upside_type = "is a 'high-ceiling' project that scouts are buzzing about"
            elif growth_diff < -5:
                upside_type = "is one of the most 'pro-ready' players in the class, though his room for growth is smaller"
            else:
                upside_type = "shows a steady developmental curve"

            return (
                f"**{player['Full_Name']}** projects as a **{archetype}** who {upside_type}. "
                f"Compared to the {selected_year} class average, his {', '.join(high_traits) if high_traits else 'fundamentals'} "
                f"stand out immediately. You'll find him{habit_str}. {shot_note} "
                f"while his long-term success will depend on reaching that **{player['Overall_Pot']:.1f}** ceiling."
            )
        except:
            return "Scouting report unavailable for this prospect."

    # --- START UI RENDERING ---
    # Now that p_data is defined, these lines will no longer error
    st.markdown(f"## {selected_player} | Class of {p_data.get(year_col, 'N/A')}")
    
    # Bio Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    if 'Pos' in p_data: c1.metric("Position", p_data['Pos'])
    if 'AGE' in p_data: c2.metric("Age", str(int(float(p_data['AGE']))))
    if 'HT' in p_data: c3.metric("Height", p_data['HT'])
    if 'WT' in p_data: c4.metric("Weight", str(p_data['WT']))
    if 'FROM' in p_data: c5.metric("School/From", str(p_data['FROM']))

    st.divider()

    # Executive Summary
    with st.expander("📝 Scouting Director's Executive Summary", expanded=True):
        st.write(generate_scout_report(p_data, filtered_stats))

    # Scouting Intelligence (Ranking Logic)
    pos_peers = filtered_stats[filtered_stats['Pos'] == p_data['Pos']].copy()
    total_in_pos = len(pos_peers)
    total_in_class = len(filtered_stats)
    
    def get_ranks(stat_name):
        pos_ranks = pos_peers[stat_name].rank(ascending=False, method='min')
        p_idx = list(pos_peers['Full_Name']).index(selected_player)
        p_rank = int(pos_ranks.iloc[p_idx])
        class_ranks = filtered_stats[stat_name].rank(ascending=False, method='min')
        c_idx = list(filtered_stats['Full_Name']).index(selected_player)
        c_rank = int(class_ranks.iloc[c_idx])
        return p_rank, c_rank

    st.subheader(f"📍 Scouting Intelligence")
    st.caption(f"Comparing to **{total_in_pos}** {p_data['Pos']}s and **{total_in_class}** total prospects in the {selected_year} class.")

    intel_tab_cur, intel_tab_pot = st.tabs(["📊 Current Ability Ranks", "🚀 Future Potential Ranks"])
    core_keys = ['SCR', 'PAS', 'HDL', 'ORB', 'DRB', 'DEF', 'STL', 'BLK', 'IQ']
    shoot_keys = ['FG_RA', 'FG_ITP', 'FG_MID', 'FG_COR', 'FG_ATB', 'FT']
    
    for intel_tab, suffix in [(intel_tab_cur, ""), (intel_tab_pot, "_POT")]:
        with intel_tab:
            m1, m2 = st.columns(2)
            if suffix == "":
                p_r, c_r = get_ranks('Current_Rating')
                m1.metric("Overall Readiness", f"#{p_r} in Pos", f"#{c_r} Overall", delta_color="off")
            else:
                p_r, c_r = get_ranks('Overall_Pot')
                m1.metric("Overall Ceiling", f"#{p_r} in Pos", f"#{c_r} Overall", delta_color="off")

            st.write("---")
            st.write("**Core Skills**")
            cols = st.columns(len(core_keys))
            for i, key in enumerate(core_keys):
                stat_key = key + suffix
                if stat_key in p_data:
                    p_r, c_r = get_ranks(stat_key)
                    cols[i].metric(key, f"#{p_r}", f"#{c_r} OVR", delta_color="off")

            st.write("**Shooting Profile**")
            cols_s = st.columns(len(shoot_keys))
            for i, key in enumerate(shoot_keys):
                stat_key = key + suffix
                if stat_key in p_data:
                    p_r, c_r = get_ranks(stat_key)
                    label = key.replace("FG_", "")
                    cols_s[i].metric(label, f"#{p_r}", f"#{c_r} OVR", delta_color="off")

    st.divider()

    # --- MIDDLE UI: GRAPHS ---
    col_a, col_b = st.columns(2)
    with col_a:
        fig_main = go.Figure()
        fig_main.add_trace(go.Bar(x=core_stats, y=p_data[core_stats].values, name='Current', marker_color='royalblue'))
        fig_main.add_trace(go.Bar(x=core_stats, y=p_data[pot_stats].values, name='Potential', marker_color='lightskyblue', opacity=0.4, width=0.8))
        fig_main.update_layout(title="Core Development", barmode='overlay', yaxis=dict(range=[0, 100]), height=350, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_main, use_container_width=True)

    with col_b:
        available_shoot = [s for s in shoot_stats if s in p_data.index]
        available_shoot_pot = [s + '_POT' for s in available_shoot if s + '_POT' in p_data.index]
        fig_shoot = go.Figure()
        fig_shoot.add_trace(go.Bar(x=available_shoot, y=p_data[available_shoot].values, name='Current', marker_color='darkorange'))
        fig_shoot.add_trace(go.Bar(x=available_shoot, y=p_data[available_shoot_pot].values, name='Potential', marker_color='gold', opacity=0.4, width=0.8))
        fig_shoot.update_layout(title="Shooting Development", barmode='overlay', yaxis=dict(range=[0, 100]), height=350, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_shoot, use_container_width=True)

    # --- BOTTOM UI: HABITS ---
    st.divider()
    st.subheader("📌 Tendencies & Floor Habits")
    h_col1, h_col2, h_col3 = st.columns([1, 1, 1.5])
    
    with h_col1:
        floor_acts = ["DriveKick", "DriveShot", "PostUp", "PullUp", "CS", "PASS"]
        available_floor = [h for h in floor_acts if h in p_data.index]
        if available_floor:
            fig_p1 = px.pie(names=available_floor, values=p_data[available_floor].values, title="Action Tendencies", hole=0.4)
            st.plotly_chart(fig_p1, use_container_width=True)
            
    with h_col2:
        floor_locs = ["LocATB", "LocCorner", "LodMid", "LocPaint"]
        available_locs = [h for h in floor_locs if h in p_data.index]
        if available_locs:
            fig_p2 = px.pie(names=available_locs, values=p_data[available_locs].values, title="Shot Locations", hole=0.4)
            st.plotly_chart(fig_p2, use_container_width=True)
            
    with h_col3:
        freq_list = ["DUNK RATE", "RIM AREA RATE"]
        available_freq = [h for h in freq_list if h in p_data.index]
        if available_freq:
            freq_values = pd.to_numeric(p_data[available_freq], errors='coerce').round(1)
            fig_freq = go.Figure(go.Bar(x=freq_values.values, y=available_freq, orientation='h', marker_color='indianred', text=freq_values.values, textposition='auto'))
            fig_freq.update_layout(title="Finishing Profile", xaxis=dict(range=[0, 100]), height=250, margin=dict(l=150, r=20, t=40, b=20), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_freq, use_container_width=True)

    # --- COMPARISON TOOL (Keep inside Tab 1) ---
    st.divider()
    st.header("⚔️ Prospect Comparison Tool")
    comp_player = st.selectbox("Select Player to Compare", ["None"] + list(player_stats['Full_Name'].unique()))

    if comp_player != "None":
        c_data = player_stats[player_stats['Full_Name'] == comp_player].iloc[0]
        st.write("### 📊 Core Skills Comparison")
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.write("**Current Ability**")
            f1 = go.Figure()
            f1.add_trace(go.Bar(x=core_stats, y=p_data[core_stats].values, name=selected_player, marker_color='#1E90FF'))
            f1.add_trace(go.Bar(x=core_stats, y=c_data[core_stats].values, name=comp_player, marker_color='#B22222'))
            f1.update_layout(barmode='group', yaxis=dict(range=[0, 100]), height=300, margin=dict(l=20,r=20,t=30,b=20))
            st.plotly_chart(f1, use_container_width=True)
        with r1c2:
            st.write("**Future Potential**")
            f2 = go.Figure()
            f2.add_trace(go.Bar(x=core_stats, y=p_data[pot_stats].values, name=selected_player, marker_color='#00BFFF'))
            f2.add_trace(go.Bar(x=core_stats, y=c_data[pot_stats].values, name=comp_player, marker_color='#DC143C'))
            f2.update_layout(barmode='group', yaxis=dict(range=[0, 100]), height=300, margin=dict(l=20,r=20,t=30,b=20))
            st.plotly_chart(f2, use_container_width=True)

        st.write("### 🎯 Shooting Profile Comparison")
        r2c1, r2c2 = st.columns(2)
        
        available_shoot = [s for s in shoot_stats if s in p_data.index and s in c_data.index]
        available_shoot_pot = [s + '_POT' for s in available_shoot if s + '_POT' in p_data.index]
        shoot_labels = [s.replace('FG_', '') for s in available_shoot]

        with r2c1:
            st.write("**Current Shooting**")
            f3 = go.Figure()
            f3.add_trace(go.Bar(x=shoot_labels, y=p_data[available_shoot].values, name=selected_player, marker_color='#FF8C00')) # Dark Orange
            f3.add_trace(go.Bar(x=shoot_labels, y=c_data[available_shoot].values, name=comp_player, marker_color='#8B0000')) # Dark Red
            f3.update_layout(barmode='group', yaxis=dict(range=[0, 100]), height=300, margin=dict(l=20,r=20,t=30,b=20))
            st.plotly_chart(f3, use_container_width=True)

        with r2c2:
            st.write("**Potential Shooting**")
            f4 = go.Figure()
            f4.add_trace(go.Bar(x=shoot_labels, y=p_data[available_shoot_pot].values, name=selected_player, marker_color='#FFD700')) # Gold
            f4.add_trace(go.Bar(x=shoot_labels, y=c_data[available_shoot_pot].values, name=comp_player, marker_color='#FF4500')) # Orange Red
            f4.update_layout(barmode='group', yaxis=dict(range=[0, 100]), height=300, margin=dict(l=20,r=20,t=30,b=20))
            st.plotly_chart(f4, use_container_width=True)

with tab2:
    st.header("🎯 Advanced Player Finder")
    
    # --- 1. SEARCH LENS ---
    st.write("### 1. Choose Scouting Lens")
    stat_mode = st.radio(
        "Filter based on current ability or projected peak?", 
        ["Current Ratings", "Potential Ratings"], 
        horizontal=True
    )
    suffix = "_POT" if stat_mode == "Potential Ratings" else ""
    
    st.divider()

    # --- 2. SKILL THRESHOLDS ---
    st.write("### 2. Set Skill Thresholds")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Offense**")
        min_scr  = st.slider("Scoring (SCR)", 0, 100, 0)
        min_pas  = st.slider("Passing (PAS)", 0, 100, 0)
        min_hdl  = st.slider("Handling (HDL)", 0, 100, 0)
        min_drfl = st.slider("Draw Foul (DRFL)", 0, 100, 0)
        min_iq   = st.slider("Bball IQ", 0, 100, 0)

    with col2:
        st.markdown("**Defense & Glass**")
        min_def = st.slider("Defense (DEF)", 0, 100, 0)
        min_blk = st.slider("Blocking (BLK)", 0, 100, 0)
        min_stl = st.slider("Steals (STL)", 0, 100, 0)
        min_dis = st.slider("Discipline (DIS)", 0, 100, 0)
        min_orb = st.slider("Off. Rebs (ORB)", 0, 100, 0)
        min_drb = st.slider("Def. Rebs (DRB)", 0, 100, 0)

    with col3:
        st.markdown("**Shooting Profile**")
        min_ra  = st.slider("Restricted Area (RA)", 0, 100, 0)
        min_itp = st.slider("In The Paint (ITP)", 0, 100, 0) # Added ITP here
        min_mid = st.slider("Mid-Range", 0, 100, 0)
        min_cor = st.slider("Corner 3s", 0, 100, 0)
        min_atb = st.slider("Above Break 3s", 0, 100, 0)
        min_ft  = st.slider("Free Throw (FT)", 0, 100, 0)

    st.divider()

    # --- 3. POSITION FILTER ---
    pos_filter = st.multiselect("Filter by Position", options=all_positions, default=all_positions)

    # --- 4. QUERY LOGIC ---
    query_df = filtered_stats[
        (filtered_stats['Pos'].isin(pos_filter)) &
        (filtered_stats['SCR' + suffix] >= min_scr) &
        (filtered_stats['DRFL' + suffix] >= min_drfl) &
        (filtered_stats['PAS' + suffix] >= min_pas) &
        (filtered_stats['HDL' + suffix] >= min_hdl) &
        (filtered_stats['IQ' + suffix] >= min_iq) &
        (filtered_stats['DEF' + suffix] >= min_def) &
        (filtered_stats['DIS' + suffix] >= min_dis) &
        (filtered_stats['BLK' + suffix] >= min_blk) &
        (filtered_stats['STL' + suffix] >= min_stl) &
        (filtered_stats['ORB' + suffix] >= min_orb) &
        (filtered_stats['DRB' + suffix] >= min_drb) &
        (filtered_stats['FG_RA' + suffix] >= min_ra) &
        (filtered_stats['FG_ITP' + suffix] >= min_itp) & # Included in query
        (filtered_stats['FG_MID' + suffix] >= min_mid) &
        (filtered_stats['FG_COR' + suffix] >= min_cor) &
        (filtered_stats['FG_ATB' + suffix] >= min_atb) &
        (filtered_stats['FT' + suffix] >= min_ft)
    ]

 # --- 5. RESULTS DISPLAY ---
    st.subheader(f"🔍 Matches Found: {len(query_df)}")
    
    if not query_df.empty:
        base_cols = ['Full_Name', 'Pos', 'Overall_Pot']
        ratings_to_show = [
            'SCR', 'PAS', 'HDL', 'DRFL', 'IQ', 
            'DEF', 'DIS', 'BLK', 'STL', 'ORB', 'DRB',
            'FG_RA', 'FG_ITP', 'FG_MID', 'FG_COR', 'FG_ATB', 'FT'
        ]
        
        display_columns = base_cols + [r + suffix for r in ratings_to_show]
        existing_cols = [c for c in display_columns if c in query_df.columns]
        
        # --- THE ROUNDING FIX ---
        # 1. Select only the columns we want to show
        # 2. Round to 0 decimals
        # 3. Convert to 'Int64' to ensure no '.0' appears
        final_table = query_df[existing_cols].copy()
        
        # We only round the columns that are actually numbers (ratings)
        numeric_cols = [c for c in existing_cols if c not in ['Full_Name', 'Pos']]
        final_table[numeric_cols] = final_table[numeric_cols].round(0).astype('Int64')

        st.dataframe(
            final_table.sort_values('Overall_Pot', ascending=False), 
            use_container_width=True
        )

        st.divider()
        
        # --- THE TELEPORT BUTTON ---
        st.write("### 🚀 Launch Report")
        target_player = st.selectbox("Select Prospect to View in Tab 1", query_df['Full_Name'].unique())
        
        if st.button(
            f"View Full Report for {target_player}", 
            use_container_width=True,
            type="primary"
        ):
            # 1. Update the session state (the "Teleport" logic)
            st.session_state.update({"selected_player": target_player})
            
            # 2. Trigger the sleek "toast" notification in the corner
            st.toast(f"Report for {target_player} loaded.", icon="📋")
            
            # 3. Add the clear instructions box
            st.success(f"**Success!** {target_player}'s profile is ready. Please click the **Individual Prospect Scout** tab at the top of your screen to view the report. ⬆️")
        
with tab3:
    st.header(f"📋 {selected_year} Draft War Room")
    
    # This filter ONLY affects the War Room table
    war_room_pos = st.multiselect("Filter Table by Position", options=all_positions, default=all_positions)
    
    # Apply the filter to create the war room dataframe
    bb_df = filtered_stats[filtered_stats['Pos'].isin(war_room_pos)].copy()
    bb_df['My Rank'] = 0
    
    # 1. Stat Pairs for the (C/P) columns
    stat_pairs = {
        'SCR': 'SCR_POT', 'PAS': 'PAS_POT', 'HDL': 'HDL_POT', 
        'ORB': 'ORB_POT', 'DRB': 'DRB_POT', 'BLK': 'BLK_POT', 
        'STL': 'STL_POT', 'DEF': 'DEF_POT', 'IQ': 'IQ_POT',
        'FG_RA': 'FG_RA_POT', 'FG_ITP': 'FG_ITP_POT', 'FG_MID': 'FG_MID_POT',
        'FG_COR': 'FG_COR_POT', 'FG_ATB': 'FG_ATB_POT', 'FT': 'FT_POT'
    }

    combined_cols = []
    for cur, pot in stat_pairs.items():
        if cur in bb_df.columns and pot in bb_df.columns:
            display_name = f"{cur.replace('FG_', '')} (C/P)"
            bb_df[display_name] = bb_df[cur].fillna(0).astype(float).round(0).astype(int).astype(str) + " / " + \
                                  bb_df[pot].fillna(0).astype(float).round(0).astype(int).astype(str)
            combined_cols.append(display_name)

    # 2. Define Columns
    bio_cols = ['My Rank', 'Full_Name', 'Pos', 'Current_Rating', 'Overall_Pot', 'Growth_Score']
    existing_cols = [c for c in bio_cols + combined_cols if c in bb_df.columns]
    
    summary_df = bb_df[existing_cols].sort_values(by='Overall_Pot', ascending=False)

    # 3. Enhanced Table Configuration
    edited_df = st.data_editor(
        summary_df,
        column_config={
            "My Rank": st.column_config.NumberColumn("My Rank", min_value=1, format="%d"),
            "Full_Name": st.column_config.TextColumn("Player", pinned=True),
            "Current_Rating": st.column_config.NumberColumn("Current", format="%.1f"),
            "Overall_Pot": st.column_config.NumberColumn("Ceiling", format="%.1f"),
            "Growth_Score": st.column_config.NumberColumn("Upside (+)", format="%.1f"),
            **{col: st.column_config.TextColumn(width="small") for col in combined_cols}
        },
        hide_index=True,
        use_container_width=True,
        key="war_room_save_fix"
    )

    st.divider()
    final_csv = edited_df.sort_values(by=['My Rank', 'Overall_Pot'], ascending=[True, False])
    
    st.download_button(
        label="📥 Export My Custom Draft Rankings",
        data=final_csv.to_csv(index=False),
        file_name=f"MyWarRoom_{selected_year}.csv",
        mime="text/csv"
    )
with tab4:
    st.header("⚖️ Risk vs. Reward Analysis")
    st.write("This chart visualizes player readiness (Current) against their remaining upside (Growth).")

    fig_risk = px.scatter(
        filtered_stats,
        x="Current_Rating",
        y="Growth_Score",
        text="Full_Name",
        color="Overall_Pot",
        size="Overall_Pot",
        hover_data=["Pos", "AGE", "HT"],
        labels={"Current_Rating": "Readiness (Current Skill)", "Growth_Score": "Risk/Reward (Growth Potential)"},
        color_continuous_scale="Viridis",
        height=600
    )

    avg_readiness = filtered_stats['Current_Rating'].mean()
    avg_growth = filtered_stats['Growth_Score'].mean()

    fig_risk.add_vline(x=avg_readiness, line_dash="dash", line_color="gray", annotation_text="Readiness Avg")
    fig_risk.add_hline(y=avg_growth, line_dash="dash", line_color="gray", annotation_text="Growth Avg")

    fig_risk.add_annotation(x=filtered_stats['Current_Rating'].max(), y=filtered_stats['Growth_Score'].max(), text="SUPERSTARS", showarrow=False, font=dict(color="green", size=16))
    
    fig_risk.update_traces(textposition='top center')
    st.plotly_chart(fig_risk, use_container_width=True)
    
    st.info(f"💡 **How to read this:** Players in the **Top-Left** have lower current ratings but huge room to grow. Players in the **Bottom-Left** have lower readiness and low growth. Players in the **Top-Right** are elite prospects who are already good but still have high ceilings. Players in the **Bottom-Right** are more ready to contribute now but have less growth potential.")






















































