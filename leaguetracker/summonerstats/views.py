# ORIGINAL

from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Summoner, Match, Junction
from datetime import date, datetime
from django.contrib import messages
from django.contrib.messages import get_messages
from .teambuilder import get_recommendation
from .getsummoner import get_summoner
import time, re

OFFSET_EPOCH_WEEK_TO_SUNDAY = 345600
EPOCH_TIME_COUNTERS = {'Year': 31557600, '30 Day Period': 2592000, 'Week': 604800, 'Day': 86400}
CUTOFF_CS_PER_MIN = 2

def home(request):
    # redirects to summoner page if summoner in get request
    if request.method == "GET" and 'summoner' in request.GET:
        return HttpResponseRedirect('summoner/' + request.GET['summoner'])
    template_name = 'summonerstats/home.html'
    return render(request, 'summonerstats/home.html', {})

def about(request):
    return render(request, 'summonerstats/about.html', {})

def championselect(request):
    context = {}
    if request.method == "GET":
        ally_champions = {}
        enemy_champions = {}
        # add champions to team dictionaries
        for player_identifier, champion in request.GET.items():
            if champion != '':
                if re.match('ally', player_identifier):
                    ally_champions[player_identifier] = champion
                elif re.match('enemy', player_identifier):
                    enemy_champions[player_identifier] = champion
        # add respective dictionaries to context
        context.update(ally_champions)
        context.update(enemy_champions)
        if 'role' in request.GET:
            context['role'] = request.GET['role']
            context['champion_select_summoner'] = request.GET['champion_select_summoner'].title()
            summoner_list = Summoner.objects.filter(summoner_name=request.GET['champion_select_summoner'].lower())
            # make sure summoner exists in database
            if len(summoner_list) > 0:
                summoner = summoner_list[0]
                # run get_recommendation function from file
                recommended_champion = get_recommendation(summoner.summoner_id, [x for x in ally_champions.values()], [x for x in enemy_champions.values()], context['role'])
                if recommended_champion == 'insufficientdata':
                    messages.error(request, 'This summoner has not played enough games as this role.')
                elif recommended_champion == 'champerror':
                    messages.error(request, 'An invalid champion name was entered.')
                else:
                    context['recommended_champion'] = recommended_champion.title()
                    # the following code gets the stats for a particular champion
                    matches = summoner.junction_set.filter(champion=recommended_champion)
                    num_matches = len(matches)
                    context['matches_played'] = num_matches
                    wins, kills, deaths, assists = 0.0, 0.0, 0.0, 0.0
                    for match in matches:
                        wins += match.winner
                        kills += match.kills
                        deaths += match.deaths
                        assists += match.assists
                    context['winrate'] ='{:.2f}'.format(100 * wins / max(1,num_matches)) + '%'
                    context['kda'] = (kills + assists) / max(1, deaths)
            else:
                messages.error(request, 'Not a valid summoner, or not currently in our database.')
    return render(request, 'summonerstats/championselect.html', context)

def summonernotfound(request, summoner_name):
    # if user has requested to pull data
    if request.method == 'GET' and 'getsummoner' in request.GET:
        # pulls the data for a summoner, returns a list if found or an
        # error message otherwise
        error_message = get_summoner(summoner_name)
        if type(error_message) != list:
            messages.error(request, error_message)
        return HttpResponseRedirect('/summoner/' + summoner_name)
    context = {}
    context['summoner_name'] = summoner_name.title()
    return render(request, 'summonerstats/summonernotfound.html', context)

def stats(request, summoner_name):
    if request.method == "GET":
        # if user has requested to pull data
        if 'getsummoner' in request.GET:
            # pulls the data for a summoner, returns a list if found or an
            # error message otherwise
            error_message = get_summoner(summoner_name)
            if type(error_message) != list:
                messages.error(request, error_message)
            return HttpResponseRedirect('/summoner/' + summoner_name)
        # if the user has input a summoner name into the search box
        if 'summoner' in request.GET:
            return HttpResponseRedirect('/summoner/' + request.GET['summoner'])
    context = {}
    try:
        summoner = Summoner.objects.filter(summoner_name=summoner_name.lower())[0]
    except:
        # if summoner is not found, redirect to summoner not found view
        return HttpResponseRedirect('/summonernotfound/' + summoner_name)
    else:
        context['summoner'] = summoner
        context['summoner_name'] = summoner.summoner_name.title()
        if request.method == "GET":
            # if there is a time interval specified, charts are to be displayed
            if 'interval' in request.GET:
                context['chart'] = True
                time_interval = request.GET['interval']
                context['role'] = request.GET['role']
                if request.GET['role'] == 'Top':
                    role = "SOLO"
                    lane = "TOP"
                elif request.GET['role'] == 'Jungle':
                    role = "NONE"
                    lane = "JUNGLE"
                elif request.GET['role'] == 'Mid':
                    role = "SOLO"
                    lane = "MID"
                elif request.GET['role'] == 'AD Carry':
                    role = "DUO_CARRY"
                    lane = "BOTTOM"
                elif request.GET['role'] == 'Support':
                    role = "DUO_SUPPORT"
                    lane = "BOTTOM"
                if request.GET['chartsize'] == 'large':
                    context['large'] = True

                # the following if/else block gets the minimum number of games
                # filter option specified by the user
                if request.GET['mingames'] == '':
                    min_games = 1
                else:
                    try:
                        min_games = int(request.GET['mingames'])
                    except ValueError:
                        messages.error(request, 'Not a valid integer.')
                        return HttpResponseRedirect('/summoner/' + summoner_name)

                matches = summoner.junction_set.all().order_by('match__time_stamp')

                # time of first ever match played
                time_start = matches[0].match.time_stamp
                # time of last ever match played
                time_end = matches[len(matches)-1].match.time_stamp

                # get the time categories for each
                time_start_category = get_epoch_time_category(time_start, time_interval)
                time_end_category = get_epoch_time_category(time_end, time_interval)

                # get the total number of time stamps (really time categories)
                num_time_stamps = get_num_time_stamps(time_interval, time_start, time_end)

                # list of values for each time category/stamp
                matches_played = [0] * num_time_stamps
                winrate_values = [0] * num_time_stamps
                damage_to_champions_per_min_values = [0] * num_time_stamps
                kill_values = [0] * num_time_stamps
                death_values = [0] * num_time_stamps
                assist_values = [0] * num_time_stamps
                kda_values = [0] * num_time_stamps
                cs_values = [0] * num_time_stamps
                gold_values = [0] * num_time_stamps
                cs_per_min_values = [0] * num_time_stamps
                gold_per_min_values = [0] * num_time_stamps
                wards_placed_values = [0] * num_time_stamps
                wards_killed_values = [0] * num_time_stamps
                # include all games if all roles selected
                if context['role'] == 'All':
                    for summoner_match in matches:
                        match_duration = summoner_match.match.match_duration/60.0
                        time_stamp = summoner_match.match.time_stamp
                        time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                        index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                        matches_played[index] += 1
                        winrate_values[index] = update_average(winrate_values, summoner_match.winner, index, summoner_match, matches_played)
                        damage_to_champions_per_min_values[index] = update_average(damage_to_champions_per_min_values, summoner_match.total_damage_dealt_champions_min/match_duration, index, summoner_match, matches_played)
                        kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, matches_played)
                        death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, matches_played)
                        assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, matches_played)
                        kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, matches_played)
                        cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, matches_played)
                        gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, matches_played)
                        cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, matches_played)
                        gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, matches_played)
                        wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, matches_played)
                        wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, matches_played)
                # otherwise if not all roles selected
                else:
                    for summoner_match in matches:
                        # if the role and lane recorded in the game match
                        # input of the user, count the match; otherwise don't
                        if summoner_match.role == role and summoner_match.lane == lane:
                            match_duration = summoner_match.match.match_duration/60.0
                            time_stamp = summoner_match.match.time_stamp
                            time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                            index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                            matches_played[index] += 1
                            winrate_values[index] = update_average(winrate_values, summoner_match.winner, index, summoner_match, matches_played)
                            damage_to_champions_per_min_values[index] = update_average(damage_to_champions_per_min_values, summoner_match.total_damage_dealt_champions_min/match_duration, index, summoner_match, matches_played)
                            kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, matches_played)
                            death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, matches_played)
                            assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, matches_played)
                            kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, matches_played)
                            cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, matches_played)
                            gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, matches_played)
                            cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, matches_played)
                            gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, matches_played)
                            wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, matches_played)
                            wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, matches_played)
                        # now there are some games where role is not fully
                        # specified because it is uncertain whether the player
                        # is a carry or support since they share a lane
                        # on average, most carries had more than 2 CS per min
                        # (just a statistic), so we will be categorizing based
                        # on that knowledge
                        elif summoner_match.role == 'DUO' and lane == 'BOTTOM':
                            if summoner_match.cs/match_duration > CUTOFF_CS_PER_MIN and role == 'DUO_CARRY':
                                match_duration = summoner_match.match.match_duration/60.0
                                time_stamp = summoner_match.match.time_stamp
                                time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                                index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                                matches_played[index] += 1
                                winrate_values[index] = update_average(winrate_values, summoner_match.winner, index, summoner_match, matches_played)
                                damage_to_champions_per_min_values[index] = update_average(damage_to_champions_per_min_values, summoner_match.total_damage_dealt_champions_min/match_duration, index, summoner_match, matches_played)
                                kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, matches_played)
                                death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, matches_played)
                                assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, matches_played)
                                kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, matches_played)
                                cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, matches_played)
                                gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, matches_played)
                                cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, matches_played)
                                gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, matches_played)
                                wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, matches_played)
                                wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, matches_played)
                            elif summoner_match.cs/match_duration <= CUTOFF_CS_PER_MIN and role == 'DUO_SUPPORT':
                                match_duration = summoner_match.match.match_duration/60.0
                                time_stamp = summoner_match.match.time_stamp
                                time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                                index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                                matches_played[index] += 1
                                winrate_values[index] = update_average(winrate_values, summoner_match.winner, index, summoner_match, matches_played)
                                damage_to_champions_per_min_values[index] = update_average(damage_to_champions_per_min_values, summoner_match.total_damage_dealt_champions_min/match_duration, index, summoner_match, matches_played)
                                kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, matches_played)
                                death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, matches_played)
                                assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, matches_played)
                                kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, matches_played)
                                cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, matches_played)
                                gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, matches_played)
                                cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, matches_played)
                                gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, matches_played)
                                wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, matches_played)
                                wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, matches_played)
                # add everything to context
                context['min_games'] = min_games
                context['matches_played'] = matches_played
                context['winrate_values'] = winrate_values
                context['damage_to_champions_per_min_values'] = damage_to_champions_per_min_values
                context['kill_values'] = kill_values
                context['death_values'] = death_values
                context['assist_values'] = assist_values
                context['kda_values'] = kda_values
                context['cs_values'] = cs_values
                context['gold_values'] = gold_values
                context['cs_per_min_values'] = cs_per_min_values
                context['gold_per_min_values'] = gold_per_min_values
                context['wards_placed_values'] = wards_placed_values
                context['wards_killed_values'] = wards_killed_values
                context['time_interval'] = EPOCH_TIME_COUNTERS[time_interval]*1000
                context['time_interval_name'] = time_interval
                # convert and add the starting time to context, because it's
                # necessary to graph time/date on highcharts
                if time_interval == 'Year':
                    context['time_start'] = [time_start_category, 1, 1]
                elif time_interval == '30 Day Period':
                    y = time_start_category / 12
                    m = time_start_category % 12
                    context['time_start'] = [y, m, 1]
                else:
                    context['time_start'] = get_UTC_time(time_start_category)
    return render(request, 'summonerstats/stats.html', context)

'''The following are auxillary functions.'''

def get_UTC_time(epoch_time):
    '''
    Returns the year, month, and day of a certain epoch time.
    '''
    return list(time.gmtime(epoch_time)[:3])

def get_epoch_time_category(epoch_time, time_interval):
    '''
    Returns the time index ('category') that the epoch time should be in.
    In other words, it returns the number of time intervals that have passed
    since either time 0 OR epoch time 0 (January 1, 1970)
    '''
    if time_interval == 'Year':
        # returns the year, RELATIVE TO YEAR 0
        category = time.gmtime(epoch_time)[0]
    elif time_interval == '30 Day Period':
        # returns the total number of months (including years as 12 months)
        # RELATIVE TO YEAR 0, MONTH 0 (1)
        category = time.gmtime(epoch_time)[0] * 12 + time.gmtime(epoch_time)[1]
    elif time_interval == 'Week':
        # returns the epoch time for the Sunday of a given week (EPOCH RELATIVE)

        # the following gets the epoch time of the most recent Thursday, then
        # subtracts time to make it Sunday
        category = epoch_time // EPOCH_TIME_COUNTERS[time_interval] * EPOCH_TIME_COUNTERS[time_interval] - OFFSET_EPOCH_WEEK_TO_SUNDAY
        # if doing the above on Sunday, Monday, Tuesday, or Wednesday,
        # the category will be a week too far back (ex. Sunday the 21st instead
        # of the 28th when the epoch_time is the 30th)
        if epoch_time % EPOCH_TIME_COUNTERS[time_interval] >= OFFSET_EPOCH_WEEK_TO_SUNDAY:
            # add one week to rectify the calculation error
            category += EPOCH_TIME_COUNTERS[time_interval]
    elif time_interval == 'Day':
        # returns the total number of days since epoch time = 0 (EPOCH RELATIVE)
        category = epoch_time // EPOCH_TIME_COUNTERS[time_interval] * EPOCH_TIME_COUNTERS[time_interval]
    return category

def update_average(values, stat, index, summoner_match, matches_played):
    '''
    Returns averages in place instead of iterating through another
    for loop to divide all of the totals and get the average
    '''
    return values[index] * (1 - 1/float(matches_played[index])) + stat / float(matches_played[index])

def get_relative_epoch_time_category(epoch_time_category, start_time_category, time_interval):
    '''
    Returns the epoch time category relative to another one.
    E.g., if the epoch time category is 7 and start time category 2,
    the relative time category is 5
    '''
    if time_interval == 'Year' or time_interval == '30 Day Period':
        return epoch_time_category - start_time_category
    elif time_interval == 'Week' or time_interval == 'Day':
        return int((epoch_time_category - start_time_category) / EPOCH_TIME_COUNTERS[time_interval])

def get_num_time_stamps(time_interval, time_start, time_end):
    '''
    Returns the number of time stamps between the starting and ending times
    based on the time interval
    '''
    if time_interval == 'Year':
        num_time_stamps = time.gmtime(time_end)[0] - time.gmtime(time_start)[0] + 1
    elif time_interval == '30 Day Period':
        gmtime_start = time.gmtime(time_start)
        gmtime_end = time.gmtime(time_end)
        num_time_stamps = 12 * (gmtime_end[0] - gmtime_start[0]) + (gmtime_end[1] - gmtime_start[1]) + 1
    elif time_interval == 'Week' or time_interval == 'Day':
        time_start = get_epoch_time_category(time_start, time_interval)
        time_end = get_epoch_time_category(time_end, time_interval)
        num_time_stamps = int(round( ((time_end - time_start) / EPOCH_TIME_COUNTERS[time_interval]) + 1 ))
    return num_time_stamps
