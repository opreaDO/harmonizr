from db_manager import db

# Tries to validate song names & artists
def validate_song_name_and_artist(song_name, artist_name):
    # Remove leading/trailing whitespace from input strings
    song_name = song_name.strip()
    artist_name = artist_name.strip()

    # If both song and artist name are empty, show an error and exit
    if not song_name and not artist_name:
        raise ValueError ("Either a song name or artist must be provided")

# Tries to validate a song limit, given an input & max song limit
def validate_song_limit(song_limit_input, max_song_limit):
    # Sees if the inputted song is a digit value (passed in as a string initally)
    if (type(song_limit_input) == str) and (not song_limit_input.isdigit()):
        raise ValueError(f"The number of songs must be an integer between 1 and {max_song_limit}.")
    
    # Casts the song limit to an integer to carry out the range check
    song_limit_input = int(song_limit_input)

    # Range check, between 1 & max song limit (inclusively)
    if song_limit_input not in range(1, max_song_limit + 1):
        raise ValueError(f"The number of songs must be between 1 and {max_song_limit}.")
    
    return song_limit_input 

# Validates a recommendation name passed in, for a given user
def validate_rec_name(rec_name, user_id):
    # Checks if the recommendation name is empty
    if (rec_name.strip() == ""):
        raise ValueError("You cannot enter an empty recommendation name")
    else:
        # Checks if the recommendation name is already present in the table, for that user
        if db.check_rec_name_in_db(rec_name, user_id):
            raise ValueError("You already have a recommendation with the same name as this. Enter a unique name")
    
    # Returns the recommendation name if it's valid
    return rec_name

# Validates the user's feature weight sliders (can't all be at 0):
def feature_weight_validation(weight_dict):
    # Iterates through every weight passed in the dictionary
    for weight in weight_dict.values():
        # If any isn't 0, not all can be 0, so leave the function
        if weight != 0:
            return
    
    # If the function hasn't returned at this point, all must be 0, so raise an error
    raise ValueError("Not all weights can be 0")