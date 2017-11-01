import sys
import spotipy
import spotipy.util as util
import requests
from bs4 import BeautifulSoup
import argparse

# you must override the config file with your own keys
from config.config import geniusToken
from config.config import geniusHeader
from config.config import spotifyClient_Id
from config.config import spotifyClient_Secret

# scopes for spotify api
scopes = {
	'recentlyPlayed': 'user-read-recently-played',
	'currentlyPlaying': 'user-read-currently-playing',
}

# genius api tokens and etc.
token = geniusToken
base_url = "https://api.genius.com"
headers = geniusHeader

# get a spotify token
def getToken(scopeKey, username):

	token = util.prompt_for_user_token(username, scopes[scopeKey], client_id=spotifyClient_Id,
									   client_secret=spotifyClient_Secret, redirect_uri='http://localhost/')
	return token

# get recent songs from current users spotify
def getRecentSongs(token):
	trackList = []
	if token:
		sp = spotipy.Spotify(auth=token)
		results = sp.current_user_recently_played(limit=20)
		for item in results['items']:
			track = item['track']
			trackList.append(track['name'] + ' - ' +
											 track['artists'][0]['name'])
	else:
		return("Can't get token for", username)
	return trackList

# get the name and artist for a given song on spotify
def getCurrentSong(token):
	if token:
		sp = spotipy.Spotify(auth=token)
		payload = sp.current_user_playing_track()
		item = payload['item']
		# song = item['name'] + ' - ' + item['artists'][0]['name']
		song = {'name':  item['name'], 'artist': item['artists'][0]['name']}
	return song

# get lyrics from genius.com song page by html scraping
def getLyricsFromApi(api_path):
	song_url = base_url + api_path
	response = requests.get(song_url, headers=headers)
	json = response.json()
	songPath = json["response"]["song"]["path"]

	# scrape the page
	page_url = "http://genius.com" + songPath
	page = requests.get(page_url)
	html = BeautifulSoup(page.text, "html.parser")
	
	# remove script tags
	[h.extract() for h in html('script')]
	lyrics = html.find('div', class_='lyrics').get_text()
	return lyrics

# get genius.com song api path
def getSongApiPath(name, artist):
	search_url = base_url + '/search?'
	data = {'q': name}
	response = requests.get(search_url, params=data, headers=headers)
	json = response.json()
	song_info = None
	for item in json['response']['hits']:
		# check if correct artist
		if item['result']['primary_artist']['name'] == artist:
			song_info = item
			break
	if song_info:
		song_api_path = song_info['result']['api_path']
		return song_api_path


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description='Spotify Lyric Searcher', add_help=False)
	parser.add_argument('query', help='Spotify account ID')
	parser.add_argument('-c', '--current', action='store_true', default=False,
						help='Print Lyrics for currently playing Spotify song.')
	parser.add_argument('-r', '--recent', action='store_true',
						default=False, help='Get list of recently played songs.')

	if len(sys.argv) < 3:
		parser.print_help()
		sys.exit(1)

	args = parser.parse_args()

	username = args.query

	if args.current is True:
		token = getToken('currentlyPlaying', username)
		if token:
			currSong = getCurrentSong(token)
			songName = currSong['name']
			artist = currSong['artist']
			apiPath = getSongApiPath(songName, artist)
			print(str(songName) + ' - ' + str(artist))
			print(getLyricsFromApi(apiPath))

	elif args.recent is True:
		token = getToken('recentlyPlayed', username)
		recentDict = {}
		if token:
			recents = getRecentSongs(token)
			for i, song in enumerate(recents, 1):
				print(str(i) + ". " + str(song))
				recentDict[i] = song
		query = int(input('Enter number of the song you want lyrics for: '))
		currSong = recentDict[int(query)]
		songName, artist = currSong.split(' - ')
		print(str(songName) + ' - ' + str(artist))
		apiPath = getSongApiPath(str(songName), str(artist))
		if apiPath is not None:
			print(getLyricsFromApi(apiPath))
		else:
			print('Can\'t find lyrics.')