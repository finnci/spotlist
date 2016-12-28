from flask import Flask, redirect, url_for, session, request, render_template
from flask_oauthlib.client import OAuth, OAuthException
from flask import Response
from urllib import urlencode
import urlparse
import requests
import logging
import time
import json

SPOTIFY_APP_ID = '<INSERT_ID>'
SPOTIFY_APP_SECRET = '<INSERT_SECRETER_KEY'

app = Flask(__name__, static_folder='stat', static_url_path="")
app.debug = False
oauth = OAuth(app)

spotify = oauth.remote_app(
    'spotify',
    consumer_key=SPOTIFY_APP_ID,
    consumer_secret=SPOTIFY_APP_SECRET,
    # Change the scope to match whatever it us you need
    # list of scopes can be found in the url below
    # https://developer.spotify.com/web-api/using-scopes/
    request_token_params={
        'scope': ('user-read-private', 'playlist-modify-public')
    },
    base_url='https://accounts.spotify.com',
    request_token_url=None,
    access_token_url='/api/token',
    authorize_url='https://accounts.spotify.com/authorize')


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login')
def login():
    callback = url_for(
        'spotify_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True)
    return spotify.authorize(callback=callback)


@app.route('/login/authorized')
def spotify_authorized():
    resp = spotify.authorized_response()
    if resp is None:
        return 'Access denied: reason={0} error={1}'.format(
            request.args['error_reason'], request.args['error_description'])
    if isinstance(resp, OAuthException):
        return 'Access denied: {0}'.format(resp.message)

    session['oauth_token'] = (resp['access_token'], '')

    data = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization':
                 'Bearer ' + session.get('oauth_token')[0]}).json()

    session['spot_id'] = data['id']

    return redirect('/playlister')


@app.route('/playlister')
def playlister():
    return render_template('playlister.html')

@app.route('/about')
def app_about():
    return render_template('about.html')

@app.route('/create/playlist/', methods=['POST'])
def ui_create_playlist():
    r_data = json.loads(request.data)
    artist = r_data['artist']
    songs = r_data['songs']
    track_uris = track_searcher(songs, artist)
    p_list = create_playlist({'name': 'Playlist for gig: %s' % artist}).json()
    emblink = "https://embed.spotify.com/?uri=%s" % p_list['uri']
    pid = p_list['id']
    if track_uris:
        plist_pop = populate_playlist(pid, track_uris)
    else:
        return Response(json.dumps({'error': 'No tracks found.'}),
                        status=500,
                        mimetype='application/json')

    return Response(json.dumps({'link': emblink}),
                    status=200,
                    mimetype='application/json')

def populate_playlist(playlist_id, tracklist):
    playlist_post = 'https://api.spotify.com/v1/users/%s/playlists/%s/tracks' % (
        session.get('spot_id'), playlist_id)
    headers = {
        'Authorization': 'Bearer ' + session.get('oauth_token')[0],
        'content_type': 'application/json'
    }
    pc = requests.post(playlist_post,
                       headers=headers,
                       data=json.dumps(list(tracklist)))
    return pc


def track_searcher(tracklist, artist):
    track_search = 'https://api.spotify.com/v1/search?q='
    track_uris = set([])
    headers = {
        'Authorization': 'Bearer ' + session.get('oauth_token')[0],
        'content_type': 'application_json'
    }
    # todo: find a nice way to format this right.
    for track in tracklist:
        params = {
            'track': track.encode('utf-8'),
            'artist': artist
        }
        final_url = do_ugly_url_stuff(track_search, params)
        track_get = requests.get(final_url, headers=headers)
        try:
            for trk in track_get.json()['tracks']['items']:
                try:
                    if artist.lower() == str(trk['artists'][0]['name']).lower():
                        track_uris.add(trk['uri'])
                        break
                except UnicodeError:
                    pass
        except IndexError:
            pass
    return track_uris

def do_ugly_url_stuff(track_search, params):
    url_parts = list(urlparse.urlparse(track_search))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    final_url = urlparse.urlunparse(url_parts)
    final_url = final_url.replace('search?', 'search?q=')
    final_url = final_url.replace('artist=', 'artist:')
    final_url = final_url.replace('track=', 'track:')
    final_url = final_url + "&type=track"
    return final_url


@app.route('/set/search/<artist>')
def search_setlist(artist):
    # takes str artist name,
    # returns list of str track names
    set_search = 'https://api.setlist.fm/rest/0.1/search/setlists.json?artistName=%s' % (artist)
    sets = requests.get(set_search)
    res_dict = {'sets': set([])}
    # sets is a list of setlists, 0 = most_recent (probably not worth using).
    for mset in sets.json()['setlists']['setlist']:
        # s looks like {'sets':{'set':[]}}
        try:
            for song_set in mset['sets']['set']:
                for slist in song_set['song']:
                    res_dict['sets'].add(slist['@name'])
        except (AttributeError, TypeError, KeyError) as e:
            logging.debug('Err was: %s' % e)
            pass
    res_d2 = {'sets': list(res_dict['sets'])}
    if not res_d2['sets']:
        res_d2['sets'] = ["Can't find this one, sorry.",
                          "Guess you're a filthy hipster.",
                          "Or maybe you spelt the artists name wrong."
                          "Or its not available on setlist.fm for some reason"]

    resp = Response(json.dumps(res_d2), status=200, mimetype='application/json')
    return resp


def create_playlist(playlist_data):
    create_playlist_url = 'https://api.spotify.com/v1/users/%s/playlists' % session.get('spot_id')
    headers = {
        'Authorization': 'Bearer ' + session.get('oauth_token')[0],
        'content_type': 'application_json'
    }
    post_plist = requests.post(
        create_playlist_url, headers=headers, data=json.dumps(playlist_data))
    # success, return the response object
    return post_plist


@spotify.tokengetter
def get_spotify_oauth_token():
    return session.get('oauth_token')


if __name__ == '__main__':
    app.run()
