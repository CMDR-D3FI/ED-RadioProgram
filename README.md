# ED-RadioProgram

An Elite Dangerous Market Connector (EDMC) plugin that displays current radio program information from online radio stations, both in the EDMC interface and as an in-game overlay.

## Features

- 📻 **Real-time Program Information**: Displays current program name, time slot, description, and presenter
- 🎮 **In-Game Overlay**: Shows program info directly in Elite Dangerous (requires EDMCOverlay)
- 📍 **Configurable Overlay Position**: Choose from 8 screen positions for the in-game overlay
- 🔄 **Auto-Refresh**: Automatically updates program information at configurable intervals (5-60 minutes)
- 🎨 **Clean UI**: Integrated seamlessly into EDMC's main window
- 🌐 **API-Based**: Uses JSON API for reliable, fast data retrieval
- 🐍 **Python 3.x**: Modern, clean Python 3 codebase

## Supported Radio Stations

Currently supports:
- **ORF Sound** stations (Austria) via AudioAPI
  - Ö1: `https://audioapi.orf.at/oe1/api/json/current/broadcasts`
  - FM4: `https://audioapi.orf.at/fm4/api/json/current/broadcasts`
  - Ö3: `https://audioapi.orf.at/oe3/api/json/current/broadcasts`
  - And other ORF radio stations

More station types can be added in the future!

## Installation

1. Download the latest release or clone this repository
2. Navigate to your EDMC plugins folder:
   - **Windows**: `%LOCALAPPDATA%\EDMarketConnector\plugins`
   - **Mac**: `~/Library/Application Support/EDMarketConnector/plugins`
   - **Linux**: `~/.local/share/EDMarketConnector/plugins`
3. Copy the `ED-RadioProgram` folder into the plugins directory
4. Restart EDMC

## Configuration

1. Open EDMC and go to **File > Settings**
2. Navigate to the **ED-RadioProgram** tab
3. Configure the following options:

### Settings

- **Radio Station API URL**: Enter the ORF AudioAPI URL for your station
  - Default: `https://audioapi.orf.at/oe1/api/json/current/broadcasts`
  - Example FM4: `https://audioapi.orf.at/fm4/api/json/current/broadcasts`
  - Example Ö3: `https://audioapi.orf.at/oe3/api/json/current/broadcasts`

- **Station Type**: Select the radio station type (currently only "ORF Sound" is supported)

- **Refresh Interval**: How often to update program information (5-60 minutes)
  - Default: 10 minutes
  - Recommended: 10-15 minutes to avoid excessive API calls

- **Enable in-game overlay**: Toggle the in-game overlay on/off
  - Requires EDMCOverlay plugin to be installed
  - Shows program info with 50% transparent background

- **Overlay Position**: Choose where the overlay appears on your screen
  - **Top-Left**: Upper left corner (default)
  - **Top-Middle**: Top center of screen
  - **Top-Right**: Upper right corner
  - **Middle-Left**: Left side, vertically centered
  - **Middle-Right**: Right side, vertically centered
  - **Bottom-Left**: Lower left corner
  - **Bottom-Middle**: Bottom center
  - **Bottom-Right**: Lower right corner

## Usage

### EDMC Main Window

Once configured, the plugin will display:
- **Program Name** (large, bold text)
- **Time Slot** (🕒 with time range in HH:MM format)
- **Description** (program subtitle/description)
- **Presenter** (host/author name, when available)
- **Last Updated** timestamp
- **Manual Refresh Button**: Click to immediately update program information
- **Show/Hide Overlay Button**: Toggle in-game overlay (if EDMCOverlay is installed)

### In-Game Overlay

When enabled, program information is displayed in-game with:
- Semi-transparent black background (50% opacity)
- Yellow text for high visibility
- Configurable position (8 screen positions available)
- Smart text alignment based on position
- Auto-updates with each refresh cycle

The overlay shows:
- Program name (large text)
- Time slot (HH:MM - HH:MM Uhr)
- Presenter name (if available)
- Description (truncated to 80 characters if too long)

### Changing Overlay Position

1. Open EDMC Settings → ED-RadioProgram tab
2. Select your preferred position from the "Overlay Position" dropdown
3. Click OK to save
4. The overlay immediately moves to the new position!

### Manual Refresh

Click the **Refresh** button in EDMC to immediately fetch the latest program information without waiting for the automatic refresh interval.

## Requirements

- **Elite Dangerous Market Connector (EDMC)** 5.0.0 or higher
- **Python** 3.7+ (included with EDMC)
- **EDMCOverlay** (optional, for in-game overlay functionality)

## How It Works

1. The plugin fetches JSON data from the ORF AudioAPI at the configured interval
2. The JSON response contains program schedules for multiple days
3. Plugin matches current timestamp to find the active broadcast
4. Extracts program information (name, time, description, presenter)
5. Information is displayed in both the EDMC window and in-game overlay (if enabled)
6. Uses smart positioning logic to ensure overlay text doesn't go off-screen

## Technical Details

### API Integration
- Uses ORF AudioAPI JSON endpoints
- Automatically parses ISO 8601 timestamps
- Handles timezone offsets correctly
- Graceful error handling for network issues

### Overlay Positioning
The overlay uses coordinate-based positioning with smart alignment:
- **Left positions**: Text starts from the left edge
- **Middle positions**: Text and background are centered
- **Right positions**: Text and background are right-aligned

Coordinates are optimized for 1920x1080 resolution but work with other resolutions.

## Troubleshooting

### Plugin not appearing in EDMC
- Ensure the plugin folder is named `ED-RadioProgram` (not `ED-RadioProgram-master` or similar)
- Restart EDMC completely
- Check EDMC logs for any error messages

### No data displayed
- Verify the API URL is correct and accessible
- Check your internet connection
- Try clicking the "Refresh" button manually
- The API may be temporarily unavailable - wait a few minutes and try again

### Wrong program displayed
- Check your system time is correct
- Verify your timezone settings
- The API uses Austrian time (CET/CEST) - plugin handles conversion automatically

### Overlay not working
- Ensure EDMCOverlay plugin is installed and working
- Check if the overlay is enabled in ED-RadioProgram settings
- Try toggling the overlay off and on again
- Verify Elite Dangerous is running
- Try changing the overlay position if text is off-screen

### Overlay text cut off or off-screen
- Try a different overlay position from the dropdown
- Some positions work better depending on your game resolution
- Middle positions typically work best for centered text

## Future Enhancements

Possible future features:
- Support for additional radio station APIs (BBC, NPR, etc.)
- Custom overlay colors and fonts
- History of recently played programs
- Multiple station profiles with quick switching
- Show current song/track information (when available)
- Notification system for favorite programs

## Contributing

Contributions are welcome! If you'd like to add support for additional radio stations:

1. Create a new parser class in `parsers/` that inherits from `BaseParser`
2. Implement the `parse()` method to extract program data from JSON/API
3. Add your parser to `parsers/__init__.py`
4. Update the station type dropdown in `load.py`
5. Submit a pull request!

### Parser Development
The plugin uses a modular parser system:
- `BaseParser`: Abstract base class with common utilities
- `ORFParser`: JSON parser for ORF AudioAPI
- Easy to extend for new station types

## Credits

Developed for the Elite Dangerous community by commanders who enjoy listening to radio while exploring the galaxy.

Special thanks to:
- The EDCD team for Elite Dangerous Market Connector
- The EDMCOverlay developers for the in-game overlay functionality
- ORF (Austrian Broadcasting Corporation) for their excellent radio programming and open API

## Changelog

### Version 1.1.0
- ✨ Added configurable overlay positions (8 positions)
- 🔄 Switched from HTML parsing to JSON API
- 🚀 Improved reliability and performance
- 🧹 Removed image functionality (not available in API)
- 🐍 Full Python 3.x compatibility
- 📍 Smart text alignment based on position

### Version 1.0.0
- 🎉 Initial release
- Basic program information display
- In-game overlay support
- ORF Sound station support

## License

This project is released under the MIT License. See LICENSE file for details.

## Support

For bug reports, feature requests, or questions:
- Open an issue on GitHub
- Contact the developer through EDMC forums

Fly safe, Commanders! o7
