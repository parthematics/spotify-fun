import json
import requests
import six
import six.moves.urllib.parse as urllibparse
from __future__ import division
# import pyperclip as cp
import heapq
import base64

_scope = "user-top-read user-read-recently-played user-library-read user-library-modify user-read-playback-state user-read-currently-playing user-modify-playback-state"

# HELPER FUNCTIONS FOR AUTHORIZATION

def get_auth_url(username, scope=_scope, client_id, client_secret, state='ilovetocodelol'):
    redirect_uri = 'https://example.com/callback/'

    auth_code_url = "https://accounts.spotify.com/authorize"
    auth_code_dict = {"client_id": client_id, "response_type": "code", "redirect_uri": redirect_uri, "state": state, "scope": scope, "show_dialog": "false"}
    auth_code_params = urllibparse.urlencode(auth_code_dict)

    get_response = requests.get(auth_code_url, params=auth_code_params)

    if get_response.status_code != 200:
        print("Error:", get_response.reason)

    return get_response.url

def get_auth_code(url):
    start = url.index('?')
    end = url.index('&')
    code = url[start + 6:end]
    return code

def create_auth_header(client_id, client_secret):
    auth_header = base64.b64encode(six.text_type(client_id + ':' + client_secret).encode('ascii'))
    return {'Authorization': 'Basic %s' % auth_header.decode('ascii')}

def get_oauth_token(response_url, scope=_scope):
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {"redirect_uri": redirect_uri, "code": get_auth_code(response_url), 
    "grant_type": "authorization_code", "scope": scope}
    token_headers = create_auth_header(client_id, client_secret)

    post_response = requests.post(token_url, data=token_data, headers=token_headers)

    if post_response.status_code != 200:
        print("Error:", post_response.reason)

    ACCESS_TOKEN = json.loads(post_response.text)["access_token"]
    # print(ACCESS_TOKEN)
    return ACCESS_TOKEN

# FUNCTIONS TO HELP PERFORM ANALYSIS

def get_all_songs(access_token):
    all_songs = []
    url = "https://api.spotify.com/v1/me/tracks"
    headers = {'Authorization': "Bearer {}".format(access_token)}
    tracks = requests.get(url, headers=headers)
    parsed = json.loads(tracks.text)

    count_songs = parsed["total"]

    for i in range(int(ceil(count_songs / 50.0))):
        offset = 50 * i
        url = "https://api.spotify.com/v1/me/tracks?limit=50&offset={}".format(offset)
        track_headers = {'Authorization': "Bearer {}".format(access_token)}
        tracks = requests.get(url, headers=track_headers)
        # cp.copy(tracks.text)
        parsed = json.loads(tracks.text)
        all_songs.extend(parsed['items'])

    return all_songs

def get_num_songs(access_token):
    all_songs = get_all_songs(access_token)
        
    try:
        if (len(all_songs) == count_songs):
            print("Number of gathered songs: {}".format(len(all_songs)))
            return len(all_songs)
    except:
        print("Response from API failed.")
        return -1

def get_most_popular_songs(access_token, limit=10, time_limit_in_sec=300):
    all_songs = get_all_songs(access_token)
    songs_all = [(all_songs[i]['track']['popularity'], all_songs[i]['track']['name']) for i in range(len(all_songs))]
    songs_under_5 = [(all_songs[i]['track']['popularity'], all_songs[i]['track']['name']) for i in range(len(all_songs)) if all_songs[i]['track']['duration_ms'] <= time_limit_in_sec * 1000]    

    print("Total songs under {} seconds:".format(str(time_limit_in_sec)), len(songs_under_5))

    largest = heapq.nsmallest(limit, songs_under_5)
    largest = [[key, value] for value, key in largest]

    return largest

def get_most_popular_albums(access_token, limit=10):
    all_songs = get_all_songs(access_token)
    album_ids = {[all_songs[i]['track']['album']['name'], all_songs[i]['track']['album']['id']]
                 for i in range(len(all_songs))}

    count = 0
    albums = []
    for item in album_ids:
        if (count < limit):
            albums.append([item[0]])
            count += 1
        else:
            break

    return albums

def get_top_music(type="artists", limit=20, time_range="medium_term", access_token=ACCESS_TOKEN):
    url = "https://api.spotify.com/v1/me/top/"
    if (type == "artists"):
        url += "artists"
    else:
        url += "tracks"
    
    query_params={"limit": str(limit), "offset": "0", "time_range": time_range}
    headers = {'Authorization': "Bearer {}".format(access_token)}
    
    top_tracks_and_artists = requests.get(url=url, params=query_params, headers=headers)
    parsed = json.loads(top_tracks_and_artists.text)
    items = parsed['items']

    top_music = []
    
    if (type == "artists"):
        for i in range(len(items)):
            top_music.append(["Rank: {}".format(str(i+1)), items[i]['name'], int(items[i]['followers']['total']), items[i]['images'][0]['url']])
    else:
        for i in range(len(items)):
            current_item = items[i]
            artists = current_item['artists']
            current_album = current_item['album']
            length_of_song = str((current_item['duration_ms'] // 1000) // 60) + "m " + str((current_item['duration_ms'] // 1000) % 60) + "s"
            top_music.append(["Rank: {}".format(str(i+1)), current_item['name'], 
                               [artists[j]['name'] for j in range(len(artists))], 
                               current_album['name'], length_of_song, current_album['release_date']])
    return top_music
    
def get_top_genres(artist_limit=50, genre_limit=10, time_range="medium_term", access_token=ACCESS_TOKEN):
    url = "https://api.spotify.com/v1/me/top/artists"
    all_genres = {}
    
    query_params={"limit": str(artist_limit), "offset": "0", "time_range": time_range}
    headers = {'Authorization': "Bearer {}".format(access_token)}
    
    top_tracks_and_artists = requests.get(url=url, params=query_params, headers=headers)
    parsed = json.loads(top_tracks_and_artists.text)
    items = parsed['items']
    
    for i in range(len(items)):
        genres = items[i]['genres']
        for genre in genres:
            if genre not in all_genres.keys():
                all_genres[genre] = 1
            else:
                all_genres[genre] += 1
                
    heap = [[value, key.upper()] for key, value in all_genres.items()]
    largest = heapq.nlargest(genre_limit, heap)
        
    return largest

