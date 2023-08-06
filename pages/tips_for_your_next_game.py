import streamlit as st
from PIL import Image
from collections import Counter
import requests
import os

st.set_page_config(layout="wide")

API_KEY = st.secrets["api_key"]
AMOUNT_GAMES = 5

root_dir = os.path.dirname(os.path.abspath(__file__))
minions_image = Image.open(os.path.join(root_dir, "../images/minions.jpeg"))
teamfight_image = Image.open(os.path.join(root_dir, "../images/teamfight.jpeg"))
conversion_image = Image.open(os.path.join(root_dir, "../images/conversion.png"))
objectives_image = Image.open(os.path.join(root_dir, "../images/objectives.jpg"))
warding_image = Image.open(os.path.join(root_dir, "../images/warding.jpeg"))
turret_image = Image.open(os.path.join(root_dir, "../images/turret.png"))
bounty_image = Image.open(os.path.join(root_dir, "../images/bounty.png"))
ping_image = Image.open(os.path.join(root_dir, "../images/ping_wheel.jpg"))
spend_image = Image.open(os.path.join(root_dir, "../images/spend.jpg"))


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


def get_info_from_match_data(match_data, puuid, information):
    players = match_data["info"]["participants"]
    for player in players:
        if(f'{player["puuid"]}' == puuid) and information in player:
            return(player[information])
    return(0)

def get_challenge_from_match_data(match_data, puuid, information):
    players = match_data["info"]["participants"]
    for player in players:
        if(f'{player["puuid"]}' == puuid) and information in player["challenges"]:
            return(player["challenges"][information])
    return(0)

def get_enemy_laner(match_data, puuid, role):
    players = match_data["info"]["participants"]
    for player in players:
        if player["teamPosition"] == role and (f'{player["puuid"]}' != puuid):
            return(player["puuid"])
        elif player["role"] == role and (f'{player["puuid"]}' != puuid):
            return(player["puuid"])

def select_tips(timeline_data, puuid):
    tipSelection = []

    index = 0
    for timeline_match_tuple in timeline_data:
        index += 1
        player_role = get_info_from_match_data(timeline_match_tuple[1], puuid, "teamPosition")
        if player_role == "none":
            player_role = get_info_from_match_data(timeline_match_tuple[1], puuid, "role")
        enemyLaner = get_enemy_laner(timeline_match_tuple[1], puuid, player_role)

        #laning phase tips
        if player_role != "JUNGLE":
            laneAdvantage = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "laningPhaseGoldExpAdvantage") == 1)
            earlyCsAdvantage = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "laneMinionsFirst10Minutes") >= get_challenge_from_match_data(timeline_match_tuple[1], enemyLaner, "laneMinionsFirst10Minutes") )
        else:
            laneAdvantage = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "moreEnemyJungleThanOpponent") > 0)
            earlyCsAdvantage = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "jungleCsBefore10Minutes") >= get_challenge_from_match_data(timeline_match_tuple[1], enemyLaner, "jungleCsBefore10Minutes"))
        
        visionScoreAdvantage = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "visionScoreAdvantageLaneOpponent") > 0)
        visionWardsBought = (get_info_from_match_data(timeline_match_tuple[1], puuid, "visionWardsBoughtInGame") > 0)
        matchResult = (get_info_from_match_data(timeline_match_tuple[1], puuid, "win") == "true")
        kda = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "kda") > get_challenge_from_match_data(timeline_match_tuple[1], enemyLaner, "kda"))
        damageDealtAdvantage = (get_info_from_match_data(timeline_match_tuple[1], puuid, "totalDamageDealtToChampions") > get_info_from_match_data(timeline_match_tuple[1], enemyLaner, "totalDamageDealtToChampions"))
        turretsDestroyedAdvantage = (get_info_from_match_data(timeline_match_tuple[1], puuid, "turretTakedowns") > get_info_from_match_data(timeline_match_tuple[1], enemyLaner, "turretTakedowns"))
        bountiesClaimed = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "bountyGold") > 0)
        noPings = (get_info_from_match_data(timeline_match_tuple[1], puuid, "allInPings") + get_info_from_match_data(timeline_match_tuple[1], puuid, "assistMePings") + 
                    get_info_from_match_data(timeline_match_tuple[1], puuid, "baitPings") + get_info_from_match_data(timeline_match_tuple[1], puuid, "dangerPings") + 
                    get_info_from_match_data(timeline_match_tuple[1], puuid, "enemyMissingPings") + get_info_from_match_data(timeline_match_tuple[1], puuid, "getBackPings") + 
                    get_info_from_match_data(timeline_match_tuple[1], puuid, "holdPings") + get_info_from_match_data(timeline_match_tuple[1], puuid, "onMyWayPings") + 
                    get_info_from_match_data(timeline_match_tuple[1], puuid, "pushPings") + get_info_from_match_data(timeline_match_tuple[1], puuid, "needVisionPings") + 
                    get_info_from_match_data(timeline_match_tuple[1], puuid, "enemyVisionPings") + get_info_from_match_data(timeline_match_tuple[1], puuid, "visionClearedPings")) == 0
        baronKills = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "teamBaronKills") >= get_challenge_from_match_data(timeline_match_tuple[1], enemyLaner, "teamBaronKills"))
        elderDragonKills = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "teamElderDragonKills") >= get_challenge_from_match_data(timeline_match_tuple[1], enemyLaner, "teamElderDragonKills"))
        dragonTakedowns = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "dragonTakedowns") >= get_challenge_from_match_data(timeline_match_tuple[1], enemyLaner, "dragonTakedowns"))
        riftHeraldKills = (get_challenge_from_match_data(timeline_match_tuple[1], puuid, "teamRiftHeraldKills") >= get_challenge_from_match_data(timeline_match_tuple[1], enemyLaner, "teamRiftHeraldKills"))

        totalGoldEarned = int(get_info_from_match_data(timeline_match_tuple[1], puuid, "goldEarned"))
        totalGoldSpent = int(get_info_from_match_data(timeline_match_tuple[1], puuid, "goldSpent"))
        goldPerMinute = int(get_challenge_from_match_data(timeline_match_tuple[1], puuid, "goldPerMinute"))
        matchLength = int(totalGoldEarned / goldPerMinute)

        unspentGold = totalGoldEarned - totalGoldSpent > 2000

        winningLane = laneAdvantage and earlyCsAdvantage
        losingLane = not laneAdvantage and not earlyCsAdvantage

        positionAdvantage = kda and damageDealtAdvantage
        positionDisadvantage = not kda and not damageDealtAdvantage
        # calculate relevant tips for match (non support)
        if player_role != "SUPPORT" and player_role != "UTILITY":
            if losingLane:
                tipSelection.append("farming_tip")
            if positionDisadvantage:
                tipSelection.append("teamfight_tip")
            if (winningLane and positionAdvantage) and not matchResult:
                tipSelection.append("conversion_tip")
            if player_role != "JUNGLE":    
                if winningLane and not turretsDestroyedAdvantage:
                    tipSelection.append("turret_tip")
    
        
        if player_role == "JUNGLE" or player_role == "SUPPORT" or player_role == "UTILITY":
            if not dragonTakedowns and not riftHeraldKills:
                tipSelection.append("monster_objective_tip")
            if not baronKills and not elderDragonKills:
                tipSelection.append("monster_objective_tip")


        if not visionScoreAdvantage and not visionWardsBought:
                tipSelection.append("warding_tip")
        if (losingLane and positionDisadvantage) and not bountiesClaimed:
                tipSelection.append("bounty_tip")
        if noPings:
            tipSelection.append("ping_tip")
        if matchLength < 40 and unspentGold:
            tipSelection.append("spend_tip")
        
     
    return tipSelection      

def get_image_for_tip(tip):
    if tip == "farming_tip":
        return minions_image
    if tip == "teamfight_tip":
        return teamfight_image
    if tip == "conversion_tip":
        return conversion_image
    if tip == "monster_objective_tip":
        return objectives_image
    if tip == "warding_tip":
        return warding_image
    if tip == "turret_tip":
        return turret_image
    if tip == "bounty_tip":
        return bounty_image
    if tip == "ping_tip":
        return ping_image
    if tip == "spend_tip":
        return spend_image

def get_header_for_tip(tip):
    if tip == "farming_tip":
        return "Focus more on your farming"
    if tip == "teamfight_tip":
        return "Get more involved in teamfights"
    if tip == "conversion_tip":
        return "Convert your lane advantage"
    if tip == "monster_objective_tip":
        return "Help your team secure objectives"
    if tip == "warding_tip":
        return "Place some more wards"
    if tip == "turret_tip":
        return "Take your opponents turrets"
    if tip == "bounty_tip":
        return "Look out for Bounties"
    if tip == "ping_tip":
        return "Use pings to communicate"
    if tip == "spend_tip":
        return "Spend all your gold on items"

def get_message_for_tip(tip):
    if tip == "farming_tip":
        return "Last hitting minions is an important and effective method for accumulating gold throughout the match. You can improve this skill by practising in bot games or the practise tool. Another important aspect to improving your farm is learning how and when to push or freeze minion waves to gain an advantage over your opponent."
    if tip == "teamfight_tip":
        return "Help your team win the game by contributing more to teamfights. Maximize your damage output by focussing on the weakest targets and be aware of threats on the enemy team. Good positioning and awareness is often the deciding factor in a teamfight."
    if tip == "conversion_tip":
        return "Winning the lane doesn't automatically win you the game! Convert your lane advantage by roaming to other lanes and helping your teammates win their matchup as well."
    if tip == "monster_objective_tip":
        return "Dragons, Heralds and Barons give your team valuable stats and resources to put immense pressure on your opponents. Don't let the enemy get away with taking them too easily! Take more note of the objective timers and adapt your gameplay around them to secure objectives more often."
    if tip == "warding_tip":
        return "Vision is an underrated part of the game. Wards help uncover enemy movement and warn you when they are taking objectives. Buying vision wards and sweeping lenses to obstruct the opponents vision is just as important."
    if tip == "turret_tip":
        return "When you have an advantage on your lane, it is often helpful to destroy your opponents turrets as well. Not only does it supply your team with gold, it also takes away an important defensive structure from your opponents."
    if tip == "bounty_tip":
        return "If you find yourself behind in a match, look out for bounties! Bounties give you and your team large amounts of gold to fight for a comeback. You should also be wary of when there's a bounty on you, as this might be a reason to play more cautiously."
    if tip == "ping_tip":
        return "Learn the different commands on the ping wheel so you can quickly and effectively communicate with your team. A timely ping can save teammates from a roaming opponent or indicate the next game winning play!"
    if tip == "spend_tip":
        return "Having lots of gold is great, but its only helpful if you spend it on items. Finding the right moment to return to base and buying the next powerful item is an important skill to learn."

# display tips
if 'puuid' in st.session_state:
    col1, col2, col3 = st.columns(3)
    with col2:
        st.title("Gameplay Hints")

    

    timeline_data = load_data(st.session_state['puuid'], st.session_state['continent'], st.session_state['ranked_only'], AMOUNT_GAMES)

    if not timeline_data:
        if st.session_state['ranked_only']:
            
            st.write("Could not find any ranked games in your recent match history")
        else:
        
             st.write("Could not find any summoners rift games in your recent match history")
    
    else:
        st.markdown("""---""")
        selected_tips = select_tips(timeline_data, st.session_state['puuid'])
        sorted_tips = [key for key, value in Counter(selected_tips).most_common()]

        if len(sorted_tips) == 0:
            st.write("No gameplay hints available")

        for i in range(len(sorted_tips)):
            if i >= 5:
                break

            if i % 2 == 0:
                tip_col1, tip_col2 = st.columns([1, 2])
            else:
                tip_col2, tip_col1 = st.columns([2, 1])
            

            tip_col1.image(get_image_for_tip(sorted_tips[i]))
            with tip_col2:
                st.header(get_header_for_tip(sorted_tips[i]))
                st.write(get_message_for_tip(sorted_tips[i]))
            
            st.markdown("""---""")

else:
    st.write("please enter your username on the login screen")
