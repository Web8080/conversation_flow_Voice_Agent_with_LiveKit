"""
Google Calendar Integration Service
Handles appointment booking to Google Calendar
"""
from typing import Optional, Dict, Any
from datetime import datetime, date, time
import json
from utils.logger import logger
from config.settings import settings


class CalendarService:
    """Service for integrating with Google Calendar"""
    
    def __init__(self):
        self.enabled = False
        self.calendar_id = None
        
        # Check if Google Calendar API is configured
        if settings.google_application_credentials or settings.google_api_key:
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                import os
                
                # Initialize Google Calendar API client
                credentials = None
                
                # Try different credential sources
                if settings.google_application_credentials:
                    if os.path.exists(settings.google_application_credentials):
                        credentials = service_account.Credentials.from_service_account_file(
                            settings.google_application_credentials,
                            scopes=['https://www.googleapis.com/auth/calendar']
                        )
                elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
                    import json as json_lib
                    creds_json = json_lib.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_json,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
                
                if credentials:
                    self.calendar_service = build('calendar', 'v3', credentials=credentials)
                    self.enabled = True
                    # Use primary calendar by default
                    self.calendar_id = 'primary'
                    logger.info("Google Calendar service initialized", calendar_id=self.calendar_id)
                else:
                    logger.warning("Google Calendar credentials not found, calendar integration disabled")
            except ImportError:
                logger.warning("Google Calendar API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            except Exception as e:
                logger.error("Failed to initialize Google Calendar service", error=str(e))
        else:
            logger.info("Google Calendar integration disabled (no credentials configured)")
    
    async def create_appointment(
        self,
        appointment_date: date,
        appointment_time: time,
        summary: str = "Appointment",
        description: str = "",
        attendee_email: Optional[str] = None,
        duration_minutes: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Create an appointment in Google Calendar
        
        Args:
            appointment_date: Date of appointment
            appointment_time: Time of appointment
            summary: Event title
            description: Event description
            attendee_email: Optional attendee email
            duration_minutes: Duration in minutes (default 30)
        
        Returns:
            Dictionary with event details including event_id, html_link, etc.
        """
        if not self.enabled:
            logger.warning("Calendar service not enabled, appointment not created")
            return None
        
        try:
            # Combine date and time into datetime
            start_datetime = datetime.combine(appointment_date, appointment_time)
            end_datetime = start_datetime.replace(
                minute=start_datetime.minute + duration_minutes
            )
            
            # Format for Google Calendar API (RFC3339)
            start_time_str = start_datetime.isoformat() + 'Z'
            end_time_str = end_datetime.isoformat() + 'Z'
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time_str,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time_str,
                    'timeZone': 'UTC',
                },
            }
            
            # Add attendee if provided
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]
            
            # Create event
            created_event = self.calendar_service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info("Appointment created in Google Calendar",
                       event_id=created_event.get('id'),
                       start=start_time_str,
                       summary=summary)
            
            return {
                'event_id': created_event.get('id'),
                'html_link': created_event.get('htmlLink'),
                'start': start_time_str,
                'end': end_time_str,
                'summary': summary,
                'status': created_event.get('status')
            }
            
        except Exception as e:
            logger.error("Failed to create appointment in Google Calendar", error=str(e))
            return None
    
    def is_enabled(self) -> bool:
        """Check if calendar service is enabled"""
        return self.enabled

