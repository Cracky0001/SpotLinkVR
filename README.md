# SpotLinkVR

**SpotLinkVR** is an application that establishes a connection between Spotify and VRChat to synchronize information about currently playing songs between the platforms.

## Features

- Displays the current song title and artist in VRChat.
- Enables interaction with music information in VRChat.

## Configuration

1. **Starting the Application:**

   Before you start the application, ensure you correctly configure your Spotify login credentials.

2. **Setting Up Spotify Login Credentials:**

   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).

   - Create an application if you don't have one.

   - Copy the "Client ID" and "Client Secret" from your Spotify application settings.

3. **Inserting Spotify Login Credentials into the Code:**

   - Open the SpotLinkVR code.

   - Locate the section with Spotify API configuration:

     ```python
     # Spotify API Configuration
     sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
         client_id='YOUR_SPOTIFY_CLIENT_ID',
         client_secret='YOUR_SPOTIFY_CLIENT_SECRET',
         redirect_uri='http://localhost:8092/callback',
         scope='user-read-playback-state user-read-currently-playing'
     ))
     ```

   - Replace `'YOUR_SPOTIFY_CLIENT_ID'` with your actual Spotify Client ID and `'YOUR_SPOTIFY_CLIENT_SECRET'` with your Client Secret.

4. **Further Configuration:**

   - Ensure that the Redirect URI ('http://localhost:8092/callback') and the scope are configured in the code according to your requirements.

5. **Starting the Application:**

   - Start the application to establish the connection between Spotify and VRChat.

6. **VRChat User Experience:**

   - VRChat users will now see the current song title and artist in their VR experience.

## Authors

- Cracky

## Support

For questions or issues, please contact [Cracky](https://discord.com/users/507464069100601363).
