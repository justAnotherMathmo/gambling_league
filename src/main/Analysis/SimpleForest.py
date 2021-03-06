# Standard library imports
import sys
# 3rd Party imports
import pandas as pd
import numpy as np
import sklearn.ensemble
# Repository Files
import _constants


def add_over_all_stats(df, stat_name):
    """Adds stat_name together for one player"""
    new_col = df[['{}/{}'.format(i, stat_name) for i in range(5)]].sum(axis=1)
    df['all/{}'.format(stat_name)] = new_col


def add_over_all_stats_new(df, stat_name):
    """Adds stat_name together for one player"""
    new_col_blue = df.ix[df.side == 1, ['{}/{}'.format(i, stat_name) for i in range(5)]].sum(axis=1)
    new_col_red = df.ix[df.side == 0, ['{}/{}'.format(i, stat_name) for i in range(5, 10)]].sum(axis=1)
    df.ix[df.side == 1, 'all/{}'.format(stat_name)] = new_col_blue
    df.ix[df.side == 0, 'all/{}'.format(stat_name)] = new_col_red


def simplify_dataframe(df, include_team_name=True):
    pivot_stats = ['kills', 'deaths', 'assists', 'goldEarned', 'totalDamageDealtToChampions',
                   'wardsPlaced', 'wardsKilled']
    pivot_timeline = []
    for desc in ['goldPerMinDeltas', 'csDiffPerMinDeltas', 'xpPerMinDeltas']:
        pivot_timeline += ['{}/{}'.format(desc, time) for time in ['0-10', '10-20', '20-30', '30-end']]

    team_stats = ['baronKills', 'dragonKills', 'firstBlood', 'firstTower']
    if include_team_name:
        team_stats.append('team_name')

    for new_stat in pivot_stats:
        add_over_all_stats_new(df, 'stats/{}'.format(new_stat))
    for new_stat in pivot_timeline:
        add_over_all_stats_new(df, 'timeline/{}'.format(new_stat))

    new_df = df[team_stats + ['all/stats/{}'.format(x) for x in pivot_stats]
                + ['all/timeline/{}'.format(x) for x in pivot_timeline]]


    return new_df


def team_data(df):
    simple_df = simplify_dataframe(df)
    gb = simple_df.groupby(['team_name']).mean()
    return gb


def forest_training_data(df):
    list_of_games = []
    team_df = team_data(df)
    for row_num in range(len(df)//2):
        # Get aggregate data for a match with both teams, flipping for games
        blue_name = df[df.index == 2*row_num].squeeze()['team_name']
        red_name = df[df.index == 2*row_num+1].squeeze()['team_name']
        team_blue = team_df.loc[blue_name].squeeze()
        team_red = team_df.loc[red_name].squeeze()
        game_data1 = np.append(team_blue.as_matrix(), team_red.as_matrix())
        game_data1 = np.append(game_data1, [0])
        game_data2 = np.append(team_red.as_matrix(), team_blue.as_matrix())
        game_data2 = np.append(game_data2, [1])
        list_of_games += [game_data1, game_data2]

    return list_of_games, list(df.win)


def predict_league(league_id):
    # To allow the league id to be called from the command line
    # Where the actual work is done
    df = pd.read_csv(_constants.data_location + 'simple_game_data_leagueId={}.csv'.format(league_id))
    training, winloss = forest_training_data(df)
    # df3 = pd.read_csv(_constants.data_location + 'simple_game_data_leagueId={}.csv'.format(5))
    # test, twin = forest_training_data(df3)
    print(len(training[0]))
    forest = sklearn.ensemble.RandomForestClassifier(n_estimators=500, oob_score=True, n_jobs=4)
    forest.fit(training, winloss)
    print(forest.oob_score_,  forest.score(training, winloss))
    print(len(forest.feature_importances_))
    return forest

