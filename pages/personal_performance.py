import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
import requests
import json
import os
st.set_page_config(layout="wide")

API_KEY = st.secrets["api_key"]

__RELEASE = True
root_dir = os.path.dirname(os.path.abspath(__file__))

if __RELEASE:
    
    build_dir = os.path.join(root_dir, "../components/chart_component/frontend/build" )

    _chart_component = components.declare_component(
        "chart-component",
        path=build_dir
    )
else: 
    _chart_component = components.declare_component(
        "chart-component",
        url="http://localhost:3001"
    )

# Retrieve Data
@st.cache_data
def load_data(puuid, continent, ranked, amount_games):
    timeline_data_result = []
    if ranked:
        match_history_url = f"https://{continent}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime=1650000000&queueId=420&start=0&count={amount_games}&api_key={API_KEY}"
    else:
        match_history_url = f"https://{continent}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime=1650000000&start=0&count={amount_games}&api_key={API_KEY}"
    match_history_res = requests.get(match_history_url)

    match_history_data = match_history_res.json()

    # loop through matches
    for match in match_history_data:
        match_timeline_url = f"https://{continent}.api.riotgames.com/lol/match/v5/matches/{match}/timeline?api_key={API_KEY}"
        match_timeline_res = requests.get(match_timeline_url)
        match_timeline_data = match_timeline_res.json()
        
        match_url = f"https://{continent}.api.riotgames.com/lol/match/v5/matches/{match}?api_key={API_KEY}"
        match_res = requests.get(match_url)
        match_data = match_res.json()
        if not match_data:
            return []

        if "info" in match_data:
            match_id = match_data["info"]["queueId"]
        if match_id >= 400 and match_id <= 440:
            champion_name = get_player_champ(match_data, st.session_state['puuid'])
            timeline_data_result.append((match_timeline_data, champion_name, match_data))
    
    return timeline_data_result


gold_data = []
minions_data = []
ward_data = []


def get_total_gold_graph(data, champ, gamenumber, uid):
    frames = data["info"]["frames"]
    index = 0
    for frame in frames:
        participantFrame = frame["participantFrames"][str(uid)]
        statdict = {"totalGold": participantFrame["totalGold"], "timestamp": index, "game": champ + ' ' + str(gamenumber), "participant": uid}
        gold_data.append(statdict)
        index += 1


def get_total_cs_graph(data, champ, gamenumber, uid):
    frames = data["info"]["frames"]
    index = 0
    for frame in frames:
        participantFrame = frame["participantFrames"][str(uid)]
        statdict = {"totalMinions": participantFrame["minionsKilled"], "timestamp": index, "game": champ + ' ' + str(gamenumber), "participant": uid}
        minions_data.append(statdict)
        index += 1


def get_total_wards_cleared_graph(data, champ, gamenumber, uid):
    frames = data["info"]["frames"]
    index = 0
    ward_count = 0
    for frame in frames:
        events = frame["events"]
        for event in events:
            if f'{event["type"]}' == "WARD_KILL" and f'{event["killerId"]}' == str(uid):
                ward_count += 1
        statdict = {"totalWardsCleared": ward_count, "timestamp": index, "game": champ + ' ' + str(gamenumber), "participant": uid}
        ward_data.append(statdict)
        index += 1

def get_info_from_match_data(match_data, information):
    if information in match_data:
        return(match_data[information])
    return(0)

def get_challenge_from_match_data(match_data, information):
    if information in match_data["challenges"]:
        return(match_data["challenges"][information])
    return(0)


def get_total_gold_chart(data, participantId, subChartName):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["participantId"]}' == str(participantId)):
            totalGoldEarned = get_info_from_match_data(player, "goldEarned")
            goldPerMinute = get_challenge_from_match_data(player, "goldPerMinute")   
            matchLength = int(totalGoldEarned / goldPerMinute)
            passiveGold = (matchLength - 2) * 120 + 500
            inhibitorGold = get_info_from_match_data(player, "inhibitorKills") * 50
            nexusGold = get_info_from_match_data(player, "nexusKills") * 50
            turretGold = get_info_from_match_data(player, "turretTakedowns") * 125 + get_info_from_match_data(player, "turretKills") * 60
            platingGold = get_challenge_from_match_data(player, "turretPlatesTaken")  * 175
            earlyMinionGold = get_challenge_from_match_data(player, "laneMinionsFirst10Minutes") * 20   
            midLateMinionGold = (get_info_from_match_data(player, "totalMinionsKilled") - get_challenge_from_match_data(player, "laneMinionsFirst10Minutes")) * 26
            jungleCampGold = get_info_from_match_data(player, "neutralMinionsKilled") * 30
            dragonGold = get_info_from_match_data(player, "dragonKills") * 25 + get_challenge_from_match_data(player, "teamElderDragonKills") * 250
            baronGold = get_challenge_from_match_data(player, "teamBaronKills") * 300
            riftHeraldGold = get_challenge_from_match_data(player, "riftHeraldTakedowns") * 250
            assistGold = get_info_from_match_data(player, "assists") * 100
            killGold = get_info_from_match_data(player, "kills") * 300
            bountyGold = get_challenge_from_match_data(player, "bountyGold") 

            structureDict = {"name": "structures", "children": [
                {"name": "inhibitors", "value": inhibitorGold},
                {"name": "nexus", "value": nexusGold},
                {"name": "turrets", "value": turretGold},
                {"name": "platings", "value": platingGold}
            ]}

            minionsDict = {"name": "minions", "children": [
                {"name": "0 - 10 mins", "value": earlyMinionGold},
                {"name": "10+ mins", "value": midLateMinionGold}
            ]}

            monsterDict = {"name": "monsters", "children": [
                {"name": "jungle camps", "value": jungleCampGold},
                {"name": "dragons", "value": dragonGold},
                {"name": "barons", "value": baronGold},
                {"name": "rift heralds", "value": riftHeraldGold}
            ]}

            takedownDict = {"name": "takedowns", "children": [
                {"name": "assists", "value": assistGold},
                {"name": "kills", "value": killGold},
                {"name": "bounties", "value": bountyGold}
            ]}

            fullGoldDict = {"name": subChartName, "children": [
                { "name": "passive", "value": passiveGold},
                structureDict,
                minionsDict,
                monsterDict,
                takedownDict
            ]}

            return fullGoldDict
    return {}


def get_total_damage_chart(data, participantId, subChartName):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["participantId"]}' == str(participantId)):
            totalPhysicalDamageDealt = get_info_from_match_data(player, "physicalDamageDealtToChampions")
            totalMagicDamageDealt = get_info_from_match_data(player, "magicDamageDealtToChampions")
            totalTrueDamageDealt = get_info_from_match_data(player, "trueDamageDealtToChampions")

            fullDamageDict = {"name": subChartName, "children": [
                { "name": "Physical Damage", "value": totalPhysicalDamageDealt},
                { "name": "Magic Damage", "value": totalMagicDamageDealt},
                { "name": "True Damage", "value": totalTrueDamageDealt}
            ]}

            return fullDamageDict
    return {}


def get_total_vision_chart(data, participantId, subChartName):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["participantId"]}' == str(participantId)):
            totalWardsPlaced = get_info_from_match_data(player, "wardsPlaced")
            controlWardsPlaced = get_challenge_from_match_data(player, "controlWardsPlaced")
            stealthWardsPlaced = get_challenge_from_match_data(player, "stealthWardsPlaced")
            otherWardsPlaced = totalWardsPlaced - (controlWardsPlaced + stealthWardsPlaced)
            totalWardTakedowns = get_challenge_from_match_data(player, "wardTakedowns")
            totalWardsKilled = get_info_from_match_data(player, "wardsKilled")
            totalWardsAssisted = totalWardTakedowns - totalWardsKilled
            totalWardsGuarded = get_challenge_from_match_data(player, "wardsGuarded")

            wardPlacedDict = {"name": "Wards Placed", "children": [
                { "name": "Control Wards", "value": controlWardsPlaced},
                { "name": "Stealth Wards", "value": stealthWardsPlaced},
                { "name": "Other Wards", "value": otherWardsPlaced}
            ]}

            wardTakedownDict = {"name": "Ward Takedowns", "children": [
                { "name": "Wards Destroyed", "value": totalWardsKilled},
                { "name": "Wards Assisted", "value": totalWardsAssisted}
            ]}

            fullVisionDict = {"name": subChartName, "children": [
                { "name": "Wards Guarded", "value": totalWardsGuarded},
                wardPlacedDict,
                wardTakedownDict
            ]}

            return fullVisionDict
    return {}


def get_player_id(data, puuid):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["puuid"]}' == puuid):
            return(player["participantId"])
    return("No Player Found")


def get_player_champ(data, puuid):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["puuid"]}' == puuid):
            return(player["championName"])
    return("No Player Found")


def display_graph(data_type):
    match_index = 0
    for timeline_champ_tuple in timeline_data:
        match_index += 1
        player_id = get_player_id(timeline_champ_tuple[0], st.session_state['puuid'])
        if data_type == "Gold":
            get_total_gold_graph(timeline_champ_tuple[0], timeline_champ_tuple[1], match_index, player_id)
        elif data_type == "Minions":
            get_total_cs_graph(timeline_champ_tuple[0], timeline_champ_tuple[1], match_index, player_id)
        else:
            get_total_wards_cleared_graph(timeline_champ_tuple[0], timeline_champ_tuple[1], match_index, player_id)
    
    if data_type == "Gold":
        pd_df = pd.DataFrame(gold_data)
        chart_y = 'totalGold'
    elif data_type == "Minions":
        pd_df = pd.DataFrame(minions_data)
        chart_y = 'totalMinions'
    else:
        pd_df = pd.DataFrame(ward_data)
        chart_y = 'totalWardsCleared'
    
    if pd_df.empty:
        if st.session_state['ranked_only']:
            with graph_container:
                st.write("Could not find any ranked games in your recent match history.")
        else:
            with graph_container:
                st.write("Could not find any summoners rift games in your recent match history") 
        return

    g = alt.Chart(pd_df).mark_line().encode(
        x='timestamp',
        y=chart_y,
        color='game',
        strokeDash='game',
    )
    with graph_container:
        st.altair_chart(g, use_container_width=True) 


def display_chart(data_type):

    if not timeline_data:
        if st.session_state['ranked_only']:
            with chart_container:
                st.write("Could not find any ranked games in your recent match history")

        else:
            with chart_container:
                st.write("Could not find any summoners rift games in your recent match history")
        return

    match_index = 0
    chart_children = []
    for timeline_champ_tuple in timeline_data:
        match_index += 1
        player_id = get_player_id(timeline_champ_tuple[0], st.session_state['puuid'])
        subchart_name = timeline_champ_tuple[1] + ' ' + str(match_index)
        if data_type == "Gold":
            child_dict = get_total_gold_chart(timeline_champ_tuple[2], player_id, subchart_name)
        elif data_type == "Damage":
            child_dict = get_total_damage_chart(timeline_champ_tuple[2], player_id, subchart_name)
        else:
            child_dict = get_total_vision_chart(timeline_champ_tuple[2], player_id, subchart_name)
        chart_children.append(child_dict)
    chart_dict = {"name": "flare", "children": chart_children}
    chart_json = json.dumps(chart_dict)
    if data_type == "Gold":
        chart_colour="#C89B3C"
    elif data_type == "Damage":
        chart_colour="#0397AB"
    else:
        chart_colour="#0AC8B9"

    with chart_container:
        _chart_component(jsonData=json.loads(chart_json), chartColour=chart_colour, key="asdf")


if 'puuid' in st.session_state:
    tab1, tab2 = st.tabs(["Graph", "Chart"])
    with tab1:
        graph_value = st.radio("Choose which data to display", ['Gold', 'Minions', 'Wards Cleared'], horizontal=True)
        graph_container = st.container()

    with tab2:
        col1, col2 = st.columns([1, 2])
        with col1:
            chart_value = st.radio("Choose which data to display", ['Gold', 'Damage', 'Vision'], horizontal=True)
        with col2:
            st.write("Click a coloured bar to drill down, or click the background to go back up.")
        chart_container = st.container()
    
    amount_games = st.slider('Select amount of games', 1, 10, 5)
    timeline_data = load_data(st.session_state['puuid'], st.session_state['continent'], st.session_state['ranked_only'], amount_games)

    # graph
    if graph_value == 'Gold':
        display_graph('Gold')
    if graph_value == 'Minions':
        display_graph('Minions')
    if graph_value == 'Wards Cleared':
        display_graph('Wards Cleared')

    # chart
    if chart_value == 'Gold':
        display_chart('Gold')
    if chart_value == 'Damage':
        display_chart('Damage')
    if chart_value == 'Vision':
        display_chart('Vision')
    
else:
    st.write("please enter your username on the login screen")
