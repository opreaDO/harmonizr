# Importing necessary libraries
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Cleans and normalises the dataframe, with columns passed in
def clean_normalise_df(df, columns, numeric_columns, duplicate_checker_column):
    # Only keeps columns which are needed 
    df = df[columns] 

    # Drops any duplicate columns
    df = df.drop_duplicates(subset=[duplicate_checker_column]) 

    # Converts all numeric fields to floats/integers (includes converting scientific notation to float)
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce") 

    # Apply normalisation to selected data
    scaler = StandardScaler()
    df[numeric_columns] = scaler.fit_transform(df[numeric_columns]) 

    # Returns the cleaned & normalised dataframe
    return df

# Database class to manage all database requests
class db_manager:
    # Creates a new session when an object is instantiated
    def __init__(self, conn_string):
        # Creates the engine & session to access the database
        self.engine = create_engine(conn_string)
        self.Session = sessionmaker(bind=self.engine)

    # Context manager to automatically open, commit & close connections once transactions are done 
    @contextmanager
    def get_session(self):
        # Gets the session from the object (starts a session)
        session = self.Session()
        try:
            # Treis to commit the transaction
            yield session
            session.commit()
        except Exception:
            # Rolls back the transaction, if it couldn't be completed properly
            session.rollback()
            raise
        finally:
            # Closes the connection once the transaction is complete/fails
            session.close()

    # Creates the user table
    def create_user_table(self):
        # Starts a session
        with self.get_session() as session:
            query = text("""
                        CREATE TABLE user_table(
                        user_id text PRIMARY KEY,
                        display_name text 
                        );
                        """)
            
            # Executes the query to create the table described above
            session.execute(query)

    # Adds user to the user table, if they are a new user
    def add_user_to_user_table(self, input_user_id, input_display_name):
        # Starts a session
        with self.get_session() as session:
            # Adds user, if they're not in the database.
            # If user is in the database, will check if inputted display name matches. If it isn't it updates the name
            query = text("""
                INSERT INTO user_table(user_id, display_name)
                VALUES(:user_id, :display_name)
                ON CONFLICT (user_id)
                DO UPDATE SET display_name = EXCLUDED.display_name
                WHERE user_table.display_name <> EXCLUDED.display_name;
            """)

            # Executes the query w/ the inputted parameters
            session.execute(query, {"user_id": input_user_id, "display_name": input_display_name})

    # Creates a lookup table, with the data in there
    def create_lookup_table(self):
        try:
            # Load track features from CSV
            df = pd.read_csv("tracks_features.csv")

            # Clean and normalize selected feature columns
            df = clean_normalise_df(
                df,
                ['id', 'danceability', 'energy', 'key', 'loudness', 'mode',
                'speechiness', 'acousticness', 'instrumentalness',
                'liveness', 'valence', 'tempo'],
                ['danceability', 'energy', 'key', 'loudness', 'mode',
                'speechiness', 'acousticness', 'instrumentalness',
                'liveness', 'valence', 'tempo'],
                "id"
            )

            # Define the query to create the table itself
            query = text("""
                        CREATE TABLE IF NOT EXISTS lookup_table (
                            song_id text PRIMARY KEY,
                            danceability FLOAT NOT NULL,
                            energy FLOAT NOT NULL,
                            key FLOAT NOT NULL,
                            loudness FLOAT NOT NULL,
                            mode FLOAT NOT NULL,
                            speechiness FLOAT NOT NULL,
                            instrumentalness FLOAT NOT NULL,
                            acousticness FLOAT NOT NULL,
                            liveness FLOAT NOT NULL,
                            valence FLOAT NOT NULL,
                            tempo FLOAT NOT NULL
                        );
                        """)

            # Rename ID column
            df = df.rename({"id": "song_id"}, axis="columns")

            with self.get_session() as session:
                # Create the table.
                session.execute(query)

            with self.get_session() as session:
                # Add data to the table
                df.to_sql('lookup_table', session.get_bind(), if_exists='append', index=False)
                
        except Exception as e:
            print(e)

    def get_song_attributes(self, song_id_list, column_list=["*"]):
        # Format the list of song IDs for the SQL query
        song_ids_str = ",".join([f"'{song_id}'" for song_id in song_id_list])
        columns_str = ",".join(column_list)

        with self.get_session() as session:
            query = text(f"""
                SELECT {columns_str}
                FROM lookup_table
                WHERE song_id IN ({song_ids_str});
            """)
            
            # Execute the query and fetch all results
            result = session.execute(query)
            
            
            # Fetch all results and return them as a list of tuples
            return result.fetchall()
        
    # Creates the recommendation table in the database
    def create_rec_table(self):
        try:
            # Start a session
            with self.get_session() as session:
                # Define the SQL query
                query = text("""
                            CREATE TABLE rec_table(
                            rec_id SERIAL PRIMARY KEY,
                            user_id text REFERENCES user_table(user_id),
                            recommended_song_ids TEXT[],
                            rec_name text,
                            timestamp TIMESTAMP);
                            """)
                
                # Executes the SQL written above
                session.execute(query)
        except Exception as e:
            # Prints the error if one occurs
            print(e)

    # Returns a boolean value for whether or not an inputted rec_name is in the database, for a specific user
    def check_rec_name_in_db(self, input_rec_name, input_user_id):
        # Start a session
        with self.get_session() as session:
            # Define the SQL query
            query = text(f"""
                        SELECT EXISTS(
                        SELECT 1
                        FROM rec_table
                        WHERE rec_name = (:rec_name) AND user_id = (:user_id))
                        """)
            
            # Execute the query, with the inputted parameters
            db_result = session.execute(query, {"rec_name": input_rec_name, "user_id": input_user_id})

            # Output a boolean value for the
            return db_result.scalar()

    # Adds a new recommendation to the recommendation table
    def add_rec_to_rec_table(self, song_id_list, input_user_id, input_rec_name):
        # Used to make sure there is no conflict with single quotes below in the query
        # 2 single quotes = 1 single quote to SQL when passing in a string
        input_rec_name = input_rec_name.replace("'", "''")

        # Gets the session
        with self.get_session() as session:
            # SQL to insert record into rec_table
            query = text("""
                        INSERT INTO rec_table(user_id, recommended_song_ids, rec_name, timestamp)
                        VALUES(:user_id, ARRAY[:song_ids], :rec_name, NOW())""")
            
            # Execute the SQL above
            session.execute(query, {
                'user_id': input_user_id,
                'song_ids': song_id_list,
                'rec_name': input_rec_name
            })

    # Gets all saved recommendations for a user
    def get_user_recommended_tracks(self, input_user_id):
        # Gets the session
        with self.get_session() as session:
            # SQL query to pull recommendations
            query = text(f"""
                        SELECT rec_id, rec_name, recommended_song_ids, timestamp
                        FROM rec_table
                        WHERE user_id = '{input_user_id}';
                        """)
            
            # Executes the SQL query
            result = session.execute(query)

            # Tuple structure for each recommendation set: [rec_id, rec_name, recommended_song_ids, timestamp]
            return result.fetchall()
        
    # Changes the name of a recommendation, given a recommendation id.
    def change_user_recommendation_name(self, input_rec_id, new_rec_name):
        # Gets the session
        with self.get_session() as session:
            # SQL Query to update the table
            query = text(f"""
                        UPDATE rec_table
                        SET rec_name = '{new_rec_name}'
                        WHERE rec_id = {input_rec_id}
                        """)
            
            # Executing the query
            session.execute(query)

    # Deletes a recommendation, given a recommendation id
    def delete_user_recommendation(self, input_rec_id):
        # SQL Query to delete a recommendation from a table
        with self.get_session() as session:
            query = text(f"""
                        DELETE FROM rec_table
                        WHERE rec_id = {input_rec_id}
                        """)

            # Executing the query
            session.execute(query)


# Load the .env file, to be able to access conn_string
load_dotenv()

# Gets the private connection string from the .env file
conn_string = os.getenv("CONN_STRING")

# Creates db object, use this to interact w/ the database
db = db_manager(conn_string)