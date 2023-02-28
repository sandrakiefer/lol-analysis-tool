import streamlit as st
import requests

# streamlit run C:\Users\ferdi\PycharmProjects\streamLitUI\main.py
API_KEY = st.secrets["api_key"]

st.set_page_config(layout="wide")

def get_continent(region):
    continents = {"BR1": "americas", "EUN1": "europe", "EUW1": "europe", "JP1": "asia", "KR": "asia", "LA1": "americas", "LA2": "americas", "NA1": "americas", "OC1": "sea", "RU": "europe", "TR1": "europe"}
    return continents.get(region, "europe")

def find_user(lol_region, lol_name, ranked):
    fstr = f"Hello {lol_name}!"
    if lol_name != "":
        url = f"https://{lol_region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{lol_name}?api_key={API_KEY}"
        res = requests.get(url)

        data = res.json()
        if "puuid" not in data:
            st.write("User not found")
        else:
            st.write(fstr)
            if 'continent' not in st.session_state:
                st.session_state['continent'] = get_continent(lol_region)
            else:
                st.session_state['continent'] = get_continent(lol_region)

            if 'puuid' not in st.session_state:
                st.session_state['puuid'] = data['puuid']
            else:
                st.session_state['puuid'] = data['puuid']

            st.session_state['ranked_only'] = ranked
            
            st.write("Analyze your games with the pages located in the left sidebar.")

col1, col2, col3 = st.columns([1, 3.5, 1])

with col2:
    st.title("League of Legends Analysis Tool")
    st.text("Please Input your Username and Region")

    with st.form(key="select_user_form"):
        region = st.selectbox("Region", ["EUW1", "BR1", "EUN1", "JP1", "KR", "LA1", "LA2", "NA1", "OC1", "RU", "TR1"])
        name = st.text_input("Username")
        ranked_only = st.checkbox("Only analyse ranked games")
        st.form_submit_button("Confirm", on_click=find_user(region, name, ranked_only))
