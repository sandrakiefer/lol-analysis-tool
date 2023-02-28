import os
import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import json
from datetime import datetime
import streamlit_nested_layout
import requests

GAME_COUNT = 30
API_KEY = st.secrets["api_key"]

# ---------------------------------------------------------------------------- #
#                          Streamlit Grid Preparation                          #
# ---------------------------------------------------------------------------- #

def make_grid(cols, rows, gap=False):
    grid = [0]*cols
    for i in range(cols):
        with st.container():
            if gap:
                grid[i] = st.columns(rows, gap="medium")
            else:
                grid[i] = st.columns(rows)
    return grid

st.set_page_config(layout="wide")

header_grid = make_grid(3, [2, 4, 2])
header_grid[0][1].markdown("<h1 style='text-align: center;'>Overview Last Games</h1>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------- #
#                               Data preparation                               #
# ---------------------------------------------------------------------------- #

@st.cache_data
def load_data(puuid, region, queue_ids, api_key = API_KEY):
    # Get list of last game ids
    url_ids = f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={GAME_COUNT}&api_key={api_key}'
    game_ids = requests.get(url_ids).json()

    prepared_data = { "top": [], "middle": [], "jungle": [], "utility": [], "bottom": [] }

    # Get match data by game id 
    for match_id in game_ids:
        url_match = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}'
        match_data = requests.get(url_match).json()
        if match_data["info"]["queueId"] in queue_ids:
            for user in match_data["info"]["participants"]:
                if user["puuid"] == puuid:
                    match_info = {
                        "gameId": match_id,
                        "role": "middle" if user["teamPosition"] == "" else user["teamPosition"],
                        "champion": user["championName"],
                        "timestamp": match_data["info"]["gameStartTimestamp"],
                        "kills": user["kills"],
                        "deaths": user["deaths"],
                        "assists": user["assists"],
                        "gold": user["goldEarned"],
                        "minions": user["totalMinionsKilled"],
                        "damage_dealt": user["totalDamageDealt"],
                        "damage_taken": user["totalDamageTaken"],
                        "heal": user["totalHeal"],
                        "vision": user["visionScore"],
                        "champ_lvl": user["champLevel"],
                        "kda": round((user["kills"] + user["assists"]) / user["deaths"], 1) if user["deaths"] > 0 else 0,
                        "cs": user["totalMinionsKilled"] + user["neutralMinionsKilled"],
                        "surrender": user["gameEndedInSurrender"],
                        "result": user["win"]
                    }
            for user in match_data["info"]["participants"]:
                if (user["teamPosition"] == match_info["role"]) and (user["puuid"] != puuid) :
                    match_info["opponent"] = {
                        "kills": user["kills"],
                        "deaths": user["deaths"],
                        "assists": user["assists"],
                        "gold": user["goldEarned"],
                        "minions": user["totalMinionsKilled"],
                        "damage_dealt": user["totalDamageDealt"],
                        "damage_taken": user["totalDamageTaken"],
                        "heal": user["totalHeal"],
                        "vision": user["visionScore"],
                        "champ_lvl": user["champLevel"],
                        "kda": round((user["kills"] + user["assists"]) / user["deaths"], 1) if user["deaths"] > 0 else 0,
                        "cs": user["totalMinionsKilled"] + user["neutralMinionsKilled"]
                    }
            prepared_data[match_info["role"].lower()].append(match_info)

    average = { "top": {}, "middle": {}, "jungle": {}, "utility": {}, "bottom": {} }

    # Calculate average values for each role
    for role in prepared_data:
        if (len(prepared_data[role]) == 0):
            average[role] = { "kills": 0, "deaths": 0, "assists": 0, "gold": 0, "minions": 0, "damage_dealt": 0, "damage_taken": 0, "heal": 0, "vision": 0, "champ_lvl": 0 }
        else:
            average[role] = {
                "kills": sum(match["kills"] for match in prepared_data[role]) / len(prepared_data[role]),
                "deaths": sum(match["deaths"] for match in prepared_data[role]) / len(prepared_data[role]),
                "assists": sum(match["assists"] for match in prepared_data[role]) / len(prepared_data[role]),
                "gold": sum(match["gold"] for match in prepared_data[role]) / len(prepared_data[role]),
                "minions": sum(match["minions"] for match in prepared_data[role]) / len(prepared_data[role]),
                "damage_dealt": sum(match["damage_dealt"] for match in prepared_data[role]) / len(prepared_data[role]),
                "damage_taken": sum(match["damage_taken"] for match in prepared_data[role]) / len(prepared_data[role]),
                "heal": sum(match["heal"] for match in prepared_data[role]) / len(prepared_data[role]),
                "vision": sum(match["vision"] for match in prepared_data[role]) / len(prepared_data[role]),
                "champ_lvl": sum(match["champ_lvl"] for match in prepared_data[role]) / len(prepared_data[role]),
                "kda": sum(match["kda"] for match in prepared_data[role]) / len(prepared_data[role]),
                "cs": sum(match["cs"] for match in prepared_data[role]) / len(prepared_data[role]),
            }

    return prepared_data, average


with header_grid[2][1]:
    spinner_grid = make_grid(1, [1, 2, 1])
    if 'puuid' not in st.session_state:
        spinner_grid[0][1].markdown(f'<h5 style="text-align: center;">please enter your username on the login screen</h5>', unsafe_allow_html=True)
        st.stop()
    else:
        with spinner_grid[0][1]:
            prepared_data, average = load_data(st.session_state['puuid'], st.session_state['continent'], [420, 440] if st.session_state['ranked_only'] else [400, 420, 430, 440])


# ---------------------------------------------------------------------------- #
#                                 Visualisation                                #
# ---------------------------------------------------------------------------- #

compare = header_grid[0][0].selectbox('Comparison', ['Compare with opponents', 'Compare with own average'], key="compare", label_visibility="hidden")
role = header_grid[0][2].selectbox('Role', ['Top', 'Middle', 'Jungle', 'Utility', 'Bottom'], key="role", label_visibility="hidden")

grid = make_grid(20, 5, gap=True)

if len(prepared_data[role.lower()]) < 1:
    grid[2][2].markdown(f'<h5 style="text-align: center;">None of the last 30 games was on this lane!</h5>', unsafe_allow_html=True)
else:
    for i, matchData in enumerate(prepared_data[role.lower()][:5]):
        champ_name = matchData["champion"]
        # get the image from the web
        response = requests.get(f'https://ddragon.leagueoflegends.com/cdn/12.4.1/img/champion/{champ_name}.png')
        img = Image.open(BytesIO(response.content))
        with grid[0][i]:
            image_grid = make_grid(1, [1, 5, 1])
            image_grid[0][1].image(img, use_column_width=True)
        # write champion name
        grid[1][i].markdown(f'<h5 style="text-align: center;">Champion {champ_name}</h5>', unsafe_allow_html=True)
        # write match time
        timestamp_utc = int(matchData["timestamp"]) / 1000
        grid[2][i].markdown( f'<p style="text-align: center;">Timestamp {datetime.utcfromtimestamp(timestamp_utc).strftime("%d.%m.%Y - %H:%M")}</p>', unsafe_allow_html=True)

        # info box 1
        with grid[4][i]:
            kill_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "middle" or role.lower() == "bottom":
                kill_grid[0][0].markdown('<p><b>Kills</b></p>', unsafe_allow_html=True)
                kill_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["kills"]}</b></p>', unsafe_allow_html=True)
            else:
                kill_grid[0][0].markdown('<p>Kills</p>', unsafe_allow_html=True)
                kill_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["kills"]}</p>', unsafe_allow_html=True)
            kill_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["kills"] > matchData["opponent"]["kills"]:
                    kill_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    kill_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                kill_grid[0][3].button("&#9432;", key=f'kill_{i}', help=f'Number of your kills in the entire game – Your direct opponent had {matchData["opponent"]["kills"]} kills', disabled=True)
            else:
                if matchData["kills"] > average[role.lower()]["kills"]:
                    kill_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    kill_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                kill_grid[0][3].button("&#9432;", key=f'kill_{i}', help=f'Number of your kills in the entire game – Your own average is {average[role.lower()]["kills"]} kills per game', disabled=True)
        with grid[5][i]:
            death_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "top" or role.lower() == "middle":
                death_grid[0][0].markdown('<p><b>Deaths</b></p>', unsafe_allow_html=True)
                death_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["deaths"]}</b></p>', unsafe_allow_html=True)
            else:
                death_grid[0][0].markdown('<p>Deaths</p>', unsafe_allow_html=True)
                death_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["deaths"]}</p>', unsafe_allow_html=True)
            death_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["deaths"] > matchData["opponent"]["deaths"]:
                    death_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    death_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                death_grid[0][3].button("&#9432;", key=f'death_{i}', help=f'Number of your deaths in the entire game – Your direct opponent had {matchData["opponent"]["deaths"]} deaths', disabled=True)
            else:
                if matchData["deaths"] > average[role.lower()]["deaths"]:
                    death_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    death_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                death_grid[0][3].button("&#9432;", key=f'death_{i}', help=f'Number of your deaths in the entire game – Your own average is {average[role.lower()]["deaths"]} deaths per game', disabled=True)
        with grid[6][i]:
            assist_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "utility":
                assist_grid[0][0].markdown('<p><b>Assists</b></p>', unsafe_allow_html=True)
                assist_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["assists"]}</b></p>', unsafe_allow_html=True)
            else:
                assist_grid[0][0].markdown('<p>Assists</p>', unsafe_allow_html=True)
                assist_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["assists"]}</p>', unsafe_allow_html=True)
            assist_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["assists"] > matchData["opponent"]["assists"]:
                    assist_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    assist_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                assist_grid[0][3].button("&#9432;", key=f'assist_{i}', help=f'Number of your assists in the entire game – Your direct opponent had {matchData["opponent"]["assists"]} assists', disabled=True)
            else:
                if matchData["assists"] > average[role.lower()]["assists"]:
                    assist_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    assist_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                assist_grid[0][3].button("&#9432;", key=f'assist_{i}', help=f'Number of your assists in the entire game – Your own average is {average[role.lower()]["assists"]} assists per game', disabled=True)
        with grid[7][i]:
            gold_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "jungle":
                gold_grid[0][0].markdown('<p><b>Gold</b></p>', unsafe_allow_html=True)
                gold_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["gold"]}</b></p>', unsafe_allow_html=True)
            else:
                gold_grid[0][0].markdown('<p>Gold</p>', unsafe_allow_html=True)
                gold_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["gold"]}</p>', unsafe_allow_html=True)
            gold_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["gold"] > matchData["opponent"]["gold"]:
                    gold_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    gold_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                gold_grid[0][3].button("&#9432;", key=f'gold_{i}', help=f'Total amount of gold at the end of the game – Your direct opponent had {matchData["opponent"]["gold"]} gold', disabled=True)
            else:
                if matchData["gold"] > average[role.lower()]["gold"]:
                    gold_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    gold_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                gold_grid[0][3].button("&#9432;", key=f'gold_{i}', help=f'Total amount of gold at the end of the game – Your own average is {average[role.lower()]["gold"]} gold', disabled=True)
        with grid[8][i]:
            minions_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "bottom":
                minions_grid[0][0].markdown('<p><b>Minions</b></p>', unsafe_allow_html=True)
                minions_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["minions"]}</b></p>', unsafe_allow_html=True)
            else:
                minions_grid[0][0].markdown('<p>Minions</p>', unsafe_allow_html=True)
                minions_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["minions"]}</p>', unsafe_allow_html=True)
            minions_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["minions"] > matchData["opponent"]["minions"]:
                    minions_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    minions_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                minions_grid[0][3].button("&#9432;", key=f'minions_{i}', help=f'Total number of Minions killed in the game – Your direct opponent had {matchData["opponent"]["minions"]} minions killed', disabled=True)
            else:
                if matchData["minions"] > average[role.lower()]["minions"]:
                    minions_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    minions_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                minions_grid[0][3].button("&#9432;", key=f'minions_{i}', help=f'Total number of Minions killed in the game – Your own average is {average[role.lower()]["minions"]} killed minions', disabled=True)

        # info box 2
        with grid[10][i]:
            damage_d_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "top" or role.lower() == "bottom":
                damage_d_grid[0][0].markdown('<p><b>DMG Dealt</b></p>', unsafe_allow_html=True)
                damage_d_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["damage_dealt"]}</b></p>', unsafe_allow_html=True)
            else:
                damage_d_grid[0][0].markdown('<p>DMG Dealt</p>', unsafe_allow_html=True)
                damage_d_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["damage_dealt"]}</p>', unsafe_allow_html=True)
            damage_d_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["damage_dealt"] > matchData["opponent"]["damage_dealt"]:
                    damage_d_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    damage_d_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                damage_d_grid[0][3].button("&#9432;", key=f'damage_d_{i}', help=f'Total number of damage caused in the game – Your direct opponent had {matchData["opponent"]["damage_dealt"]} damage dealt', disabled=True)
            else:
                if matchData["damage_dealt"] > average[role.lower()]["damage_dealt"]:
                    damage_d_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    damage_d_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                damage_d_grid[0][3].button("&#9432;", key=f'damage_d_{i}', help=f'Total number of damage caused in the game – Your own average is {average[role.lower()]["damage_dealt"]} damage dealt', disabled=True)
        with grid[11][i]:
            damage_t_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "middle":
                damage_t_grid[0][0].markdown('<p><b>DMG Taken</b></p>', unsafe_allow_html=True)
                damage_t_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["damage_taken"]}</b></p>', unsafe_allow_html=True)
            else:
                damage_t_grid[0][0].markdown('<p>DMG Taken</p>', unsafe_allow_html=True)
                damage_t_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["damage_taken"]}</p>', unsafe_allow_html=True)
            damage_t_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["damage_taken"] > matchData["opponent"]["damage_taken"]:
                    damage_t_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    damage_t_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                damage_t_grid[0][3].button("&#9432;", key=f'damage_t_{i}', help=f'Total number of damage taken in the game – Your direct opponent had {matchData["opponent"]["damage_taken"]} damage taken', disabled=True)
            else:
                if matchData["damage_taken"] > average[role.lower()]["damage_taken"]:
                    damage_t_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    damage_t_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                damage_t_grid[0][3].button("&#9432;", key=f'damage_t_{i}', help=f'Total number of damage taken in the game – Your own average is {average[role.lower()]["damage_taken"]} damage taken', disabled=True)
        with grid[12][i]:
            heal_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "utility":
                heal_grid[0][0].markdown('<p><b>Heal</b></p>', unsafe_allow_html=True)
                heal_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["heal"]}</b></p>', unsafe_allow_html=True)
            else:
                heal_grid[0][0].markdown('<p>Heal</p>', unsafe_allow_html=True)
                heal_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["heal"]}</p>', unsafe_allow_html=True)
            heal_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["heal"] > matchData["opponent"]["heal"]:
                    heal_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    heal_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                heal_grid[0][3].button("&#9432;", key=f'heal_{i}', help=f'Total number of heal in the game – Your direct opponent had {matchData["opponent"]["heal"]} heal', disabled=True)
            else:
                if matchData["heal"] > average[role.lower()]["heal"]:
                    heal_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    heal_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                heal_grid[0][3].button("&#9432;", key=f'heal_{i}', help=f'Total number of heal in the game – Your own average is {average[role.lower()]["heal"]} heal', disabled=True)
        with grid[13][i]:
            vision_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "utility":
                vision_grid[0][0].markdown('<p><b>Vision</b></p>', unsafe_allow_html=True)
                vision_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["vision"]}</b></p>', unsafe_allow_html=True)
            else:
                vision_grid[0][0].markdown('<p>Vision</p>', unsafe_allow_html=True)
                vision_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["vision"]}</p>', unsafe_allow_html=True)
            vision_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["vision"] > matchData["opponent"]["vision"]:
                    vision_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    vision_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                vision_grid[0][3].button("&#9432;", key=f'vision_{i}', help=f'Total number of vision in the game – Your direct opponent had {matchData["opponent"]["vision"]} vision', disabled=True)
            else:
                if matchData["vision"] > average[role.lower()]["vision"]:
                    vision_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    vision_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                vision_grid[0][3].button("&#9432;", key=f'vision_{i}', help=f'Total number of vision in the game – Your own average is {average[role.lower()]["vision"]} vision', disabled=True)
        with grid[14][i]:
            champ_grid = make_grid(1, [4, 3, 1, 1])
            champ_grid[0][0].markdown('<p>Champ LVL</p>', unsafe_allow_html=True)
            champ_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["champ_lvl"]}</b></p>', unsafe_allow_html=True)
            champ_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["champ_lvl"] > matchData["opponent"]["champ_lvl"]:
                    champ_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    champ_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                champ_grid[0][3].button("&#9432;", key=f'champ_{i}', help=f'Level of the currently played champion – Your direct opponent had level {matchData["opponent"]["champ_lvl"]}', disabled=True)
            else:
                if matchData["champ_lvl"] > average[role.lower()]["champ_lvl"]:
                    champ_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    champ_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                champ_grid[0][3].button("&#9432;", key=f'champ_{i}', help=f'Level of the currently played champion – Your champion Level average is {average[role.lower()]["champ_lvl"]}', disabled=True)
        
        # ending box
        with grid[16][i]:
            kda_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "top" or role.lower() == "jungle":
                kda_grid[0][0].markdown('<p><b>KDA</b></p>', unsafe_allow_html=True)
                kda_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["kda"]}</b></p>', unsafe_allow_html=True)
            else:
                kda_grid[0][0].markdown('<p>KDA</p>', unsafe_allow_html=True)
                kda_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["kda"]}</p>', unsafe_allow_html=True)
            kda_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["kda"] > matchData["opponent"]["kda"]:
                    kda_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    kda_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                kda_grid[0][3].button("&#9432;", key=f'kda_{i}', help=f'Kill-Death-Assist Relation – Your direct opponent kda is {matchData["opponent"]["kda"]}', disabled=True)
            else:
                if matchData["kda"] > average[role.lower()]["kda"]:
                    kda_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    kda_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                kda_grid[0][3].button("&#9432;", key=f'kda_{i}', help=f'Kill-Death-Assist Relation - Your own average kda is {average[role.lower()]["kda"]}', disabled=True)
        with grid[17][i]:
            cs_grid = make_grid(1, [4, 3, 1, 1])
            if role.lower() == "jungle":
                cs_grid[0][0].markdown('<p><b>CS</b></p>', unsafe_allow_html=True)
                cs_grid[0][1].markdown(f'<p style="text-align: right;"><b>{matchData["cs"]}</b></p>', unsafe_allow_html=True)
            else:
                cs_grid[0][0].markdown('<p>CS</p>', unsafe_allow_html=True)
                cs_grid[0][1].markdown(f'<p style="text-align: right;">{matchData["cs"]}</p>', unsafe_allow_html=True)
            cs_grid[0][3].markdown('<style>div.stTooltipIcon > div[id^="bui"] > button:first-child { color: white; border: 0; cursor: default; position: relative; top: -7px; height: 0px !important; }</style>', unsafe_allow_html=True)
            if "opponents" in compare:
                if matchData["cs"] > matchData["opponent"]["cs"]:
                    cs_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    cs_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                cs_grid[0][3].button("&#9432;", key=f'cs_{i}', help=f'Creep Score (amaount of killed minions in lane and jungle) – Your direct opponent cs is {matchData["opponent"]["cs"]}', disabled=True)
            else:
                if matchData["cs"] > average[role.lower()]["cs"]:
                    cs_grid[0][2].markdown('<p style="color: green; text-align: right;">&#9650;</p>', unsafe_allow_html=True)
                else:
                    cs_grid[0][2].markdown('<p style="color: red; text-align: right;">&#9660;</p>', unsafe_allow_html=True)
                cs_grid[0][3].button("&#9432;", key=f'cs_{i}', help=f'Creep Score (amaount of killed minions in lane and jungle) – Your own average cs is {average[role.lower()]["cs"]}', disabled=True)
        with grid[18][i]:
            surrender_grid = make_grid(1, [4, 3, 1])
            surrender_grid[0][0].markdown('<p>Surrender</p>', unsafe_allow_html=True)
            surrender_result = matchData["surrender"]
            if surrender_result:
                surrender_grid[0][1].markdown('<p style="text-align: right; color: red;"><b>TRUE</b></p>', unsafe_allow_html=True)
            else:
                surrender_grid[0][1].markdown('<p style="text-align: right; color: green;"><b>FALSE</b></p>', unsafe_allow_html=True)
        with grid[19][i]:
            vision_grid = make_grid(1, [4, 3, 1])
            vision_grid[0][0].markdown('<p>Result</p>', unsafe_allow_html=True)
            match_result = matchData["result"]
            if match_result:
                vision_grid[0][1].markdown('<p style="text-align: right; color: green;"><b>WIN</b></p>', unsafe_allow_html=True)
            else:
                vision_grid[0][1].markdown('<p style="text-align: right; color: red;"><b>LOSS</b></p>', unsafe_allow_html=True)
