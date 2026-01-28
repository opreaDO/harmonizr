# Importing libraries needed
import streamlit as st
import spotipy
from db_manager import db
from validation import validate_song_name_and_artist, validate_song_limit

# Searches for songs
def song_search(sp, song_limit, song_name = "", artist_name = ""):
    # Tries to validate inputs
    try:
        validate_song_name_and_artist(song_name, artist_name)   # Song & artist validation
        song_limit = validate_song_limit(song_limit, 50)        # Song limit validation
    except ValueError as e:
        # Outputs the error & quits the function if validation fails
        st.error(str(e))
        return

    # Build the search query based on the song and/or artist, if they're inputted
    query = ""

    if song_name:
        query += f"track:{song_name} "
    if artist_name:
        query += f"artist:{artist_name} "

    # Constants for pagination and API limitations
    QUERY_LIMIT = 50  # Max number of tracks returned per API call
    num_songs_found = 0  # Count of valid songs found
    max_paginations = 5  # Maximum number of paginated API calls
    paginations = 0  # Current pagination count
    track_list = []  # Raw track list from Spotify

    # Loop until enough songs are found or pagination limit is reached
    while (num_songs_found < song_limit) and (paginations < max_paginations):
        # Call Spotify's search API with pagination
        results = sp.search(q=query, type="track", limit=QUERY_LIMIT, offset=(paginations * QUERY_LIMIT))
        for track in results['tracks']['items']:
            track_list.append(track)

        # Deletes songs not in db and duplicates
        present_track_list = get_songs_in_db(track_list)
        unique_track_list = remove_duplicate_songs(present_track_list)

        # Update number of valid songs found and increment pagination
        num_songs_found = len(unique_track_list) 
        paginations += 1

    # If no valid tracks were found, show an error
    if unique_track_list == []:
        st.error("No tracks with your search parameters found")
        return None   

    # Return the final list, trimmed to match the requested song limit
    return unique_track_list[0:song_limit]

# Adds & deletes songs/playlists from selections dictionary in session
def toggle_selection(track_playlist_id, track_playlist=None):
    if track_playlist_id in st.session_state["selections"]:
        # Deletes if song is unselected
        del st.session_state["selections"][track_playlist_id]
    else:
        # Added if song is selected
        st.session_state["selections"][track_playlist_id] = track_playlist
    

# Displays search results, given them in a list
def display_search_results(track_list):
    # Create a container to group all the search results together
    with st.container():
        # Loop through each track and its index in the list of tracks
        for track in track_list:  # idx = index of the track in the list 
            with st.container():  
                # Creating columns to display all content for a song in one row
                image_column, track_column, artist_column, select_column = st.columns(
                    [0.125, 0.375, 0.3, 0.2], vertical_alignment="center", gap="medium"
                )

                try: 
                    # Display the album cover image in the first column
                    image_column.image(track['album']['images'][0]['url'])
                except:
                    # Displays warning if it couldn't show an image
                    image_column.text("No image available for this track")

                # Display the track name in the second column
                track_column.text(track["name"])

                # Display the first listed artist in the third column
                artist_column.text(track["artists"][0]["name"])

                # Display a checkbox in the fourth column to allow selection of the track
                select_column.checkbox("Select",                        # Label for what the checkbox does  
                                       key=f"select_{track["id"]}",     # Unique identifier for the checkbox)
                                       value = track["id"] in st.session_state["selections"],   # true if in session dictionary, false if not
                                       on_change=toggle_selection,      # function to toggle selected status
                                       args = (track["id"], track))                            

# Removes any duplicate song name & artist name pairs passed into it
def remove_duplicate_songs(track_list):
    # This list will store unique [track name, artist name] pairs we've seen
    unique_names_and_artists = []
    
    # This list will store the actual track dicts that are unique
    unique_track_list = []

    for track in track_list:
        # Get the track name and remove leading/trailing whitespace
        track_name = (track["name"]).strip()
        
        # Get the name of the first artist and remove leading/trailing whitespace
        artist_name = (track["artists"][0]["name"]).strip()
        
        # If this track/artist combo hasn't been seen before
        if [track_name, artist_name] not in unique_names_and_artists:
            # Mark it as seen
            unique_names_and_artists.append([track_name, artist_name])
            
            # Add the full track to the list of unique tracks
            unique_track_list.append(track)

    # Return only the unique tracks
    return unique_track_list

# Returns only the songs present in the lookup table
def get_songs_in_db(track_list):
    # Initialize an empty list to store song IDs from the track_list
    song_id_list = []
    
    # Initialize an empty list to store the tracks that are already in the database
    updated_track_list = []
    
    # Loop through each track in the track_list
    for track in track_list:
        # Append the song ID from each track to the song_id_list
        song_id_list.append(track["id"])

    # Query the database to get the song IDs that already exist in the database
    song_ids_in_db = db.get_song_attributes(song_id_list, column_list=["song_id"])
    
    # If the database returns any matching song IDs
    if song_ids_in_db:
        # Extract the song IDs from the query result
        updated_song_id_list = [row[0] for row in song_ids_in_db]
        
        # Loop through each track in the original track_list
        for track in track_list:
            # If the song ID of the track is already in the database, add it to updated_track_list
            if track["id"] in updated_song_id_list:
                updated_track_list.append(track)

    # Return the list of tracks that are already in the database
    return updated_track_list
                

# Main function to display the content in the search tab
def search_tab_func():
    # Fetch sp object to get user info
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()

    # UI: Title & Sidebar logo
    st.title("Recommendations")
    st.logo("logo_white.svg", size="large")

    # Defines columns for search textboxex
    song_column, artist_column, song_limit_column = st.columns(3)

    # Search textboxes
    song_name_input = song_column.text_input("Song Name")
    artist_name_input = artist_column.text_input("Artist Name")
    song_limit_input = song_limit_column.text_input("Number of Songs", 
                                                    placeholder="Max 50 Songs",
                                                    help="This is only a maximum number of songs, as Spotify may not find" \
                                                    " the number of songs that you may want.")

    # Defines columns for search buttons
    search_col, clear_col, empty_col = st.columns([0.175, 0.3, 0.525])

    # Creates empty space on the right, to push buttons closer
    empty_col.empty()

    # Search Button
    if search_col.button("Search 🔍", type="primary"):
        search_results = song_search(sp, song_limit_input, song_name=song_name_input, artist_name=artist_name_input)
        st.session_state["search_results"] = search_results

    # Clear Search Results button
    if clear_col.button("Clear Search Results 🧹"):
        st.session_state["search_results"] = None 

    # Check to see if any search results found, before trying to display them
    if st.session_state["search_results"]:
        st.subheader("Search Results")
        display_search_results(st.session_state["search_results"])