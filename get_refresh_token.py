from google_auth_oauthlib.flow import InstalledAppFlow

# 구글 캘린더 및 유튜브 분석 읽기 권한 설정
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]

def get_refresh_token():
    # credentials.json 파일을 기반으로 인증 플로우 시작
    # access_type='offline' 설정이 들어가야 Refresh Token이 발급됩니다.
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    # prompt='consent'를 주어 매번 동의 화면을 띄우고 Refresh Token을 강제로 받아옵니다.
    credentials = flow.run_local_server(port=0, prompt='consent', access_type='offline')
    
    print("\n=== 인증 성공! ===")
    print(f"Access Token: {credentials.token}")
    print(f"Refresh Token: {credentials.refresh_token}") # 👈 우리가 원하는 것!
    
    # 발급된 Refresh Token과 관련 정보를 나중에 쓰기 쉽게 파일로 저장하면 좋습니다.
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    
    import json
    with open('token_response.json', 'w') as f:
        json.dump(token_data, f, indent=4)
    print("\n인증 정보가 'token_response.json' 파일에 저장되었습니다.")

if __name__ == '__main__':
    get_refresh_token()
