# Importing libraries and modules needed
import streamlit as st
import spotipy
from validation import validate_rec_name, validate_song_limit, feature_weight_validation

# Creates sliders for list of given attribures
def feature_weight_sliders(attribute_list):
    # Iterates through every attribute in list, to create a slider for that
    for attribute in attribute_list:
        st.slider(label=attribute.capitalize(), min_value=0, max_value=200, value=100, key=f"{attribute}_slider", format="%d%%")

# Defines the main function which will run when the preference page loacs
def preference_page():
    # Fetch sp object to get user info
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()

    # UI: Title & Sidebar logo
    st.title("Recommendations Preferences")
    st.logo("logo_white.svg", size="large")

    # Placeholder for error message for validation
    error_message_placeholder = st.empty()

    # Textbox Inputs
    rec_name_col, song_limit_col, genre_col = st.columns(3)
    rec_name_input = rec_name_col.text_input("Recommendation Name")
    song_limit_input = song_limit_col.text_input("Number of Songs", placeholder="Max 20 Songs")
    genre_input = (genre_col.selectbox("Song Genre",
                                      ("Pop", "Rock/Metal", "Electronic/Dance", 'Hip-Hop/R&B', 'Jazz/Blues', 'Classical/Ambient',
                                       'Country/Folk', 'World', 'Soundtrack/Thematic'))).lower()

    # Feature weight headings & sliders
    st.subheader("Feature Weights")
    attribute_list = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
    feature_weight_sliders(attribute_list)

    # Continue button
    if st.button(label="Generate Recommendations", type="primary"):
        try:
            # Pulls feature weights from the sliders
            feature_weights = get_feature_weights(attribute_list)

            # Tries to validate all inputted features
            song_limit_input = validate_song_limit(song_limit_input, 20)
            rec_name = validate_rec_name(rec_name_input, user["id"])
            feature_weight_validation(feature_weights)

            # Adds all validated inputs to session
            st.session_state["feature_weights"] = feature_weights
            st.session_state["num_recommended_songs"] = song_limit_input
            st.session_state["genre_input"] = genre_input
            st.session_state["rec_name"] = rec_name

            # Takes the user to the next page
            st.session_state["rec_page_state"] = "show_recommendations"
            st.rerun()
        except ValueError as e:
            # Prints the error if values couldn't be validated
            error_message_placeholder.error(str(e))

# Function to get values from sliders, given a list of attributes
def get_feature_weights(attribute_list):
    # Defines the weights dictionary
    weights = {}

    # Iterates through every attribute in the list, get their slider value & append it to the dictionary
    for attribute in attribute_list:
        weights[attribute] = (st.session_state[f"{attribute}_slider"]) / 100

    # Returns the weights dictionary
    return weights