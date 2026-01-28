# Importing libraries & modules needed
import streamlit as st
import spotipy
from math import ceil
from db_manager import db

# Returns a list of all playlists passed into the function
def split_playlists_into_songs(sp, selections_dict):
    # Max number of items Spotify allows per playlist_items call
    QUERY_LIMIT = 100
    playlist_items = {}

    # Loop through all selected items and process playlists
    for selection_id, selection in selections_dict.items():
        if selection["type"] == "playlist":
            num_songs = selection["tracks"]["total"]
            num_pages = ceil(num_songs / QUERY_LIMIT)

            track_list = []

            # Paginate through playlist tracks
            for pagination in range(num_pages):
                offset = pagination * QUERY_LIMIT
                result = sp.playlist_items(selection_id, offset=offset)

                # Collect track data from each page
                for song in result["items"]:
                    track_list.append(song["track"])

            playlist_items[selection_id] = track_list

    # Return mapping from playlist ID to list of tracks
    return playlist_items

# Function to return songs both in, and not in the database
def get_songs_in_db(track_list):
    # Initialising lists needed
    song_id_list = []
    present_track_list = []
    deleted_track_list = []

    # For rare case when some items in the list are empty, removes these items
    track_list = list(filter(lambda x: x is not None, track_list)) 

    # Builds a list of song id's in the filtered track list
    for track in track_list:
        song_id_list.append(track["id"])

    # Query DB for which song IDs already exist
    result = db.get_song_attributes(song_id_list, column_list=["song_id"])

    # Formats result to get a list of songs
    present_song_id_list = [row[0] for row in result]

    # Separate tracks based on presence in DB
    for track in track_list:
        if track["id"] in present_song_id_list:
            present_track_list.append(track)
        else:
            deleted_track_list.append(track)

    # Returns both lists of songs in, and not in the database
    return present_track_list, deleted_track_list    

# Removes a playlist from the selections dictionary, and adds the items passed in
def update_selections(playlist_id, updated_track_list):
    # Pulls selections dictionary from session
    selections = st.session_state["selections"]

    # Deletes the playlist passed in
    del st.session_state["selections"][playlist_id]

    # Adds all the tracks passed in to the 
    for track in updated_track_list:
        selections[track["id"]] = track

# Displays a list of songs, w/ their image, track name and artists, given a list of track dictionaries
def display_songs(track_list):
    with st.container():
        # Iterates through every song in the list
        for idx, track in enumerate(track_list): # idx = track index in track_list
            with st.container():
                # Defines columns for displaying each song in one row
                image_column, track_column, artist_column = st.columns([0.15, 0.6, 0.3], vertical_alignment="center", gap="medium")

                # Displaying images w/ error handling
                try:
                    image_column.image(track['album']['images'][0]['url'])
                except:
                    image_column.write("Couldn't pull the image for this track")

                # Track & artist names being displayed
                track_column.text(track["name"])
                artist_column.text(track["artists"][0]["name"])

def display_playlist_warning(playlist_name, songs_in_db, songs_not_in_db):
    # Shows the subheader for each name
    st.subheader(playlist_name)

    # Finds number of songs that had to be deleted (used later)
    num_deleted_songs = len(songs_not_in_db)
    num_present_songs = len(songs_in_db)
    num_total_songs = num_deleted_songs + num_present_songs

    # If all songs are in the db
    if songs_not_in_db == []:
        st.success("All songs in this playlist are in the database")

    # If only some songs are in the db (some are, but some also have to be deleted)
    elif songs_in_db:
        st.warning(f"Not all songs in this playlist are available. {num_deleted_songs} out of" \
                   f" {num_total_songs} songs had to be removed. See below")

        # Displays songs which were & weren't deleted
        with st.expander("Songs available"):
            display_songs(songs_in_db)
        with st.expander("Songs not available"):
            display_songs(songs_not_in_db)

    # Error if no songs were present in the db
    else:
        st.error("No songs in this playlist were found in the database")

# Defines actions for what to do when a button on this page is pressed
def playlist_checker_button_action(new_rec_page_state):
    # Clears selections if user wants to return
    if new_rec_page_state == "song_selection":
        st.session_state["selections"] = {}

    # Forwards user to the new page
    st.session_state["rec_page_state"] = new_rec_page_state

def display_overall_warning(error_placeholder, songs_deleted):
    # As long as the user has some selections, this will run, and let the user continue
    if st.session_state["selections"]:
        # Runs if some songs did have to be deleted
        if songs_deleted:
            # Shows the correct warning, for only some songs being available
            error_placeholder.warning("Not all songs selected are in playlists, but you still " \
            "have some valid selections, so you can proceed if you wish")

            # Define columns for buttons
            continue_col, return_col, empty_col = st.columns([0.175, 0.3, 0.525])
            empty_col.empty()

            continue_col.button("Continue", type="primary", on_click=playlist_checker_button_action, args=["preferences"])
            return_col.button("Return", type="secondary", on_click=playlist_checker_button_action, args=["song_selection"])

        # Runs if no songs had to be deleted
        else:
            # Shows the correct message, for all songs being available
            error_placeholder.success("All songs you have selected are in the database")

            # Shows the button to continue
            st.button("Continue", type="primary", on_click=playlist_checker_button_action, args=["preferences"])


    # Runs if no songs were present in the database, for any selections
    else:
        # Shows the correct errror, for no songs being available
        error_placeholder.error("No songs you have selected are in the database. Please go back and select new songs/playlists")

        # Shows the button to return
        st.button("Return", type="primary", on_click=playlist_checker_button_action, args=["song_selection"])

# Function to display the page itself & run all the functions needed
def playlist_checker_page():
    if st.session_state.get("rec_page_state") != "playlist_checker":
        return  # Don't run this page if user just navigated away

    # Fetch sp object to get user info
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()

    # Basic UI Elements
    st.title("Playlist Warning")
    st.logo("logo_white.svg", size="large")

    # Placeholder for where main error, about overall state of selections will go
    error_placeholder = st.empty()
    songs_deleted = False

    # Splits playlists into their individual songs
    playlist_selections = split_playlists_into_songs(sp, st.session_state["selections"])
    for playlist_id, track_list in playlist_selections.items():
        # Gets songs in & not in the database, for the playlist currently being processed
        songs_in_db, songs_not_in_db = get_songs_in_db(track_list)
        playlist_name = (st.session_state["selections"])[playlist_id]["name"]

        # Sets songs_deleted to true if songs had to be deleted, for later
        if songs_not_in_db:
            songs_deleted = True

        # Updates the selection dictionary as necessary
        update_selections(playlist_id, songs_in_db)

        # Displays the warning for the playlist being processed to the user
        display_playlist_warning(playlist_name, songs_in_db, songs_not_in_db)
    
    display_overall_warning(error_placeholder, songs_deleted)