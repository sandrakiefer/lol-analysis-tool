# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 18:37:58 2023

@author: lordv
"""

import os
import streamlit as st
import json
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime
import streamlit_nested_layout
import numpy as np


root_dir = os.path.dirname(os.path.abspath(__file__))


API_KEY = st.secrets["api_key"]
GAME_COUNT = 5

# ---------------------------------------------------------------------------- #
#                               Data Preperation                               #
# ---------------------------------------------------------------------------- #




version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
version = requests.get(version_url).json()[0] # get current version


@st.cache_data
def load_data(puuid, region, ranked, apiKey = API_KEY):
    timeline_data_result = []
    if ranked:
        match_history_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&queueId=420&count={GAME_COUNT}&api_key={API_KEY}"
    else:
        match_history_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={GAME_COUNT}&api_key={API_KEY}"
    match_history_res = requests.get(match_history_url)
    match_history_data = match_history_res.json()
    
    for match in match_history_data:
        match_timeline_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match}/timeline?api_key={API_KEY}"
        match_timeline_res = requests.get(match_timeline_url)
        match_timeline_data = match_timeline_res.json()
        
        match_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match}?api_key={API_KEY}"
        match_res = requests.get(match_url)
        match_data = match_res.json()

        timeline_data_result.append((match_timeline_data, match_data))
    
    return timeline_data_result




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



# ---------------------------------------------------------------------------- #
#                        Custom Functions for Data Calls                       #
# ---------------------------------------------------------------------------- #

def getGameMinute(data):
  timeFrames = data["info"]["frames"]
  gameMinutes = np.array([])
  for timeFrame in timeFrames:
    # Convert the timestamp to seconds
    timeStamp = int(timeFrame["timestamp"]) / 1000
    # Calculate the game minute
    gameMinute = timeStamp // 60
    # Append the game minute to the numpy array
    gameMinutes = np.append(gameMinutes, gameMinute)
  return gameMinutes

def getPlayerId(data, puuid):
    players = data["info"]["participants"]
    for player in players:
        if(f'{player["puuid"]}' == puuid):
            return(player["participantId"])
    return("No Player Found")

st.set_page_config(layout="wide")


   
# ---------------------------------------------------------------------------- #
#                                   Styling                                    #
# ---------------------------------------------------------------------------- #


st.markdown("""
<style>
    .css-1r6slb0{ 
        width: 32%;
        flex: unset;
        border: 1px solid #fff;
        padding: 0 20px;
    }
    .css-1fv8s86{
        width: 98%;
    }
    .css-1mqgob .css-1r6slb0{
        border: none;
    }
    .items{
        
    }
    .right{
        float: right;
        padding-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------- #
#                               Streamlit Display                              #
# ---------------------------------------------------------------------------- #
if 'puuid' not in st.session_state:
    st.markdown(f'<h5 style="text-align: center;">please enter your username on the login screen</h5>', unsafe_allow_html=True)
    st.stop()
    
if 'puuid' in st.session_state:
    gameData = load_data(st.session_state['puuid'], st.session_state['continent'], st.session_state['ranked_only'])
    gameDataTupleZero = []
    gameDataTupleOne =  []
    
    options = (1, 2, 3, 4, 5)
    option = st.selectbox('Which Game do you want displayed?', options)
    option = option - 1
    
    
    
    for gameDataTuple in gameData:   
        gameDataTupleZero.append(gameDataTuple[0])
        gameDataTupleOne.append(gameDataTuple[1])

        

    st.markdown("<h1 style='text-align: center;'>Overview-Early-Mid-Late-Game</h1>", unsafe_allow_html=True)
    gameInfo = gameDataTupleOne[option]
    champs = gameInfo["info"]
    for champ in champs["participants"]:
        if st.session_state['puuid'] == champ["puuid"]:
            champName = champ["championName"]
            responseChamp = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champName}.png')
            imgChamp = Image.open(BytesIO(responseChamp.content))

            image_grid = make_grid(1, [1, 0.3, 1])
            image_grid[0][1].image(imgChamp, use_column_width=True)
            st.markdown(f"<h4 style='text-align: center;'>{champName}</h4>", unsafe_allow_html=True)
            startTime = gameInfo["info"]["gameStartTimestamp"] / 1000
            st.markdown(f"<p style='text-align: center;'> TimeStamp {datetime.utcfromtimestamp(startTime).strftime('%d.%m.%Y - %H:%M')}</span>", unsafe_allow_html=True)
    
    gameMinute = getGameMinute(gameDataTupleZero[option])
    userId = getPlayerId(gameDataTupleZero[option], st.session_state['puuid'])
    if (not gameMinute[-1] < 14):
        participantFrame15 = gameDataTupleZero[option]["info"]["frames"][14]["participantFrames"]
    else:
        participantFrame15 = gameDataTupleZero[option]["info"]["frames"][int(gameMinute[-1])]["participantFrames"]
    if (not gameMinute[-1] < 24):
        participantFrame25 = gameDataTupleZero[option]["info"]["frames"][24]["participantFrames"]
    participantFrameEnd = gameDataTupleZero[option]["info"]["frames"][int(gameMinute[-1])]["participantFrames"]
    playerFrame15 = participantFrame15[str(userId)]
    if (not gameMinute[-1] < 24):
        playerFrame25 = participantFrame25[str(userId)]
    playerFrameEnd = participantFrameEnd[str(userId)]
    frames = gameDataTupleZero[option]["info"]["frames"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<h2 style='text-align: center;'>Early Game</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center;'>Minute 15</h4>", unsafe_allow_html=True)
        st.markdown("<h6 style='text-align: center;'>Soft Game Stats</h6>", unsafe_allow_html=True)
        st.write(' ')
        st.write(' ')
        st.write(f"<span><b>Level: </b></span> <span class='right'> {str(playerFrame15['level'])}</span>", unsafe_allow_html=True)
        st.write(f"<span><b>Total Gold: </b></span> <span class='right'> {str(playerFrame15['totalGold'])}</span>", unsafe_allow_html=True)
        st.write(f"<span><b>Minions Killed: </b></span> <span class='right'> {str(playerFrame15['minionsKilled'])}</span>", unsafe_allow_html=True)
        st.write(f"<span><b>Jungle Minions Killed: </b></span> <span class='right'> { str(playerFrame15['jungleMinionsKilled'])}</span>", unsafe_allow_html=True)
        st.write(f"<span><b>Experience Points: </b></span> <span class='right'> { str(playerFrame15['xp'])}</span>", unsafe_allow_html=True)
        st.write(' ')
        st.write(' ')
        st.markdown("<h6 style='text-align: center;'>items</h6>", unsafe_allow_html=True)
        
        
        itemImages = []
    
        for frame in frames:
            events = frame["events"]
            for event in events:
                if (event["type"] == "ITEM_PURCHASED" and event["participantId"] == userId and event["itemId"] >= 3000 and event["timestamp"] <= 900000):
                    itemId = event["itemId"]
                    responseItem = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{itemId}.png')
                    imgItem = Image.open(BytesIO(responseItem.content))
                    itemImages.append((imgItem, event["timestamp"]))
        
        cols_per_row = 2
        num_rows = (len(itemImages) // cols_per_row) + 1
        
        st.markdown("<div class='items'>", unsafe_allow_html=True)
        for i in range(num_rows):
            row_images = itemImages[i*cols_per_row:(i+1)*cols_per_row]
            cols = st.columns(cols_per_row)
            for j, (img, timestamp) in enumerate(row_images):
                with cols[j]:
                    st.image(img, use_column_width=False)
                    st.write(f"Timestamp: {round(timestamp / 60000, 2)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

    
                
        st.write(' ')
        st.write(' ')
        if st.checkbox("Show Early Game Stats"):
            st.markdown("<h6 style='text-align: center;'>Champion Stats</h6>", unsafe_allow_html=True)
            st.write(f"<span><b>Health: </b></span> <span class='right'> { str(playerFrame15['championStats']['healthMax'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Armor: </b></span> <span class='right'> { str(playerFrame15['championStats']['armor'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Magic Resistance: </b></span> <span class='right'> { str(playerFrame15['championStats']['magicResist'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Health Regen: </b></span> <span class='right'> { str(playerFrame15['championStats']['healthRegen'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Movement Speed: </b></span> <span class='right'> { str(playerFrame15['championStats']['movementSpeed'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Tenacity: </b></span> <span class='right' title='Tenacity: the value, that reduces the time of crowd control on the champion'>&#9432;</span> <span class='right'> { str(playerFrame15['championStats']['ccReduction'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Attack Damage: </b></span> <span class='right'> { str(playerFrame15['championStats']['attackDamage'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Attack Speed: </b></span> <span class='right'> { str(playerFrame15['championStats']['attackSpeed'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Abillity Power: </b></span> <span class='right'> { str(playerFrame15['championStats']['abilityPower'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Cooldown Reduction: </b></span> <span class='right'> { str(playerFrame15['championStats']['cooldownReduction'])} </span>", unsafe_allow_html=True)
            st.write(f"<span><b>Armor Penetration: </b></span> <span class='right'> { str(playerFrame15['championStats']['armorPenPercent'])}% </span>", unsafe_allow_html=True)
            st.write(f"<span><b>Magic Penetration: </b></span> <span class='right'> { str(playerFrame15['championStats']['magicPenPercent'])}% </span>", unsafe_allow_html=True)
            st.write(f"<span><b>Life Steal: </b></span> <span class='right' title='Life Steal: percentage heal value of auto attack damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame15['championStats']['lifesteal'])}% </span>", unsafe_allow_html=True)
            st.write(f"<span><b>Physical Vamp: </b></span> <span class='right' title='Physical Vamp: percentage heal value of physical damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame15['championStats']['physicalVamp'])}% </span>", unsafe_allow_html=True)
            st.write(f"<span><b>Spell Vamp: </b></span> <span class='right' title='Spell Vamp: percentage heal value of magical and true damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame15['championStats']['spellVamp'])}% </span>", unsafe_allow_html=True)
            st.write(f"<span><b>Omni Vamp: </b></span> <span class='right' title='Omni Vamp: percentage heal value of damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame15['championStats']['omnivamp'])}% </span>", unsafe_allow_html=True)
        st.write(' ')
        st.write(' ')
        if st.checkbox("Show Early Damage Stats"):
            st.markdown("<h6 style='text-align: center;'>Damage Stats</h6>", unsafe_allow_html=True)
            st.write(f"<span><b>Total Damage Done: </b></span> <span class='right'> { str(playerFrame15['damageStats']['totalDamageDone'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Total Damage to Champions: </b></span> <span class='right'> { str(playerFrame15['damageStats']['totalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Magic Damage Done: </b></span> <span class='right'> { str(playerFrame15['damageStats']['magicDamageDone'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Magic Damage to Champions: </b></span> <span class='right'> { str(playerFrame15['damageStats']['magicDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Physical Damage Done: </b></span> <span class='right'> { str(playerFrame15['damageStats']['physicalDamageDone'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Physical Damage to Champions: </b></span> <span class='right'> { str(playerFrame15['damageStats']['physicalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
            #st.write(f"<span><b>Ture Damage Done: </b></span> <span class='right'> { str(playerFrame15['damageStats']['TrueDamageDone'])}</span>", unsafe_allow_html=True)
            #st.write(f"<span><b>True Damage Done to Champions: </b></span> <span class='right'> { str(playerFrame15['damageStats']['TrueDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Magic Damage Taken: </b></span> <span class='right'> { str(playerFrame15['damageStats']['magicDamageTaken'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Physical Damage Taken: </b></span> <span class='right'> { str(playerFrame15['damageStats']['physicalDamageTaken'])}</span>", unsafe_allow_html=True)
            #st.write(f"<span><b>True Damage Taken: </b></span> <span class='right'> { str(playerFrame15['damageStats']['TrueDamageTaken'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Total Damage Taken: </b></span> <span class='right'> { str(playerFrame15['damageStats']['totalDamageTaken'])}</span>", unsafe_allow_html=True)
    
      
    
    with col2:
        if (not gameMinute[-1] < 24):
            st.markdown("<h2 style='text-align: center;'>Mid Game</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center;'>Minute 25</h4>", unsafe_allow_html=True)
            st.markdown("<h6 style='text-align: center;'>Soft Game Stats</h6>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            st.write(f"<span><b>Level: </b></span> <span class='right'> {str(playerFrame25['level'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Total Gold: </b></span> <span class='right'> {str(playerFrame25['totalGold'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Minions Killed: </b></span> <span class='right'> {str(playerFrame25['minionsKilled'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Jungle Minions Killed: </b></span> <span class='right'> { str(playerFrame25['jungleMinionsKilled'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Experience Points: </b></span> <span class='right'> { str(playerFrame25['xp'])}</span>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            st.markdown("<h6 style='text-align: center;'>items</h6>", unsafe_allow_html=True)
            
                        
            itemImages = []
        
            for frame in frames:
                events = frame["events"]
                for event in events:
                    if (event["type"] == "ITEM_PURCHASED" and event["participantId"] == userId and event["itemId"] >= 3000 and event["timestamp"] > 900000 and event["timestamp"] <= 1500000):
                        itemId = event["itemId"]
                        responseItem = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{itemId}.png')
                        imgItem = Image.open(BytesIO(responseItem.content))
                        itemImages.append((imgItem, event["timestamp"]))
            
            cols_per_row = 2
            num_rows = (len(itemImages) // cols_per_row) + 1
            
            for i in range(num_rows):
                row_images = itemImages[i*cols_per_row:(i+1)*cols_per_row]
                cols = st.columns(cols_per_row)
                for j, (img, timestamp) in enumerate(row_images):
                    with cols[j]:
                        st.image(img, use_column_width=False)
                        st.write(f"Timestamp: {round(timestamp / 60000, 2)}")
                        
                    
                
            
            if st.checkbox("Show Mid Game Stats"):
                st.markdown("<h6 style='text-align: center;'>Champion Stats</h6>", unsafe_allow_html=True)
                st.write(f"<span><b>Health: </b></span> <span class='right'> { str(playerFrame25['championStats']['healthMax'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Armor: </b></span> <span class='right'> { str(playerFrame25['championStats']['armor'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Resistance: </b></span> <span class='right'> { str(playerFrame25['championStats']['magicResist'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Tenacity: </b></span> <span class='right' title='Tenacity: the value, that reduces the time of crowd control on the champion'>&#9432;</span> <span class='right'> { str(playerFrame25['championStats']['ccReduction'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Attack Damage: </b></span> <span class='right'> { str(playerFrame25['championStats']['attackDamage'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Attack Speed: </b></span> <span class='right'> { str(playerFrame25['championStats']['attackSpeed'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Abillity Power: </b></span> <span class='right'> { str(playerFrame25['championStats']['abilityPower'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Cooldown Reduction: </b></span> <span class='right'> { str(playerFrame25['championStats']['cooldownReduction'])} </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Armor Penetration: </b></span> <span class='right'> { str(playerFrame25['championStats']['armorPenPercent'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Penetration: </b></span> <span class='right'> { str(playerFrame25['championStats']['magicPenPercent'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Life Steal: </b></span> <span class='right' title='Life Steal: percentage heal value of auto attack damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame25['championStats']['lifesteal'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Vamp: </b></span> <span class='right' title='Physical Vamp: percentage heal value of physical damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame25['championStats']['physicalVamp'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Spell Vamp: </b></span> <span class='right' title='Spell Vamp: percentage heal value of magical and true damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame25['championStats']['spellVamp'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Omni Vamp: </b></span> <span class='right' title='Omni Vamp: percentage heal value of damage dealt'>&#9432;</span> <span class='right'> { str(playerFrame25['championStats']['omnivamp'])}% </span>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            if st.checkbox("Show Mid Damage Stats"):
                st.write(f"<span><b>Total Damage Done: </b></span> <span class='right'> { str(playerFrame25['damageStats']['totalDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage to Champions: </b></span> <span class='right'> { str(playerFrame25['damageStats']['totalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage Done: </b></span> <span class='right'> { str(playerFrame25['damageStats']['magicDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage to Champions: </b></span> <span class='right'> { str(playerFrame25['damageStats']['magicDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage Done: </b></span> <span class='right'> { str(playerFrame25['damageStats']['physicalDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage to Champions: </b></span> <span class='right'> { str(playerFrame25['damageStats']['physicalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>Ture Damage Done: </b></span> <span class='right'> { str(playerFrame25['damageStats']['TrueDamageDone'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>True Damage Done to Champions: </b></span> <span class='right'> { str(playerFrame25['damageStats']['TrueDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage Taken: </b></span> <span class='right'> { str(playerFrame25['damageStats']['magicDamageTaken'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage Taken: </b></span> <span class='right'> { str(playerFrame25['damageStats']['physicalDamageTaken'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>True Damage Taken: </b></span> <span class='right'> { str(playerFrame25['damageStats']['TrueDamageTaken'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage Taken: </b></span> <span class='right'> { str(playerFrame25['damageStats']['totalDamageTaken'])}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='text-align: center;'>Mid Game</h2>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align: center;'>Minute {gameMinute[-1]}</h4>", unsafe_allow_html=True)
            st.markdown("<h6 style='text-align: center;'>Soft Game Stats</h6>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            st.write(f"<span><b>Level: </b></span> <span class='right'> {str(playerFrameEnd['level'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Total Gold: </b></span> <span class='right'> {str(playerFrameEnd['totalGold'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Minions Killed: </b></span> <span class='right'> {str(playerFrameEnd['minionsKilled'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Jungle Minions Killed: </b></span> <span class='right'> { str(playerFrameEnd['jungleMinionsKilled'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Experience Points: </b></span> <span class='right'> { str(playerFrameEnd['xp'])}</span>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            st.markdown("<h6 style='text-align: center;'>items</h6>", unsafe_allow_html=True)
                        
            
            itemImages = []
        
            for frame in frames:
                events = frame["events"]
                for event in events:
                    if (event["type"] == "ITEM_PURCHASED" and event["participantId"] == userId and event["itemId"] >= 3000 and event["timestamp"] > 1500000):
                        itemId = event["itemId"]
                        responseItem = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{itemId}.png')
                        imgItem = Image.open(BytesIO(responseItem.content))
                        itemImages.append((imgItem, event["timestamp"]))
                        
            cols_per_row = 2
            num_rows = (len(itemImages) // cols_per_row) + 1
            
            for i in range(num_rows):
                row_images = itemImages[i*cols_per_row:(i+1)*cols_per_row]
                cols = st.columns(cols_per_row)
                for j, (img, timestamp) in enumerate(row_images):
                    with cols[j]:
                        st.image(img, use_column_width=False)
                        st.write(f"Timestamp: {round(timestamp / 60000, 2)}")
                    
                
        
            if st.checkbox("Show End Game Stats"):
                st.markdown("<h6 style='text-align: center;'>Champion Stats</h6>", unsafe_allow_html=True)
                st.markdown("<h6 style='text-align: center;'>Champion Stats</h6>", unsafe_allow_html=True)
                st.write(f"<span><b>Health: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['healthMax'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Armor: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['armor'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Resistance: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['magicResist'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Health Regen: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['healthRegen'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Tenacity: </b></span> <span class='right' title='Tenacity: the value, that reduces the time of crowd control on the champion'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['ccReduction'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Attack Damage: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['attackDamage'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Attack Speed: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['attackSpeed'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Abillity Power: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['abilityPower'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Cooldown Reduction: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['cooldownReduction'])} </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Armor Penetration: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['armorPenPercent'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Penetration: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['magicPenPercent'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Life Steal: </b></span> <span class='right' title='Life Steal: percentage heal value of auto attack damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['lifesteal'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Vamp: </b></span> <span class='right' title='Physical Vamp: percentage heal value of physical damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['physicalVamp'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Spell Vamp: </b></span> <span class='right' title='Spell Vamp: percentage heal value of magical and true damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['spellVamp'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Omni Vamp: </b></span> <span class='right' title='Omni Vamp: percentage heal value of damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['omnivamp'])}% </span>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            if st.checkbox("Show End Damage Stats"):
                st.markdown("<h6 style='text-align: center;'>Damage Stats</h6>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['totalDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['totalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['magicDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['magicDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['physicalDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['physicalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>Ture Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['TrueDamageDone'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>True Damage Done to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['TrueDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['magicDamageTaken'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['physicalDamageTaken'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>True Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['TrueDamageTaken'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['totalDamageTaken'])}</span>", unsafe_allow_html=True)
    
    
    with col3:
        if (not gameMinute[-1] < 24):
            st.markdown("<h2 style='text-align: center;'>Late Game</h2>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='text-align: center;'>End of Game</h4>", unsafe_allow_html=True)
            st.markdown("<h6 style='text-align: center;'>Soft Game Stats</h6>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            st.write(f"<span><b>Level: </b></span> <span class='right'> {str(playerFrameEnd['level'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Total Gold: </b></span> <span class='right'> {str(playerFrameEnd['totalGold'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Minions Killed: </b></span> <span class='right'> {str(playerFrameEnd['minionsKilled'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Jungle Minions Killed: </b></span> <span class='right'> { str(playerFrameEnd['jungleMinionsKilled'])}</span>", unsafe_allow_html=True)
            st.write(f"<span><b>Experience Points: </b></span> <span class='right'> { str(playerFrameEnd['xp'])}</span>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            st.markdown("<h6 style='text-align: center;'>items</h6>", unsafe_allow_html=True)
                        
            
            itemImages = []
        
            for frame in frames:
                events = frame["events"]
                for event in events:
                    if (event["type"] == "ITEM_PURCHASED" and event["participantId"] == userId and event["itemId"] >= 3000 and event["timestamp"] > 1500000):
                        itemId = event["itemId"]
                        responseItem = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{itemId}.png')
                        imgItem = Image.open(BytesIO(responseItem.content))
                        itemImages.append((imgItem, event["timestamp"]))
            
            cols_per_row = 2
            num_rows = (len(itemImages) // cols_per_row) + 1
            
            for i in range(num_rows):
                row_images = itemImages[i*cols_per_row:(i+1)*cols_per_row]
                cols = st.columns(cols_per_row)
                for j, (img, timestamp) in enumerate(row_images):
                    with cols[j]:
                        st.image(img, use_column_width=False)
                        st.write(f"Timestamp: {round(timestamp / 60000, 2)}")
                    
                
        
            if st.checkbox("Show End Game Stats"):
                st.markdown("<h6 style='text-align: center;'>Champion Stats</h6>", unsafe_allow_html=True)
                st.write(f"<span><b>Health: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['healthMax'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Armor: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['armor'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Resistance: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['magicResist'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Health Regen: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['healthRegen'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Movement Speed: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['movementSpeed'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Tenacity: </b></span> <span class='right' title='Tenacity: the value, that reduces the time of crowd control on the champion'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['ccReduction'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Attack Damage: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['attackDamage'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Attack Speed: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['attackSpeed'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Abillity Power: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['abilityPower'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Cooldown Reduction: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['cooldownReduction'])} </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Armor Penetration: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['armorPenPercent'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Penetration: </b></span> <span class='right'> { str(playerFrameEnd['championStats']['magicPenPercent'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Life Steal: </b></span> <span class='right' title='Life Steal: percentage heal value of auto attack damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['lifesteal'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Vamp: </b></span> <span class='right' title='Physical Vamp: percentage heal value of physical damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['physicalVamp'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Spell Vamp: </b></span> <span class='right' title='Spell Vamp: percentage heal value of magical and true damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['spellVamp'])}% </span>", unsafe_allow_html=True)
                st.write(f"<span><b>Omni Vamp: </b></span> <span class='right' title='Omni Vamp: percentage heal value of damage dealt'>&#9432;</span> <span class='right'> { str(playerFrameEnd['championStats']['omnivamp'])}% </span>", unsafe_allow_html=True)
            st.write(' ')
            st.write(' ')
            if st.checkbox("Show End Damage Stats"):
                st.markdown("<h6 style='text-align: center;'>Damage Stats</h6>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['totalDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['totalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['magicDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['magicDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['physicalDamageDone'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['physicalDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>Ture Damage Done: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['TrueDamageDone'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>True Damage Done to Champions: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['TrueDamageDoneToChampions'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Magic Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['magicDamageTaken'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Physical Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['physicalDamageTaken'])}</span>", unsafe_allow_html=True)
                #st.write(f"<span><b>True Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['TrueDamageTaken'])}</span>", unsafe_allow_html=True)
                st.write(f"<span><b>Total Damage Taken: </b></span> <span class='right'> { str(playerFrameEnd['damageStats']['totalDamageTaken'])}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='text-align: center;'>Game has Ended before the Beginning of the Endgame at Minute {gameMinute[-1]}</h1>", unsafe_allow_html=True)




grid = make_grid(21, 3, gap=True)
