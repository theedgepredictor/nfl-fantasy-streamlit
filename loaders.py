import pandas as pd

from consts import META, VEGAS, TARGETS, POINT_FEATURES, RANKING_FEATURES, JUST_SIMPLE_FEATURES
from utils import df_rename_shift, df_rename_exavg, df_rename_fold, team_id_repl

import streamlit as st

def get_event_feature_store(season):
    #return pd.read_parquet(f'../nfl-feature-store/data/feature_store/event/regular_season_game/{season}.parquet')
    return pd.read_parquet(f'https://github.com/theedgepredictor/nfl-feature-store/raw/main/data/feature_store/event/regular_season_game/{season}.parquet')

def get_player_fantasy_projections(season, mode='weekly', group='OFF'):
    """
    Fetches fantasy projections for players based on position group and timeframe.
    """
    try:
        df = pd.read_parquet(f'https://github.com/theedgepredictor/fantasy-data-pump/raw/main/processed/season/football/nfl/{season}.parquet')
        df = team_id_repl(df)
        
        weekly_meta = [
            'season', 'week', 'player_id', 'name', 'position', 'team',
            'percent_owned', 'percent_started', 'projected_points'
        ]
        
        season_meta = [
            'season', 'player_id', 'name', 'position', 'team',
            'percent_owned', 'percent_started', 'total_points',
            'projected_total_points', 'avg_points', 'projected_avg_points'
        ]
        
        offensive_cols = [
            'projected_rushing_attempts', 'projected_rushing_yards',
            'projected_rushing_touchdowns', 'projected_rushing2_pt_conversions',
            'projected_rushing40_plus_yard_td', 'projected_rushing50_plus_yard_td',
            'projected_rushing100_to199_yard_game', 'projected_rushing200_plus_yard_game',
            'projected_rushing_yards_per_attempt', 'projected_receiving_yards',
            'projected_receiving_touchdowns', 'projected_receiving2_pt_conversions',
            'projected_receiving40_plus_yard_td', 'projected_receiving50_plus_yard_td',
            'projected_receiving_receptions', 'projected_receiving100_to199_yard_game',
            'projected_receiving200_plus_yard_game', 'projected_receiving_targets',
            'projected_receiving_yards_per_reception', 'projected_2_pt_conversions',
            'projected_fumbles', 'projected_lost_fumbles', 'projected_turnovers',
            'projected_passing_attempts', 'projected_passing_completions',
            'projected_passing_yards', 'projected_passing_touchdowns',
            'projected_passing_interceptions', 'projected_passing_completion_percentage'
        ]
        
        defensive_cols = [
            'projected_defensive_solo_tackles', 'projected_defensive_total_tackles',
            'projected_defensive_interceptions', 'projected_defensive_fumbles',
            'projected_defensive_blocked_kicks', 'projected_defensive_safeties',
            'projected_defensive_sacks', 'projected_defensive_touchdowns',
            'projected_defensive_forced_fumbles', 'projected_defensive_passes_defensed',
            'projected_defensive_points_allowed', 'projected_defensive_yards_allowed',
            'projected_defensive_assisted_tackles'
        ]
        
        special_teams_cols = [
            'projected_made_field_goals', 'projected_attempted_field_goals',
            'projected_missed_field_goals', 'projected_made_extra_points',
            'projected_attempted_extra_points', 'projected_missed_extra_points',
            'projected_kickoff_return_touchdowns', 'projected_kickoff_return_yards',
            'projected_punt_return_touchdowns', 'projected_punt_return_yards',
            'projected_punts_returned', 'projected_made_field_goals_from50_plus',
            'projected_attempted_field_goals_from50_plus',
            'projected_made_field_goals_from40_to49',
            'projected_attempted_field_goals_from40_to49',
            'projected_made_field_goals_from_under40',
            'projected_attempted_field_goals_from_under40'
        ]
        
        if group == 'OFF':
            stat_cols = offensive_cols
            positions = ['QB', 'RB', 'WR', 'TE']
        elif group == 'DEF':
            stat_cols = defensive_cols
            positions = ['D/ST']
        elif group == 'ST':
            stat_cols = special_teams_cols
            positions = ['K']
        else:
            raise ValueError("group must be one of ['OFF', 'DEF', 'ST']")
            
        meta_cols = season_meta if mode == 'season' else weekly_meta
        all_cols = meta_cols + stat_cols
        df = df[all_cols]
        df = df[df.position.isin(positions)].copy()
        
        if mode == 'season':
            meta_df = df[meta_cols].drop_duplicates(['player_id'])
            stats_df = df[['player_id'] + stat_cols].groupby(['player_id']).sum()
            df = pd.merge(meta_df, stats_df, on=['player_id'])
        return df
    except Exception as e:
        print(f"Error fetching fantasy projections: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_player_data(seasons):
    """Load player data for all position groups"""
    all_player_data = []
    for season in seasons:
        # Load data for each position group
        off_data = get_player_fantasy_projections(season, mode='weekly', group='OFF')
        def_data = get_player_fantasy_projections(season, mode='weekly', group='DEF')
        st_data = get_player_fantasy_projections(season, mode='weekly', group='ST')
        
        # Combine all groups
        season_data = pd.concat([off_data, def_data, st_data], ignore_index=True)
        all_player_data.append(season_data)
    
    # Combine all seasons
    return pd.concat(all_player_data, ignore_index=True)

@st.cache_data(ttl=3600) # Invalidate cache after an hour
def load_feature_store(seasons):
    event_fs = pd.concat([get_event_feature_store(season) for season in seasons], ignore_index=True)
    event_fs = event_fs[event_fs.away_elo_pre.notnull()].copy()

    columns_for_base = META + ['home_elo_pre', 'away_elo_pre'] + VEGAS + TARGETS + ['away_offensive_rank','away_defensive_rank','home_offensive_rank','home_defensive_rank',]
    columns_for_shift = ['team', 'season', 'week', 'is_home'] + POINT_FEATURES + JUST_SIMPLE_FEATURES
    shifted_df = event_fs.copy()
    base_dataset_df = event_fs[columns_for_base].copy()

    del event_fs

    #### Shift Features
    shifted_df = df_rename_shift(shifted_df)[columns_for_shift]

    #### Rename for Expected Average
    t1_cols = [i for i in shifted_df.columns if '_offense' in i and (i not in TARGETS + META) and i.replace('home_', '') in columns_for_shift]
    t2_cols = [i for i in shifted_df.columns if '_defense' in i and (i not in TARGETS + META) and i.replace('away_', '') in columns_for_shift]

    #### Apply Expected Average
    expected_features_df = df_rename_exavg(shifted_df, '_offense', '_defense', t1_cols=t1_cols, t2_cols=t2_cols)

    #### Rename back into home and away features
    home_exavg_features_df = expected_features_df[expected_features_df['is_home'] == 1].copy().drop(columns='is_home')
    away_exavg_features_df = expected_features_df[expected_features_df['is_home'] == 0].copy().drop(columns='is_home')
    home_exavg_features_df.columns = ["home_" + col if 'exavg_' in col or col == 'team' else col for col in home_exavg_features_df.columns]
    away_exavg_features_df.columns = ["away_" + col if 'exavg_' in col or col == 'team' else col for col in away_exavg_features_df.columns]

    #### Merge home and away Expected Average features into base as dataset_df
    dataset_df = pd.merge(base_dataset_df, home_exavg_features_df, on=['home_team', 'season', 'week'], how='left')
    dataset_df = pd.merge(dataset_df, away_exavg_features_df, on=['away_team', 'season', 'week'], how='left')
    dataset_df['game_id'] = dataset_df.apply(lambda x: f"{x['season']}_{x['week']}_{x['away_team']}_{x['home_team']}", axis=1)

    #### Fold base from away and home into team
    folded_dataset_df = base_dataset_df.copy()
    folded_dataset_df['game_id'] = folded_dataset_df.apply(lambda x: f"{x['season']}_{x['week']}_{x['away_team']}_{x['home_team']}", axis=1)
    folded_dataset_df = folded_dataset_df.rename(columns={'spread_line': 'away_spread_line'})
    folded_dataset_df['home_spread_line'] = - folded_dataset_df['away_spread_line']
    folded_dataset_df['actual_home_spread'] = -folded_dataset_df['actual_away_spread']
    folded_dataset_df['actual_home_team_win'] = folded_dataset_df['actual_away_team_win'] == 0
    folded_dataset_df['actual_home_team_covered_spread'] = folded_dataset_df['actual_away_team_covered_spread'] == 0
    folded_dataset_df = df_rename_fold(folded_dataset_df, 'away_', 'home_')
    folded_dataset_df = pd.merge(folded_dataset_df, expected_features_df, on=['team', 'season', 'week'], how='left')
    dataset_df.index = dataset_df.game_id

    # Customize Column names from feature store into friendly_names
    dataset_df['expected_spread'] = dataset_df['home_exavg_avg_points'] - dataset_df['away_exavg_avg_points']
    dataset_df['expected_total'] = dataset_df['home_exavg_avg_points'] + dataset_df['away_exavg_avg_points']
    dataset_df = dataset_df.rename(columns={
        #'away_team_spread': 'actual_away_spread',
        #'total_target': 'actual_point_total',
        'away_exavg_avg_points': 'away_expected_points',
        'home_exavg_avg_points': 'home_expected_points',
        'home_elo_pre': 'home_rating',
        'away_elo_pre': 'away_rating',
        'actual_away_score': 'actual_away_points',
        'actual_home_score': 'actual_home_points',
        'away_exavg_avg_carries': 'away_expected_carries',
        'home_exavg_avg_carries': 'home_expected_carries',
        'home_exavg_avg_rushing_yards': 'home_expected_rushing_yards',
        'away_exavg_avg_rushing_yards': 'away_expected_rushing_yards',
        'home_exavg_avg_rushing_tds': 'home_expected_rushing_tds',
        'away_exavg_avg_rushing_tds': 'away_expected_rushing_tds',
        'home_exavg_avg_completions': 'home_expected_completions',
        'away_exavg_avg_completions': 'away_expected_completions',
        'home_exavg_avg_attempts': 'home_expected_attempts',
        'away_exavg_avg_attempts': 'away_expected_attempts',
        'home_exavg_avg_passing_yards': 'home_expected_passing_yards',
        'away_exavg_avg_passing_yards': 'away_expected_passing_yards',
        'home_exavg_avg_passing_tds': 'home_expected_passing_tds',
        'away_exavg_avg_passing_tds': 'away_expected_passing_tds',
        'home_exavg_avg_time_of_possession': 'home_expected_time_of_possession',
        'away_exavg_avg_time_of_possession': 'away_expected_time_of_possession',
        'home_exavg_avg_turnover': 'home_expected_turnover',
        'away_exavg_avg_turnover': 'away_expected_turnover',
        'home_exavg_avg_field_goal_made': 'home_expected_field_goal_made',
        'away_exavg_avg_field_goal_made': 'away_expected_field_goal_made'
    })
    dataset_df['away_rating'] = dataset_df['away_rating'].astype(int)
    dataset_df['home_rating'] = dataset_df['home_rating'].astype(int)

    folded_dataset_df = folded_dataset_df.rename(columns={
        'exavg_avg_points': 'expected_points',
        'exavg_avg_q1_points': 'expected_q1_points',
        'exavg_avg_q2_points': 'expected_q2_points',
        'exavg_avg_q3_points': 'expected_q3_points',
        'exavg_avg_q4_points': 'expected_q4_points',
        'exavg_avg_q5_points': 'expected_q5_points',
        'elo_pre': 'rating',
        'actual_score': 'actual_points',
        'exavg_avg_carries': 'expected_carries',
        'exavg_avg_rushing_yards': 'expected_rushing_yards',
        'exavg_avg_rushing_tds': 'expected_rushing_tds',
        'exavg_avg_completions': 'expected_completions',
        'exavg_avg_attempts': 'expected_attempts',
        'exavg_avg_passing_yards': 'expected_passing_yards',
        'exavg_avg_passing_tds': 'expected_passing_tds',
        'exavg_avg_time_of_possession': 'expected_time_of_possession',
        'exavg_avg_turnover': 'expected_turnover',
        'exavg_avg_field_goal_made': 'expected_field_goal_made'
    })
    folded_dataset_df['rating'] = folded_dataset_df['rating'].astype(int)
    folded_dataset_df['expected_time_of_possession'] = folded_dataset_df['expected_time_of_possession'].apply(lambda x: f"{int(x // 60)}:{int(x % 60):02}")
    # Load player data
    player_df = load_player_data(seasons)
    
    return dataset_df, folded_dataset_df, player_df

