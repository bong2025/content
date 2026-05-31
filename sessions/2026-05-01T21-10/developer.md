# 💻 Developer — Business와 Researcher가 확정한 명확한 Scope(최소 권한 원칙 기반)와 승인 절차를 전제로, 재연동에 필요한 최소 기능(MVP)의 기술 아키텍처 설계도를 업데이트하고, 필요한 API 호출 및 데이터 파이프라인 변경 사항을 단계별로 구체화합니다.

💻 Developer: 작업 시작합니다.

사용자님의 요청("다시연동좀 잡아줘")은 현재 프로젝트의 초기 목표와는 다소 거리가 있습니다. 지난 논의(Researcher, Business, Secretary)를 종합했을 때, 지금 필요한 것은 단순히 코드를 재실행하는 것이 아니라, **'신뢰성'과 '안정성'을 보장하는 새로운 아키텍처와 파이프라인 설계**입니다.

따라서, 저는 현재의 기술적 요구사항을 반영하여 **'PoLP 기반의 데이터 동기화 파이프라인 MVP 아키텍처 설계도'**를 업데이트하고, 이를 구현하기 위한 단계별 API 호출 및 데이터 처리 로직을 구체화했습니다. 이 설계도는 향후 개발팀이 따라야 할 **기술 표준(Technical Standard)**이 됩니다.

---

## ⚙️ 1. 데이터 동기화 파이프라인 (Sync Pipeline) MVP 아키텍처 설계도

**[목표]**: 최소 권한 원칙(PoLP)을 준수하며, 오류 발생 시에도 데이터 무결성을 유지하는 비동기식 동기화 파이프라인 구축.

**[주요 변경 사항]**:
1.  **비밀 관리:** 환경 변수 사용 금지. Vault/KMS 기반으로 인증 토큰을 관리.
2.  **흐름 제어:** 요청-처리-검증의 3단계 로직을 적용하여 데이터 신뢰성을 확보.
3.  **강건성(Resilience):** 모든 외부 API 호출에 재시도(Retry) 및 지수 백오프(Exponential Backoff) 로직을 의무화.

**[아키텍처 다이어그램 (논리적 흐름)]**

```mermaid
graph TD
    A[Source System (e.g., GitHub API)] -->|1. API Gateway| B(Data Sync Service);
    B -->|2. Auth Token Request| C[Vault / KMS];
    C -->|3. Valid Token| B;
    B -->|4. API Call (PoLP Scope)| D{API 호출 로직};
    D -- Success --> E[Data Transformation & Validation];
    D -- Fail (4xx/5xx) --> F[Error Logger & Alert];
    E -->|5. Load Data| G[Target Database / Data Lake];
    F --> G;
    G --> H(Audit Log);
    H --> B;
```

## 💻 2. 단계별 구현 상세화 (Implementation Blueprints)

### Step 1: 인증 및 권한 관리 모듈 (Credential Module)

*   **기능:** API 토큰 요청 및 검증.
*   **기술:** Vault/KMS 연동 라이브러리 사용.
*   **핵심 로직:**
    1.  `get_token(service_name, scope)` 함수를 호출한다.
    2.  토큰 만료(Expired) 여부를 확인하고, 만료 시 자동으로 재발급을 시도한다.
    3.  토큰 요청 시, Vault/KMS에 **요청 주체(Caller ID)**와 **사용 목적(Purpose)**을 기록하여 감사 추적(Audit Log)을 남긴다.

### Step 2: 데이터 수집 및 처리 모듈 (Extraction & Loading Module)

*   **기능:** Source API 호출, 데이터 수집, 변환.
*   **기술:** Python (requests + pandas/pydantic).
*   **핵심 로직 (재연동 핵심):**
    1.  **멱등성(Idempotency) 확보:** 데이터를 가져올 때, 이미 처리된 데이터의 범위(예: `last_sync_timestamp` 또는 `batch_id`)를 반드시 파라미터로 전달하여 중복 수집을 방지한다.
    2.  **에러 핸들링:** API 호출 실패 시, 단순히 실패 처리하는 것이 아니라, 재시도 횟수(Retry Count)와 지연 시간(Backoff Time)을 적용하는 **지수 백오프(Exponential Backoff)** 전략을 구현한다.

### 🛠️ 코드 구조 (가상 Python Pseudo-code)

```python
# 1. Configuration & Connection
def connect_api(source_id, api_key):
    # 실제 API 연결 로직 (토큰 획득 및 기본 연결)
    pass

# 2. Core Data Fetching Logic (Retry & Backoff 적용)
def fetch_data_with_retry(api_call_func, max_retries=5, initial_delay=2):
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            data = api_call_func()
            return data  # 성공 시 데이터 반환
        except API_Error as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay) # 지연 시간 대기
                delay *= 2 # 지수 백오프: 2초 -> 4초 -> 8초...
            else:
                raise Exception("API 호출 실패: 최대 재시도 횟수 초과")

# 3. Main Execution Flow
def sync_data_pipeline(source_id, source_api_key):
    try:
        # 1. 연결 및 인증
        conn = connect_api(source_id, source_api_key)
        
        # 2. 데이터 가져오기 (재시도 로직 포함)
        raw_data = fetch_data_with_retry(lambda: conn.get_data(last_sync_timestamp))
        
        # 3. 데이터 변환 및 검증 (Data Transformation & Validation)
        validated_data = validate_and_transform(raw_data)
        
        # 4. 데이터 로드 (Data Loading)
        load_to_destination(validated_data)
        
        print("데이터 동기화 성공 완료.")
    except Exception as e:
        print(f"파이프라인 실패: {e}")

```
