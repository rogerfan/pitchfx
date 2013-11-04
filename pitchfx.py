import os, sys, time, re
import datetime as dt
import concurrent.futures
import xml.etree.cElementTree as ET

import requests
from bs4 import BeautifulSoup


def main():
    '''Script for testing.'''

    # loc = "M:/Libraries/Documents/Code/Python/Baseball/Data/test/"
    loc = "/home/rogerfan/Documents_Local/pitchfx/Data/test/"
    _create_folder(loc)

    dl_pitchfx_data(("2012-09-18", "2012-09-20"), loc, date_list=False,
                    max_workers=50, timeout=20, sleep=5, retry=True)

    print("Done.")


def dl_pitchfx_data(dates, loc, date_list=False, max_workers=30, timeout=20,
                    sleep=1, retry=False):
    '''Download all regular season pitch f/x data for a given date range.

    Arguments
    ---------
    dates : list of strings
        List of strings formatted as "YYYY-MM-DD".
        If len(dates) == 2 they are used as the endpoints of a range.
        If len(dates) == 1 it is used as the startdate and the enddate is set to
        the day before the current day.
    loc : str
        Directory to download data to.
    date_list=False: bool
        If True, treats dates as a list of dates rather than range endpoints.
    max_workers=30: int
        Maximum threads to use when downloading data.
    timeout=20: float
        Timeout in seconds for http requests.
    sleep=1: float
        Time in seconds to sleep between game downloads.
    retry=False: bool
        Retry downloading problem dates until all dates are successfully dled.

    '''

    # Handle dates
    if not date_list:
        dlen = len(dates)
        if dlen == 0: raise ValueError("Requires at least one date.")
        if dlen  > 2: raise ValueError("Too many dates. Set date_list=True?")

        d1 = dt.datetime.strptime(dates[0], "%Y-%m-%d").date()
        if dlen == 1: d2 = dt.date.today() - dt.timedelta(days=1)
        if dlen == 2: d2 = dt.datetime.strptime(dates[1], "%Y-%m-%d").date()
        dlist = [d1 + dt.timedelta(days=i) for i in range((d2-d1).days + 1)]
    else:
        dlist = [dt.datetime.strptime(date, "%Y-%m-%d").date()
                 for date in dates]

    # Misc
    baseurl  = "http://gd2.mlb.com/components/game/mlb"
    tagmatch = re.compile("gid[0-9a-zA-Z_]+/")
    problems = []

    for date in dlist:

        # Extract date components
        yr = str(date.year)
        mn = str(date.month).zfill(2)
        dy = str(date.day).zfill(2)

        # Create folder
        dayloc = os.path.join(loc, yr, mn, dy)
        _create_folder(dayloc)

        # Access date URL
        dayurl = "{}/year_{}/month_{}/day_{}".format(baseurl, yr, mn, dy)

        try:
            page = _get_url(dayurl, timeout=timeout)
        except Error404:
            continue
        except requests.exceptions.Timeout:
            print(" !!! HTTP Timeout {}: {}".format(timeout, date))
            problems.append(date)
            continue

        # Create list of games on that date
        glist = BeautifulSoup(page).find_all('a', href=tagmatch)
        glist = [x.contents[0].strip(' /') for x in glist]

        # Select only regular games
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
                f_reggame = {ex.submit(_confirm_regular_game, "{}/{}".format(
                             dayurl, game), timeout=timeout): game for game in
                             glist}

            reggame = {f_reggame[future]: future.result() for future in
                       concurrent.futures.as_completed(f_reggame)}
        except requests.exceptions.Timeout:
            print(" !!! HTTP Timeout {}: {}".format(timeout, date))
            problems.append(date)
            continue

        glist = [game for game, reg in reggame.items() if reg]
        num = len(glist)

        # Download game data
        try:
            for i, game in enumerate(glist):
                _dl_game_data(dayurl, dayloc, game, i=i+1, num=num,
                              max_workers=30, timeout=timeout)
                time.sleep(sleep)

        except requests.exceptions.Timeout:
            print(" !!! HTTP Timeout {:>2}: {}".format(timeout, date))
            problems.append(str(date))

    # Problems
    if problems:
        probformat = ',\n    '.join(problems)
        print("\nDates with HTTP timeouts:\n[\n    {}\n]".format(probformat))

        if retry:
            print("\nRetrying dates with HTTP timeouts.")
            dl_pitchfx_data(problems, loc, date_list=True, max_workers=max_workers,
                            timeout=timeout, sleep=sleep, retry=retry)


def _confirm_regular_game(url, timeout=10):
    '''Check that a game exists and that it is a regular season game.'''

    # Check if game exists.
    try:
        game_text = _get_url(url, timeout=timeout)
        if not "boxscore.xml" in game_text: return False
    except Error404:
        return False

    # Check game is a regular season game.
    linescore_text = _get_url(url + "/linescore.xml", timeout=timeout)
    root = ET.fromstring(linescore_text)
    if not root.attrib['game_type'] == 'R':
        return False

    return True


def _dl_game_data(url_loc, loc, gamename, i="", num="",
                  max_workers=30, timeout=10):
    '''Download game data.'''

    # Combine URLs and location paths
    gameurl    = "{}/{}".format(url_loc, gamename)
    gameloc    = os.path.join(loc, gamename)
    batterloc  = os.path.join(gameloc, "batters")
    pitcherloc = os.path.join(gameloc, "pitchers")

    # Create folders
    _create_folder(gameloc)
    _create_folder(batterloc)
    _create_folder(pitcherloc)

    # Timing and printing
    time1 = time.time()
    sys.stdout.write("Downloading: {:<30} {:>2}/{:<2}".format(gamename, i, num))
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

    print(" ==> Done ({:5.2f} sec)".format(time.time() - time1))


def _get_url(url, timeout=10):
    '''Load url contents.'''

    r = requests.get(url, timeout=timeout)
    if r.status_code == 404:
        raise Error404(url)

    return r.text


def _create_folder(path):
    if not os.path.isdir(path):
        os.makedirs(path)


class Error404(Exception):
    pass


if __name__ == "__main__":
    main()
