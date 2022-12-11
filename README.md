# apple-tv-now-playing-server

simple apple-tv now playing http server using pyatv under the hood (and also displaying apple tv now playing info on your [Tidbyt](https://tidbyt.com))

### Getting Started..

### Start the server
```bash
python app.py
```

### Scan local network for Apple TVs

navigate to `http://localhost:5005/scan`
and select an Apple TV to pair

### Select and Pair your Apple TV

turn on your Apple TV and enter the pairing code

### Access the Now Playing API for your Paired Apple TV

```bash
$ curl http://localhost:5005/playing?mac=<appletv-mac-address>&width=<optional>&height=<optional>
```
height and width are used for returning now_playing artwork when available

##### Example Responses

Example Response while Playing Apple Music on Apple TV
```bash
curl http://localhost:5005/playing?mac=AA:BB:CC:DD:EE:FF&width=100
```
```json
{
    "album": "Donda (Deluxe)",
    "artist": "Kanye West & André 3000",
    "artwork":
    {
        "bytes": "/9j/4QC+RXhpZgAATU0AKgAAAAgABQEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAIAAAITAAMAAAABAAEAAIdpAAQAAAABAAAAWgAAAAAAAABIAAAAAQAAAEgAAAABAAeQAAAHAAAABDAyMjGRAQAHAAAABAECAwCgAAAHAAAABDAxMDCgAQADAAAAAQABAACgAgAEAAAAAQAAAGSgAwAEAAAAAQAAAGSkBgADAAAAAQAAAAAAAAAAAAD/2wCEAAICAgICAgMCAgMFAwMDBQYFBQUFBggGBgYGBggKCAgICAgICgoKCgoKCgoMDAwMDAwODg4ODg8PDw8PDw8PDw8BAgICBAQEBwQEBxALCQsQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEP/dAAQAB//AABEIAGQAZAMBIgACEQEDEQH/xAGiAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgsQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+gEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoLEQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/APwLooorQzCiiigAooooAKKKKACiiigAooooAhl7VDU0vaoahlo//9D8C6KKK0MwooooAKKKKACiiigAooooAKKKKAIZe1Q1NL2qGoZaP//R/AuiiitDMKKKKACiiigAooooAKKKKACiiigCGXtUNTS9qhqGWj//0vwLooorQzCiiigAooooAKKKKACiiigAooooAhl7VDU0vaoahlo//9P8C6KKK0MwooooAKKKKACiiigAooooAKKKKAIZe1Q1NL2qGoZaP//U/AuiiitDMKKKKACiiigAooooAKKKKACiiigCGXtUNTS9qhqGWj//1fwLooorQzCiiigAooooAKKKKACiiigAooooAhl7VDU0vaoahlo//9k=",
        "height": 100,
        "id": "https://is2-ssl.mzstatic.com/image/thumb/Music116/v4/cf/a7/f9/cfa7f9be-2d62-89a4-19bf-26276ab39f16/21UMGIM64738.rgb.jpg/{w}x{h}bb.{f}",
        "mimetype": "image/jpeg",
        "width": 100
    },
    "content_identifier": "",
    "device_state": "DeviceState.Playing",
    "episode_number": "",
    "genre": "Hip-Hop/Rap",
    "hash": "gN8p6N6lN∆l8ep4wESS",
    "media_type": "MediaType.Music",
    "position": "36",
    "repeat": "RepeatState.Off",
    "season_number": "",
    "series_name": "",
    "shuffle": "ShuffleState.Off",
    "title": "Life Of The Party",
    "total_time": "391"
}
```

### Display "Now Playing" Information on your [Tidbyt](https://tidbyt.com)

Follow instructions above to pair w/ an Apple TV. After successfully pairing w/ an Apple TV click the "Configure a Tidbyt" button to configure a tidbyt with the paired Apple TV.
