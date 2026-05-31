# 💻 Developer — 획득한 PAT를 사용하여, 실제 데이터를 읽어오는 '읽기 전용(Read-Only)' 테스트 API 호출 함수를 작성하라. 이 함수는 오류 발생 시 (예: 401 Unauthorized, 403 Forbidden) 정확한 에러 코드를 반환하도록 Try/Catch 로직을 포함해야 한다.

💻 Developer: 작업 시작합니다.

CEO님의 지시에 따라, 획득한 PAT를 사용하여 특정 자산 저장소의 콘텐츠를 읽어오는 **읽기 전용(Read-Only) 테스트 API 호출 함수**를 작성했습니다. 이 함수는 네트워크 오류와 API 응답 오류(401, 403 등)를 명확하게 구분하고, 발생한 오류 코드를 반환하도록 설계되었습니다.

이 코드는 `requests` 라이브러리와 환경 변수(`GITHUB_PAT`) 사용을 전제로 합니다.

### 🚀 API 테스트 함수 (Python)

```python
import requests
import os
from typing import Optional, Dict, Any

# 환경 변수에서 PAT를 로드합니다.
# 보안을 위해 실제 PAT를 코드에 하드코딩하지 않고, 환경변수로 관리합니다.
# 실행 전 반드시 'export GITHUB_PAT="***REMOVED***..."'를 실행해야 합니다.
GITHUB_PAT = os.environ.get("GITHUB_PAT")

def fetch_github_content_read_only(
    owner: str, 
    repo: str, 
    path: str = "main/README.md"
) -> Dict[str, Any]:
    """
    GitHub API를 사용하여 특정 경로의 콘텐츠를 읽어오는 Read-Only 테스트 함수.

    Args:
        owner (str): 저장소 소유자 (예: 'jaycorp-org').
        repo (str): 저장소 이름 (예: 'assets-repo').
        path (str): 읽어올 파일의 경로 (예: 'docs/index.md').

    Returns:
        Dict[str, Any]: 성공 시 콘텐츠 정보를 담거나, 실패 시 오류 코드를 담은 딕셔너리.
    """
    
    # GitHub Contents API 엔드포인트 구성
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    # 헤더 설정: PAT를 Bearer Token으로 전달하고, 에이전트 정보 설정
    headers = {
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    print(f"--- API 호출 시도: {url} ---")

    try:
        # 1. API 호출 실행
        response = requests.get(url, headers=headers, timeout=10)
        
        # 2. HTTP 상태 코드 기반 오류 처리 (API 레벨 오류)
        if response.status_code == 200:
            # 성공 시: JSON 파싱 및 데이터 반환
            data = response.json()
            return {
                "status": "SUCCESS",
                "http_code": 200,
                "data": data
            }
        
        elif response.status_code == 401:
            # 401 Unauthorized: 토큰이 만료되었거나 유효하지 않음 (Credential 문제)
            return {
                "status": "ERROR",
                "http_code": 401,
                "error_message": "Unauthorized Access: PAT가 유효하지 않거나 만료되었습니다. 토큰을 확인해주세요.",
                "action": "PAT 재발급 또는 환경변수 확인 필요."
            }
        
        elif response.status_code == 403:
            # 403 Forbidden: 토큰은 유효하지만, 요청된 Scope가 부족하거나 권한이 없음 (Permission 문제)
            # (이것이 가장 흔하게 발생하는 보안 오류입니다.)
            return {
                "status": "ERROR",
                "http_code": 403,
                "error_message": "Forbidden Access: PAT의 권한(Scope)이 요청된 자산에 접근하기에 부족합니다. (예: Read 권한만 필요함)",
                "action": "Business Agent에게 최소 Scope 재요청이 필요합니다."
            }
        
        elif response.status_code == 404:
            # 404 Not Found: 저장소나 경로 자체가 존재하지 않음 (Resource 문제)
            return {
                "status": "ERROR",
                "http_code": 404,
                "error_message": "Not Found: 지정된 저장소 또는 파일 경로가 존재하지 않습니다.",
                "action": "Owner, Repo, Path 인자를 재확인해주세요."
            }
        
        else:
            # 그 외의 HTTP 오류 처리
            return {
                "status": "ERROR",
                "http_code": response.status_code,
                "error_message": f"알 수 없는 API 오류가 발생했습니다. 상태 코드: {response.status_code}",
                "action": "GitHub API 문서를 참고하거나, 로그를 확인해주세요."
            }

    # 3. 네트워크 오류 처리 (연결 끊김, 타임아웃 등)
    except requests.exceptions.Timeout:
        return {
            "status": "FATAL_ERROR",
            "http_code": 408, # 408 Request Timeout을 임시 사용
            "error_message": "Timeout Error: API 요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요.",
            "action": "네트워크 연결 상태를 점검해주세요."
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "FATAL_ERROR",
            "http_code": 503, # 503 Service Unavailable을 임시 사용
            "error_message": "Connection Error: 네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해주세요.",
            "action": "로컬 네트워크 설정을 점검해주세요."
        }
    except requests.exceptions.RequestException as e:
        # 모든 나머지 requests 관련 예외 처리
        return {
            "status": "FATAL_ERROR",
            "http_code": 500,
            "error_message": f"요청 처리 중 예상치 못한 오류가 발생했습니다: {e}",
            "action": "시스템 로그와 네트워크 환경을 점검해주세요."
        }

# ====================================================================
# 🧪 사용 예시 (실제 실행 시 주석 해제 및 환경변수 설정 필요)
# ====================================================================
# if __name__ == '__main__':
#     # 환경변수 설정 예시 (실제 PAT로 대체 필요)
#     # os.environ["GITHUB_PAT"] = "***REMOVED***
