# Importing libraries & modules necessary
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from db_manager import db

# Class for all recommendation functions,
class recommendation_engine:
    # Sets variables needed when the object is instantiated
    def __init__(self, dataset_path="dataset.csv"):
        # Sets the dataset path passed in
        self.dataset_path = dataset_path

        # Defines numeric columns, on which the NN model will base its distance metrics off
        self.numeric_columns = ['danceability', 'energy', 'key', 'loudness', 'mode', 
                              'speechiness', 'acousticness', 'instrumentalness', 
                              'liveness', 'valence', 'tempo']
        
        # Sets the parent genre mapping function
        self.genre_mapping = {
            'pop': ['pop', 'power-pop', 'synth-pop', 'j-pop', 'k-pop', 'cantopop', 
                    'mandopop', 'j-idol', 'disney', 'pop-film', 'happy', 'sad', 'romance'],
            'rock/metal': ['rock', 'alt-rock', 'alternative', 'hard-rock', 'grunge', 
                            'psych-rock', 'metal', 'heavy-metal', 'black-metal', 
                            'death-metal', 'punk', 'punk-rock', 'emo', 'indie', 
                            'indie-pop', 'goth', 'grindcore', 'metalcore', 'rock-n-roll', 
                            'rockabilly', 'j-rock'],
            'electronic/dance': ['electronic', 'edm', 'electro', 'dubstep', 'house', 
                                'techno', 'trance', 'drum-and-bass', 'dub', 'trip-hop', 
                                'idm', 'deep-house', 'disco', 'dance', 'club', 
                                'dancehall', 'breakbeat', 'garage', 'hardcore', 
                                'hardstyle', 'chicago-house', 'detroit-techno', 
                                'minimal-techno', 'progressive-house', 'party', 
                                'j-dance', 'industrial'],
            'hip-hop/r&b': ['hip-hop', 'r-n-b', 'trap', 'reggaeton'],
            'jazz/blues': ['jazz', 'blues', 'soul', 'funk', 'groove'],
            'classical/ambient': ['classical', 'opera', 'ambient', 'new-age', 'piano', 
                                'guitar', 'chill', 'sleep', 'study'],
            'country/folk': ['country', 'honky-tonk', 'bluegrass', 'folk', 
                            'singer-songwriter', 'acoustic'],
            'world': ['world-music', 'afrobeat', 'brazil', 'latin', 'latino', 
                        'salsa', 'samba', 'tango', 'forro', 'pagode', 'sertanejo', 
                        'indian', 'iranian', 'turkish', 'malay', 'mpb', 'british', 
                        'french', 'spanish', 'swedish', 'german', 'reggae', 'ska'],
            'soundtrack/thematic': ['soundtrack', 'show-tunes', 'comedy', 'children', 
                                    'kids', 'gospel', 'anime']
        }
        
    # Converts the specifc genres into more general parent genres, using the genre mapping dictonary
    def _split_into_parent_genres(self, df):
        # Create a reverse mapping from child genre to its parent genre
        parent_genres = {}

        # Iterate through the genre mapping: parent -> list of child genres
        for parent, children in self.genre_mapping.items():
            for child in children:
                parent_genres[child] = parent   # Map each child to its corresponding parent genre

        # Replace each track's genre with its parent genre (if it exists in the mapping)
        df['track_genre'] = df['track_genre'].map(lambda x: parent_genres.get(x, x))

        return df

    # Method to clean & normalise a dataframe passed in
    def _clean_normalize_df(self, df, columns, duplicate_checker_column):
        # Removes any unwanted columns from the df
        df = df[columns]
        
        # Drops any duplicates, from a column passed into it
        df = df.drop_duplicates(subset=[duplicate_checker_column])

        # Converts all values into numeric values (some may be in scientific notation)
        df[self.numeric_columns] = df[self.numeric_columns].apply(pd.to_numeric, errors="coerce")

        # Normalises all numeic values in the dataframe
        scaler = StandardScaler()
        df[self.numeric_columns] = scaler.fit_transform(df[self.numeric_columns])

        # Returns the cleaned & normalised df
        return df

    # Applies weights passed in, to a dataframe passed in (only for numeric columns)
    def _apply_weights(self, df, weights_dict):
        # Converts weights to a series for easier calculations
        weights_series = pd.Series(data=weights_dict)

        # Makes a copy of the dataframe to be weighted, before calculations performed
        weighted_df = df.copy()

        # Multiplies dataframe by weights, to weight the df
        weighted_df[self.numeric_columns] = weighted_df[self.numeric_columns].mul(weights_series, axis=1)

        return weighted_df
    
    # Method to load & prepare the training data needed to pass into the NN model
    def _load_training_data(self):
        # Reads the csv file, and creates a dataframe from its data
        df = pd.read_csv(self.dataset_path)

        # Defines columns which are needed
        columns = ['track_id', 'track_name', 'track_genre', 'artists'] + self.numeric_columns
        
        # Cleans & normalises the df
        df = self._clean_normalize_df(df, columns, 'track_id')
        df = df.rename({"track_id": "song_id"}, axis="columns")

        # Drops duplicate songs & removes columns no longer needed
        df = df.drop_duplicates(subset=["track_name", "artists"])
        df = df[['song_id', 'track_genre'] + self.numeric_columns]

        # Puts each song's genre into its parent genre
        df = self._split_into_parent_genres(df)

        # Returns the prepared df, ready for the NN model
        return df

    # Method to find song recommendations, using the nearest neighbors model
    def _find_recommendations(self, user_song_id_list, training_data, user_data, num_songs):
        # Find and remove the user's already selected songs from the training data
        user_song_index = training_data[training_data["song_id"].isin(user_song_id_list)].index
        training_data = training_data.drop(user_song_index)

        # Prepare the training data and fit the nearest neighbors model
        X_train = training_data[self.numeric_columns]
        nn_model = NearestNeighbors(n_neighbors=num_songs, algorithm="ball_tree", metric="euclidean")
        nn_model.fit(X_train)

        # Get distances and indices of nearest neighbors for the user data
        user_data_numeric = user_data[self.numeric_columns]
        distances, neighbor_indices = nn_model.kneighbors(user_data_numeric)
        
        # Flatten distance & neighbour arrays to sort them
        distances = distances.flatten()
        neighbor_indices = neighbor_indices.flatten()

        # Sort distances, & neighbours in same order as distances
        sorted_distance_indices = np.argsort(distances)
        sorted_neighbor_indices = neighbor_indices[sorted_distance_indices]

        # Return unique song IDs from the top neighbors
        recommended_song_id_series = training_data.iloc[sorted_neighbor_indices]["song_id"].copy()
        unique_song_id_series = recommended_song_id_series.drop_duplicates()

        # Converts the series to a list
        unique_song_id_list = unique_song_id_series.to_list()

        # Keeps only the number of songs wanted
        cut_off_song_id_list = unique_song_id_list[0:num_songs]

        # Returns list of the song ids
        return cut_off_song_id_list

    # Main method used to get recommendations, based on songs passed in to it
    def get_recommendations(self, song_id_list, genre, weights_dict, num_songs, user_id, rec_name):
        # Get user's inputted song's attributes, and store them in a dataframe
        user_song_attribute_list = db.get_song_attributes(song_id_list, column_list=self.numeric_columns)
        user_song_attribute_df = pd.DataFrame(data=user_song_attribute_list, columns=self.numeric_columns)

        # Load and prepare training data
        training_df = self._load_training_data()
        training_df = training_df[training_df['track_genre'] == genre]

        # Apply weights to both user and training data
        weighted_user_df = self._apply_weights(user_song_attribute_df, weights_dict)
        weighted_training_df = self._apply_weights(training_df, weights_dict)

        # Find recommendations
        recommended_song_ids = self._find_recommendations(
            song_id_list, 
            weighted_training_df, 
            weighted_user_df, 
            num_songs
        )
        
        # Adds this new recommendation to the database
        db.add_rec_to_rec_table(recommended_song_ids, user_id, rec_name)

        # Returns list of recommended song ids
        return recommended_song_ids
    
rec_engine = recommendation_engine()