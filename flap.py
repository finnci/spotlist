from flask import Flask, redirect, url_for, session, request, render_template
from flask_oauthlib.client import OAuth, OAuthException
import requests
import json

SPOTIFY_APP_ID = '0e78fc3c02324da885aab026fe730863'
SPOTIFY_APP_SECRET = '5d86d3b7fc1b4e6dae07c64e0ff0af3a'


app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

spotify = oauth.remote_app(
    'spotify',
    consumer_key=SPOTIFY_APP_ID,
    consumer_secret=SPOTIFY_APP_SECRET,
    # Change the scope to match whatever it us you need
    # list of scopes can be found in the url below
    # https://developer.spotify.com/web-api/using-scopes/
    request_token_params={'scope': ('user-read-private','playlist-modify-public')},
    base_url='https://accounts.spotify.com',
    request_token_url=None,
    access_token_url='/api/token',
    authorize_url='https://accounts.spotify.com/authorize'
)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login')
def login():
    callback = url_for(
        'spotify_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return spotify.authorize(callback=callback)


@app.route('/login/authorized')
def spotify_authorized():
    resp = spotify.authorized_response()
    if resp is None:
        return 'Access denied: reason={0} error={1}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: {0}'.format(resp.message)

    session['oauth_token'] = (resp['access_token'], '')
    data = requests.get('https://api.spotify.com/v1/me', headers={ 'Authorization': 'Bearer ' + session.get('oauth_token')[0]}).json()
    session['spot_id'] = data['id']
    print 'Logged in %s' % data
 
    return redirect('/playlister')

@app.route('/playlister')
def playlister():
    return render_template('playlister.html')

@app.route('/create/playlist/<name>')
def ui_create_playlist(name):
    plist_data = {'name': name}
    playlist_obj = create_playlist(session.get('spot_id'), plist_data)


def populate_playlist(playlist_id, tracklist, artist):
    playlist_post = 'https://api.spotify.com/v1/users/%s/playlists/%s/tracks' % (session.get('spot_id'), '2tAcbeaDEk0357Q4YZ7QEU')
    headers = { 'Authorization': 'Bearer ' + session.get('oauth_token')[0],
               'content_type': 'application/json'}
    # call get track uris
    track_uris = track_searcher(tracklist, artist)
    return requests.post(playlist_post, headers=headers, data=json.dumps(track_uris))

def track_searcher(tracklist, artist):
    track_search= 'https://api.spotify.com/v1/search?q='
    track_uris = []
    headers = { 'Authorization': 'Bearer ' + session.get('oauth_token')[0],
                'content_type': 'application_json'}
    import urlparse
    from urllib import urlencode 
    params = {'track': 'finnplaceholder', 'artist': artist}
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    final_url = urlparse.urlunparse(url_parts)
    for track in tracklist:
        finalurl.replace('finnplaceholder', track)
        track_get = requests.get(final_url, headers=headers)
   

       
       
def create_playlist( playlist_data):
    create_playlist_url = 'https://api.spotify.com/v1/users/1155665355/playlists'
    headers = { 'Authorization': 'Bearer ' + session.get('oauth_token')[0],
               'content_type': 'application_json'}
    post_plist = requests.post(create_playlist_url, headers=headers,  data=json.dumps(playlist_data))
        # success, return the response object
    return post_plist
                

@spotify.tokengetter
def get_spotify_oauth_token():
    return session.get('oauth_token')


if __name__ == '__main__':
    app.run()
