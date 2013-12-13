import os
import shutil

import nose

import pitchfx


# Setup and Teardown Functions
def c_folder_func(path):
    def create_folder():
        if not os.path.isdir(path):
            os.makedirs(path)
    return create_folder


def d_folder_func(path):
    def delete_folder():
        if os.path.isdir(path):
            shutil.rmtree(path)
    return delete_folder


# Testing _create_folder()
@nose.tools.with_setup(teardown=d_folder_func("test_folder"))
def test_create_folder():
    pitchfx._create_folder("test_folder")
    assert os.path.isdir("test_folder")

@nose.tools.with_setup(setup=c_folder_func("test_folder"),
                       teardown=d_folder_func("test_folder"))
def test_create_folder_already_Exists():
    pitchfx._create_folder("test_folder")
    assert os.path.isdir("test_folder")

# Testing _get_url()
def test_get_url():
    url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
           "month_03/day_11/gid_2012_03_11_chamlb_colmlb_1/linescore.xml")
    test_texts = [
        '''Copyright 2012 MLB Advanced Media, L.P.''',
        '''home_name_abbrev="COL"''',
        '''away_code="cha"''',
        '''gameday_link="2012_03_11_chamlb_colmlb_1"''',
        '''winning_pitcher first_name="Jamie" first="Jamie" id="119469"'''
    ]
    text = pitchfx._get_url(url)

    for test_text in test_texts:
        assert test_text in text


@nose.tools.raises(pitchfx.Error404)
def test_get_url_nonexistent():
    url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
           "month_03/day_11/gid_2012_03_11_chamlb_colmlb_1/linesgfcore.xml")
    pitchfx._get_url(url)


# Testing _confirm_regular_game()
def test_confirm_regular_game_pass():
    url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
           "month_06/day_10/gid_2012_06_10_nynmlb_nyamlb_1")
    assert pitchfx._confirm_regular_game(url)


def test_confirm_nonregular_game_fail():
    url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
           "month_06/day_10/gid_2012_06_10_tbamlb_flomlb_1")
    assert not pitchfx._confirm_regular_game(url)


def test_confirm_playoff_game_fail():
    url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
           "month_10/day_06/gid_2012_10_06_oakmlb_detmlb_1/")
    assert not pitchfx._confirm_regular_game(url)


def test_confirm_allstar_game_fail():
    url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
           "month_07/day_10/gid_2012_07_10_nasmlb_aasmlb_1/")
    assert not pitchfx._confirm_regular_game(url)


def test_confirm_springtrain_game_fail():
    url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
           "month_03/day_11/gid_2012_03_11_chamlb_colmlb_1/")
    assert not pitchfx._confirm_regular_game(url)


# Testing _dl_game_data()
@nose.tools.with_setup(setup=c_folder_func("test_folder"),
                       teardown=d_folder_func("test_folder"))
def test_dl_game_data():
    url_loc  = "http://gd2.mlb.com/components/game/mlb/year_2012/month_06/day_10/"
    gamename = "gid_2012_06_10_nynmlb_nyamlb_1"
    loc      = "test_folder"

    pitchfx._dl_game_data(url_loc, loc, gamename, max_workers=5)

    assert os.path.isdir(loc + "/" + gamename + "/batters")
    assert os.path.isfile(loc + "/" + gamename + "/batters/121250.xml")
    assert os.path.isfile(loc + "/" + gamename + "/batters/579799.xml")

    assert os.path.isdir(loc + "/" + gamename + "/pitchers")
    assert os.path.isfile(loc + "/" + gamename + "/pitchers/110683.xml")
    assert os.path.isfile(loc + "/" + gamename + "/pitchers/579799.xml")

    assert os.path.isfile(loc + "/" + gamename + "/boxscore.xml")
    assert os.path.isfile(loc + "/" + gamename + "/game.xml")
    assert os.path.isfile(loc + "/" + gamename + "/inning_all.xml")
    assert os.path.isfile(loc + "/" + gamename + "/players.xml")
