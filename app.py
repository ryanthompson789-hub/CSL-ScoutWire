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

uploaded_files = st.file_uploader("Upload Scouting CSVs", accept_multiple_files=True, type=['csv'])

if not uploaded_files:
    st.info("👋 Welcome! Please upload your scouting CSVs to begin.")
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

st.sidebar.header(f"🚀 Top Growth ({selected_year})")
project_board = filtered_stats.sort_values(by='Growth_Score', ascending=False).head(5)

for i, row in project_board.iterrows():
    if st.sidebar.button(f"{row['Full_Name']} (+{row['Growth_Score']:.1f})", key=f"side_{row['Full_Name']}"):
        st.session_state.selected_player = row['Full_Name']
        st.rerun()

# --- TABBED NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["👤 Individual Prospect Scout", "📋 Draft Big Board", "📈 Strategy & Analysis"])

with tab1:
    player_list = list(filtered_stats['Full_Name'].unique())
    default_index = 0
    if st.session_state.get('selected_player') in player_list:
        default_index = player_list.index(st.session_state.selected_player)

    selected_player = st.selectbox(
        "Select Primary Prospect", 
        player_list, 
        index=default_index,
        key="main_player_selector"
    )

    p_data = filtered_stats[filtered_stats['Full_Name'] == selected_player].iloc[0]

    # --- ADVANCED SCOUTING REPORT FUNCTION ---
    def generate_scout_report(player, df_context):
        avg = df_context.mean(numeric_only=True)
        high_traits = [stat for stat in ['SCR', 'DEF', 'PAS', 'IQ', 'BLK', 'STL', 'ORB'] 
                       if stat in player and player[stat] > avg[stat] + 8]
        
        archetype = "Well-Rounded Prospect"
        if player.get('SCR', 0) >= 70 and player.get('FG_ATB', 0) > 38:
            archetype = "Dynamic Perimeter Scorer"
        elif player.get('DEF', 0) >= 70 and (player.get('BLK', 0) > 55 or player.get('STL', 0) > 60):
            archetype = "High-Impact Defensive Specialist"
        elif player.get('PAS', 0) >= 70 and player.get('IQ', 0) >= 70:
            archetype = "High-IQ Playmaker"
        elif player.get('ORB', 0) >= 70 or player.get('BLK', 0) >= 55:
            archetype = "Interior Anchor"

        if player.get('SCR', 0) >= 70 and player.get('DEF', 0) >= 70:
            archetype = "Elite Two-Way Threat"

        habits = []
        if player.get('DriveKick', 0) > 7: habits.append("attacking the paint to collapse defenses")
        if player.get('CS', 0) > 10: habits.append("finding space as a catch-and-shoot threat")
        if player.get('PostUp', 0) > 8: habits.append("using their size in the low post")
        
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
            f"while his long-term success will depend on refining his overall efficiency to reach that **{player['Overall_Pot']:.1f}** ceiling."
        )

    # --- SIMILAR PLAYERS LOGIC ---
    with st.spinner('Scanning database for similar archetypes...'):
        match_traits = ['SCR', 'PAS', 'HDL', 'DRB', 'ORB', 'BLK', 'STL', 'DEF', 'IQ']
        target_vector = p_data[match_traits].values
        others = player_stats[player_stats['Full_Name'] != selected_player].copy()
        others['Similarity'] = others.apply(lambda row: sum((target_vector - row[match_traits].values) ** 2) ** 0.5, axis=1)
        similar_players = others.sort_values('Similarity').head(3)

    # --- REORDERED INDIVIDUAL VIEW ---
    
    # 1. Player Name
    st.markdown(f"## {selected_player} | Class of {p_data.get(year_col, 'N/A')}")
    
    # 2. Bio Metrics (Moved below name)
    c1, c2, c3, c4, c5 = st.columns(5)
    if 'Pos' in p_data: c1.metric("Position", p_data['Pos'])
    if 'AGE' in p_data: c2.metric("Age", str(int(float(p_data['AGE']))))
    if 'HT' in p_data: c3.metric("Height", p_data['HT'])
    if 'WT' in p_data: c4.metric("Weight", str(p_data['WT']))
    if 'FROM' in p_data: c5.metric("School/From", str(p_data['FROM']))

    st.divider()

    # 3. Scouting Director's Executive Summary
    with st.expander("📝 Scouting Director's Executive Summary", expanded=True):
        st.write(generate_scout_report(p_data, filtered_stats))

    # 4. Scouting Intelligence (Ranking Logic)
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

    # --- MIDDLE UI: GRAPHS & SIMILAR PLAYERS ---
    col_main, col_sim = st.columns([2.5, 1])

    with col_main:
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

    with col_sim:
        st.subheader("🔍 Similar Archetypes")
        st.caption("Statistical twins from history")
        for _, sim in similar_players.iterrows():
            with st.expander(f"**{sim['Full_Name']}** ({sim.get(year_col, 'N/A')})"):
                st.write(f"**Pos:** {sim['Pos']} | **HT:** {sim['HT']}")
                st.write(f"Scoring: {sim['SCR']:.0f} | Defense: {sim['DEF']:.0f}")

    # --- BOTTOM UI: HABITS & COMPARISON ---
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

    st.divider()
    st.header("⚔️ Prospect Comparison Tool")
    comp_player = st.selectbox("Select Player to Compare", ["None"] + list(player_stats['Full_Name'].unique()))

    if comp_player != "None":
        c_data = player_stats[player_stats['Full_Name'] == comp_player].iloc[0]
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.write("### Core (Current)")
            f1 = go.Figure()
            f1.add_trace(go.Bar(x=core_stats, y=p_data[core_stats].values, name=selected_player, marker_color='royalblue'))
            f1.add_trace(go.Bar(x=core_stats, y=c_data[core_stats].values, name=comp_player, marker_color='indianred'))
            f1.update_layout(barmode='group', yaxis=dict(range=[0, 100]), height=300)
            st.plotly_chart(f1, use_container_width=True)
        with r1c2:
            st.write("### Core (Potential)")
            f2 = go.Figure()
            f2.add_trace(go.Bar(x=core_stats, y=p_data[pot_stats].values, name=selected_player, marker_color='royalblue', opacity=0.6))
            f2.add_trace(go.Bar(x=core_stats, y=c_data[pot_stats].values, name=comp_player, marker_color='indianred', opacity=0.6))
            f2.update_layout(barmode='group', yaxis=dict(range=[0, 100]), height=300)
            st.plotly_chart(f2, use_container_width=True)
with tab2:
    st.header(f"📋 {selected_year} Editable Draft Board")
    
    bb_df = filtered_stats.copy()
    bb_df['My Rank'] = 0 
    
    stat_pairs = {
        'SCR': 'SCR_POT', 'PAS': 'PAS_POT', 'HDL': 'HDL_POT', 
        'ORB': 'ORB_POT', 'DRB': 'DRB_POT', 'BLK': 'BLK_POT', 
        'STL': 'STL_POT', 'DEF': 'DEF_POT', 'IQ': 'IQ_POT',
        'DIS': 'DIS_POT', 'DRFL': 'DRFL_POT'
    }

    combined_cols = []
    for cur, pot in stat_pairs.items():
        if cur in bb_df.columns and pot in bb_df.columns:
            display_name = f"{cur} (C/P)"
            bb_df[display_name] = bb_df[cur].fillna(0).astype(float).round(0).astype(int).astype(str) + " / " + \
                                  bb_df[pot].fillna(0).astype(float).round(0).astype(int).astype(str)
            combined_cols.append(display_name)

    bio_cols = ['My Rank', 'Full_Name', 'Pos', 'Overall_Pot', 'Growth_Score']
    existing_cols = [c for c in bio_cols + combined_cols if c in bb_df.columns]
    summary_df = bb_df[existing_cols].sort_values(by='Overall_Pot', ascending=False)

    edited_df = st.data_editor(
        summary_df,
        column_config={
            "My Rank": st.column_config.NumberColumn("My Rank", min_value=1, format="%d"),
            "Full_Name": st.column_config.TextColumn("Player", pinned=True),
            "Overall_Pot": st.column_config.NumberColumn("Ceiling", format="%.1f"),
            "Growth_Score": st.column_config.NumberColumn("Upside (+)", format="%.1f"),
        },
        hide_index=True,
        use_container_width=True,
        key="big_board_save_fix"
    )

    st.divider()
    final_csv = edited_df.sort_values(by=['My Rank', 'Overall_Pot'], ascending=[True, False])
    
    st.download_button(
        label="📥 Export My Custom Draft Rankings",
        data=final_csv.to_csv(index=False),
        file_name=f"MyDraftBoard_{selected_year}.csv",
        mime="text/csv"
    )

with tab3:
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
    
    st.info(f"💡 **How to read this:** Players in the **Top-Left** have lower current ratings but huge room to grow. Players in the **Top-Right** are elite prospects who are already good but still have high ceilings.")






