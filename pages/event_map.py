import os
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
API_KEY = st.secrets["api_key"]

__RELEASE = True
root_dir = os.path.dirname(os.path.abspath(__file__))

if __RELEASE:    
    build_dir = os.path.join(root_dir, "../components/map_component/frontend/build" )

    _map_component = components.declare_component(
        "map-component",
        path=build_dir
    )
else: 
    _map_component = components.declare_component(
        "map-component",
        url="http://localhost:3001"
    )


# get player id
def getPlayerId(data, puuid):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["puuid"]}' == puuid) and "participantId" in player:
            return(player["participantId"])
    return("No Player Found")


# get champ for participantId
def get_player_champ(data, participantId):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["participantId"]}' == str(participantId)) and "championName" in player:
            return(player["championName"])
    return("No Player Found")


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
            timeline_data_result.append((match_timeline_data, match_data))
    
    return timeline_data_result


# get kill locations
def getKillLocations(timeline_data, match_data, selected, what, puuid):
    killData = []
    frames = timeline_data["info"]["frames"]
    userId = getPlayerId(timeline_data, puuid)
    for frame in frames:
        events = frame["events"]
        for event in events:
            if event["type"] == "CHAMPION_KILL":
                killerId = int(event["killerId"])
                victimId = int(event["victimId"])
                killerChamp = get_player_champ(match_data, killerId)
                victimChamp = get_player_champ(match_data, victimId)
                assistingParticipantIds = event.get("assistingParticipantIds")
                assistantChamps = []
                if (assistingParticipantIds != None):
                    for id in assistingParticipantIds:
                        assistantChamps += [get_player_champ(match_data, id)]
                position = event["position"]
                victimX = position["x"]
                victimY = position["y"]
                if (selected):
                    if (killerId == userId):
                        if (what == "kill"):
                            killData += [[str(round(int(event["timestamp"]) / 60000, 2)), killerChamp, victimChamp, victimX, victimY, assistantChamps]]
                    if (victimId == userId):
                        if (what == "death"):
                            killData += [[str(round(int(event["timestamp"]) / 60000, 2)), killerChamp, victimChamp, victimX, victimY, assistantChamps]]
                    if (assistingParticipantIds != None and userId in assistingParticipantIds):
                        if (what == "assist"):
                            killData += [[str(round(int(event["timestamp"]) / 60000, 2)), killerChamp, victimChamp, victimX, victimY, assistantChamps]]
                else:   
                    killData += [[str(round(int(event["timestamp"]) / 60000, 2)), killerChamp, victimChamp, victimX, victimY, assistantChamps]]
                
    return killData


# get dragon locations
def getDragonKills(timeline_data, match_data):
    dragonData = []
    frames = timeline_data["info"]["frames"]
    for frame in frames:
        events = frame["events"]
        for event in events:
            if event.get("monsterType") == "DRAGON":
                dragonType = str(event["monsterSubType"])
                killerId = event["killerId"]
                killerChamp = get_player_champ(match_data, killerId)
                position = event["position"]
                x = position["x"]
                y = position["y"]
                assistingParticipantIds = event.get("assistingParticipantIds")
                assistantChamps = []
                if (assistingParticipantIds != None):
                    for id in assistingParticipantIds:
                        assistantChamps += [get_player_champ(match_data, id)]
                dragonData = [[str(round(int(event["timestamp"]) / 60000, 2)), dragonType, killerChamp, str(x), str(y), assistantChamps]]
    
    return dragonData


# get Herald locations
def getHeraldKills(timeline_data, match_data):
    heraldData = []
    frames = timeline_data["info"]["frames"]
    for frame in frames:
        events = frame["events"]
        for event in events:
            if event.get("monsterType") == "RIFTHERALD":
                herald = str(event["monsterType"])
                killerId = event["killerId"]
                killerChamp = get_player_champ(match_data, killerId)
                position = event["position"]
                x = position["x"]
                y = position["y"]
                heraldData = [[str(round(int(event["timestamp"]) / 60000, 2)), herald, killerChamp, str(x), str(y)]]
    
    return heraldData


# get Baron locations
def getBaronKills(timeline_data, match_data):
    baronData = []
    frames = timeline_data["info"]["frames"]
    for frame in frames:
        events = frame["events"]
        for event in events:
            if event.get("monsterType") == "BARON_NASHOR":
                baron = str(event["monsterType"])
                killerId = event["killerId"]
                killerChamp = get_player_champ(match_data, killerId)
                position = event["position"]
                x = position["x"]
                y = position["y"]
                assistingParticipantIds = event["assistingParticipantIds"]
                assistantChamps = []
                if (assistingParticipantIds != None):
                    for id in assistingParticipantIds:
                        assistantChamps += [get_player_champ(match_data, id)]
                baronData = [[str(round(int(event["timestamp"]) / 60000, 2)), baron, killerChamp, str(x), str(y), assistantChamps]]
    
    return baronData

def getBuildingKills(timeline_data, match_data, selected, puuid):
    buildingData = []
    frames = timeline_data["info"]["frames"]
    userId = getPlayerId(match_data, puuid)
    for frame in frames:
        events = frame["events"]
        for event in events:
            if event.get("type") == "BUILDING_KILL":
                buildingType = str(event["buildingType"])
                lane = str(event["laneType"])
                if (lane == ''):
                    lane = "NEXUS_TURRET"
                killerId = event["killerId"]
                killerChamp = get_player_champ(match_data, killerId)
                teamId = event["teamId"]
                towerType = event.get("towerType")
                bounty = event["bounty"]
                position = event["position"]
                x = position["x"]
                y = position["y"]
                if (selected):
                    if (killerId == userId):
                        buildingData += [[str(round(int(event["timestamp"]) / 60000, 2)), buildingType, lane, towerType, x, y, bounty, killerChamp, teamId]]
                else:           
                    buildingData += [[str(round(int(event["timestamp"]) / 60000, 2)), buildingType, lane, towerType, x, y, bounty, killerId, teamId]]
    
    return buildingData


default_tr_low = 10
default_tr_high = 25

col1, col2, col3 = st.columns([1, 3.5, 1])
if 'puuid' in st.session_state:
    amount_games = 10
    timeline_data = load_data(st.session_state['puuid'], st.session_state['continent'], st.session_state['ranked_only'], amount_games)

    x_vals = []
    y_vals = []

    event_time = []
    event_type = []

    killer_champ = []
    victim_champ = []
    assist_champs = []
    game_index = []
    index = 0
    for timeline_champ_tuple in timeline_data:
        # kills
        kill_locations = getKillLocations(timeline_champ_tuple[0], timeline_champ_tuple[1], True, "kill", st.session_state['puuid'])
        x_kill_vals = [item[3] for item in kill_locations]
        y_kill_vals = [item[4] for item in kill_locations]

        event_kill_time = [item[0] for item in kill_locations]
        event_kill_type = ["Kills"] * len(x_kill_vals)

        killer_champ_kill = [item[1] for item in kill_locations]
        victim_champ_kill = [item[2] for item in kill_locations]
        assist_champs_kill = [item[5] for item in kill_locations]

        # deaths
        death_locations = getKillLocations(timeline_champ_tuple[0], timeline_champ_tuple[1], True, "death", st.session_state['puuid'])
        x_death_vals = [item[3] for item in death_locations]
        y_death_vals = [item[4] for item in death_locations]

        event_death_time = [item[0] for item in death_locations]
        event_death_type = ["Deaths"] * len(x_death_vals)

        killer_champ_death = [item[1] for item in death_locations]
        victim_champ_death = [item[2] for item in death_locations]
        assist_champs_death = [item[5] for item in death_locations]

        # assists
        assist_locations = getKillLocations(timeline_champ_tuple[0], timeline_champ_tuple[1], True, "assist", st.session_state['puuid'])
        x_assist_vals = [item[3] for item in assist_locations]
        y_assist_vals = [item[4] for item in assist_locations]

        event_assist_time = [item[0] for item in assist_locations]
        event_assist_type = ["Assists"] * len(x_assist_vals)

        killer_champ_assist = [item[1] for item in assist_locations]
        victim_champ_assist = [item[2] for item in assist_locations]
        assist_champs_assist = [item[5] for item in assist_locations]

        # dragons
        dragon_locations = getDragonKills(timeline_champ_tuple[0], timeline_champ_tuple[1])

        x_drag_vals = [item[3] for item in dragon_locations]
        y_drag_vals = [item[4] for item in dragon_locations]

        event_drag_time = [item[0] for item in dragon_locations]
        event_drag_type = ["Dragons"] * len(x_drag_vals)

        killer_champ_drag = [item[2] for item in dragon_locations]
        victim_champ_drag = [item[2] for item in dragon_locations]
        assist_champs_drag = [item[5] for item in dragon_locations]

        # herald
        herald_locations = getHeraldKills(timeline_champ_tuple[0], timeline_champ_tuple[1])

        x_herald_vals = [item[3] for item in herald_locations]
        y_herald_vals = [item[4] for item in herald_locations]

        event_herald_time = [item[0] for item in herald_locations]
        event_herald_type = ["Heralds"] * len(x_herald_vals)

        killer_champ_herald = [item[2] for item in herald_locations]
        victim_champ_herald = [item[2] for item in herald_locations]
        assist_champ_herald = [item[2] for item in herald_locations]

        # baron
        baron_locations = getBaronKills(timeline_champ_tuple[0], timeline_champ_tuple[1])

        x_baron_vals = [item[3] for item in baron_locations]
        y_baron_vals = [item[4] for item in baron_locations]

        event_baron_time = [item[0] for item in baron_locations]
        event_baron_type = ["Barons"] * len(x_baron_vals)

        killer_champ_baron = [item[2] for item in baron_locations]
        victim_champ_baron = [item[2] for item in baron_locations]
        assist_champ_baron = [item[5] for item in baron_locations]

        # buildings
        building_locations = getBuildingKills(timeline_champ_tuple[0], timeline_champ_tuple[1], True, st.session_state['puuid'])

        x_building_vals = [item[4] for item in building_locations]
        y_building_vals = [item[5] for item in building_locations]

        event_building_time = [item[0] for item in building_locations]
        event_building_type = ["Buildings"] * len(x_building_vals)

        killer_champ_building = [item[7] for item in building_locations]
        victim_champ_building = [item[7] for item in building_locations]
        assist_champ_building = [item[7] for item in building_locations]

        # append all to list
        x_vals += x_kill_vals + x_death_vals + x_assist_vals + x_drag_vals + x_herald_vals + x_baron_vals + x_building_vals
        y_vals += y_kill_vals + y_death_vals + y_assist_vals + y_drag_vals + y_herald_vals + y_baron_vals + y_building_vals

        event_time += event_kill_time + event_death_time + event_assist_time + event_drag_time + event_herald_time + event_baron_time + event_building_time
        event_type += event_kill_type + event_death_type + event_assist_type + event_drag_type + event_herald_type + event_baron_type + event_building_type

        killer_champ += killer_champ_kill + killer_champ_death + killer_champ_assist + killer_champ_drag + killer_champ_herald + killer_champ_baron + killer_champ_building
        victim_champ += victim_champ_kill + victim_champ_death + victim_champ_assist + victim_champ_drag + victim_champ_herald + victim_champ_baron + victim_champ_building
        assist_champs += assist_champs_kill + assist_champs_death + assist_champs_assist + assist_champs_drag + assist_champ_herald + assist_champ_baron + assist_champ_building
        temp_game_index = [index] * (len(x_vals) - len(game_index))
        
        game_index += temp_game_index
        
        index += 1
        
    if not timeline_data:
        if st.session_state['ranked_only']:
            with col2:
                st.write("Could not find any ranked games in your recent match history")
        else:
            with col2:
                st.write("Could not find any summoners rift games in your recent match history")

    else:
        with st.sidebar:
            game1 = st.checkbox("Show game 1 data 🟧", value=True)
            game2 = st.checkbox("Show game 2 data 🔶", value=True)
            game3 = st.checkbox("Show game 3 data 🟠", value=True)
            game4 = st.checkbox("Show game 4 data 🥚", value=False)
            game5 = st.checkbox("Show game 5 data ⚠️", value=False)
            game_array = [game1, game2, game3, game4, game5]

        with col2:
            events = st.multiselect("Select type of event to display", ["Kills 🔵", "Deaths 🔴", "Assists 🟢", "Dragons 🟡", "Heralds 🟤", "Barons 🟣", "Buildings ⚪"], ["Kills 🔵", "Deaths 🔴", "Dragons 🟡"])
            map_events = [event[:-2] for event in events]
            container = st.container()
            time_range = st.slider('Select event time frame', 0, 60, (default_tr_low, default_tr_high))
            with container:
                _map_component(x_coords=x_vals, y_coords=y_vals, killer_champ=killer_champ, victim_champ=victim_champ, assist_champs=assist_champs, event_type=event_type, events=map_events, event_time=event_time, time_range=time_range, game_index=game_index, game_array=game_array, key="foo")

else:
    st.write("please enter your username on the login screen")