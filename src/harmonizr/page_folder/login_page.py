# Importing libraries necessary
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from db_manager import db

# Load .env file
load_dotenv()

# Pull client authentication details from .env file
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Spotify client variables
REDIRECT_URI = "http://localhost:8501"  # Placeholder, as app is currently running locally
SCOPE = "user-library-read user-top-read user-read-recently-played playlist-modify-public"
    
def get_spotify_oauth():
    # Returns Spotify OAuth object, to use for authentication
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = REDIRECT_URI,
        scope = SCOPE
    )

def show_login_page(auth_url):
    # Displays the login page UI Elements

    # Basic/Static UI
    st.image("logo_white.svg")
    st.header("Login")
    st.text("Welcome to Harmonizr. Here you can view your Spotify stats & generate new song recommendations") 
    st.text("In order to use this app you must login with your Spotify account.")

    # Display login link button (TEMPORARY URL, as needed to define a link button)
    st.link_button("🎵 Login with Spotify", auth_url, icon=":material/login:", type="primary")

def handle_spotify_login(sp_oauth):
    # Handles authorisation with Spotify, once the user has logged in with their Spotify account

    # Checks if user isn't authorised on the app yet, but has logged in with Spotify
    if "code" in st.query_params and st.session_state["token_info"] is None:
        try:
            # Exchange authorisation code for token
            code = st.query_params["code"]
            token_info = sp_oauth.get_access_token(code=code, check_cache=False, as_dict=False)

            # Adds token info to session, to be pulled by other pages in the program
            st.session_state["token_info"] = token_info

            # Clear the query parameters to stop the loop
            st.query_params.clear()  # Removes query params
            
        except Exception as e:
            # Outputs an error if it occurs during token exchange
            st.error(f"Error during token exchange: {e}")
            return None
        
        # Returns the token info, to use to get an authenticated Spotify client object
        return st.session_state["token_info"]
    
    # Returns None if the user is already authorised, or if they haven't logged in with Spotify
    return None

def get_spotify_client(token_info):
    # Returns the authenticated Spotify Client Object
    if token_info:
        return spotipy.Spotify(auth=token_info)
    
    # Returns None if there isn't any token info passed in
    return None

def main():
    # Tries to authorise the user, with the Spotify OAuth authorisation flow
    sp_oauth = get_spotify_oauth()
    token_info = handle_spotify_login(sp_oauth)

    if not token_info:
        # ONLY shows login page if no auth token can be pulled i.e. user needs to login
        # Pulls login link for to pass into login page function
        auth_url = sp_oauth.get_authorize_url()
        show_login_page(auth_url)

    else:
        # Gets the Spotify client object, to interact with the API
        sp_client = get_spotify_client(token_info)

        # Pulls the user's details from the API as a test to see if it's correctly authenticated 
        try:
            user = sp_client.current_user()

            # Fetches user details to potentially add to the database
            user_id = user["id"]
            display_name = user["display_name"]

            # Adds the user to the database to the database if this is a first time login 
            db.add_user_to_user_table(user_id, display_name)
            st.rerun()
        except Exception as e:
            # Outputs error if the the program can't add the user to the db, or can't pull the user
            st.error(f"Error occured: {e}")

main() 