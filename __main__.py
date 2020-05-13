# Ten Man Stats Viewer
# (c) 2020 Jacob "Wayz" Rice
VERSION = "0.5"

import time
import math
import threading
import numpy as np
import matplotlib.pyplot as ppl

from faceit_data import FaceitData

HUB_ID = "9ace3498-5c27-47a4-9d8b-59d10e0a19c5"
API_KEY = "f09a58a1-40b3-472f-af5d-47fe6e2770fe"
CHUNK_SIZE = 10  # 10 is probably optimal for most use cases
players = {}
player_ids = {}
hub_matches = {}
player_final_stats = []
DEBUG = False



class main():
    def __init__(self):
        print("10 Mans Stats Viewer v" + VERSION)
        print("Created by Wayz")
        start_time = 1580082900
        end_time = 1589950800
        print("Initializing with season 1 data from UMN 10 Mans...")  # does this so no null errors occur
        self.File_Handler(start_time, end_time)
        self.calculate_player_stats()
        self.take_commands()

    def take_commands(self):
        global DEBUG
        thread = None
        print('Type "?" for a list of commands')
        while (True):
            try:
                command = input(">>> ").lower().split()
                if (len(command) == 0):
                    print("Please enter a command")
                elif (command[0] == "record"):
                    if(len(command) > 1):
                        self.get_record(command[1])
                    else:
                        print("""Invalid entry. Type "record ?" to get a list of stats""")
                elif (command[0] == "top"):
                    if ((len(command) == 2) and (command[1] == "?")):
                        print("Flags:")
                        print("    -v | prints the values of the stats next to the player names")
                    elif (((len(command) == 4) or (len(command) == 5)) and self.stat_exists(command[1]) and int(
                            command[2]) > 0):
                        top_players = self.top(command[1], int(command[2]), int(command[3]))
                        stat_array = []
                        stat_array = self.get_stat_values(command[1], len(player_final_stats), int(command[3]))
                        stat_array.sort(reverse=True)
                        data = [top_players, stat_array]
                        if ((len(command) == 5) and command[4] == "-v"):
                            data = [top_players, stat_array]
                            self.print_ranked_list(data,
                                                   (self.ret_uppercase(command[1]) + " Ranking: (Names and Values)"),
                                                   int(command[2]))
                        else:
                            data = [top_players]
                            self.print_ranked_list(data, (self.ret_uppercase(command[1]) + " Ranking: (Names)"),
                                                   int(command[2]))
                    else:
                        if ((len(command) > 1) and not (self.stat_exists(command[1]))):
                            print('Stat does not exist. Type "stats" for a list of supported stats')
                        else:
                            print("Usage: top <stat> <len> <min_games> [flags]")
                elif (command[0] == "debug"):  # not listed in ? menu
                    if (command[1] == "1"):
                        DEBUG = True
                    elif (command[1] == "0"):
                        DEBUG = False
                    else:
                        print("Usage: debug <0 or 1>")
                elif (command[0] == "exit"):
                    exit(0)
                elif (command[0] == "time"):
                    try:
                        if (len(command) == 2):
                            if (command[1] == "s1"):
                                self.File_Handler(1580082900, 1589950800)
                                self.calculate_player_stats()
                            elif (command[1] == "all"):
                                self.File_Handler(0, 2**63-1)
                                self.calculate_player_stats()
                            else:
                                print('"' + command[1] + '" is not a valid season')
                        elif (len(command) == 3):
                            if (int(command[1]) >= 0 and int(command[2]) > int(command[1])):
                                self.File_Handler(int(command[1]), int(command[2]))
                                self.calculate_player_stats()
                            else:
                                print("start_time and end_time must be valid Unix Time integers")
                        else:
                            print('Invalid command arguments for "time"')
                    except:
                        print("FATAL ERROR: Error while gathering new dataset")
                        exit(6)
                elif (command[0] == "box_plot") or (command[0] == "boxplot"):
                    try:
                        if (command[1] == "?"):
                            self.print_box_plot_flags()
                        else:
                            stat_array = []
                            stat_array = self.get_stat_values(command[1], len(player_final_stats), int(command[2]))
                            stat_array.sort(reverse=True)

                            if ((len(command) > 3) and ((len(command) - 3) % 2) == 0):
                                x = 3
                                while (x < len(command)):
                                    if (x != 3):
                                        print("")
                                    if (command[x] == "-la"):
                                        top_players = self.top(command[1], int(command[x + 1]), int(command[2]))
                                        data = [top_players, stat_array]
                                        self.print_ranked_list(data, (
                                                    self.ret_uppercase(command[1]) + " Ranking: (Names and Values)"),
                                                               int(command[x + 1]))
                                        x += 2
                                    elif (command[x] == "-ln"):
                                        top_players = self.top(command[1], int(command[x + 1]), int(command[2]))
                                        data = [top_players]
                                        self.print_ranked_list(data,
                                                               (self.ret_uppercase(command[1]) + " Ranking: (Names)"),
                                                               int(command[x + 1]))
                                        x += 2
                                    elif (command[x] == "-lv"):
                                        data = [stat_array]
                                        self.print_ranked_list(data,
                                                               (self.ret_uppercase(command[1]) + " Ranking: (Values)"),
                                                               int(command[x + 1]))
                                        x += 2
                                    else:
                                        raise RuntimeError
                            if (thread is None):
                                thread = (threading.Thread(target=self.display_box_plot, args=(command[1], stat_array)))
                                thread.start()
                            else:
                                if (thread.is_alive()):
                                    print("Cannot create new graph, as only 1 graph instance is allowed at once.")
                                    print("Please close the current open graph before opening a new one.")
                                else:
                                    thread = (
                                        threading.Thread(target=self.display_box_plot, args=(command[1], stat_array)))
                                    thread.start()

                    except:
                        print("""An error occurred. Usage: box_plot <stat> <min_games> [flags]""")
                elif (command[0] == "scatter_plot") or (command[0] == "scatterplot"):
                    try:
                        if (command[1] == "?"):
                            self.print_scatter_plot_flags()
                        else:
                            regression = None

                            temp = self.get_stat_values(command[1], len(player_final_stats), int(command[3]), stat2=command[2])
                            x_array = temp[0]
                            y_array = temp[1]

                            '''INSERT FLAGS HERE'''
                            if (len(command) > 4):
                                x = 4
                                space_needed = False
                                while (x < len(command)):
                                    if (command[x] == "-la"):
                                        if space_needed:
                                            print("")
                                            space_needed = False
                                        top_players = self.top(command[1], int(command[x + 1]), int(command[3]))
                                        two_d_list_array = self.sort_2d_array(x_array, y_array)
                                        data = [top_players, two_d_list_array[0], two_d_list_array[1]]
                                        self.print_ranked_list(data, self.ret_uppercase(command[1]) + " vs " + self.ret_uppercase(command[2]) + " Ranking:", int(command[x + 1]))
                                        x += 2
                                        space_needed = True
                                    elif (command[x] == "-ln"):
                                        if space_needed:
                                            print("")
                                            space_needed = False
                                        top_players = self.top(command[1], int(command[x + 1]), int(command[3]))
                                        data = [top_players]
                                        self.print_ranked_list(data, self.ret_uppercase(
                                            command[1]) + " vs " + self.ret_uppercase(command[2]) + " Ranking:",
                                                               int(command[x + 1]))
                                        x += 2
                                        space_needed = True
                                    elif (command[x] == "-lv"):
                                        if space_needed:
                                            print("")
                                            space_needed = False
                                        two_d_list_array = self.sort_2d_array(x_array, y_array)
                                        data = [two_d_list_array[0], two_d_list_array[1]]
                                        self.print_ranked_list(data, self.ret_uppercase(
                                            command[1]) + " vs " + self.ret_uppercase(command[2]) + " Ranking:",
                                                               int(command[x + 1]))
                                        x += 2
                                        space_needed = True
                                    elif (command[x] == "-r"):
                                        regression = "lin"
                                        x += 1
                                    else:
                                        raise RuntimeError

                            if (thread is None):
                                thread = (threading.Thread(target=self.display_scatter_plot, args=(command[1], command[2], x_array, y_array, regression)))
                                thread.start()
                            else:
                                if (thread.is_alive()):
                                    print("Cannot create new graph, as only 1 graph instance is allowed at once.")
                                    print("Please close the current open graph before opening a new one.")
                                else:
                                    thread = (threading.Thread(target=self.display_scatter_plot, args=(command[1], command[2], x_array, y_array, regression)))
                                    thread.start()

                    except:
                        print("""An error occurred. Usage: scatter_plot <x_stat> <y_stat> <min_games> [flags]""")



                elif (command[0] == "?"):
                    self.print_help_lists()
                elif (command[0] == "stats"):
                    self.print_stats_list()
                else:
                    print("""Invalid command. Type "?" for a list of commands""")
            except:
                if (command[0] == "exit"):
                    exit(0)
                print("WARNING: Exception occurred!")
                print("""Invalid command. Type "?" for a list of commands""")

    def print_help_lists(self, command=None):
        if (command is None):
            print("Commands:")
            print("box_plot <stat> <min_games> [flags]| displays the stats as a box plot. Use 'box_plot ?' for a list of flags")
            print("exit | exits the program")
            print("record <stat> | lists the record high for a stat in a single pug and lists the record holder")
            print("scatter_plot <x_stat> <y_stat> <min_games> | displays the stats given as a scatter plot")
            print("stats | lists the supported stats")
            print("time <start_time> <end_time> | updates stats with new timeframe, TIMES ARE IN UNIX TIME FORMAT (may fix later)")
            print("time <season> | same as above, but use 's1' for season 1 data")
            print("top <stat> <len> <min_games> | displays the top players in a stat. Use 'top ?' for a list of flags")

    def print_stats_list(self):
        print(
            "Stats currently supported: assists*, deaths*, headshots*, headshot_percentage, KDR, KRR, kills, mvps*, aces*, four_kill_rounds*, three_kill_rounds*")
        print("""* indicates that you can add "_r" to the stat to get the average per round instead of per game""")

    def print_box_plot_flags(self):
        print("Flags:")
        print("    -la <len> | prints both the names and values of the data on the box plot, up to <len> players/entries")
        print("    -ln <len> | prints the names of the players on the box plot, up to <len> players")
        print("    -lv <len> | prints the numerical values of the data on the box plot, up to <len> entries")

    def print_scatter_plot_flags(self):
        print("Flags:")
        print("    -la <len> | prints both the names and (x,y) values of the data on the scatter plot, up to <len> players/entries")
        print("    -ln <len> | prints the names of the players on the scatter plot, up to <len> players, ordered by x values")
        print("    -lv <len> | prints the numerical values of the data on the scatter plot, up to <len> entries, ordered by x values")
        print("    -r | adds a linear regression line to the resulting graph")

    def display_box_plot(self, stat, stat_array):
        xmd = ppl
        xmd.show(block=False)
        fig1, ax1 = ppl.subplots()
        ax1.set_title(self.ret_uppercase(stat) + " Distribution (n = " + str(len(stat_array)) + ")")
        ax1.boxplot(stat_array, vert=False)
        xmd.show()

    def display_scatter_plot(self, x_stat, y_stat, x_array, y_array, regression=None):
        ppl.show(block=False)
        m = None
        if not (regression is None):
            if(regression == "lin"):
                m, b = np.poly1d(np.polyfit(x_array, y_array, 1))
        fig1, ax1 = ppl.subplots()
        ax1.set_title(self.ret_uppercase(x_stat) + " vs " + self.ret_uppercase(y_stat) + " (n = " + str(len(x_array)) + ")")
        ax1.scatter(x_array, y_array)
        if not (m is None):
            yp = np.polyval([m, b], x_array)
            ax1.plot(x_array, yp, color="red", label="Linear Regression")
        ppl.show()

    @staticmethod
    def sort_2d_array(x_array, y_array):
        sorted_x = []
        for x in x_array:
            sorted_x.append(x)
        sorted_x.sort(reverse=True)
        sorted_y = []

        c = 0
        for x in sorted_x:
            found = False
            i = 0
            while not found:
                if(x == x_array[i]):
                    sorted_y.append(y_array[i])
                    found = True
                i += 1
            c += 1

        return [sorted_x, sorted_y]



    def print_ranked_list(self, data, title, stop_point):
        columns = len(data) + 1
        max_width = []
        max_width.append(int(math.log(len(data[0]))))
        total_width = max_width[0] + columns + 1
        for dataset in data:
            temp_max_width_val = 0
            for element in dataset:
                if (len(str(element)) > temp_max_width_val):
                    temp_max_width_val = len(str(element))
            max_width.append(temp_max_width_val)
            total_width += temp_max_width_val
        if (len(title) > total_width):
            total_width = len(title)

        x = 0
        dashes = ""
        print(title)
        while (x < total_width):
            dashes += "-"
            x += 1
        print(dashes)
        x = 1
        for entry in data[0]:
            if (x > stop_point):
                break
            line = ""
            z = 0
            while ((z + len(str(x))) < max_width[0]):
                line += " "
                z += 1
            line += str(x) + "| "
            y = 1
            while y < columns:
                z = 0
                spaces = ""
                while ((z + len(str(data[y - 1][x - 1]))) < max_width[y]):
                    spaces += " "
                    z += 1
                line += str(data[y - 1][x - 1]) + spaces + "| "
                y += 1
            line = line[:len(line) - 2]
            print(line)
            x += 1

    def top(self, stat, length, min_games):  # except id rather bottom
        working_array = []
        for e in player_final_stats:
            if (e.games_played >= min_games):
                working_array.append(e)

        if length < len(working_array):
            leng = length
        else:
            leng = len(working_array)

        return_array = []
        x = 0
        while x < leng:
            y = 0
            current_top_val = 0
            current_top_val_y = 0
            for pfs in working_array:
                if (self.ret_val_helper(pfs, stat) > current_top_val):
                    current_top_val = self.ret_val_helper(pfs, stat)
                    current_top_val_y = y
                y += 1
            return_array.append(working_array[current_top_val_y].nickname)
            working_array.pop(current_top_val_y)
            x += 1
        return return_array

    def get_stat_values(self, stat, length, min_games, stat2=None):
        if(stat2 is None):
            working_array = []
            for e in player_final_stats:
                if (e.games_played >= min_games):
                    working_array.append(e)

            if length < len(working_array):
                leng = length
            else:
                leng = len(working_array)

            return_array = []
            for pfs in working_array:
                return_array.append(self.ret_val_helper(pfs, stat))
            return return_array
        else:
            working_array = []
            for e in player_final_stats:
                if (e.games_played >= min_games):
                    working_array.append(e)

            if length < len(working_array):
                leng = length
            else:
                leng = len(working_array)

            return_array = []
            return_array2 = []
            for pfs in working_array:
                return_array.append(self.ret_val_helper(pfs, stat))
                return_array2.append(self.ret_val_helper(pfs, stat2))
            return [return_array, return_array2]

    def get_record(self, stat):
        return_string = ""
        supported_stats_pug = ["assists", "deaths", "headshots", "headshots_percentage", "kdr", "krr", "kills",
                               "mvps", "aces", "four_kill_rounds", "three_kill_rounds", "rounds"]
        if(self.stat_exists_pug(stat)):
            record = 0.
            record_holders = []
            for player_id in players:
                for match_id in players[player_id]:
                    player_pug_stats = players[player_id][match_id]
                    player_pug_stats.calc_stats()
                    TEST_DEBUG = float(self.get_stat_pug(stat, player_pug_stats))
                    if(float(self.get_stat_pug(stat, player_pug_stats)) >= record):
                        record = float(self.get_stat_pug(stat, player_pug_stats))
                        if(player_id in record_holders):
                            continue
                        else:
                            record_holders.append(player_id)
            for record_holder in record_holders:
                return_string += player_ids[record_holder].nickname + ", "
            return_string = "The record for " + self.ret_uppercase(stat) + " in one game is " + str(record) + ".\n    It is held by: " + \
                            return_string[:len(return_string) - 2]
            print(return_string)
            return
        elif(stat == "all"):
            for statistic in supported_stats_pug:
                self.get_record(statistic)
        elif(stat == "?"):
            return_string = "all, "
            for statistic in supported_stats_pug:
                return_string += statistic + ", "
                print("""Supported stats for "record": """ + return_string[:len(return_string) - 2])
        else:
            print("This stat does not exist or is not currently supported by this function.")


    #yes, I could have implemented these static methods better, but they work and its not worth fixing what isnt broke
    @staticmethod
    def get_stat_pug(stat, pps):
        if (stat == "assists"):
            return pps.assists
        elif (stat == "deaths"):
            return pps.deaths
        elif (stat == "headshots"):
            return pps.headshots
        elif (stat == "headshots_percentage"):
            return pps.headshots_percentage
        elif (stat == "kdr"):
            return pps.kdr
        elif (stat == "krr"):
            return pps.krr
        elif (stat == "kills"):
            return pps.kills
        elif (stat == "mvps"):
            return pps.mvps
        elif (stat == "aces"):
            return pps.aces
        elif (stat == "four_kill_rounds"):
            return pps.four_kill_rounds
        elif (stat == "three_kill_rounds"):
            return pps.three_kill_rounds
        elif (stat == "rounds"):
            return pps.rounds
        else:
            return None

    @staticmethod
    def ret_val_helper(pfs, stat):
        if (stat == "assists"):
            return pfs.assists_avg
        elif (stat == "deaths"):
            return pfs.deaths_avg
        elif (stat == "headshots"):
            return pfs.headshots_avg
        elif (stat == "headshot_percentage"):
            return pfs.headshots_percent_avg
        elif (stat == "kdr"):
            return pfs.KDR_avg
        elif (stat == "krr"):
            return pfs.KRR_avg
        elif (stat == "kills"):
            return pfs.kills_avg
        elif (stat == "mvps"):
            return pfs.mvps_avg
        elif (stat == "aces"):
            return pfs.aces_avg
        elif (stat == "four_kill_rounds"):
            return pfs.four_kill_rounds_avg
        elif (stat == "three_kill_rounds"):
            return pfs.three_kill_rounds_avg
        elif (stat == "assists_r"):
            return pfs.assists_avg_r
        elif (stat == "deaths_r"):
            return pfs.deaths_avg_r
        elif (stat == "headshots_r"):
            return pfs.headshots_avg_r
        elif (stat == "kills_r"):
            return pfs.kills_avg_r
        elif (stat == "mvps_r"):
            return pfs.mvps_avg_r
        elif (stat == "aces_r"):
            return pfs.aces_avg_r
        elif (stat == "four_kill_rounds_r"):
            return pfs.four_kill_rounds_avg_r
        elif (stat == "three_kill_rounds_r"):
            return pfs.three_kill_rounds_avg_r
        elif (stat == "games_played"):
            return pfs.games_played
        elif (stat == "win_rate"):
            return pfs.win_rate
        else:
            return None

    @staticmethod
    def ret_uppercase(stat):
        if (stat == "assists"):
            return "Assists"
        elif (stat == "deaths"):
            return "Deaths"
        elif (stat == "headshots"):
            return "Headshots"
        elif (stat == "headshot_percentage" or stat == "headshots_percentage"):
            return "Headshot Percentage"
        elif (stat == "kdr"):
            return "KDR"
        elif (stat == "krr"):
            return "KRR"
        elif (stat == "kills"):
            return "Kills"
        elif (stat == "mvps"):
            return "MVPs"
        elif (stat == "aces"):
            return "Aces"
        elif (stat == "four_kill_rounds"):
            return "Four Kill Rounds"
        elif (stat == "three_kill_rounds"):
            return "Three Kill Rounds"
        elif (stat == "assists_r"):
            return "Assists per Round"
        elif (stat == "deaths_r"):
            return "Deaths per Round"
        elif (stat == "headshots_r"):
            return "Headshots per Round"
        elif (stat == "kills_r"):
            return "Kills per Round"
        elif (stat == "mvps_r"):
            return "MVPs per Round"
        elif (stat == "aces_r"):
            return "Aces per Round"
        elif (stat == "four_kill_rounds_r"):
            return "Four Kill Rounds per Round"
        elif (stat == "three_kill_rounds_r"):
            return "Three Kill Rounds per Round"
        elif (stat == "games_played"):
            return "Games Played"
        elif (stat == "win_rate"):
            return "Win Rate"
        elif (stat == "rounds"):
            return "Rounds"
        else:
            raise ValueError

    @staticmethod
    def stat_exists(stat):
        if (stat == "assists"):
            return True
        elif (stat == "deaths"):
            return True
        elif (stat == "headshots"):
            return True
        elif (stat == "headshot_percentage"):
            return True
        elif (stat == "kdr"):
            return True
        elif (stat == "krr"):
            return True
        elif (stat == "kills"):
            return True
        elif (stat == "mvps"):
            return True
        elif (stat == "aces"):
            return True
        elif (stat == "four_kill_rounds"):
            return True
        elif (stat == "three_kill_rounds"):
            return True
        elif (stat == "assists_r"):
            return True
        elif (stat == "deaths_r"):
            return True
        elif (stat == "headshots_r"):
            return True
        elif (stat == "kills_r"):
            return True
        elif (stat == "mvps_r"):
            return True
        elif (stat == "aces_r"):
            return True
        elif (stat == "four_kill_rounds_r"):
            return True
        elif (stat == "three_kill_rounds_r"):
            return True
        elif (stat == "games_played"):
            return True
        elif (stat == "win_rate"):
            return True
        else:
            return False

    @staticmethod
    def stat_exists_pug(stat):
        if (stat == "assists"):
            return True
        elif (stat == "deaths"):
            return True
        elif (stat == "headshots"):
            return True
        elif (stat == "headshots_percentage"):
            return True
        elif (stat == "kdr"):
            return True
        elif (stat == "krr"):
            return True
        elif (stat == "kills"):
            return True
        elif (stat == "mvps"):
            return True
        elif (stat == "aces"):
            return True
        elif (stat == "four_kill_rounds"):
            return True
        elif (stat == "three_kill_rounds"):
            return True
        elif (stat == "rounds"):
            return True
        else:
            return False

    def File_Handler(self, start_time, end_time):
        global CHUNK_SIZE
        global HUB_ID
        global API_KEY
        if (start_time == 0):
            CHUNK_SIZE = 100
        else:
            CHUNK_SIZE = 10
        total_matches = 0
        d_start_time = time.time()

        global players
        global player_ids
        global player_final_stats
        global hub_matches
        players = {}
        player_ids = {}
        player_final_stats = []
        hub_matches = {}

        data_handler = FaceitData(API_KEY)

        loop = True
        x = CHUNK_SIZE * (-1)

        print("Downloading data from FACEIT servers... this may take a while")
        while loop:
            x += CHUNK_SIZE
            retry = 0
            hub_matches_builder = data_handler.hub_matches(HUB_ID, "past", x, CHUNK_SIZE)
            while (hub_matches_builder is None and retry < 10):
                hub_matches_builder = data_handler.hub_matches(HUB_ID, "past", x, CHUNK_SIZE)
                retry += 1
            if (not (hub_matches_builder is None) and retry == 10):
                print("FATAL ERROR: data_handler.hub_matches feed is constantly null")
                exit(1)

            if (hub_matches_builder["items"] == []):
                # print("WARNING: Items = NULL. Continuing, but these results may be incorrect")
                # print("Note: This usually means your start date was before the hub's creation")
                break
            if hub_matches_builder is None and hub_matches == {}:
                print("FATAL ERROR: data_handler.hub_matches feed is constantly null")
                exit(1)
            if (x == 0 and hub_matches_builder is None):
                print("FATAL ERROR: data_handler.hub_matches feed is originally null")
                exit(1)

            hub_matches_builder = hub_matches_builder["items"]
            y = True
            for match in hub_matches_builder:
                if (match["finished_at"] > start_time) and (match["finished_at"] < end_time):
                    # if the match is valid to be included in this data set
                    total_matches += 1
                    match_id = match["match_id"]
                    hub_matches[match_id] = Pug(match_id, data_handler)
                    hub_matches[match_id].import_teams()
                else:
                    if hub_matches == {}:
                        continue
                    else:
                        loop = False

        print(str(len(players)) + " players detected in " + str(total_matches) + " matches from " + str(start_time)
              + " to " + str(end_time))
        if (DEBUG): print("*** DEBUG *** | CHUNK_SIZE = " + str(CHUNK_SIZE) + " took " + str(
            time.time() - d_start_time) + " seconds to complete")

    def calculate_player_stats(self):
        global player_final_stats
        for player_id in players:
            assists = 0
            deaths = 0
            headshots = 0
            kills = 0
            mvps = 0
            aces = 0
            four_kill_rounds = 0
            rounds = 0
            three_kill_rounds = 0
            wins = 0
            games_played = 0
            for match_id in players[player_id]:
                player_pug_stats = players[player_id][match_id]
                assists += int(player_pug_stats.assists)
                deaths += int(player_pug_stats.deaths)
                headshots += int(player_pug_stats.headshots)
                kills += int(player_pug_stats.kills)
                mvps += int(player_pug_stats.mvps)
                aces += int(player_pug_stats.aces)
                four_kill_rounds += int(player_pug_stats.four_kill_rounds)
                rounds += int(player_pug_stats.rounds)
                three_kill_rounds += int(player_pug_stats.three_kill_rounds)
                wins += int(player_pug_stats.win)
                games_played += 1

            # stats are now added up
            if DEBUG: print(str(player_ids[player_id].nickname) + " played in " + str(games_played) + " games")
            stats = Player_Overall_Stats()

            stats.nickname = player_ids[player_id].nickname
            stats.playerID = player_id
            stats.games_played = games_played
            stats.assists_avg = assists / games_played
            stats.assists_avg_r = assists / rounds
            stats.deaths_avg = deaths / games_played
            stats.deaths_avg_r = deaths / rounds
            if(kills == 0):
                stats.headshots_percent_avg = 0
            else:
                stats.headshots_percent_avg = headshots / kills
            stats.headshots_avg = headshots / games_played
            stats.headshots_avg_r = headshots / rounds
            stats.kills_avg = kills / games_played
            stats.kills_avg_r = kills / rounds
            stats.mvps_avg = mvps / games_played
            stats.mvps_avg_r = mvps / rounds
            stats.aces_avg = aces / games_played
            stats.aces_avg_r = aces / rounds
            stats.four_kill_rounds_avg = four_kill_rounds / games_played
            stats.four_kill_rounds_avg_r = four_kill_rounds / rounds
            stats.three_kill_rounds_avg = three_kill_rounds / games_played
            stats.three_kill_rounds_avg_r = three_kill_rounds / rounds
            if(deaths == 0):
                stats.KDR_avg = 0
            else:
                stats.KDR_avg = kills / deaths
            stats.KRR_avg = kills / rounds
            stats.win_rate = wins / games_played

            player_final_stats = player_final_stats + [stats]


class Pug():
    match_id = None
    teams = None
    rounds = 0
    data_handler = None

    def __init__(self, match_id, data_handler):
        self.data_handler = data_handler
        self.match_id = match_id

    def import_teams(self):
        match_stats = self.data_handler.match_stats(self.match_id)
        if (match_stats is None):
            return
        rounds_played = match_stats["rounds"][0]["round_stats"]["Rounds"]

        team1 = match_stats["rounds"][0]["teams"][0]
        team2 = match_stats["rounds"][0]["teams"][1]

        roster = team1["players"] + team2["players"]

        for person in roster:
            player_id = person["player_id"]
            if (not (player_id in players)):
                # this person is not yet in the main player dictionary
                player_ids[player_id] = Player(player_id, person["nickname"])
                players[player_id] = {}

            players[player_id][self.match_id] = Player_Pug_Stats(person["player_stats"]["Assists"],
                                                                 person["player_stats"]["Deaths"],
                                                                 person["player_stats"]["Headshot"],
                                                                 person["player_stats"]["Kills"],
                                                                 person["player_stats"]["MVPs"],
                                                                 person["player_stats"]["Penta Kills"],
                                                                 person["player_stats"]["Quadro Kills"],
                                                                 rounds_played,
                                                                 person["player_stats"]["Triple Kills"],
                                                                 person["player_stats"]["Result"])


class Player():
    player_id = None
    nickname = None

    def __init__(self, player_id, nickname):
        self.player_id = player_id
        self.nickname = nickname


class Player_Pug_Stats():
    assists = 0
    deaths = 0
    headshots = 0
    kills = 0
    mvps = 0
    aces = 0
    four_kill_rounds = 0
    rounds = 0
    three_kill_rounds = 0
    win = 0

    headshots_percentage = 0.0
    krr = 0.0
    kdr = 0.0

    def __init__(self, assists, deaths, headshots, kills, mvps, aces, four_kill_rounds, rounds, three_kill_rounds, win):
        self.assists = assists
        self.deaths = deaths
        self.headshots = headshots
        self.kills = kills
        self.mvps = mvps
        self.aces = aces
        self.four_kill_rounds = four_kill_rounds
        self.rounds = rounds
        self.three_kill_rounds = three_kill_rounds
        self.win = win
        self.calc_stats()

    def calc_stats(self):
        if(int(self.kills) > 0):
            self.headshots_percentage = float(self.headshots) / float(self.kills) * 100.0
        if(int(self.rounds) > 0):
            self.krr = float(self.kills) / float(self.rounds)
        if(int(self.deaths) > 0):
            self.kdr = float(self.kills) / float(self.deaths)
        else:
            self.kdr = float(self.kills)


class Player_Overall_Stats():
    playerID = None
    nickname = None

    games_played = 0

    assists_avg = 0.
    deaths_avg = 0.
    headshots_percent_avg = 0.
    headshots_avg = 0.
    KDR_avg = 0.
    KRR_avg = 0.
    kills_avg = 0.
    mvps_avg = 0.
    aces_avg = 0.
    four_kill_rounds_avg = 0.
    three_kill_rounds_avg = 0.

    assists_avg_r = 0.
    deaths_avg_r = 0.
    headshots_avg_r = 0.
    kills_avg_r = 0.
    mvps_avg_r = 0.
    aces_avg_r = 0.
    four_kill_rounds_avg_r = 0.
    three_kill_rounds_avg_r = 0.

    win_rate = 0.

if __name__ == '__main__': main()
