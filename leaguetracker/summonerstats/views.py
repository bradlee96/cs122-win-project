from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from .models import Summoner, Match, Junction
from datetime import date, datetime
from django.contrib import messages
from .teambuilder import get_recommendation
from .getsummoner import get_summoner
import time, re

OFFSET_EPOCH_WEEK_TO_SUNDAY = 345600
EPOCH_TIME_COUNTERS = {'Year': 31557600, '30 Day Period': 2592000, 'Week': 604800, 'Day': 86400}
CUTOFF_CS_PER_MIN = 2

def home(request):
    '''Remember to comment'''
    if request.method == "GET" and 'summoner' in request.GET:
        return HttpResponseRedirect('summoner/' + request.GET['summoner'])
    template_name = 'summonerstats/home.html'
    summoner_list = Summoner.objects.all()
    return render(request, 'summonerstats/home.html', {'summoner_list': summoner_list})

def about(request):
    '''Remember to comment'''
    return render(request, 'summonerstats/about.html', {})

def championselect(request):
    context = {}
    if request.method == "GET":
        ally_champions = {}
        enemy_champions = {}
        for player_identifier, champion in request.GET.items():
            if champion != '':
                if re.match('ally', player_identifier):
                    ally_champions[player_identifier] = champion
                elif re.match('enemy', player_identifier):
                    enemy_champions[player_identifier] = champion
        context.update(ally_champions)
        context.update(enemy_champions)
        if 'role' in request.GET:
            context['role'] = request.GET['role']
            context['champion_select_summoner'] = request.GET['champion_select_summoner']
            summoner_list = Summoner.objects.filter(summoner_name=request.GET['champion_select_summoner'].lower())
            if len(summoner_list) > 0:
                summoner = summoner_list[0]
                recommended_champion = get_recommendation(summoner.summoner_id, [x for x in ally_champions.values()], [x for x in enemy_champions.values()], context['role'])
                if recommended_champion != '':
                    context['recommended_champion'] = recommended_champion.capitalize()
                else:
                    messages.error(request, 'An invalid champion name was entered.')
            else:
                messages.error(request, 'Not a valid summoner, or not currently in our database.')
    return render(request, 'summonerstats/championselect.html', context)

def summonernotfound(request, summoner_name):
    if request.method == 'GET' and 'getsummoner' in request.GET:
        get_summoner(summoner_name)
        return HttpResponseRedirect('/summoner/' + summoner_name)
    context = {}
    context['summoner_name'] = summoner_name
    return render(request, 'summonerstats/summonernotfound.html', context)

def stats(request, summoner_name):
    '''Remember to comment'''
    if request.method == "GET" and 'summoner' in request.GET:
        return HttpResponseRedirect('/summoner/' + request.GET['summoner'])
    context = {}
    try:
        summoner = Summoner.objects.filter(summoner_name=summoner_name.lower())[0]
    except:
        return HttpResponseRedirect('/summonernotfound/' + summoner_name)
    else:
        context['summoner'] = summoner
        if request.method == "GET":
            if 'interval' in request.GET and 'chartsize' in request.GET and 'role' in request.GET:
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

                matches = summoner.junction_set.all().order_by('match__time_stamp')

                time_start = matches[0].match.time_stamp
                time_end = matches[len(matches)-1].match.time_stamp

                time_start_category = get_epoch_time_category(time_start, time_interval)
                time_end_category = get_epoch_time_category(time_end, time_interval)

                num_time_stamps = get_num_time_stamps(time_interval, time_start, time_end)

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
                average_counter = [0.0] * num_time_stamps
                if context['role'] == 'All':
                    for summoner_match in matches:
                        match_duration = summoner_match.match.match_duration/60.0
                        time_stamp = summoner_match.match.time_stamp
                        time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                        index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                        average_counter[index] += 1
                        kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, average_counter)
                        death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, average_counter)
                        assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, average_counter)
                        kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, average_counter)
                        cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, average_counter)
                        gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, average_counter)
                        cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, average_counter)
                        gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, average_counter)
                        wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, average_counter)
                        wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, average_counter)
                else:
                    for summoner_match in matches:
                        if summoner_match.role == role and summoner_match.lane == lane:
                            match_duration = summoner_match.match.match_duration/60.0
                            time_stamp = summoner_match.match.time_stamp
                            time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                            index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                            average_counter[index] += 1
                            kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, average_counter)
                            death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, average_counter)
                            assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, average_counter)
                            kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, average_counter)
                            cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, average_counter)
                            gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, average_counter)
                            cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, average_counter)
                            gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, average_counter)
                            wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, average_counter)
                            wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, average_counter)
                        elif summoner_match.role == 'DUO' and lane == 'BOTTOM':
                            if summoner_match.cs/match_duration > CUTOFF_CS_PER_MIN and role == 'DUO_CARRY':
                                match_duration = summoner_match.match.match_duration/60.0
                                time_stamp = summoner_match.match.time_stamp
                                time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                                index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                                average_counter[index] += 1
                                kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, average_counter)
                                death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, average_counter)
                                assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, average_counter)
                                kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, average_counter)
                                cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, average_counter)
                                gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, average_counter)
                                cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, average_counter)
                                gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, average_counter)
                                wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, average_counter)
                                wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, average_counter)
                            elif summoner_match.cs/match_duration <= CUTOFF_CS_PER_MIN and role == 'DUO_SUPPORT':
                                match_duration = summoner_match.match.match_duration/60.0
                                time_stamp = summoner_match.match.time_stamp
                                time_stamp_category = get_epoch_time_category(time_stamp, time_interval)
                                index = get_relative_epoch_time_category(time_stamp_category, time_start_category, time_interval)
                                average_counter[index] += 1
                                kill_values[index] = update_average(kill_values, summoner_match.kills, index, summoner_match, average_counter)
                                death_values[index] = update_average(death_values, summoner_match.deaths, index, summoner_match, average_counter)
                                assist_values[index] = update_average(assist_values, summoner_match.assists, index, summoner_match, average_counter)
                                kda_values[index] = update_average(kda_values, ((summoner_match.kills + summoner_match.assists)/max(1,summoner_match.deaths)), index, summoner_match, average_counter)
                                cs_values[index] = update_average(cs_values, summoner_match.cs, index, summoner_match, average_counter)
                                gold_values[index] = update_average(gold_values, summoner_match.gold, index, summoner_match, average_counter)
                                cs_per_min_values[index] = update_average(cs_per_min_values, summoner_match.cs/match_duration, index, summoner_match, average_counter)
                                gold_per_min_values[index] = update_average(gold_per_min_values, summoner_match.gold/match_duration, index, summoner_match, average_counter)
                                wards_placed_values[index] = update_average(wards_placed_values, summoner_match.wards_placed, index, summoner_match, average_counter)
                                wards_killed_values[index] = update_average(wards_killed_values, summoner_match.wards_killed, index, summoner_match, average_counter)
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
                if time_interval == 'Year':
                    context['time_start'] = [time_start_category, 1, 1]
                elif time_interval == '30 Day Period':
                    y = time_start_category / 12
                    m = time_start_category % 12
                    context['time_start'] = [y, m, 1]
                else:
                    context['time_start'] = get_UTC_time(time_start_category)
    return render(request, 'summonerstats/stats.html', context)

def get_UTC_time(epoch_time):
    return list(time.gmtime(epoch_time)[:3])

def get_epoch_time_category(epoch_time, time_interval):
    '''Remember to comment'''
    if time_interval == 'Year':
        category = time.gmtime(epoch_time)[0]
    elif time_interval == '30 Day Period':
        category = time.gmtime(epoch_time)[0] * 12 + time.gmtime(epoch_time)[1]
    elif time_interval == 'Week':
        category = epoch_time // EPOCH_TIME_COUNTERS[time_interval] * EPOCH_TIME_COUNTERS[time_interval] - OFFSET_EPOCH_WEEK_TO_SUNDAY
        if epoch_time % EPOCH_TIME_COUNTERS[time_interval] >= OFFSET_EPOCH_WEEK_TO_SUNDAY:
            category += EPOCH_TIME_COUNTERS[time_interval]
    elif time_interval == 'Day':
        category = epoch_time // EPOCH_TIME_COUNTERS[time_interval] * EPOCH_TIME_COUNTERS[time_interval]
    return category

def update_average(values, stat, index, summoner_match, average_counter):
    return values[index] * (1 - 1/average_counter[index]) + stat / average_counter[index]

def get_relative_epoch_time_category(epoch_time_category, start_time_category, time_interval):
    '''Remember to comment'''
    if time_interval == 'Year' or time_interval == '30 Day Period':
        return epoch_time_category - start_time_category
    elif time_interval == 'Week' or time_interval == 'Day':
        return int((epoch_time_category - start_time_category) / EPOCH_TIME_COUNTERS[time_interval])

def get_num_time_stamps(time_interval, time_start, time_end):
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
