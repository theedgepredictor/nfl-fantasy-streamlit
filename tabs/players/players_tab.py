import streamlit as st
import pandas as pd

def display_event_player_tab(dataset_df, event_player_df):
    st.subheader("Event Players", anchor=False)
    
    # Filter controls
    season_options = sorted(dataset_df['season'].unique())
    default_season_idx = season_options.index(max(season_options))
    season = st.selectbox('Select Season:', season_options, index=default_season_idx, key='event_player_season')
    
    week_options = sorted(dataset_df[dataset_df['season'] == season]['week'].unique())
    default_week_idx = week_options.index(max(week_options))
    week = st.selectbox('Select Week:', week_options, index=default_week_idx, key='event_player_week')
    
    # Filter events for selected season and week
    filtered_events = dataset_df[
        (dataset_df['season'] == season) & 
        (dataset_df['week'] == week)
    ].copy()
    
    # Create game selection options
    game_options = [f"{row['away_team']} @ {row['home_team']}" for _, row in filtered_events.iterrows()]
    selected_game = st.selectbox('Select Game:', game_options, key='event_player_game')
    
    if selected_game:
        away_team, home_team = selected_game.split(' @ ')
        
        # Filter player data for selected teams
        away_players = event_player_df[
            (event_player_df['season'] == season) & 
            (event_player_df['week'] == week) & 
            (event_player_df['team'] == away_team)
        ]
        
        home_players = event_player_df[
            (event_player_df['season'] == season) & 
            (event_player_df['week'] == week) & 
            (event_player_df['team'] == home_team)
        ]
        
        # Display side by side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(away_team)
            for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                st.write(f"### {pos}")
                pos_players = away_players[away_players['position'] == pos]
                if not pos_players.empty:
                    st.dataframe(pos_players[[
                        'name', 'projected_points', 'percent_owned', 'percent_started'
                    ]])
        
        with col2:
            st.subheader(home_team)
            for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                st.write(f"### {pos}")
                pos_players = home_players[home_players['position'] == pos]
                if not pos_players.empty:
                    st.dataframe(pos_players[[
                        'name', 'projected_points', 'percent_owned', 'percent_started'
                    ]])

def display_player_tab(player_df):
    st.subheader("Players", anchor=False)
    
    # Filter controls
    season_options = sorted(player_df['season'].unique())
    default_season_idx = season_options.index(max(season_options))
    season = st.selectbox('Select Season:', season_options, index=default_season_idx, key='player_season')
    
    week_options = sorted(player_df[player_df['season'] == season]['week'].unique())
    default_week_idx = week_options.index(max(week_options))
    week = st.selectbox('Select Week:', week_options, index=default_week_idx, key='player_week')
    
    # Filter type selection
    filter_type = st.radio("Filter by:", ["Team", "Position"])
    
    filtered_df = player_df[
        (player_df['season'] == season) & 
        (player_df['week'] == week)
    ].copy()
    
    if filter_type == "Team":
        team_options = sorted(filtered_df['team'].unique())
        selected_team = st.selectbox('Select Team:', team_options)
        filtered_df = filtered_df[filtered_df['team'] == selected_team]
        
        # Group by position
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_players = filtered_df[filtered_df['position'] == pos]
            if not pos_players.empty:
                st.write(f"### {pos}")
                st.dataframe(pos_players[[
                    'name', 'projected_points', 'percent_owned', 'percent_started'
                ]])
    
    else:  # Position
        pos_options = sorted(filtered_df['position'].unique())
        selected_pos = st.selectbox('Select Position:', pos_options)
        filtered_df = filtered_df[filtered_df['position'] == selected_pos]
        
        # Show all players of selected position
        st.dataframe(filtered_df[[
            'team', 'name', 'projected_points', 'percent_owned', 'percent_started'
        ]])
