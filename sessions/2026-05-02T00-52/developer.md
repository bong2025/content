# 💻 Developer — 기술적인 관점에서, 연결이 실패하는 가장 흔한 원인 3가지(예: 권한 범위 초과, 환경 변수 누락, 데이터 파이프라인의 비동기 처리 지연)를 목록화하고, 각 원인별로 체크리스트와 해결 방안을 구체적인 코드로 제시할 것.

💻 Developer: 작업 시작합니다.

요청하신 기술적 실패 원인 3가지와 그 해결 방안을 목록화하고, 각 원인별 체크리스트와 구체적인 코드를 제시합니다.

이 세 가지 실패 원인은 단순한 코딩 실수가 아니라, **'거버넌스(Governance)'** 및 **'아키텍처 설계(Architecture Design)'**의 미비함에서 비롯된 문제들이므로, 제시된 코드 예시와 함께 **'사전 점검 체크리스트'**를 반드시 수행해야 합니다.

---

### ⚠️ 1. 권한/범위 초과 및 인증 실패 (Authorization & Scope Failure)

**[원인 진단]**
가장 흔하며 치명적인 오류입니다. API 키나 토큰이 특정 자원(Resource)에 접근할 권한(Scope)을 가지고 있지 않거나, 이미 만료되었을 때 발생합니다. 단순히 코드를 재실행하거나 토큰을 새로 발급해도 해결되지 않으며, **'어떤 권한이 필요한지'**를 명확히 정의하는 프로세스(PoLP)가 선행되어야 합니다.

**✅ 체크리스트 (Governance Focus)**
*   [ ] **Scope 정의:** 현재 API 호출에 필요한 최소한의 권한 목록(예: `read:user`, `write:content`)을 비즈니스 승인서로 확보했는가?
*   [ ] **토큰 만료 주기:** 사용 중인 자격 증명(Credential)의 자동 만료 주기와 갱신 로직이 정상 작동하는가?
*   [ ] **PoLP 준수:** 토큰 발급 시, 과도한 권한(예: `*` 와일드카드)이 포함되어 있지 않은가?

**💻 해결 방안 (Code Implementation: Python 예시)**
실패 시 재시도 로직(Retry Logic)을 구현하고, HTTP 에러 코드 401(Unauthorized) 또는 403(Forbidden)을 명시적으로 처리하여 근본 원인을 로깅해야 합니다.

```python
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout

MAX_RETRIES = 3

def fetch_data_with_auth(api_url: str, token: str, scope: str) -> dict:
    """권한 검증을 포함한 안전한 API 호출 함수"""
    for attempt in range(3):
        try:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            response = requests.get(f"{api_url}?scope={scope}", headers=headers, timeout=5)
            response.raise_for_status() # 4xx/5xx 에러 발생 시 예외 발생
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("🚨 [ERROR] 401 Unauthorized: 토큰이 만료되었거나 권한이 부족합니다. 재인증 필요.")
                # 재인증 로직 호출 (예: refresh_token())
                return None
            elif response.status_code == 403:
                print(f"🚨 [ERROR] 403 Forbidden: 요청한 스코프({scope})에 대한 권한이 없습니다.")
                return None
            else:
                print(f"🚨 [ERROR] HTTP 에러 발생: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"🚨 [ERROR] 네트워크 오류 발생: {e}")
            return None
        time.sleep(2 ** attempt) # 지수 백오프(Exponential Backoff) 적용
    
    print("❌ 최대 재시도 횟수 초과. API 호출 실패.")
    return None
```

---

### ⚡️ 2. 데이터 전송/처리 오류 (Payload/Schema Mismatch)

**문제:** API가 예상하는 데이터 형식(JSON 스키마, 필드명 등)과 실제 전송하는 데이터가 일치하지 않아 발생하는 오류입니다.
**예시:** `user_id`를 기대하는데 `userId`로 보내거나, 문자열을 보내야 할 곳에 리스트를 보내는 경우.

**해결책:** 데이터를 전송하기 전에 엄격한 유효성 검사(Validation) 과정을 거쳐야 합니다.

```python
import pydantic # 강력한 데이터 스키마 검증 라이브러리 사용 권장

# 1. 기대하는 데이터 구조(스키마)를 정의합니다.
class UserPayload(BaseModel):
    user_id: int
    username: str = Field(min_length=3)
    email: EmailStr
    is_active: bool

# 2. 전송할 데이터를 스키마에 맞게 변환하고 유효성 검사를 수행합니다.
def validate_and_prepare_payload(raw_data: dict) -> Optional[UserPayload]:
    try:
        # Pydantic이 타입 변환 및 유효성 검사를 수행합니다.
        validated_data = UserPayload(**raw_data)
        return validated_data # 검증된 객체를 반환
