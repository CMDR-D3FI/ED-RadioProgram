"""
Parser for ORF Sound radio station JSON API
"""

import json
import re
from datetime import datetime
from .base_parser import BaseParser


class ORFParser(BaseParser):
    """
    Parser for ORF Sound radio stations (e.g., Ö1, FM4, etc.)
    Fetches current program information from ORF AudioAPI JSON endpoint
    """
    
    def __init__(self):
        super().__init__()
    
    def parse(self, json_content):
        """
        Parse ORF AudioAPI JSON content and extract current program information.
        
        Args:
            json_content (str): Raw JSON string from ORF AudioAPI
            
        Returns:
            dict: Program information or None if parsing fails
        """
        try:
            # Parse JSON
            data = json.loads(json_content)
            
            if not isinstance(data, list) or len(data) == 0:
                return None
            
            # Get current timestamp in milliseconds
            current_time_ms = int(datetime.now().timestamp() * 1000)
            
            # Search through all days and broadcasts to find the current one
            current_broadcast = None
            
            for day_data in data:
                if 'broadcasts' not in day_data:
                    continue
                
                for broadcast in day_data['broadcasts']:
                    start_time = broadcast.get('start', 0)
                    end_time = broadcast.get('end', 0)
                    
                    # Check if current time falls within this broadcast
                    if start_time <= current_time_ms <= end_time:
                        current_broadcast = broadcast
                        break
                
                if current_broadcast:
                    break
            
            if not current_broadcast:
                # No current broadcast found, return None
                return None
            
            # Extract program information
            program_data = {
                'program_name': '',
                'time_slot': '',
                'description': '',
                'author': '',
                'image_url': ''
            }
            
            # Program name - prefer programTitle, fallback to title
            program_title = current_broadcast.get('programTitle')
            title = current_broadcast.get('title', '')
            
            if program_title:
                program_data['program_name'] = program_title
                # If there's also a different title, use it as description
                if title and title != program_title:
                    program_data['description'] = title
            else:
                program_data['program_name'] = title
            
            # Time slot - format the start and end times
            start_iso = current_broadcast.get('startISO', '')
            end_iso = current_broadcast.get('endISO', '')
            
            if start_iso and end_iso:
                try:
                    # Parse ISO datetime and format as HH:MM
                    start_dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
                    program_data['time_slot'] = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')} Uhr"
                except:
                    pass
            
            # Description - from subtitle field (may contain HTML)
            subtitle = current_broadcast.get('subtitle', '')
            if subtitle:
                # Clean HTML tags from subtitle
                program_data['description'] = self._clean_html(subtitle)
            
            # Image URL - we need to fetch the detailed broadcast info
            # The href field points to detailed broadcast data which contains the image
            href = current_broadcast.get('href', '')
            if href:
                # Store href so we can fetch image later
                program_data['detail_url'] = href
            
            # Author/presenter - not directly available in this API
            # Would need to parse from subtitle or fetch detail URL
            
            return program_data
            
        except Exception as e:
            print(f"ORFParser error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _clean_html(self, text):
        """
        Clean HTML tags and entities from text.
        
        Args:
            text (str): Text with potential HTML
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
