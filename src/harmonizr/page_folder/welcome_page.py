# Importing libraries necessary
import streamlit as st
import spotipy
from collections import Counter
from datetime import datetime, timezone

# Returns a list w/ needed attributes of a user's top songs
def get_top_tracks(sp, num_tracks, chosen_time_frame):
    # Pulls the user's top tracks
    top_tracks = sp.current_user_top_tracks(limit=num_tracks, time_range=chosen_time_frame)

    top_track_list = []

    for idx, track in enumerate(top_tracks['items']): # Iterate through every song to extract data needed
        # List Strucutre: [[name_1, artists_1, image_url_1], [name_2, ...], ...]
        top_track_list.append([])
        top_track_list[idx].append(track['name'])                           # Adds each song name to the list
        top_track_list[idx].append(track['artists'][0]['name'])             # Adds main artist to the list
        top_track_list[idx].append(track['album']['images'][0]['url'])      # Adds URL of song's cover art

    return top_track_list

# Show tracks, given a track list
def display_top_tracks(track_list):
    # Gets the number of tracks, to define the right number of columns to display to the user
    num_tracks = len(track_list)
    columns = st.columns(num_tracks, vertical_alignment="top")

    # Iterates through every column/track to be displayed
    for idx, column_x in enumerate(columns): # idx = track index in track_list
        try:
            # Tries to show the image to the user, if it's there
            column_x.image(track_list[idx][2])
        except:
            # If it can't be shown, a warning is displayed to them instead
            column_x.text("Couldn't pull an image for this track")

        # Writes the song's name
        column_x.write(track_list[idx][0])

        # Writes the song's main artist
        column_x.write(track_list[idx][1])

# Returns a list w/ needed attributes of a user's top artists
def get_top_artists(sp, num_artists, chosen_time_frame):
    # Pulls the user's top artists
    top_arists = sp.current_user_top_artists(limit=num_artists, time_range=chosen_time_frame)

    top_artists_list = []
    
    for idx, artist in enumerate(top_arists["items"]): # Iterate through every artist to extract data needed
        # List Strucutre: [[name_1, image_url_1], [name_2, ...], ...]
        top_artists_list.append([])
        top_artists_list[idx].append(artist["name"])                # Adds each arist name to the list
        top_artists_list[idx].append(artist["images"][0]["url"])    # Adds each picture URL to the list
        
    return top_artists_list

# Show tracks, given a track list
def display_top_artists(artist_list):
    # Gets the number of tracks, to define the right number of columns to display to the user
    num_artists = len(artist_list)
    columns = st.columns(num_artists, vertical_alignment="top")

    for idx, column_x in enumerate(columns): # idx = track index in track_list
        # Defines HTML & CSS for displaying the image
        image_html = f"""
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 10%;">
            <div style="aspect-ratio: 1; overflow: hidden; position: relative; border-radius: 8px;">
                <img src="{artist_list[idx][1]}" 
                     alt="{artist_list[idx][0]}" 
                     style="width: 100%; height: 100%; object-fit: cover;">
            </div>
        </div>"""

        try:
            # Tries to show the image to the user, if it's there
            column_x.markdown(image_html, unsafe_allow_html=True)  
        except:
            # If it can't be shown, a warning is displayed to them instead
            column_x.text("Couldn't pull an image for this artist")   

        # Writes the artists name
        column_x.write(artist_list[idx][0])

# Pulls the user's top genres
def get_top_genres(sp, num_genres, chosen_time_frame):
    # Pulls the user's top artists
    top_artists = sp.current_user_top_artists(limit=50, time_range=chosen_time_frame)
    
    genres = []
    for artist in top_artists["items"]:
        # Appends all genres associated to the artist currenly being processed to the list 
        genres.extend(artist["genres"])
    
    # Finds how many times each genre is in the list (creates a dictionary, key = genre, value = count)
    genre_counts = Counter(genres)

    # Returns the top 'num_genres' genres
    top_genres = genre_counts.most_common()
    return top_genres[0:num_genres]

# Displays the user's top genres to the user
def display_top_genres(top_genres):    
    # HTML & CSS for pill styling (to display horizontally)
    pill_html = """
    <style>
    .pill-container {
        display: flex;
        flex-wrap: wrap;  /* Allow pills to wrap to the next line if necessary */
        gap: 10px;  /* Space between pills */
        margin-bottom: 10px;
    }
    
    .pill {
        padding: 8px 16px;
        background-color: #262730;
        border-radius: 25px;
        color: #fafafa;
        font-weight: bold;
        font-size: 14px;
    }
    </style>
    """

    # Inject HTML styling
    st.markdown(pill_html, unsafe_allow_html=True)

    # Create a container to hold all the pills in a row
    pill_container_html = '<div class="pill-container">'

    # Loop through the genres and display each one as a pill
    for genre, count in top_genres:
        pill_container_html += f'<span class="pill">{genre}</span>'
    
    pill_container_html += '</div>'

    # Display the pills in the container
    st.markdown(pill_container_html, unsafe_allow_html=True)

# Pulls the users most recently played tracks from Spotify
def get_recently_played(sp, num_songs):
    # Pulls their most recently played songs from the API
    recently_played = (sp.current_user_recently_played(limit=num_songs))["items"]
    recently_played_list = []

    # Iterate through every track to extract data needed
    for idx, track in enumerate(recently_played):
        # List Strucutre: [[image_url_1, name_1, artist_1, time_stamp_1], [image_url_2, ...], ...]
        recently_played_list.append([])
        recently_played_list[idx].append(track["track"]["album"]["images"][0]["url"])   # Appends the image URL          
        recently_played_list[idx].append(track["track"]["name"])                        # Appends the songs name
        recently_played_list[idx].append(track["track"]["artists"][0]["name"])          # Appends the song's main artist
        recently_played_list[idx].append(track["played_at"])                            # Appends when the song was played

    # Returns the processed list of recently played tracks
    return recently_played_list
    
# Returns string of how long ago a track was played
def find_time_difference(date_time):
    # Finds datetime object for the difference of time, UTC used as this is what Spotify uses
    current_date_time = datetime.now(timezone.utc)
    date_time = date_time.replace(tzinfo=timezone.utc) 
    difference = current_date_time - date_time

    # If time difference is less than a minute
    if (difference.seconds < 60):
        return "Now"
    
    # If time difference is in between 1 min & an hour
    elif (difference.seconds >= 60) and (difference.seconds < 3600):
        mins_ago = difference.seconds // 60 # Convert seconds to minutes
        return str(mins_ago) + f" minute{'s' if (mins_ago != 1) else ''} ago" # Handles pluralisation
    
    # If time difference is in between 1 & 24 hours
    elif (difference.seconds >= 3600) and (difference.days == 0):
        hrs_ago = difference.seconds // 3600 # Convert seconds to hours
        return str(hrs_ago) + f" hour{'s' if (hrs_ago != 1) else ''} ago" # Handles pluralisation
    
    # If time difference is more than 24 hours
    else:
        days_ago = difference.days
        return str(days_ago) + f" day{'s' if (days_ago != 1) else ''} ago" # Handles pluralisation

# Displays a list of recently played tracks using Streamlit UI components
def display_recently_played(tracks):
    with st.container():
        # Loop through each track in the list, with its index
        for idx, track in enumerate(tracks):  # idx = track index in track list
            # Container for an individual track row
            with st.container():
                # Create 4 columns with specific widths and alignment for layout
                image_column, track_column, artist_column, timestamp_column = st.columns(
                    [0.15, 0.375, 0.275, 0.2], vertical_alignment="center", gap="medium"
                )
        
                image_column.image(track[0]) # Display album art or track image
                track_column.text(track[1])  # Display track name
                artist_column.text(track[2]) # Display artist name

                # Extract and parse timestamp string into a datetime object
                timestamp = track[3]
                date_time = datetime(
                    year=int(timestamp[0:4]),
                    month=int(timestamp[5:7]),
                    day=int(timestamp[8:10]),
                    hour=int(timestamp[11:13]),
                    minute=int(timestamp[14:16]),
                    second=int(timestamp[17:19]))

                # Display how long ago the track was played using helper function
                timestamp_column.text(find_time_difference(date_time))

def display_recently_played(tracks):
    with st.container():
        for idx, track in enumerate(tracks): # idx = track index in track_list
            with st.container():
                image_column, track_column, artist_column, timestamp_column = st.columns([0.15, 0.375, 0.275, 0.2], vertical_alignment="center", gap="medium")
                image_column.image(track[0])
                track_column.text(track[1])
                artist_column.text(track[2])
                timestamp = track[3]
                date_time = datetime(year=int(timestamp[0:4]), month=int(timestamp[5:7]),
                                     day=int(timestamp[8:10]), hour=int(timestamp[11:13]),
                                     minute=int(timestamp[14:16]), second=int(timestamp[17:19]))
                timestamp_column.text(find_time_difference(date_time))

# Formatting for time-frame options in selectbox
def timeframe_formatting(text):
    # Checks each time-frame, and converts it accordingly
    if text == "short_term":
        return "Short Term (4 weeks)"
    elif text == "medium_term":
        return "Medium Term (6 months)"
    elif text == "long_term":
        return "Long Term (Lifetime)"
    else:
        # Returns None, if no valid time-frame is passed in
        return None

def main():
    # Displays the UI & calls functions to get & display recommendations

    # Resets state of rec'dation page, in case user clicks off it
    st.session_state["rec_page_state"] = None

    # Basic UI elements
    st.title("Welcome")
    st.logo("logo_white.svg", size='large')

    # Fetch sp object to get user info
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()

    # Shows the user their display name, to make sure they're logged in with the right account
    st.success(f"Logged in as {user['display_name']}")

    # Sets up columns to place time frame selectbox inline w/ most played tracks header
    subheader_col, timeframe_col = st.columns([0.7, 0.3], vertical_alignment="center")

    # Displays the time-frame selectbox
    time_frame = timeframe_col.selectbox("Time Frame",
                                ('short_term', 'medium_term', 'long_term'),
                                format_func=lambda x: timeframe_formatting(x))

    # Displays their most played tracks
    subheader_col.subheader("Your Most Played Tracks")
    display_top_tracks(get_top_tracks(sp, 5, time_frame)) 

    # Displays their top artists
    st.subheader("Your Top Artists")
    display_top_artists(get_top_artists(sp, 5, time_frame)) 

    # Displays their top artists
    st.header("Your Top Genres")
    display_top_genres(get_top_genres(sp, 20, time_frame)) 

    # Displays most recently played tracks
    st.header("Recently Played Tracks")
    display_recently_played(get_recently_played(sp, 5))

main()