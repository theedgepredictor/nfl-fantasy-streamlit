
import streamlit as st

from loaders import load_feature_store
from streamlit_controller import STYLE
import pandas as pd

import datetime

# Import tab modules
from tabs.players.players_tab import display_event_player_tab, display_player_tab

def find_year_for_season( date: datetime.datetime = None):
    """
    Find the year for a specific season based on the league and date.

    Args:
        league (ESPNSportTypes): Type of sport.
        date (datetime.datetime): Date for the sport (default is None).

    Returns:
        int: Year for the season.
    """
    SEASON_START_MONTH = {

        "NFL": {'start': 6, 'wrap': False},
    }
    if date is None:
        today = datetime.datetime.utcnow()
    else:
        today = date
    start = SEASON_START_MONTH["NFL"]['start']
    wrap = SEASON_START_MONTH["NFL"]['wrap']
    if wrap and start - 1 <= today.month <= 12:
        return today.year + 1
    elif not wrap and start == 1 and today.month == 12:
        return today.year + 1
    elif not wrap and not start - 1 <= today.month <= 12:
        return today.year - 1
    else:
        return today.year

# Path to the folder containing your Jupyter Notebooks
SEASONS = list(range(2019, find_year_for_season() + 1))
NOTEBOOK_FOLDER = './experiments/'  # Change this to the correct path
st.set_page_config(layout='wide')

# Function to read and convert Jupyter Notebook to markdown


def main():
    st.title('The Edge Predictor NFL Fantasy Statistics', anchor=False)
    # Load data
    dataset_df, folded_df, player_df = load_feature_store(SEASONS)

    ### Define tabs for Team, Event, Event Players, and Players
    event_player_tab, player_tab = st.tabs([
        "Event Players",
        "Players"
    ])

    with event_player_tab:
        st.markdown(STYLE, unsafe_allow_html=True)
        display_event_player_tab(dataset_df, player_df)

    with player_tab:
        st.markdown(STYLE, unsafe_allow_html=True)
        display_player_tab(player_df)


if __name__ == "__main__":
    main()