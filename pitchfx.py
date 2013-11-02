import os, sys, time, re
import concurrent.futures
from datetime import date, timedelta as td
import xml.etree.cElementTree as ET
from urllib.parse import urljoin

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
        yesterday as the end date.
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
            # parallelize this with a filter of sorts using _confirm_reg_game?
        # download each game

        # error handling: delete entire day's folder if Error404


def _confirm_regular_game(url):
    '''Check that a game exists and that it is a regular season game.'''

    # Check if game exists.
    try:
        game_text = _get_url(url)
        if not "boxscore.xml" in game_text: return False
    except Error404:
        return False

    # Check game is a regular season game.
    linescore_text = _get_url(url + "/linescore.xml")
    root = ET.fromstring(linescore_text)
    if not root.attrib['game_type'] == 'R': return False

    return True


def _dl_game_data(url_loc, loc, gamename, max_workers=30, timeout=10):
    '''Download all game data.'''

    # Combine URLs and location paths
    gameurl    = urljoin(url_loc, gamename)
    gameloc    = os.path.join(loc, gamename)
    batterloc  = os.path.join(gameloc, "batters")
    pitcherloc = os.path.join(gameloc, "pitchers")

    # Create folders
    _create_folder(gameloc)
    _create_folder(batterloc)
    _create_folder(pitcherloc)

    # Timing and printing
    time1 = time.clock()
    sys.stdout.write("Downloading: {:<35}".format(gamename))
    sys.stdout.flush()

    try:
        # Download and parse player lists
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f_plists = {ex.submit(_get_url, "{}/{}".format(gameurl, ptype),
                        timeout=timeout): ptype for ptype in
                        ("batters", "pitchers")}

        plists = {f_plists[future]: future.result() for future in
                  concurrent.futures.as_completed(f_plists)}

        for ptype in ("batters", "pitchers"):
            soup = BeautifulSoup(plists[ptype])
            playerlist_raw = soup.find_all('a', href=re.compile("[0-9]*\.xml"))
            plists[ptype] = [x.contents[0].strip(' ') for x in playerlist_raw]

        # Create URL and location path lists
        urllist = ["{}{}.xml".format(gameurl, item) for item in
                   ("/boxscore", "/game", "/players", "/inning/inning_all")]
        loclist = ["{}{}.xml".format(gameloc, item) for item in
                   ("/boxscore", "/game", "/players", "/inning_all")]

        for ptype in ("batters", "pitchers"):
            urllist_t = ["{}/{}/{}".format(gameurl, ptype, item) for item in
                         plists[ptype]]
            loclist_t = ["{}/{}/{}".format(gameloc, ptype, item) for item in
                         plists[ptype]]
            urllist.extend(urllist_t)
            loclist.extend(loclist_t)

        # Download data
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            f_xml = {ex.submit(_get_url, xmlurl, timeout=timeout): xmlloc
                     for (xmlloc, xmlurl) in zip(loclist, urllist)}

        xmldict = {f_xml[future]: future.result() for future in
                   concurrent.futures.as_completed(f_xml)}

        # Save data
        for xmlloc, xmlval in xmldict.items():
            with open(xmlloc, 'w') as file_:
                file_.write(xmlval)

    except Error404:
        print("\nData cannot be found for game: " + gamename)
        raise

    print("==> Done ({:5.2f} sec)".format(time.clock() - time1))


def _get_url(url, timeout=10):
    '''Load url contents.'''

    r = requests.get(url, timeout=timeout)
    if r.status_code == 404:
        raise Error404(url)

    return r.text


def _create_folder(path):
    if not os.path.isdir(path):
        os.mkdir(path)


class Error404(Exception):
    pass


def main():
    '''Script for testing.'''

    # loc = "M:/Libraries/Documents/Code/Python/Baseball/Data/test/"
    loc = "/home/rogerfan/Documents_Local/pitchfx/Data/test/"
    url_loc = "http://gd2.mlb.com/components/game/mlb/year_2012/month_06/day_15/"
    gamename = "gid_2012_06_15_bosmlb_chnmlb_1"

    _create_folder(loc)
    _dl_game_data(url_loc, loc, gamename)

    print(_confirm_regular_game(urljoin(url_loc, gamename)))
    print(_confirm_regular_game('''http://gd2.mlb.com/components/game/mlb/year_2012/
month_10/day_10/gid_2012_10_10_detmlb_adtmlb_1'''))
    print(_confirm_regular_game('''http://gd2.mlb.com/components/game/mlb/year_2012/
month_07/day_10/gid_2012_07_10_nasmlb_aasmlb_1'''))

    print("Done.")

if __name__ == "__main__":
    main()
