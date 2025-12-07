"""
Base parser class for radio station data extraction
"""


class BaseParser:
    """
    Abstract base class for radio station parsers.
    Each radio station type should implement this interface.
    """
    
    def __init__(self):
        pass
    
    def parse(self, html_content):
        """
        Parse HTML content and extract program information.
        
        Args:
            html_content (str): Raw HTML content from the radio station page
            
        Returns:
            dict: Program information with keys:
                - program_name (str): Name of the current program
                - time_slot (str): Time slot (e.g., "12:10 - 12:56")
                - description (str): Program description/subtitle
                - author (str): Presenter/author name
                - image_url (str): URL to program image
                
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement parse() method")
    
    def get_parser_name(self):
        """
        Get the name of this parser.
        
        Returns:
            str: Parser name
        """
        return self.__class__.__name__
