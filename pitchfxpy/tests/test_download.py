import os
import shutil

from nose.tools import raises

import pitchfxpy.download as download


# Functions to create and delete folders
def create_folder(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def delete_folder(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


# Tests
class TestGetURL:
    def test_basic(self):
        url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
               "month_03/day_11/gid_2012_03_11_chamlb_colmlb_1/linescore.xml")
        test_texts = [
            '''Copyright 2012 MLB Advanced Media, L.P.''',
            '''home_name_abbrev="COL"''',
            '''away_code="cha"''',
            '''gameday_link="2012_03_11_chamlb_colmlb_1"''',
            '''winning_pitcher first_name="Jamie" first="Jamie" id="119469"'''
        ]
        text = download._get_url(url)

        for test_text in test_texts:
            assert test_text in text

    @raises(download.Error404)
    def test_nonexistent_url(self):
        url = ("http://gd2.mlb.com/components/game/mlb/year_2012/" +
               "month_03/day_11/gid_2012_03_11_chamlb_colmlb_1/linesgfcore.xml")
        download._get_url(url)


class TestConfirmRegularGame:
    def setup(self):
        self.urlstub = "http://gd2.mlb.com/components/game/mlb/year_2012"

    def test_regular_game(self):
        url = self.urlstub + "/month_06/day_10/gid_2012_06_10_nynmlb_nyamlb_1"
        assert download._confirm_regular_game(url)

    def test_error_game(self):
        url = self.urlstub + "month_06/day_10/gid_2012_06_10_tbamlb_flomlb_1"
        assert not download._confirm_regular_game(url)

    def test_playoff_game(self):
        url = self.urlstub + "month_10/day_06/gid_2012_10_06_oakmlb_detmlb_1/"
        assert not download._confirm_regular_game(url)

    def test_allstar_game(self):
        url = self.urlstub + "month_07/day_10/gid_2012_07_10_nasmlb_aasmlb_1/"
        assert not download._confirm_regular_game(url)

    def test_springtrain_game(self):
        url = self.urlstub + "month_03/day_11/gid_2012_03_11_chamlb_colmlb_1/"
        assert not download._confirm_regular_game(url)


class TestDLGameData:
    def setup(self):
        self.folder   = "test_folder/"
        self.url_loc  = ("http://gd2.mlb.com/components/game/mlb/" +
                         "year_2012/month_06/day_10/")
        self.gamename = "gid_2012_06_10_nynmlb_nyamlb_1"

        create_folder(self.folder)

    def teardown(self):
        delete_folder(self.folder)

    def test_basic(self):

        download._dl_game_data(self.url_loc, self.folder, self.gamename)

        assert os.path.isdir(self.folder + self.gamename + "/batters")
        assert os.path.isfile(self.folder + self.gamename + "/batters/121250.xml")
        assert os.path.isfile(self.folder + self.gamename + "/batters/579799.xml")

        assert os.path.isdir(self.folder + self.gamename + "/pitchers")
        assert os.path.isfile(self.folder + self.gamename + "/pitchers/110683.xml")
        assert os.path.isfile(self.folder + self.gamename + "/pitchers/579799.xml")

        assert os.path.isfile(self.folder + self.gamename + "/boxscore.xml")
        assert os.path.isfile(self.folder + self.gamename + "/game.xml")
        assert os.path.isfile(self.folder + self.gamename + "/inning_all.xml")
        assert os.path.isfile(self.folder + self.gamename + "/players.xml")


class TestDownloadData:
    def setup(self):
        self.folder = "test_folder"
        create_folder(self.folder)

    def teardown(self):
        delete_folder(self.folder)

    @raises(ValueError)
    def test_0dates(self):
        download.download_data(
            (),
            self.folder, date_list=False,
            max_workers=50, timeout=10, sleep=1, retry=False
        )

    @raises(ValueError)
    def test_m2dates(self):
        download.download_data(
            ("2012-09-20", "2012-09-20", "2012-09-21"),
            self.folder, date_list=False,
            max_workers=50, timeout=10, sleep=1, retry=False
        )

    @raises(ValueError)
    def test_bad_date_format1(self):
        download.download_data(
            ("2012-09-20", "2012-15-20"),
            self.folder, date_list=False,
            max_workers=50, timeout=10, sleep=1, retry=False
        )

    @raises(ValueError)
    def test_bad_date_format2(self):
        download.download_data(
            ("9/20/2012"),
            self.folder, date_list=False,
            max_workers=50, timeout=10, sleep=1, retry=False
        )
