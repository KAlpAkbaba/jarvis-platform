import os
import json
from datetime import datetime, timedelta
from typing import Optional, List

class CalendarService:
    def __init__(self):
        self.google_service = None
        self.outlook_token = None
        self.provider = None

    # ---- GOOGLE CALENDAR ----
    def connect_google(self, credentials_json: str):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ['https://www.googleapis.com/auth/calendar']
            token_path = '/app/data/google_token.json'
            creds = None

            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_json, SCOPES)
                creds = flow.run_local_server(port=0)
                os.makedirs('/app/data', exist_ok=True)
                with open(token_path, 'w') as f:
                    f.write(creds.to_json())

            self.google_service = build('calendar', 'v3', credentials=creds)
            self.provider = 'google'
            return True
        except Exception as e:
            print(f'Google Calendar baglanti hatasi: {e}')
            return False

    def get_google_events(self, days: int = 7) -> List[dict]:
        if not self.google_service:
            return []
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
            result = self.google_service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=end,
                maxResults=20,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return result.get('items', [])
        except Exception as e:
            print(f'Google events hatasi: {e}')
            return []

    def add_google_event(self, title: str, start: datetime, end: datetime = None, description: str = '') -> bool:
        if not self.google_service:
            return False
        try:
            if not end:
                end = start + timedelta(hours=1)
            event = {
                'summary': title,
                'description': description,
                'start': {'dateTime': start.isoformat(), 'timeZone': 'Europe/Istanbul'},
                'end': {'dateTime': end.isoformat(), 'timeZone': 'Europe/Istanbul'},
            }
            self.google_service.events().insert(calendarId='primary', body=event).execute()
            return True
        except Exception as e:
            print(f'Google event ekle hatasi: {e}')
            return False

    # ---- OUTLOOK CALENDAR ----
    def connect_outlook(self, client_id: str, tenant_id: str = 'common') -> str:
        try:
            import msal
            self.outlook_app = msal.PublicClientApplication(
                client_id,
                authority=f'https://login.microsoftonline.com/{tenant_id}'
            )
            SCOPES = ['Calendars.ReadWrite']
            flow = self.outlook_app.initiate_device_flow(scopes=SCOPES)
            return flow.get('message', 'Outlook baglantisi baslatildi')
        except Exception as e:
            return f'Outlook baglanti hatasi: {e}'

    def get_outlook_events(self, days: int = 7) -> List[dict]:
        if not self.outlook_token:
            return []
        try:
            import requests
            headers = {'Authorization': f'Bearer {self.outlook_token}', 'Content-Type': 'application/json'}
            now = datetime.utcnow().isoformat() + 'Z'
            end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
            url = f'https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={now}&endDateTime={end}&$top=20&$orderby=start/dateTime'
            res = requests.get(url, headers=headers)
            return res.json().get('value', [])
        except Exception as e:
            print(f'Outlook events hatasi: {e}')
            return []

    # ---- GENEL ----
    def get_events(self, days: int = 7) -> List[dict]:
        if self.provider == 'google':
            return self.get_google_events(days)
        elif self.provider == 'outlook':
            return self.get_outlook_events(days)
        return []

    def format_events(self, events: List[dict]) -> str:
        if not events:
            return 'Takvimde yaklaşan etkinlik yok.'
        result = []
        for e in events[:10]:
            if self.provider == 'google':
                title = e.get('summary', 'Başlıksız')
                start = e.get('start', {}).get('dateTime', e.get('start', {}).get('date', ''))
            else:
                title = e.get('subject', 'Başlıksız')
                start = e.get('start', {}).get('dateTime', '')
            if start:
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    start = dt.strftime('%d %B %Y %H:%M')
                except:
                    pass
            result.append(f'{start} — {title}')
        return '\n'.join(result)
