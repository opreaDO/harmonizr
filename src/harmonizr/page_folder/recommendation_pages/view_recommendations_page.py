# Importing libraries & modules needed
import streamlit as st
import spotipy

def get_recommended_tracks(sp, song_id_list):
    recommended_track_list = []
    results = sp.tracks(song_id_list)
    recommended_track_list = results['tracks']
    
    return recommended_track_list

def toggle_recommendation_selection(track_id, track):
    # Changes whether or not a song is in the selections dictionary, to change BOTH select & unselect checkboxes
    if track_id in st.session_state["recommended_selections"]:
        del st.session_state["recommended_selections"][track_id]
    else:
        st.session_state["recommended_selections"][track_id] = track

# Creates a playlist and adds songs passed in to it
def add_playlist_to_library(sp, user, song_id_list, playlist_name):
    # Creates the playlist
    new_playlist = sp.user_playlist_create(user["id"], playlist_name, public=True)

    # Adds inputted songs to this new playlist
    new_playlist_id = new_playlist["id"]
    sp.playlist_add_items(new_playlist_id, song_id_list)

# Displays results for recommended tracks, given a recommendation name & track list
def display_recommended_results(track_list, rec_name):
    # Displays the name of the recommendation being displayed
    st.subheader(rec_name)

    with st.container():
        # Iterate through every track in the list
        for idx, track in enumerate(track_list): # idx = track index in track_list
            with st.container():
                # Define columns, to display each of the songs in one row
                image_column, track_column, artist_column, select_column = st.columns([0.125, 0.375, 0.3, 0.2], 
                                                                                      vertical_alignment="center", 
                                                                                      gap="medium")

                try:
                    # Displays the image, if it's available
                    image_column.image(track['album']['images'][0]['url'])
                except:
                    # Displays a warning if no image could be displayed
                    image_column.text("Couldn't pull a image for this track")

                # Displays the name of the track
                track_column.text(track["name"])

                # Displays the name of the main artist for the song
                artist_column.text(track["artists"][0]["name"])

                # Displays the checkbox for this song
                select_column.checkbox("Select",                                                            # Label for what the checkbox does  
                                       key=f"select_{track["id"]}",                                         # Unique identifier for the checkbox
                                       value = track["id"] in st.session_state["recommended_selections"],   # true if in session dictionary, false if not
                                       on_change=toggle_recommendation_selection,                           # function to toggle selected status
                                       args = (track["id"], track))                                         # parameters necessary to toggle the current song                                 
                
# Main function for viewing this page is here
def view_recommendations_page():
    # Fetch sp object to get user info
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()

    # UI Elements (title and sidebar logo)
    st.title("View Recommendations")
    st.logo("logo_white.svg", size="large")

    # Sets position for success/error message, always at the top of the page
    message_placeholder = st.empty()

    # Gets the recommendation name & song ids from session
    rec_name = st.session_state["rec_name"]
    recommended_song_id_list = st.session_state["recommended_songs"]

    # Pulls details about recommended tracks from Spotify, to display to the user
    recommended_track_list = get_recommended_tracks(sp, recommended_song_id_list)

    # Displays songs the rec engine recommended to the user, allowing them to select songs they like
    display_recommended_results(recommended_track_list, rec_name)

    # Pulls all the songs a user has selected, and stores them in a list of song_ids
    recommended_selections = st.session_state["recommended_selections"]
    recommended_selections_id_list = list(recommended_selections.keys())

    # Will only display the button if the user has selected songs, acts as a form of validation
    if recommended_selections_id_list:
        if st.button("Create Playlist", type="primary"):
            try:
                # Call function to add all selected songs to the playlist
                add_playlist_to_library(sp, user, recommended_selections_id_list, rec_name)

                # Tells user the playlist has been added
                message_placeholder.success("New playlist created with selected songs")
            except:
                # Tells the user if an error has occured, tells them to try again
                message_placeholder.error("Error in adding playlist to Spotify. Try again")