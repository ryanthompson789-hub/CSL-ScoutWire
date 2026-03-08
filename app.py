import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="CSL Scoutwire", layout="wide")

# --- COMPACT SIDEBAR CSS ---
st.markdown("""
    <style>
    /* Shrink the file uploader height */
    [data-testid="stFileUploader"] {
        padding-top: 0px;
    }
    [data-testid="stFileUploaderDropzone"] {
        padding: 0.5rem;
    }
    /* Tighten sidebar button spacing */
    .stButton button {
        width: 100%;
        padding: 2px 10px;
        min-height: 1.5rem;
        margin-bottom: -10px;
    }
    /* Reduce sidebar header sizes */
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem !important;
    }
    [data-testid="stSidebar"] h2 {
        font-size: 1.1rem !important;
        margin-top: -15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None

def select_player(name):
    st.session_state.selected_player = name

# 1. SIDEBAR CONTENT (Uploader & Title)
st.sidebar.title("🏀 CSL ScoutWire")
uploaded_files = st.sidebar.file_uploader("Upload CSVs", accept_multiple_files=True, type=['csv'])

# 2. THE CONDITIONAL BRANDING (Only shows when empty)
if not uploaded_files:
    st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; }
        .league-title { color: #1E293B; font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -1px; text-align: center; margin-top: 20px; }
        .league-subtitle { color: #D4AF37; font-size: 1rem; font-weight: 700; text-transform: uppercase; letter-spacing: 4px; text-align: center; margin-bottom: 20px; }
        .instruction { color: #64748B; font-size: 1.1rem; text-align: center; margin-bottom: 30px; }
        .trophy-icon { font-size: 50px; background: white; border: 4px solid #D4AF37; width: 100px; height: 100px; line-height: 90px; border-radius: 50%; margin: 0 auto 30px auto; display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='league-title'>CSL ScoutWire</h1>", unsafe_allow_html=True)
        st.markdown("<p class='league-subtitle'>Scouting Analysis Tool</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 2px solid #D4AF37; width: 40%; margin: 20px auto;'>", unsafe_allow_html=True)
        st.markdown('<div class="trophy-icon">🏆</div>', unsafe_allow_html=True)
        st.markdown("<p class='instruction'>Please upload league-standard scouting CSVs from CSLO to begin.</p>", unsafe_allow_html=True)

    st.markdown("<p style='color: #94A3B8; font-size: 0.8rem; text-align: center; margin-top: 40px; font-weight: bold;'>VERSION 1.0</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #CBD5E1; font-size: 0.7rem; text-align: center;'>Internal data for CSL GMs only.</p>", unsafe_allow_html=True)
    
    st.stop() 

# --- DATA PROCESSING ---
try:
    df_list = [pd.read_csv(file) for file in uploaded_files]
    df = pd.concat(df_list)
    
    if 'DRFL' in df.columns:
        df = df[df['DRFL'] <= 25]

    df['Full_Name'] = df['First'].astype(str) + " " + df['Last'].astype(str)
    
    rename_map = {
        'POS': 'Pos', 'Pos': 'Pos', 'AGE': 'AGE', 'Age': 'AGE',
        'HT': 'HT', 'Ht': 'HT', 'Height': 'HT', 'WT': 'WT', 
        'Wt': 'WT', 'Weight': 'WT', 'FROM': 'FROM', 'From': 'FROM'
    }
    df = df.rename(columns=rename_map)
    
    year_col = 'YEAR' 
    bio_cols = ['Pos', 'AGE', 'HT', 'WT', 'FROM']
    pos_map = {1: 'PG', 2: 'SG', 3: 'SF', 4: 'PF', 5: 'C', '1': 'PG', '2': 'SG', '3': 'SF', '4': 'PF', '5': 'C'}
    if 'Pos' in df.columns:
        df['Pos'] = df['Pos'].map(pos_map).fillna(df['Pos'])
        
    core_stats = ['SCR', 'PAS', 'HDL', 'ORB', 'DRB', 'BLK', 'STL', 'DEF', 'DIS', 'IQ', 'DRFL']
    calc_stats = ['SCR', 'PAS', 'HDL', 'ORB', 'DRB', 'BLK', 'STL', 'DEF', 'IQ']
    pot_stats = [s + '_POT' for s in core_stats]
    calc_pot = [s + '_POT' for s in calc_stats]
    shoot_stats = ['FG_RA', 'FG_ITP', 'FG_MID', 'FG_COR', 'FG_ATB', 'FT']
    shoot_pot = [s + '_POT' for s in shoot_stats]
    
    all_numeric_stats = core_stats + pot_stats + shoot_stats + shoot_pot + ["DriveKick", "DriveShot", "PostUp", "PullUp", "CS", "PASS", "LocATB", "LocCorner", "LodMid", "LocPaint", "DUNK RATE", "RIM AREA RATE"]
    existing_numeric = [s for s in all_numeric_stats if s in df.columns]
    existing_bio = [col for col in bio_cols if col in df.columns]
    if year_col in df.columns: existing_bio.append(year_col)

# 1. Define how to aggregate each column
    # For stats, we want mean, min, and max
    stats_agg = {stat: ['mean', 'min', 'max'] for stat in existing_numeric}
    # For bio info, we just want the first entry (since Name/Team shouldn't change)
    bio_agg = {bio: 'first' for bio in existing_bio}
    
    # Combine them and add the "Count" feature
    full_agg = {**stats_agg, **bio_agg}
    full_agg['Full_Name'] = 'count'

    # 2. Run the GroupBy
    player_stats = df.groupby('Full_Name').agg(full_agg)

    # 3. Flatten the column names (so 'SCR' 'mean' becomes 'SCR')
    # We keep 'mean' as the primary name so your existing charts don't break
    new_cols = []
    for col, stat in player_stats.columns:
        if stat == 'mean':
            new_cols.append(col)
        elif stat in ['min', 'max']:
            new_cols.append(f"{col}_{stat}")
        elif col == 'Full_Name' and stat == 'count':
            new_cols.append('Reports_Count')
        else:
            new_cols.append(col)
    
    player_stats.columns = new_cols
    player_stats = player_stats.reset_index()

    # 4. Standard Clean-up & Calculations
    if year_col in player_stats.columns:
        player_stats[year_col] = player_stats[year_col].astype(str).str.replace('.0', '', regex=False)
    
# 1. Calculate Average, Min, and Max for the Floor (Current Rating)
    player_stats['Current_Rating'] = player_stats[calc_stats].mean(axis=1)
    # Create the min/max versions by looking at the min/max of the individual components
    player_stats['Current_Rating_min'] = player_stats[[f"{s}_min" for s in calc_stats if f"{s}_min" in player_stats.columns]].mean(axis=1)
    player_stats['Current_Rating_max'] = player_stats[[f"{s}_max" for s in calc_stats if f"{s}_max" in player_stats.columns]].mean(axis=1)

    # 2. Calculate Average, Min, and Max for the Ceiling (Overall Potential)
    player_stats['Overall_Pot'] = player_stats[calc_pot].mean(axis=1)
    player_stats['Overall_Pot_min'] = player_stats[[f"{s}_min" for s in calc_pot if f"{s}_min" in player_stats.columns]].mean(axis=1)
    player_stats['Overall_Pot_max'] = player_stats[[f"{s}_max" for s in calc_pot if f"{s}_max" in player_stats.columns]].mean(axis=1)
    
    # 3. Growth Score (Difference of averages)
    player_stats['Growth_Score'] = player_stats['Overall_Pot'] - player_stats['Current_Rating']

except Exception as e:
    st.error(f"⚠️ Error processing data: {e}")
    st.stop()

# --- SIDEBAR FILTERS (Now more compact) ---
st.sidebar.divider()
st.sidebar.subheader("🔍 Filters") # Changed from header to subheader for size
if year_col in player_stats.columns:
    available_years = sorted(player_stats[year_col].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Select Year", available_years) # Shorter label
    filtered_stats = player_stats[player_stats[year_col] == selected_year]
else:
    filtered_stats = player_stats
    selected_year = "All"

all_positions = sorted(filtered_stats['Pos'].unique())
    
st.sidebar.subheader(f"🚀 Top Growth") # Removed the year to save space
project_board = filtered_stats.sort_values(by='Growth_Score', ascending=False).head(5)

# Rendering the buttons with the new compact CSS
for i, row in project_board.iterrows():
    if st.sidebar.button(f"{row['Full_Name']} (+{row['Growth_Score']:.1f})", key=f"side_{row['Full_Name']}"):
        st.session_state.selected_player = row['Full_Name']
        st.rerun()

if 'teleport_success' in st.session_state:
    st.success(f"✅ **Report Loaded:** {st.session_state.teleport_success} is ready in the 'Individual Prospect Scout' tab.")
    # We delete it immediately so the message doesn't pop up again on the next click
    del st.session_state.teleport_success
    
# --- MAIN APP ---
tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Individual Prospect Scout", 
    "🎯 Advanced Player Finder", 
    "📋 Draft War Room", 
    "📈 Strategy & Analysis"
])
    
with tab1:
    player_list = list(filtered_stats['Full_Name'].unique())
    
    # 1. Sync session state if it's missing or invalid
    if st.session_state.selected_player not in player_list:
        st.session_state.selected_player = player_list[0]
    
    # 2. CALLBACK FUNCTION: This solves the "double-click" bug
    def update_player():
        st.session_state.selected_player = st.session_state.player_selector_key

    # 3. THE DROPDOWN: Uses 'key' and 'on_change' for instant response
    selected_player = st.selectbox(
        "Select Primary Prospect", 
        player_list, 
        index=player_list.index(st.session_state.selected_player),
        key="player_selector_key",
        on_change=update_player
    )
    
    # Ensure the local variable matches the session state
    selected_player = st.session_state.selected_player

    # --- p_data Definition ---
    p_data = filtered_stats[filtered_stats['Full_Name'] == selected_player].iloc[0]

    def generate_scout_report(player, df_context):
        try:
            # 1. Define Universal "Pro-Level" Benchmarks
            PLUS = 65
            SOLID = 55

            # 2. Identify Core Identities
            is_scorer = player.get('SCR', 0) >= PLUS or player.get('FG_ATB', 0) >= 38
            is_playmaker = player.get('PAS', 0) >= PLUS and player.get('IQ', 0) >= PLUS
            is_defender = player.get('DEF', 0) >= PLUS
            is_big_man = (player.get('ORB', 0) >= PLUS) or (player.get('BLK', 0) >= 55)
        
            # 3. Determine Archetype
            if is_scorer and is_defender:
                archetype = "Elite Two-Way Prospect"
            elif is_playmaker and is_scorer:
                archetype = "Dynamic Offensive Engine"
            elif is_playmaker:
                archetype = "High-IQ Floor General"
            elif is_scorer:
                archetype = "Natural Scorer"
            elif is_defender and is_big_man:
                archetype = "Paint-Protecting Anchor"
            elif is_defender:
                archetype = "Lockdown Specialist"
            elif is_big_man:
                archetype = "Interior Physical Presence"
            else:
                archetype = "Raw Developmental Project"

            # 4. Contextual Dual-Ranking
            sample_size = len(df_context)
            if sample_size > 10:
                # We use player.name which is the Full_Name in the grouped dataframe
                pot_rank = int(df_context['Overall_Pot'].rank(ascending=False, method='min').iloc[df_context.index.get_loc(player.name)])
                cur_rank = int(df_context['Current_Rating'].rank(ascending=False, method='min').iloc[df_context.index.get_loc(player.name)])
            
                context_note = (
                    f"Within this class of {sample_size}, he ranks **#{cur_rank} in Immediate Readiness** "
                    f"and **#{pot_rank} in Long-Term Ceiling**."
                )
            else:
                context_note = "Evaluation based on independent pro-style benchmarks (Limited class data available)."

            # 5. Narrative Construction
            report = (
                f"**Scouting Director's Note:** {player['Full_Name']} projects as a **{archetype}**. "
                f"His current toolkit is defined by {player.get('SCR', 0):.0f} scoring and {player.get('DEF', 0):.0f} defense. "
                f"{context_note} "
            )

           # 6. The "Upside" Finisher (Tiered Variance)
            growth = player.get('Growth_Score', 0)
        
            if growth > 12:
                report += f"Drafting him is a high-reward play—his **+{growth:.1f}** upside suggests a significantly higher peak than his current tape shows."
            elif growth > 7:
                report += f"He has a moderate ceiling with a **+{growth:.1f}** projected growth; he should develop into a more impactful player with proper coaching."
            elif growth >= 3:
                report += f"With a **+{growth:.1f}** growth curve, he offers some room for improvement, but he is largely seen as a safe, predictable prospect."
            else:
                report += f"Scouts believe he is already playing near his physical peak (**+{growth:.1f}** growth); what you see now is likely the finished product."

            return report

        except Exception as e:
            return f"Scouting report unavailable: {str(e)}"

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

# --- UPDATED: SCOUTING METRICS ---
        st.divider()
        
        # Only show the Report Count as a main metric
        st.metric("Total Scout Reports", f"{p_data['Reports_Count']}")
            
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

# --- SCOUTING VARIANCE (Full Width & Dual Expanders) ---
    st.divider() 
        
        # Define the lists for both categories
    core_stats = [
        'SCR', 'PAS', 'HDL', 'ORB', 'DRB', 'BLK', 'STL', 'DEF', 
        'DIS', 'IQ', 'DRFL', 'FG_RA', 'FG_ITP', 'FG_MID', 
        'FG_COR', 'FG_ATB', 'FT'
    ]

       # --- SCOUTING VARIANCE (Full Width & Dual Expanders) ---
    st.divider() 
        
# 1. CURRENT RATINGS VARIANCE
    with st.expander("📊 View Current Rating Variance (Convergent Range)", expanded=False):
        current_list = []
        for s in core_stats:
            if s in p_data:
                # Deviation Rule: 2 for shooting/fouls, 5 for core
                dev = 2 if s in ['FG_RA', 'FG_ITP', 'FG_MID', 'FT', 'FG_ATB', 'FG_COR', 'DRFL', 'RA_RATE', 'DUNK_RATE'] else 5
                    
                raw_low = p_data.get(f"{s}_min", p_data[s])
                raw_high = p_data.get(f"{s}_max", p_data[s])
                    
                # NARROW THE RANGE: Pull floor up, pull ceiling down
                true_low = int(raw_low + dev)
                true_high = int(raw_high - dev)
                    
                # Safety check: ensure low isn't higher than high if data is tight
                if true_low > true_high:
                    true_low, true_high = int(round(p_data[s], 0)), int(round(p_data[s], 0))

                current_list.append({
                    "Attribute": s,
                    "Raw Low": int(raw_low),
                    "AVERAGE": int(round(p_data[s], 0)),
                    "Raw High": int(raw_high),
                    "Standard Deviation Range": f"{true_low} - {true_high}"
                })
        st.table(pd.DataFrame(current_list).set_index('Attribute'))

        # 2. POTENTIAL RATINGS VARIANCE
    with st.expander("🚀 View Potential Rating Variance (Convergent Range)", expanded=False):
        potential_list = []
        for s in core_stats:
            pot_col = f"{s}_POT" 
            if pot_col in p_data:
                # Deviation Rule: 2 for shooting/fouls, 15 for core potential
                dev = 2 if s in ['FG_RA', 'FG_ITP', 'FG_MID', 'FT', 'FG_ATB', 'FG_COR', 'DRFL', 'RA_RATE', 'DUNK_RATE'] else 15
                    
                raw_low = p_data.get(f"{pot_col}_min", p_data[pot_col])
                raw_high = p_data.get(f"{pot_col}_max", p_data[pot_col])
                    
                # NARROW THE RANGE: (Low + 15) to (High - 15)
                true_low = int(raw_low + dev)
                true_high = int(raw_high - dev)
                    
                # Safety check
                if true_low > true_high:
                        # If range is smaller than deviation, use the average as a fixed point
                    true_low = true_high = int(round(p_data[pot_col], 0))

                potential_list.append({
                    "Attribute": s,
                    "Raw Low": int(raw_low),
                    "AVERAGE": int(round(p_data[pot_col], 0)),
                    "Raw High": int(raw_high),
                    "Standard Deviation Range": f"{true_low} - {true_high}"
                })
            
        if potential_list:
            st.table(pd.DataFrame(potential_list).set_index('Attribute'))
        else:
            st.info("No specific potential variance data found for this prospect.")
        
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

    # --- DRAFT SIMILAR (FULL DNA VERSION) ---
    st.divider()
    st.header("🧬 Similar Prospect Profiles")
    st.caption("These players share the most similar ratings.")

    # 1. Expanded DNA including the shooting profile
    identity_stats = [
        'SCR', 'PAS', 'HDL', 'ORB', 'DRB', 'DEF', 'STL', 'BLK', 'IQ', 
        'FG_RA', 'FG_ITP', 'FG_MID', 'FG_COR', 'FG_ATB', 'FT'
    ]

    # Ensure we only use stats that actually exist in the data to avoid errors
    existing_identity = [s for s in identity_stats if s in filtered_stats.columns]

    # 2. Calculate the "Distance" using a more sensitive penalty
    comparison_df = filtered_stats.copy()
    comparison_df = comparison_df[comparison_df['Full_Name'] != selected_player]

    # Calculate the mean difference across identity stats
    # We use a 'Squared Difference' (Euclidean) to punish outliers more heavily
    def calculate_match(row, target_stats):
        # Sum of absolute differences
        diff = sum(abs(row[existing_identity] - target_stats[existing_identity]))
    
        # We calibrate the percentage: 
        # In a typical draft, a total diff of ~150 points across 13 stats 
        # should feel like a 'Low Match' (~60-70%).
        # We'll use 400 as a "Max Realistic Difference" for scaling.
        max_realistic_diff = 400 
        percentage = 100 - (min(diff, max_realistic_diff) / max_realistic_diff * 100)
        return percentage

    comparison_df['Match_Pct'] = comparison_df.apply(
        lambda row: calculate_match(row, p_data), axis=1
    )

    # 3. Get the Top 3
    similar_prospects = comparison_df.sort_values('Match_Pct', ascending=False).head(3)

    # 4. Display Cards
    sim_cols = st.columns(3)
    for i, (idx, sim_p) in enumerate(similar_prospects.iterrows()):
        with sim_cols[i]:
            match_val = sim_p['Match_Pct']
        
            # Changed height to auto and added min-height for better spacing
            st.markdown(f"""
                <div style="
                    border: 1px solid #D4AF37; 
                    padding: 15px; 
                    border-radius: 10px; 
                    background-color: white; 
                    min-height: 120px; 
                    height: auto; 
                    margin-bottom: 10px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                ">
                    <p style="margin:0; font-size: 0.8rem; color: #64748B; font-weight: bold;">{match_val:.1f}% STYLE MATCH</p>
                    <h4 style="margin:5px 0; color: #1E293B; line-height: 1.2;">{sim_p['Full_Name']}</h4>
                    <p style="margin:0; color: #D4AF37; font-weight: bold; font-size: 0.9rem;">{sim_p['Pos']} | Pot: {sim_p['Overall_Pot']:.1f}</p>
                </div>
            """, unsafe_allow_html=True)
        
            if st.button(f"View {sim_p['Full_Name']}", key=f"sim_{sim_p['Full_Name']}", use_container_width=True):
                st.session_state.selected_player = sim_p['Full_Name']
                st.session_state.teleport_success = sim_p['Full_Name']
                st.rerun()

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
        
        # --- THE TELEPORT BUTTON (RE-RUN PERSISTENCE FIX) ---
        st.write("### 🚀 Launch Report")
        target_player = st.selectbox("Select Prospect to View in Tab 1", query_df['Full_Name'].unique())
        
        if st.button(
            f"View Full Report for {target_player}", 
            use_container_width=True,
            type="primary"
        ):
            # 1. Update the session state so Tab 1 knows who to show
            st.session_state.selected_player = target_player
            
            # 2. Set the "Flag" that we will check for after the rerun
            st.session_state.teleport_success = target_player
            
            # 3. REFRESH
            st.rerun()
        
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

































































































