"""
ED-RadioProgram Plugin for Elite Dangerous Market Connector
Displays current radio program information from online radio stations
"""
import tkinter as tk
from tkinter import ttk
import sys
import os
from datetime import datetime
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

this = sys.modules[__name__]

try:
    from config import config
except ImportError:
    config = dict()

try:
    import myNotebook as nb
except ImportError:
    nb = None

# Try to import EDMCOverlay
try:
    edmc_overlay_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'EDMCOverlay')
    if edmc_overlay_path not in sys.path:
        sys.path.append(edmc_overlay_path)
    from edmcoverlay import Overlay
    OVERLAY_AVAILABLE = True
except ImportError:
    OVERLAY_AVAILABLE = False
    Overlay = None

# Add plugin directory to path for parser imports
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from parsers import ORFParser

# Configuration keys
CFG_STATION_URL = "RadioProgramURL"
CFG_STATION_TYPE = "RadioProgramStationType"
CFG_OVERLAY_ENABLED = "RadioProgramOverlayEnabled"
CFG_OVERLAY_POSITION = "RadioProgramOverlayPosition"
CFG_SCREEN_WIDTH = "RadioProgramScreenWidth"
CFG_SCREEN_HEIGHT = "RadioProgramScreenHeight"
CFG_REFRESH_INTERVAL = "RadioProgramRefreshInterval"

# Default values
DEFAULT_URL = "https://audioapi.orf.at/oe1/api/json/current/broadcasts"
DEFAULT_STATION_TYPE = "ORF Sound"
DEFAULT_REFRESH_INTERVAL = 10  # minutes
DEFAULT_OVERLAY_POSITION = "top-left"
DEFAULT_SCREEN_WIDTH = 1920
DEFAULT_SCREEN_HEIGHT = 1080

# Overlay position presets (percentage-based for scaling)
OVERLAY_POSITIONS = {
    "top-left": (0.03, 0.08),      # 3% from left, 8% from top
    "top-middle": (0.40, 0.08),     # 40% from left (shifted left for better centering), 8% from top
    "top-right": (0.85, 0.08),      # 85% from left (adjusted to stay on-screen), 8% from top
    "middle-left": (0.03, 0.45),    # 3% from left, 45% from top (middle)
    "middle-right": (0.85, 0.45),   # 85% from left (adjusted to stay on-screen), 45% from top
    "bottom-left": (0.03, 0.75),    # 3% from left, 75% from top (raised from 82%)
    "bottom-middle": (0.40, 0.75),  # 40% from left (shifted left), 75% from top (raised from 82%)
    "bottom-right": (0.85, 0.75)    # 85% from left (adjusted), 75% from top (raised from 82%)
}

# Common screen resolutions
SCREEN_RESOLUTIONS = {
    "1920x1080 (Full HD)": (1920, 1080),
    "1920x1200 (WUXGA)": (1920, 1200),
    "2560x1440 (2K)": (2560, 1440),
    "3840x2160 (4K)": (3840, 2160),
    "Custom": (0, 0)  # User will enter manually
}


class RadioProgramPlugin:
    """Main class for the ED-RadioProgram plugin"""
    
    def __init__(self):
        self.station_url = DEFAULT_URL
        self.station_type = DEFAULT_STATION_TYPE
        self.overlay_enabled = True
        self.overlay_position = DEFAULT_OVERLAY_POSITION
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_height = DEFAULT_SCREEN_HEIGHT
        self.refresh_interval = DEFAULT_REFRESH_INTERVAL
        
        self.program_data = None
        self.last_update = None
        self.refresh_timer = None
        self.parent = None
        self.is_fetching = False
        
        # Parser
        self.parser = ORFParser()
        
        # UI widgets
        self.status_label = None
        self.program_frame = None
        self.program_name_label = None
        self.time_slot_label = None
        self.description_label = None
        self.author_label = None
        self.refresh_button = None
        self.overlay_button = None
        
        # Initialize overlay if available
        self.overlay_client = None
        if OVERLAY_AVAILABLE:
            try:
                self.overlay_client = Overlay()
            except Exception as e:
                print(f"ED-RadioProgram: Could not initialize overlay: {e}")

    def load_config(self):
        """Load saved configuration"""
        self.station_url = config.get(CFG_STATION_URL) or DEFAULT_URL
        self.station_type = config.get(CFG_STATION_TYPE) or DEFAULT_STATION_TYPE
        self.overlay_enabled = config.get_bool(CFG_OVERLAY_ENABLED, default=True)
        self.overlay_position = config.get(CFG_OVERLAY_POSITION) or DEFAULT_OVERLAY_POSITION
        
        # Load screen resolution
        try:
            self.screen_width = config.get_int(CFG_SCREEN_WIDTH) or DEFAULT_SCREEN_WIDTH
            self.screen_height = config.get_int(CFG_SCREEN_HEIGHT) or DEFAULT_SCREEN_HEIGHT
        except:
            self.screen_width = DEFAULT_SCREEN_WIDTH
            self.screen_height = DEFAULT_SCREEN_HEIGHT
        
        # Validate overlay position
        if self.overlay_position not in OVERLAY_POSITIONS:
            self.overlay_position = DEFAULT_OVERLAY_POSITION
        
        try:
            interval = config.get_int(CFG_REFRESH_INTERVAL)
            if interval and 5 <= interval <= 60:
                self.refresh_interval = interval
            else:
                self.refresh_interval = DEFAULT_REFRESH_INTERVAL
        except:
            self.refresh_interval = DEFAULT_REFRESH_INTERVAL

    def save_config(self):
        """Save configuration"""
        config.set(CFG_STATION_URL, self.station_url)
        config.set(CFG_STATION_TYPE, self.station_type)
        config.set(CFG_OVERLAY_ENABLED, self.overlay_enabled)
        config.set(CFG_OVERLAY_POSITION, self.overlay_position)
        config.set(CFG_SCREEN_WIDTH, self.screen_width)
        config.set(CFG_SCREEN_HEIGHT, self.screen_height)
        config.set(CFG_REFRESH_INTERVAL, self.refresh_interval)

    def toggle_overlay(self):
        """Toggle overlay on/off"""
        self.overlay_enabled = not self.overlay_enabled
        self.save_config()
        
        if self.overlay_enabled:
            self.update_overlay()
            if self.overlay_button:
                self.overlay_button.config(text="Hide Overlay")
        else:
            self.clear_overlay()
            if self.overlay_button:
                self.overlay_button.config(text="Show Overlay")

    def _wrap_text(self, text, max_chars=50):
        """
        Wrap text to fit within specified character width
        
        Args:
            text: Text to wrap
            max_chars: Maximum characters per line
            
        Returns:
            List of wrapped lines
        """
        if not text or len(text) <= max_chars:
            return [text] if text else []
        
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            # +1 for space
            if current_length + word_length + (1 if current_line else 0) <= max_chars:
                current_line.append(word)
                current_length += word_length + (1 if current_line else 0)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def clear_overlay(self):
        """Clear all overlay messages"""
        if not OVERLAY_AVAILABLE or not self.overlay_client:
            return
        
        try:
            # Clear background shape
            self.overlay_client.send_shape("radioprogram_bg", "rect", "#000000", "#000000", 0, 0, 1, 1, ttl=1)
            
            # Clear all overlay messages  
            for i in range(20):  # Increased for more lines
                self.overlay_client.send_message(f"radioprogram_{i}", "", "yellow", 0, 0, ttl=1)
        except Exception as e:
            print(f"ED-RadioProgram: Error clearing overlay: {e}")

    def update_overlay(self):
        """Update the overlay with current program data - Radio Station Styled"""
        if not self.overlay_enabled or not OVERLAY_AVAILABLE or not self.overlay_client:
            return
        
        if not self.program_data or "error" in self.program_data:
            self.clear_overlay()
            return
        
        try:
            # Calculate TTL: refresh interval + 1 minute buffer (in seconds)
            ttl_seconds = (self.refresh_interval + 1) * 60
            
            # Get position percentages and convert to actual pixels based on resolution
            pos_x_pct, pos_y_pct = OVERLAY_POSITIONS.get(self.overlay_position, OVERLAY_POSITIONS[DEFAULT_OVERLAY_POSITION])
            overlay_x = int(pos_x_pct * self.screen_width)
            overlay_y = int(pos_y_pct * self.screen_height)
            
            # Build styled overlay content
            lines = []
            colors = []
            sizes = []
            
            # Top border
            lines.append("╔════════════════════════════════════╗")
            colors.append("#00FFFF")  # Cyan
            sizes.append("normal")
            
            # Program name with music note icons (large, cyan)
            program_name = self.program_data.get('program_name', 'Unknown Program')
            wrapped_name = self._wrap_text(program_name, 32)
            for name_line in wrapped_name:
                lines.append(f"║ 🎵 {name_line}")
                colors.append("#00FFFF")  # Cyan for station name
                sizes.append("large")
            
            # Separator
            lines.append("║────────────────────────────────────║")
            colors.append("#00FFFF")
            sizes.append("normal")
            
            # Time slot (green like digital clock)
            time_slot = self.program_data.get('time_slot', '')
            if time_slot:
                lines.append(f"║ ⏰ {time_slot}")
                colors.append("#00FF00")  # Green
                sizes.append("normal")
            
            # Presenter (orange, warm)
            author = self.program_data.get('author', '')
            if author:
                wrapped_author = self._wrap_text(author, 30)
                for author_line in wrapped_author:
                    lines.append(f"║ 🎙️ {author_line}")
                    colors.append("#FFA500")  # Orange
                    sizes.append("normal")
            
            # Separator before description
            if author or time_slot:
                lines.append("║────────────────────────────────────║")
                colors.append("#00FFFF")
                sizes.append("normal")
            
            # Description (white, wrapped)
            description = self.program_data.get('description', '')
            if description:
                wrapped_desc = self._wrap_text(description, 34)
                for desc_line in wrapped_desc[:3]:  # Max 3 lines for description
                    lines.append(f"║ {desc_line}")
                    colors.append("#FFFFFF")  # White
                    sizes.append("normal")
                if len(wrapped_desc) > 3:
                    lines.append("║ ...")
                    colors.append("#FFFFFF")
                    sizes.append("normal")
            
            # Bottom border
            lines.append("╚════════════════════════════════════╝")
            colors.append("#00FFFF")
            sizes.append("normal")
            
            # Calculate box dimensions
            box_width = 400  # Fixed width for consistent look
            box_height = len(lines) * 18 + 20
            
            # Adjust position based on alignment
            if "right" in self.overlay_position:
                box_x = overlay_x - box_width
                text_x = overlay_x - box_width + 10
            elif "middle" in self.overlay_position and "left" not in self.overlay_position and "right" not in self.overlay_position:
                box_x = overlay_x - (box_width // 2)
                text_x = box_x + 10
            else:
                box_x = overlay_x
                text_x = overlay_x + 10
            
            # Draw background box with transparency
            try:
                self.overlay_client.send_shape(
                    "radioprogram_bg",
                    "rect",
                    "#000000",
                    "rgba(0,0,0,0.7)",  # Slightly more opaque for better readability
                    box_x,
                    overlay_y,
                    box_width,
                    box_height,
                    ttl=ttl_seconds
                )
            except Exception as e:
                print(f"ED-RadioProgram: Could not draw background box: {e}")
            
            # Send styled text to overlay
            y_offset = overlay_y + 5
            for i, (line, color, size) in enumerate(zip(lines, colors, sizes)):
                if i < 20:
                    try:
                        self.overlay_client.send_message(
                            f"radioprogram_{i}",
                            line,
                            color,
                            text_x,
                            y_offset,
                            ttl=ttl_seconds,
                            size=size
                        )
                        y_offset += 22 if size == "large" else 18
                    except Exception as e:
                        print(f"ED-RadioProgram: Error sending line {i}: {e}")
            
            # Clear any remaining old lines
            for i in range(len(lines), 20):
                self.overlay_client.send_message(f"radioprogram_{i}", "", "#FFFFFF", 0, 0, ttl=1)
                
        except Exception as e:
            print(f"ED-RadioProgram: Error updating overlay: {e}")

    def fetch_program_data(self):
        """Fetch program data from the radio station URL"""
        if not self.station_url:
            return {"error": "Station URL is required"}
        
        if self.is_fetching:
            return {"error": "Already fetching data"}
        
        self.is_fetching = True
        
        try:
            # Fetch the API data
            request = Request(
                self.station_url,
                headers={'User-Agent': 'ED-RadioProgram/1.0 (EDMC Plugin)'}
            )
            
            response = urlopen(request, timeout=15)
            json_content = response.read().decode('utf-8')
            
            self.is_fetching = False
            
            # Parse the content
            program_data = self.parser.parse(json_content)
            
            if not program_data:
                return {"error": "Could not parse program data"}
            
            return program_data
            
        except HTTPError as e:
            self.is_fetching = False
            return {"error": f"HTTP Error {e.code}: {e.reason}"}
        except URLError as e:
            self.is_fetching = False
            return {"error": f"Network Error: {str(e.reason)}"}
        except Exception as e:
            self.is_fetching = False
            return {"error": f"Error: {str(e)}"}

    def update_display(self):
        """Update the UI with current program data"""
        # Update overlay if enabled
        if self.overlay_enabled:
            self.update_overlay()
        
        if not self.program_frame:
            return
        
        # Check if it's an error
        if self.program_data and "error" in self.program_data:
            self._show_error(self.program_data['error'])
            return
        
        if not self.program_data:
            self._show_no_data()
            return
        
        # Update program name
        program_name = self.program_data.get('program_name', 'Unknown Program')
        if self.program_name_label:
            self.program_name_label.config(text=program_name, fg="black")
        
        # Update time slot
        time_slot = self.program_data.get('time_slot', '')
        if self.time_slot_label:
            if time_slot:
                self.time_slot_label.config(text=f"🕒 {time_slot}", fg="black")
            else:
                self.time_slot_label.config(text="")
        
        # Update description
        description = self.program_data.get('description', '')
        if self.description_label:
            if description:
                self.description_label.config(text=description, fg="black")
            else:
                self.description_label.config(text="")
        
        # Update author
        author = self.program_data.get('author', '')
        if self.author_label:
            if author:
                self.author_label.config(text=f"Presenter: {author}")
            else:
                self.author_label.config(text="")
        
        # Update status
        if self.status_label and self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            self.status_label.config(text=f"Last updated: {time_str}")

    def _show_error(self, error_msg):
        """Show error message in UI"""
        if self.program_name_label:
            self.program_name_label.config(text="Error", fg="red")
        if self.time_slot_label:
            self.time_slot_label.config(text="")
        if self.description_label:
            self.description_label.config(text=error_msg, fg="red")
        if self.author_label:
            self.author_label.config(text="")
        if self.status_label:
            self.status_label.config(text="Status: Error")

    def _show_no_data(self):
        """Show no data message in UI"""
        if self.program_name_label:
            self.program_name_label.config(text="No program data", fg="gray")
        if self.time_slot_label:
            self.time_slot_label.config(text="")
        if self.description_label:
            self.description_label.config(text="Waiting for data...", fg="gray")
        if self.author_label:
            self.author_label.config(text="")
        if self.status_label:
            self.status_label.config(text="Status: No data")

    def fetch_and_update(self):
        """Fetch data and update display (non-blocking)"""
        def fetch_thread():
            result = self.fetch_program_data()
            self.program_data = result
            self.last_update = datetime.now()
            
            # Schedule UI update on main thread
            if self.parent:
                self.parent.after(0, self.update_display)
        
        thread = Thread(target=fetch_thread)
        thread.daemon = True
        thread.start()

    def manual_refresh(self):
        """Handle manual refresh button click"""
        if self.status_label:
            self.status_label.config(text="Status: Refreshing...")
        self.fetch_and_update()

    def schedule_refresh(self):
        """Schedule automatic refresh"""
        if self.station_url:
            self.fetch_and_update()
        
        # Schedule next refresh (convert minutes to milliseconds)
        if self.parent and self.refresh_interval > 0:
            interval_ms = self.refresh_interval * 60 * 1000
            self.refresh_timer = self.parent.after(interval_ms, self.schedule_refresh)

    def stop_refresh(self):
        """Stop automatic refresh timer"""
        if self.refresh_timer and self.parent:
            self.parent.after_cancel(self.refresh_timer)
            self.refresh_timer = None
        
        # Clear overlay on stop
        self.clear_overlay()


def plugin_start3(plugin_dir):
    """Plugin start for Python 3"""
    return plugin_start(plugin_dir)


def plugin_start(plugin_dir):
    """Initialize plugin"""
    plugin = RadioProgramPlugin()
    plugin.load_config()
    this.plugin = plugin
    return "ED-RadioProgram"


def plugin_stop():
    """Clean up when plugin stops"""
    if hasattr(this, 'plugin') and this.plugin:
        this.plugin.stop_refresh()


def plugin_app(parent):
    """Create UI for EDMC main window"""
    if not hasattr(this, 'plugin'):
        return None
    
    plugin = this.plugin
    plugin.parent = parent
    
    # Main frame
    frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    
    # Program frame
    plugin.program_frame = tk.Frame(frame)
    plugin.program_frame.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)
    plugin.program_frame.columnconfigure(0, weight=1)
    
    # Program name (large, bold)
    plugin.program_name_label = tk.Label(
        plugin.program_frame,
        text="ED-RadioProgram",
        font=("TkDefaultFont", 11, "bold"),
        justify=tk.LEFT,
        wraplength=300
    )
    plugin.program_name_label.grid(row=0, column=0, sticky=tk.W)
    
    # Time slot
    plugin.time_slot_label = tk.Label(
        plugin.program_frame,
        text="",
        justify=tk.LEFT
    )
    plugin.time_slot_label.grid(row=1, column=0, sticky=tk.W)
    
    # Description
    plugin.description_label = tk.Label(
        plugin.program_frame,
        text="Configure in Settings",
        justify=tk.LEFT,
        wraplength=300,
        fg="gray"
    )
    plugin.description_label.grid(row=2, column=0, sticky=tk.W)
    
    # Author
    plugin.author_label = tk.Label(
        plugin.program_frame,
        text="",
        justify=tk.LEFT,
        fg="blue"
    )
    plugin.author_label.grid(row=3, column=0, sticky=tk.W)
    
    # Button frame
    button_frame = tk.Frame(frame)
    button_frame.grid(row=1, column=0, sticky=tk.E, padx=5)
    
    # Refresh button
    plugin.refresh_button = tk.Button(
        button_frame,
        text="Refresh",
        command=plugin.manual_refresh
    )
    plugin.refresh_button.pack(side=tk.LEFT, padx=2)
    
    # Overlay toggle button (only if overlay is available)
    if OVERLAY_AVAILABLE and plugin.overlay_client:
        overlay_text = "Hide Overlay" if plugin.overlay_enabled else "Show Overlay"
        plugin.overlay_button = tk.Button(
            button_frame,
            text=overlay_text,
            command=plugin.toggle_overlay
        )
        plugin.overlay_button.pack(side=tk.LEFT, padx=2)
    
    # Status label
    plugin.status_label = tk.Label(
        frame,
        text="Status: Initializing...",
        justify=tk.LEFT,
        fg="gray"
    )
    plugin.status_label.grid(row=2, column=0, sticky=tk.W, padx=5)
    
    # Start automatic refresh
    plugin.schedule_refresh()
    
    return frame


def plugin_prefs(parent, cmdr, is_beta):
    """Create preferences UI"""
    if not hasattr(this, 'plugin'):
        return None
    
    plugin = this.plugin
    
    # Create frame
    if nb:
        frame = nb.Frame(parent)
    else:
        frame = tk.Frame(parent)
    
    frame.columnconfigure(1, weight=1)
    
    # Title
    row = 0
    if nb:
        title_label = nb.Label(frame, text="ED-RadioProgram Configuration")
    else:
        title_label = tk.Label(frame, text="ED-RadioProgram Configuration")
    title_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
    
    # Station URL
    row += 1
    if nb:
        url_label = nb.Label(frame, text="Radio Station API URL:")
    else:
        url_label = tk.Label(frame, text="Radio Station API URL:")
    url_label.grid(row=row, column=0, sticky=tk.W, padx=10)
    
    this.station_url_var = tk.StringVar(value=plugin.station_url)
    if nb:
        url_entry = nb.Entry(frame, textvariable=this.station_url_var, width=50)
    else:
        url_entry = tk.Entry(frame, textvariable=this.station_url_var, width=50)
    url_entry.grid(row=row, column=1, sticky=tk.EW, padx=10)
    
    # Station Type (for future extensibility)
    row += 1
    if nb:
        type_label = nb.Label(frame, text="Station Type:")
    else:
        type_label = tk.Label(frame, text="Station Type:")
    type_label.grid(row=row, column=0, sticky=tk.W, padx=10)
    
    this.station_type_var = tk.StringVar(value=plugin.station_type)
    if nb:
        type_combo = ttk.Combobox(
            frame,
            textvariable=this.station_type_var,
            values=["ORF Sound"],
            state="readonly",
            width=47
        )
    else:
        type_combo = ttk.Combobox(
            frame,
            textvariable=this.station_type_var,
            values=["ORF Sound"],
            state="readonly",
            width=47
        )
    type_combo.grid(row=row, column=1, sticky=tk.EW, padx=10)
    
    # Refresh Interval
    row += 1
    if nb:
        interval_label = nb.Label(frame, text="Refresh Interval (minutes):")
    else:
        interval_label = tk.Label(frame, text="Refresh Interval (minutes):")
    interval_label.grid(row=row, column=0, sticky=tk.W, padx=10)
    
    this.refresh_interval_var = tk.IntVar(value=plugin.refresh_interval)
    if nb:
        interval_spinbox = tk.Spinbox(
            frame,
            from_=5,
            to=60,
            textvariable=this.refresh_interval_var,
            width=10
        )
    else:
        interval_spinbox = tk.Spinbox(
            frame,
            from_=5,
            to=60,
            textvariable=this.refresh_interval_var,
            width=10
        )
    interval_spinbox.grid(row=row, column=1, sticky=tk.W, padx=10)
    
    # Screen Resolution
    row += 1
    if nb:
        res_label = nb.Label(frame, text="Game Screen Resolution:")
    else:
        res_label = tk.Label(frame, text="Game Screen Resolution:")
    res_label.grid(row=row, column=0, sticky=tk.W, padx=10)
    
    # Find current resolution in presets
    current_res_name = "Custom"
    for res_name, (width, height) in SCREEN_RESOLUTIONS.items():
        if width == plugin.screen_width and height == plugin.screen_height and res_name != "Custom":
            current_res_name = res_name
            break
    
    this.screen_resolution_var = tk.StringVar(value=current_res_name)
    resolution_values = list(SCREEN_RESOLUTIONS.keys())
    
    if nb:
        res_combo = ttk.Combobox(
            frame,
            textvariable=this.screen_resolution_var,
            values=resolution_values,
            state="readonly",
            width=47
        )
    else:
        res_combo = ttk.Combobox(
            frame,
            textvariable=this.screen_resolution_var,
            values=resolution_values,
            state="readonly",
            width=47
        )
    res_combo.grid(row=row, column=1, sticky=tk.EW, padx=10)
    
    # Custom resolution fields (only shown if Custom is selected)
    row += 1
    if nb:
        custom_res_label = nb.Label(frame, text="Custom Resolution (WxH):")
    else:
        custom_res_label = tk.Label(frame, text="Custom Resolution (WxH):")
    custom_res_label.grid(row=row, column=0, sticky=tk.W, padx=10)
    
    custom_frame = tk.Frame(frame)
    custom_frame.grid(row=row, column=1, sticky=tk.W, padx=10)
    
    this.custom_width_var = tk.IntVar(value=plugin.screen_width)
    this.custom_height_var = tk.IntVar(value=plugin.screen_height)
    
    width_spinbox = tk.Spinbox(
        custom_frame,
        from_=800,
        to=7680,
        textvariable=this.custom_width_var,
        width=8
    )
    width_spinbox.pack(side=tk.LEFT, padx=2)
    
    tk.Label(custom_frame, text="x").pack(side=tk.LEFT)
    
    height_spinbox = tk.Spinbox(
        custom_frame,
        from_=600,
        to=4320,
        textvariable=this.custom_height_var,
        width=8
    )
    height_spinbox.pack(side=tk.LEFT, padx=2)
    
    # Enable Overlay checkbox
    row += 1
    if OVERLAY_AVAILABLE:
        this.overlay_enabled_var = tk.IntVar(value=1 if plugin.overlay_enabled else 0)
        if nb:
            overlay_check = nb.Checkbutton(
                frame,
                text="Enable in-game overlay",
                variable=this.overlay_enabled_var
            )
        else:
            overlay_check = tk.Checkbutton(
                frame,
                text="Enable in-game overlay",
                variable=this.overlay_enabled_var
            )
        overlay_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
        # Overlay Position
        row += 1
        if nb:
            position_label = nb.Label(frame, text="Overlay Position:")
        else:
            position_label = tk.Label(frame, text="Overlay Position:")
        position_label.grid(row=row, column=0, sticky=tk.W, padx=10)
        
        # Create human-readable position names
        position_names = {
            "top-left": "Top Left",
            "top-middle": "Top Middle",
            "top-right": "Top Right",
            "middle-left": "Middle Left",
            "middle-right": "Middle Right",
            "bottom-left": "Bottom Left",
            "bottom-middle": "Bottom Middle",
            "bottom-right": "Bottom Right"
        }
        
        this.overlay_position_var = tk.StringVar(value=plugin.overlay_position)
        position_values = list(OVERLAY_POSITIONS.keys())
        position_display = [position_names.get(p, p) for p in position_values]
        
        if nb:
            position_combo = ttk.Combobox(
                frame,
                textvariable=this.overlay_position_var,
                values=position_values,
                state="readonly",
                width=47
            )
        else:
            position_combo = ttk.Combobox(
                frame,
                textvariable=this.overlay_position_var,
                values=position_values,
                state="readonly",
                width=47
            )
        position_combo.grid(row=row, column=1, sticky=tk.EW, padx=10)
    
    # Help text
    row += 1
    help_text = (
        "Enter the ORF AudioAPI URL for your radio station.\n"
        "Currently supports ORF Sound stations (Ö1, FM4, Ö3, etc.).\n\n"
        "Examples:\n"
        "  • Ö1: https://audioapi.orf.at/oe1/api/json/current/broadcasts\n"
        "  • FM4: https://audioapi.orf.at/fm4/api/json/current/broadcasts\n"
        "  • Ö3: https://audioapi.orf.at/oe3/api/json/current/broadcasts\n\n"
        "The plugin displays the current program name, time slot, and\n"
        "description both in EDMC and in-game (overlay)."
    )
    if nb:
        help_label = nb.Label(frame, text=help_text, justify=tk.LEFT)
    else:
        help_label = tk.Label(frame, text=help_text, justify=tk.LEFT)
    help_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
    
    return frame


def prefs_changed(cmdr, is_beta):
    """Handle preference changes"""
    if not hasattr(this, 'plugin'):
        return
    
    plugin = this.plugin
    
    # Update configuration
    if hasattr(this, 'station_url_var'):
        plugin.station_url = this.station_url_var.get()
    
    if hasattr(this, 'station_type_var'):
        plugin.station_type = this.station_type_var.get()
    
    if hasattr(this, 'refresh_interval_var'):
        try:
            interval = this.refresh_interval_var.get()
            if 5 <= interval <= 60:
                plugin.refresh_interval = interval
        except:
            pass
    
    # Update screen resolution
    if hasattr(this, 'screen_resolution_var'):
        resolution_name = this.screen_resolution_var.get()
        if resolution_name in SCREEN_RESOLUTIONS:
            width, height = SCREEN_RESOLUTIONS[resolution_name]
            # If Custom, use the custom values
            if resolution_name == "Custom" and hasattr(this, 'custom_width_var') and hasattr(this, 'custom_height_var'):
                try:
                    custom_width = this.custom_width_var.get()
                    custom_height = this.custom_height_var.get()
                    if 800 <= custom_width <= 7680 and 600 <= custom_height <= 4320:
                        plugin.screen_width = custom_width
                        plugin.screen_height = custom_height
                except:
                    pass
            elif width > 0 and height > 0:
                # Use preset resolution
                plugin.screen_width = width
                plugin.screen_height = height
    
    # Update overlay setting
    if OVERLAY_AVAILABLE and hasattr(this, 'overlay_enabled_var'):
        old_overlay_state = plugin.overlay_enabled
        plugin.overlay_enabled = bool(this.overlay_enabled_var.get())
        
        if old_overlay_state != plugin.overlay_enabled:
            if plugin.overlay_button:
                button_text = "Hide Overlay" if plugin.overlay_enabled else "Show Overlay"
                plugin.overlay_button.config(text=button_text)
            
            if plugin.overlay_enabled:
                plugin.update_overlay()
            else:
                plugin.clear_overlay()
    
    # Update overlay position setting
    if OVERLAY_AVAILABLE and hasattr(this, 'overlay_position_var'):
        new_position = this.overlay_position_var.get()
        if new_position in OVERLAY_POSITIONS:
            old_position = plugin.overlay_position
            plugin.overlay_position = new_position
            
            # If position changed and overlay is enabled, refresh it
            if old_position != new_position and plugin.overlay_enabled:
                plugin.update_overlay()
    
    plugin.save_config()
    
    # Restart refresh timer with new interval
    plugin.stop_refresh()
    plugin.schedule_refresh()
