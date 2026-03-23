import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="4211bade7d42451eb64ef23b05a147a9",
    client_secret="1e5e5c4dcd2a4213929c39e5775e8ae9",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-modify-playback-state user-read-playback-state"
))

@app.route('/api/play')
def play():
    sp.start_playback()
    return {"status": "playing"}

@app.route('/api/pause')
def pause():
    sp.pause_playback()
    return {"status": "paused"}

@app.route('/api/next')
def next_track():
    sp.next_track()
    return {"status": "next"}

@app.route('/api/volume/<int:vol>')
def volume(vol):
    sp.volume(vol)
    return {"status": f"volume {vol}"}

@app.route('/api/current')
def current():
    return sp.current_playback()

if __name__ == '__main__':
    #app.run(debug=True) #by default, solo funciona en LocalHost
    app.run(host='0.0.0.0', port=5000, debug=True)