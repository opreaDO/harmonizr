# Import libraries & modules necessary
import streamlit as st
from page_folder.recommendation_pages.search_page import search_tab_func
from page_folder.recommendation_pages.library_page import library_tab_func
from page_folder.recommendation_pages.playlist_checker_page import playlist_checker_page
from page_folder.recommendation_pages.preference_page import preference_page
from page_folder.recommendation_pages.view_recommendations_page import view_recommendations_page
from recommendation_engine import rec_engine
import spotipy

def display_selected_tracks():
    # Display a header for the section that shows the user's current selections
    st.subheader("Currently Selected Tracks/Playlists")

    # Get the current selections (a dictionary) from Streamlit's session state
    selections = st.session_state["selections"]
    
    # Convert the dictionary of selections into a list of (id, item) pairs
    selection_items = list(selections.items())

    # Create a container to group the displayed selections
    with st.container():
        # Iterate over each selected track or playlist
        for idx, (track_playlist_id, track_playlist) in enumerate(selection_items):
            # Create another container for each item to keep layout consistent
            with st.container():
                # Define a layout with four columns: image, track/playlist name, artist/owner name, and an unselect checkbox
                image_column, track_column, artist_column, select_column = st.columns(
                    [0.125, 0.375, 0.3, 0.2], vertical_alignment="center", gap="medium"
                )

                # Display the appropriate image based on whether it's a track or playlist
                if track_playlist["type"] == "track":
                    image_column.image(track_playlist['album']['images'][0]['url'])
                elif track_playlist["type"] == "playlist":
                    image_column.image(track_playlist['images'][0]['url'])

                # Display the name of the track or playlist
                track_column.text(track_playlist["name"])

                # Display the artist (for a track) or owner (for a playlist)
                if track_playlist["type"] == "track":
                    artist_column.text(track_playlist["artists"][0]["name"])
                elif track_playlist["type"] == "playlist":
                    artist_column.text(track_playlist["owner"]["display_name"])
                
                # Add a checkbox to allow the user to unselect this track/playlist
                # If checked, remove the item from selections and refresh the app
                if select_column.checkbox("Unselect", key=f"unselect_{track_playlist["id"]}"):
                    del (st.session_state["selections"])[track_playlist["id"]]
                    st.rerun()

# Finds if there are any playlists in the user's selections
def playlist_in_selections(selection_dict):
    # Pulls all items in selections (dictionaries, not the ids)
    selection_items = list(selection_dict.items())

    # Returns true if any playlists are found
    for (selection_id, selection) in selection_items:
        if selection["type"] == "playlist":
            return True
        
    # Returns false if list is empty, or only songs are present
    return False

# Decides on what page to forward user from the song selector page, depending on their selections
def song_selector_continue_button_actions():
    if playlist_in_selections(st.session_state["selections"]):
        # Will forward user to the playlist warning page, if playlists are found
        st.session_state["rec_page_state"] = "playlist_checker"
    else:
        # Will forward user to the preference page, if only sons are selected
        st.session_state["rec_page_state"] = "preferences"

# Sets session variables to default, if the page has just been clicked on (set to None/empty on other pages)
# Refreshes of the page don't cause this to run
if st.session_state["rec_page_state"] is None:
    st.session_state["rec_page_state"] = "song_selection"   # Sets default to selecting songs for rec'dations
    st.session_state["search_results"] = None               # Resets search results if user clicks off & back on
    st.session_state["selections"] = {}                     # Resets selections if user clicks off & back on
    st.session_state["playlist_page"] = 1                   # Resets playlist page to 1st page
    st.session_state["feature_weights"] = None              # Resets all user selected feature weights
    st.session_state["num_recommended_songs"] = None        # Resets number of songs user wants recommended
    st.session_state["genre_input"] = None                  # Resets genre inputted on preference page
    st.session_state["rec_name"] = None                     # Resets recommendation name inputted
    st.session_state["recommended_songs"] = None            # Resets recommended song id list
    st.session_state["recommended_selections"] = {}         # Resets recommended songs the user has selected

st.session_state["saved_rec_page_state"] = None

# Song selection pages defined here
if st.session_state["rec_page_state"] == "song_selection":
    # Defines tabs at the top
    search_tab, library_tab = st.tabs(["Search", "Library"])
    
    # Defines what runs when each tab is selected
    with search_tab:
        search_tab_func()
    with library_tab:
        library_tab_func()

    # Display selected tracks & playlists to the user, if they have any selected
    if st.session_state["selections"]:
        display_selected_tracks()
        st.button("Continue", type="primary", on_click=song_selector_continue_button_actions, key="song_selection_continue")
    
elif st.session_state["rec_page_state"] == "playlist_checker":
    # Forwards user to the playlist checker page
    playlist_checker_page()

elif st.session_state["rec_page_state"] == "preferences":
    # Forwards user to the preferences page
    preference_page()

elif st.session_state["rec_page_state"] == "show_recommendations":
    # If no songs generated yet, this runs
    if st.session_state["recommended_songs"] is None:
        # Fetch sp object to get user info
        sp = spotipy.Spotify(auth=st.session_state["token_info"])
        user = sp.current_user()

        # Spinner while recommendations are generated
        with st.spinner("Generating Recommendations"):
            # Pulls songs the user selected to base recommendations off previously, from session
            selections = st.session_state["selections"]

            # Generates a list of songs, based on song_id's (keys of dictionary)
            song_id_list = list(selections.keys())

            # Pulls user selected weights & number of songs from session
            weights = st.session_state["feature_weights"]
            num_songs = st.session_state["num_recommended_songs"]
            genre = st.session_state["genre_input"]
            rec_name = st.session_state["rec_name"]

            # Runs the recommendation engine & saves song ids to session
            recommended_song_id_list = rec_engine.get_recommendations(song_id_list, 
                                                                      genre, 
                                                                      weights, 
                                                                      num_songs, 
                                                                      user["id"], 
                                                                      rec_name)
            st.session_state["recommended_songs"] = recommended_song_id_list   

    view_recommendations_page()