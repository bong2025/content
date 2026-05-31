# 💻 Developer — 1. 현재 사용 중인 GitHub API 호출 로직을 재검토하고, 토큰을 사용하는 모든 부분(Credential Management)을 점검합니다. 2. '토큰 만료' 또는 '권한 부족' 시도를 가정한 Try/Catch 블록을 추가하고, 실패 시 구체적인 오류 코드(Error Code)와 스코프(Scope)를 로그로 남기도록 코드를 수정합니다.

💻 Developer: 작업 시작합니다.

CEO님의 지시에 따라, GitHub API 호출 로직을 재설계하고 토큰 인증 및 오류 처리를 강화하는 `GitHubClient` 클래스를 구현했습니다.

이 코드는 다음과 같은 개선 사항을 적용했습니다:
1.  **Credential Management 강화:** 토큰을 하드코딩하지 않고 `GITHUB_TOKEN` 환경변수에서 로드합니다.
2.  **견고한 에러 핸들링:** `try...except` 블록을 사용하여 API 호출 실패 시 인증 오류(권한/만료)와 속도 제한 오류를 구분하여 처리합니다.
3.  **정보 로깅:** 실패 발생 시 단순히 "실패"가 아닌, **오류 코드(HTTP Status)**와 **문제의 스코프/원인**을 구체적으로 로그로 남깁니다.

### 🛠️ Refactored GitHub Client (Python)

이 코드를 `src/github_api_client.py`에 적용하세요.

```python
import os
import requests
import logging
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException

# 로깅 설정 (실제 로그 시스템에 맞게 조정 필요)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GitHubClient:
    """
    GitHub API 호출을 위한 클라이언트.
    토큰 인증 및 오류 처리를 강화하여 안정성을 확보합니다.
    """
    def __init__(self):
        # 1. Credential Management: 환경 변수에서 토큰 로드
        self.token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        
        if not self.token:
            logging.error("🚨 [CRITICAL] GITHUB_TOKEN 환경변수가 설정되지 않았습니다. API 호출을 수행할 수 없습니다.")
            self.is_authenticated = False
        else:
            self.headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            self.is_authenticated = True
            logging.info("✅ GitHubClient 초기화 완료. 토큰 기반 인증을 준비했습니다.")

    def get_repo_data(self, owner: str, repo_name: str) -> dict or None:
        """
        특정 저장소의 데이터를 안전하게 가져오는 메서드.
        토큰 만료 및 권한 부족 시나리오를 가정하여 오류를 처리합니다.
        """
        if not self.is_authenticated:
            logging.error("API 호출 실패: 인증 토큰이 누락되어 작업을 중단합니다.")
            return None

        url = f"{self.base_url}/repos/{owner}/{repo_name}"
        logging.info(f"⚙️ GitHub API 호출 시도: {url}")

        try:
            # API 호출 실행
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # 4xx 또는 5xx 상태 코드를 HTTPError로 발생시킴

            # 성공 로직
            return response.json()

        except HTTPError as e:
            # 2. Try/Catch 블록 및 오류 코드 로깅
            status_code = e.response.status_code
            
            if status_code == 401:
                logging.error(f"❌ [AUTH ERROR 401]: 인증 실패. 토큰이 만료되었거나 권한(Scope)이 부족합니다. (재발급/권한 재검토 필요)")
                # 실패 시 상세 오류 메시지를 로그로 남김
                logging.error(f"   -> 상세 오류 응답: {e.response.json().get('message', 'Unknown Error')}")
                return None
            
            elif status_code == 403:
                # 403 Forbidden: Rate Limit 초과 또는 권한 부족
                if 'rate limit exceeded' in e.response.text:
                    logging.error(f"⚠️ [RATE LIMIT 403]: API 호출 한도 초과. 잠시 후 재시도하거나, 조직 레벨의 토큰을 사용해야 합니다.")
                else:
                    logging.error(f"❌ [PERMISSION ERROR 403]: 권한 부족 또는 리소스 접근 제한. 필요한 Scope를 확인하세요.")
                return None
            
            elif status_code == 404:
                # 404 Not Found: 저장소가 실제로 존재하지 않거나 경로가 틀린 경우
                logging.error(f"🚨 [NOT FOUND 404]: 저장소 '{owner}/{repo_name}'를 찾을 수 없습니다. URL 또는 이름을 확인해주세요.")
                return None
            
            else:
                # 기타 HTTP 오류
                logging.error(f"❌ [HTTP ERROR {status_code}]: 예상치 못한 HTTP 오류 발생. {e}")
                return None

        except ConnectionError:
            logging.error("🛑 [CONNECTION ERROR]: 네트워크 연결 오류가 발생했습니다. 인터넷 연결을 확인하세요.")
            return None
        except Timeout:
            logging.error("🛑 [TIMEOUT ERROR]: API 응답 시간 초과. 네트워크 지연 또는 서버 과부하일 수 있습니다.")
            return None
        except RequestException as e:
            # 모든 requests 관련 예외를 포괄적으로 처리
            logging.critical(f"🔥 [FATAL EXCEPTION]: 치명적인 API 요청 예외 발생: {e}")
            return None


# --- 사용 예시 ---
if __name__ == "__main__":
    # 환경 변수 설정 (실제 운영 환경에서는 반드시 이 방식으로 관리해야 합니다.)
    # export GITHUB_TOKEN="***REMOVED***_actual_token_here"
    
    client = GitHubClient()

    # 1. 성공 케이스 (실제 존재하는 Public Repo 예시)
    # success_data = client.get_repo_data("pallets", "
