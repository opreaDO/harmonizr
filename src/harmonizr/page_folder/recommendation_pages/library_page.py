# Importing libraries & modules needed
import streamlit as st
import spotipy
from math import ceil

# Returns the total number of playlists in the user's Spotify account
def find_num_songs(sp):
    results = sp.current_user_playlists()  # Fetch user's playlists metadata
    num_playlists = results["total"]       # Extract total number of playlists
    return num_playlists

# Retrieves a paginated list of user playlists based on the page number
def get_user_playlists(sp, num_playlists, page):
    offset = (page - 1) * num_playlists     # Calculate the offset for pagination
    results = sp.current_user_playlists(limit=num_playlists, offset=offset)  # Fetch playlists for this page
    playlist_list = results["items"]        # Extract the list of playlists
    return playlist_list

# Adds & deletes playlists from selections dictionary in session
def toggle_selection(playlist_id, playlist=None):
    if playlist_id in st.session_state["selections"]:
        # Deletes if playlist is unselected
        del st.session_state["selections"][playlist_id]
    else:
        # Added if playlist is selected
        st.session_state["selections"][playlist_id] = playlist

# Displays the user's playlists in a structured layout with checkboxes for selection
def display_user_playlists(playlist_list):
    st.subheader("Your Playlists") 

    with st.container():
        for idx, playlist in enumerate(playlist_list):  # Loop through each playlist in the list
            with st.container(): 
                # Define four columns: image, name, author, and selection checkbox
                image_column, name_column, author_column, select_column = st.columns(
                    [0.125, 0.375, 0.3, 0.2],  # Proportions of each column
                    vertical_alignment="center",  # Vertically center contents in columns
                    gap="medium"  # Space between columns
                )

                # Display the playlist image if one exists
                if playlist["images"]:
                    image_column.image(playlist['images'][0]['url'])

                # Display the playlist name
                name_column.text(playlist["name"])

                # Display the playlist owner's display name
                author_column.text(playlist["owner"]["display_name"])

                # Display a checkbox to allow the user to select or deselect the playlist
                select_column.checkbox(
                    "Select",  # Label for the checkbox
                    key=f"select_{playlist['id']}",                             # key to track the checkbox state
                    value=playlist["id"] in st.session_state["selections"],     # Make sure value matches w/ selected status
                    on_change=toggle_selection,                                 # function to toggle selected status
                    args = (playlist["id"], playlist))                          # parameters necessary to toggle the current song
                
# Handles pagination controls for navigating through pages of playlists
def paginate_content(num_playlists_per_page, total_playlists):
    # Get the current page from session
    current_page = st.session_state["playlist_page"]
    
    # Create columns for the pagination UI: Previous button, current page display, Next button
    previous_page_col, current_page_col, next_page_col = st.columns(
        [0.375, 0.475, 0.15], 
        vertical_alignment="center"  
    )

    # Show previous button if the user is not already on the first page
    if current_page != 1:
        if previous_page_col.button(label="Previous", type="primary"):  # Render a button in the first column
            # Decrements the page if the button is pressed
            current_page -= 1
            st.session_state["playlist_page"] = current_page 
            st.rerun()  # Rerun the app to show the new page

    # Calculate the maximum number of pages needed
    max_pages = ceil(total_playlists / num_playlists_per_page)

    # Display the current page number, if there is more than one page of playlists to display
    if max_pages > 1:
        current_page_col.write(f"Current Page: {current_page}")

    # Show "Next" button if the user is not already on the last page
    if current_page != max_pages:
        if next_page_col.button(label="Next", type="primary"):
            # Increments the page if the button is pressed
            current_page += 1 
            st.session_state["playlist_page"] = current_page  
            st.rerun()  # Rerun the app to show the new page


# Runs when the library tab is selected
def library_tab_func():
    # Fetch sp object to get user info
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()

    # UI: Title & Sidebar logo
    st.title("Recommendations")
    st.logo("logo_white.svg", size="large")

    # Handles pulling playlists from user, for the current page selected
    num_playlists_per_page = 10
    total_playlists = find_num_songs(sp)
    playlist_list = get_user_playlists(sp, num_playlists_per_page, st.session_state["playlist_page"])

    # Displays the current page
    display_user_playlists(playlist_list)

    # Shows pagination UI & updates current page
    paginate_content(num_playlists_per_page, total_playlists)