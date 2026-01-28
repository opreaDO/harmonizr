# Importing libraries & modules needed
import streamlit as st
import spotipy
from datetime import datetime
from db_manager import db
from validation import validate_rec_name

# Sets session variables to default
if st.session_state["saved_rec_page_state"] is None:
    st.session_state["saved_rec_page_state"] = "pre_selection"
    st.session_state["rec_page_state"] = None

# Displays all recommendation a user has saved
def display_generated_recommendations(recommendation_list):
    st.write(" ")
    with st.container():
        # Creates columns needed to display header
        rec_name_column, timestamp_column, buttons_column = st.columns([0.4, 0.3, 0.25], 
                                                                       vertical_alignment="center", 
                                                                       gap="small")

        # Displays rec_name header
        with rec_name_column:
            st.markdown(
            "<div style='text-align: left;'>"
            "<h5>Recommendation Name</h5>"
            "</div>",
            unsafe_allow_html=True,
        )
    
        # Displays timestamp header
        with timestamp_column:
            st.markdown(
                "<div style='text-align: left;'>"
                "<h5>Time Created</h5>"
                "</div>",
                unsafe_allow_html=True,
            )

        # Displays buttons header
        with buttons_column:
            st.markdown(
                "<div style='text-align: left;'>"
                "<h5>Edit Options</h5>"
                "</div>",
                unsafe_allow_html=True,
            )

        # Displays line in between headers & content
        st.markdown("<hr style='margin-top: 0rem; margin-bottom: 0rem;'>", unsafe_allow_html=True)

    # Now iterates through recommendations
    for recommendation in recommendation_list:
        with st.container():
            # Defines columns for all options a user has
            rec_name_column, timestamp_column, edit_column, delete_column = st.columns([0.4, 0.3, 0.10, 0.15], 
                                                                                       vertical_alignment="center", 
                                                                                       gap="small")

            # Defines a 'button', which the user can press to forward them to the recommendation page
            rec_name_column.button(label=recommendation[1],                         # Label = rec_name
                                   type='tertiary',                                 # Button just shows as text
                                   on_click=forward_to_rec_page,                    # Callback for when button is pressed
                                   key = f"{recommendation[0]}_rec_name",           # Key for each button
                                   args=[recommendation[2], recommendation[1]])     # Songs & rec_name to show to user

            # Showing the correct timestamp to the user
            timestamp_date = recommendation[3].strftime("%d-%m-%Y")
            timestamp_time = recommendation[3].strftime("%H:%M")
            timestamp_column.markdown(timestamp_date + "&nbsp;&nbsp;&nbsp;&nbsp;" + timestamp_time)

            # Defines an edit button to show to the user
            edit_column.button(label="Edit",                        # Label for the button
                               key = f"{recommendation[0]}_edit",   # Unique key for a button
                               on_click=edit_recommendation_name,   # Callback for when button is pressed
                               args=[recommendation[0]])            # Unique rec_id passed into callback function
            
            delete_column.button(label="Delete",                                # Label for the button
                                 key = f"{recommendation[0]}_delete",           # Unique key for a button
                                 on_click=deleting_recommendation_dialog_box,   # Callback for when button is pressed
                                 args=[recommendation[0]])                      # Unique rec_id passed into callback function
            
# Forwards user to recommendation they selected
def forward_to_rec_page(song_id_list, rec_name):
    # Sets session variables, for view rec' page to display correct songs & rec name
    st.session_state["recommended_songs"] = song_id_list[0]
    st.session_state["rec_name"] = rec_name

    # Sets page session variables, to forward user to the correct page
    st.session_state["rec_page_state"] = "show_recommendations"
    st.session_state["saved_rec_page_state"] = "post_selection"

# Edit dialog box code
@st.dialog("Edit Recommendation")
def edit_recommendation_name(rec_id):
    # Gets user info from Spotify
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()
    user_id = user["id"]

    # Set the logo to show on the sidebar
    st.logo("logo_white.svg", size="large")

    # Placeholder for an error
    error_placeholder = st.empty()

    # New name input
    new_name = st.text_input(label="What would you like to rename your recommendation to? ")

    # Defines a submit button
    if st.button(label="Submit", type="primary"):
        try:
            # Tries to validate the new name
            new_name = validate_rec_name(new_name, user_id)

            # Updates the name in the database
            db.change_user_recommendation_name(rec_id, new_name)

            # Reruns streamlit, to close the dialog box
            st.rerun()
        except ValueError as e:
            # Reports back an error if there is one
            error_placeholder.error(str(e))

# Delete dialog box code
@st.dialog("Deleting Recommendation")
def deleting_recommendation_dialog_box(rec_id):
    # Set the logo to show on the sidebar
    st.logo("logo_white.svg", size="large")

    # Warning for if the user wants to proceed
    st.write("Are you sure you want to proceed? You will not be able to recover these recommendations once you delete them.")

    # Defines columns for buttons
    delete_button_col, cancel_button_col = st.columns([0.2, 0.8], vertical_alignment="center", gap="medium")

    # Defines actions for the delete button
    if delete_button_col.button(label="Delete", type="primary"):
        # Removes the recommendation from the database & reruns the program
        db.delete_user_recommendation(rec_id)
        st.rerun()
    if cancel_button_col.button(label="Cancel"):
        # Reruns, to quit the dialog box
        st.rerun()

# Main function for this page
def main():
    # Fetch sp object to get user info
    sp = spotipy.Spotify(auth=st.session_state["token_info"])
    user = sp.current_user()

    # UI Elements (title and sidebar logo)
    st.title("Saved Recommendations")
    st.logo("logo_white.svg", size="large")

    # Generates a list of tuples, with details of each recommendation
    recommendation_list = db.get_user_recommended_tracks(user["id"])
    display_generated_recommendations(recommendation_list)

    # Forwarding user if a song has been selected
    if st.session_state["saved_rec_page_state"] == "post_selection":
        st.session_state["recommended_selections"] = {}
        st.switch_page("page_folder/recommendation_manager.py")

main()