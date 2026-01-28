# Importing libraries necessary
import streamlit as st

# Initalises session state variables
session_variable_list = [['token_info', None],
                         ['rec_page_state', None],
                         ['search_results', None],
                         ['selections', {}],
                         ['playlist_page', 1],
                         ['search_results', None], 
                         ['feature_weights', None], 
                         ['num_recommended_songs', None],
                         ['rec_name', None],
                         ['genre_input', None],
                         ['recommended_songs', None],
                         ['recommended_selections', {}],
                         ['saved_rec_page_state', None]]

for session_variable_and_value in session_variable_list:
    st.session_state.setdefault(session_variable_and_value[0], session_variable_and_value[1])

# Clears token from session, to let users log-out of their accounts
def logout():
    # Clears access token & therefore ability to authenticate the client
    st.session_state["token_info"] = None

    # Reruns to clear the authenticated client & show the login page
    st.rerun()

# Selects correct pages to show to user, depending on authentication status
if st.session_state["token_info"] == None:
    # Selects this if the user isn't authenticated
    pg = st.navigation([st.Page("page_folder/login_page.py", title="Login", icon=":material/login:")])
else:
    # Selects this if the user is authenticated
    pg = st.navigation([st.Page("page_folder/welcome_page.py", title="Welcome", icon=":material/home:"),
                        st.Page("page_folder/recommendation_manager.py", title="Recommendations", icon=":material/recommend:"),
                        st.Page("page_folder/saved_recommendations_page.py", title="Saved Recommendations", icon=":material/history:"),
                        st.Page(logout, title="Log out", icon=":material/logout:")])

# Running the navigation code to be able to display pages
pg.run()