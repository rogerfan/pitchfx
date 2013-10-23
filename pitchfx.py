import os, sys, re
from datetime import date, timedelta as td
from time import sleep
from urllib.parse import urljoin
import xml.etree.cElementTree as ET

import requests
from bs4 import BeautifulSoup


def dl_pitchfx_data(startdate, enddate, loc):
    '''Download all regular season pitch f/x data for a given date range.

    Arguments
    ---------
    startdate : str
        Date as string, formatted as "YYYY/MM/DD".
    enddate : str
        Date as string, formatted as "YYYY/MM/DD". Use None to use
        current date as end date.
    loc : str
        Directory to download data to.

    '''

    # handle dates, including if enddate = None

    # create list of days in between

    # iterate over dates
        # create month folder
        # create day folder

        # check date url exists
        # create list of games on that date
        # confirm regular game for each game
        # download each game

        # error handling: delete entire day's folder if Error404





def _confirm_regular_game(url):
    '''Check that a game exists and that it is a regular season game.'''

    # check if game exists at all, as duplicate entries with no data exist
    # choose what to check with, probably if bocscore.xml or game.xml exist

    # use game_type in linescore.xml to check for if it's a regular season game
    # real games have game_type == "R"


def _dl_game_data(url_loc, loc, gamename):
    '''Download all game data.'''

    gameurl    = urljoin(url_loc, gamename)
    gameloc    = os.path.join(loc, gamename)
    batterloc  = os.path.join(gameloc, "batters")
    pitcherloc = os.path.join(gameloc, "pitchers")

    _create_folder(gameloc)
    _create_folder(batterloc)
    _create_folder(pitcherloc)

    try:
        sys.stdout.write("Downloading data for game: " + gamename)
        sys.stdout.flush()

        _dl_game_data_part(gameurl + "/boxscore.xml", gameloc, "boxscore.xml")
        _dl_game_data_part(gameurl + "/game.xml"    , gameloc, "game.xml")
        _dl_game_data_part(gameurl + "/players.xml" , gameloc, "players.xml")
        _dl_game_data_part(gameurl + "/inning/inning_all.xml" , gameloc, 
                           "inning_all.xml")

        batterlist  = _get_playerlist(gameurl + "/batters/")
        pitcherlist = _get_playerlist(gameurl + "/pitchers/")

        for batter in batterlist:
            _dl_game_data_part(gameurl + "/batters/" + batter, batterloc, batter)
        for pitcher in pitcherlist:
            _dl_game_data_part(gameurl + "/pitchers/" + pitcher, pitcherloc, pitcher)
    except Error404:
        print("\nData cannot be found for game: " + gamename)
        raise

    print("    ==> Done.")

def _get_playerlist(url):
    '''Create a list of player .xml files at a url.'''
    r = requests.get(url)
    if r.status_code == 404:
        raise Error404(url)

    soup = BeautifulSoup(r.text)
    playerlist_raw = soup.find_all('a', href=re.compile("[0-9]*\.xml"))
    playerlist = [x.contents[0].strip(' ') for x in playerlist_raw]

    return playerlist

def _get_gamelist(url):
    '''Create a list of game folders at a url.'''
    pass

def _dl_game_data_part(url, loc, filename):
    '''Download a game data piece.'''

    r = requests.get(url)
    if r.status_code == 404:
        raise Error404(url)
    
    with open(os.path.join(loc, filename), 'w') as file_:
        file_.write(r.text)

def _create_folder(path):
    if not os.path.isdir(path):
        os.mkdir(path)

class Error404(Exception):
    '''Exception raised for 404 errors.'''
    pass


def main():
    '''Script for testing.'''

    loc = "M:/Libraries/Documents/Code/Python/Baseball/Data/test/"
    url_loc = "http://gd2.mlb.com/components/game/mlb/year_2012/month_06/day_15/"
    gamename = "gid_2012_06_15_bosmlb_chnmlb_1"

    _create_folder(loc)
    _dl_game_data(url_loc, loc, gamename)

    print("Done.")

if __name__ == "__main__":
    main()



