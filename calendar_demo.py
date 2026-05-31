import datetime
import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# 구글 캘린더 API를 사용할 수 있는 범위(Scope) 설정
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    token_response.json에 저장된 Refresh Token을 활용하여 
    구글 캘린더 API 서비스 객체를 반환합니다.
    """
    token_path = 'token_response.json'
    
    if not os.path.exists(token_path):
        raise FileNotFoundError(
            "먼저 'get_refresh_token.py'를 실행하여 'token_response.json' 파일을 생성해 주세요!"
        )
        
    with open(token_path, 'r') as f:
        token_data = json.load(f)
        
    # token_response.json에서 저장한 정보를 기반으로 Credentials 객체를 생성합니다.
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes')
    )
    
    # 만약 Access Token이 만료되었다면 Refresh Token을 이용해 자동으로 갱신합니다.
    if creds and creds.expired and creds.refresh_token:
        print("Access Token이 만료되어 Refresh Token으로 갱신을 진행합니다...")
        creds.refresh(Request())
        
        # 갱신된 Access Token 정보를 파일에 다시 업데이트합니다.
        token_data['token'] = creds.token
        with open(token_path, 'w') as f:
            json.dump(token_data, f, indent=4)
        print("새로운 Access Token이 'token_response.json'에 업데이트되었습니다.")
        
    # 구글 캘린더 API 서비스 객체 빌드
    service = build('calendar', 'v3', credentials=creds)
    return service

def list_upcoming_events(max_results=10):
    """최근 일정을 조회하여 출력합니다."""
    try:
        service = get_calendar_service()
        
        # '현재 시간'을 ISO 포맷으로 설정
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z'는 UTC를 나타냅니다.
        print(f"\n📅 향후 {max_results}개의 일정을 조회합니다...")
        
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            print('가까운 미래에 예정된 일정이 없습니다.')
            return

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"- {start} : {event.get('summary')} (ID: {event.get('id')})")
            
    except Exception as e:
        print(f"일정 조회 중 에러 발생: {e}")

def create_event(summary, description, start_time_str, duration_minutes=60):
    """
    새로운 일정을 추가합니다.
    start_time_str 형식 예: '2026-06-01T15:00:00' (YYYY-MM-DDTHH:MM:SS)
    """
    try:
        service = get_calendar_service()
        
        # 입력받은 시작 시간을 기반으로 끝나는 시간 계산
        start_time = datetime.datetime.fromisoformat(start_time_str)
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)
        
        # 구글 캘린더는 시간대(Timezone) 정보가 필요하므로 한국 시간대(Asia/Seoul)를 기준으로 설정합니다.
        event_body = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
        }

        event = service.events().insert(calendarId='primary', body=event_body).execute()
        print(f"\n🎉 일정이 성공적으로 생성되었습니다!")
        print(f"일정 제목: {event.get('summary')}")
        print(f"링크: {event.get('htmlLink')}")
        
    except Exception as e:
        print(f"일정 생성 중 에러 발생: {e}")

if __name__ == '__main__':
    # 1. 캘린더 일정 목록 조회 테스트
    list_upcoming_events(max_results=5)
    
    # 2. 새로운 일정 추가 테스트 (주석을 해제하여 테스트해보세요!)
    # print("\n새로운 테스트 일정을 추가해 봅니다...")
    # tomorrow_3pm = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT15:00:00')
    # create_event(
    #     summary='구글 캘린더 API 테스트 일정',
    #     description='안티그래비티 코딩 에이전트와 함께 만든 캘린더 API 연동 테스트 일정입니다.',
    #     start_time_str=tomorrow_3pm,
    #     duration_minutes=30
    # )
