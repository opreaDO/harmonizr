# Harmonizr

Harmonizr is a Streamlit app that connects to Spotify, shows account listening data, and generates song recommendations based on tracks or playlists the user selects.

## What this project currently needs

To run the app locally, you need all of the following:

- A Spotify Developer account
- Your own Spotify app `CLIENT_ID` and `CLIENT_SECRET`
- A PostgreSQL database connection string in `CONN_STRING`
- The local CSV data files the app expects:
  - `dataset.csv`
  - `tracks_features.csv`

The repo currently ignores `*.env` and `*.csv`, so those files are expected to be supplied locally.

## Local setup

### 1. Install dependencies

This project uses Poetry.

```bash
poetry install
```

### 2. Create a Spotify app

Go to the Spotify Developer Dashboard and create an app:

- Dashboard: <https://developer.spotify.com/dashboard>
- Copy the app's Client ID
- Copy the app's Client Secret

Add this redirect URI to your Spotify app settings:

```text
http://localhost:8501
```

That exact value matters because the app currently hardcodes:

```python
REDIRECT_URI = "http://localhost:8501"
```

in [login_page.py](/Users/darius/Documents/harmonizr/src/harmonizr/page_folder/login_page.py:17).

### 3. Create `.env`

Create a `.env` file in the project root:

```env
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
CONN_STRING=postgresql://username:password@localhost:5432/your_database_name
```

What each value is for:

- `CLIENT_ID`: from your Spotify app
- `CLIENT_SECRET`: from your Spotify app
- `CONN_STRING`: PostgreSQL connection string used by the app's database layer

### 4. Add the required CSV files

Place these files in the project root:

- `dataset.csv`
- `tracks_features.csv`

They are referenced in the code here:

- [recommendation_engine.py](/Users/darius/Documents/harmonizr/src/harmonizr/recommendation_engine.py:10)
- [db_manager.py](/Users/darius/Documents/harmonizr/src/harmonizr/db_manager.py:70)

Without them, recommendation generation and lookup-table setup will fail.

## Running the app

Start Streamlit with Poetry:

```bash
poetry run streamlit run src/harmonizr/streamlit_app.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## How to test the project with your own Spotify account

This project does not currently have a real automated test suite in `tests/`. The practical way to test it today is to run the app locally with your own Spotify developer credentials and Spotify account.

Use this flow:

1. Create your own Spotify app in the Spotify Developer Dashboard.
2. Set the redirect URI to `http://localhost:8501`.
3. Put your `CLIENT_ID`, `CLIENT_SECRET`, and `CONN_STRING` into `.env`.
4. Make sure `dataset.csv` and `tracks_features.csv` are present in the project root.
5. Run:

```bash
poetry run streamlit run src/harmonizr/streamlit_app.py
```

6. Click `Login with Spotify`.
7. Sign in with your Spotify account and approve the requested scopes.
8. Verify the app loads your account data and lets you move through the recommendation flow.

The current Spotify scopes requested by the app are:

```text
user-library-read user-top-read user-read-recently-played playlist-modify-public
```

## Project structure

- [streamlit_app.py](/Users/darius/Documents/harmonizr/src/harmonizr/streamlit_app.py): app entry point
- [login_page.py](/Users/darius/Documents/harmonizr/src/harmonizr/page_folder/login_page.py): Spotify OAuth login flow
- [welcome_page.py](/Users/darius/Documents/harmonizr/src/harmonizr/page_folder/welcome_page.py): user stats view
- [recommendation_manager.py](/Users/darius/Documents/harmonizr/src/harmonizr/page_folder/recommendation_manager.py): recommendation workflow
- [recommendation_engine.py](/Users/darius/Documents/harmonizr/src/harmonizr/recommendation_engine.py): recommendation logic
- [db_manager.py](/Users/darius/Documents/harmonizr/src/harmonizr/db_manager.py): database access
