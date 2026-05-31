# 💻 Developer — 진단된 문제 유형(권한 문제 가정)을 기반으로, '최소 권한 원칙(PoLP)'을 적용하는 단계별 해결 가이드를 작성합니다. (예: Read-Only 토큰 사용 요청 $	o$ Vault/KMS를 통한 토큰 관리 프로세스 확립 $	o$ 코드 레벨의 에러 핸들링 추가 등)

💻 Developer: 작업 시작합니다.

제시된 `[GitHub Sync 실패]` 오류는 기술적인 오류(Syntax Error)가 아닌, **접근 권한 및 거버넌스 체계의 부재**에서 오는 **'권한 실패(Authorization Failure)'**입니다. 따라서 단순히 주소나 토큰을 수정하는 것은 근본적인 해결책이 될 수 없습니다.

CEO의 지시와 기존의 거버넌스 로그를 종합하여, 가장 안전하고 확장 가능한 **'최소 권한 원칙(PoLP) 기반의 GitHub 연동 3단계 해결 로드맵'**을 제시합니다. 이 로드맵은 **'비즈니스 승인 $\to$ 아키텍처 설계 $\to$ 기술 구현'**의 순서를 엄격하게 따릅니다.

---

## 🚀 GitHub Sync 실패 해결 로드맵: PoLP 기반 3단계 접근법

### 🟢 Stage 1: 거버넌스 및 승인 확보 (Gate Check)
*이 단계는 코드를 한 줄도 작성하지 않고, 반드시 거쳐야 할 필수 전제 조건입니다. 개발 착수 전 완료되어야 합니다.*

| 순서 | 활동 내용 | 목표 (PoLP 준수) | 산출물 (필수) |
| :--- | :--- | :--- | :--- |
| **1. 목적 정의** | **비즈니스 사용 목적 정의서** 작성. (Business 에이전트의 요구사항 충족) | *WHY:* 이 데이터가 회사의 어떤 KPI에 기여하는지 명확히 정의. (단순 참고 금지) | `Purpose_Definition_Doc.pdf` |
| **2. 범위 축소** | **최소 권한 범위(Scope)**를 정의하고, 이를 기반으로 GitHub의 **읽기 전용(Read-Only)만 허용**하는 토큰을 요청. | *SCOPE:* 필요 이상의 Write, Admin 권한은 절대 요청하지 않음. | `Required_Scopes_List.txt` |
| **3. 아키텍처 승인** | 토큰 관리 방안으로 **Vault/KMS 연동**을 필수적으로 포함하고, 해당 아키텍처 설계에 대한 경영진 승인 획득. | *GOVERNANCE:* 모든 비밀 자산(Secret)은 중앙 집중식 시스템으로 관리함을 확정. | `Architecture_Design_Review.ppt` |

### 🟡 Stage 2: 아키텍처 설계 및 표준화 (Blueprint)
*승인된 목적과 Scope를 기반으로, 시스템의 기술적 구조를 설계합니다.*

**1. 데이터 흐름도 재설계 (Data Flow Diagram)**
*   **Old Flow (Bad):** `[Sync Agent] $\xrightarrow{\text{PAT}}$ [GitHub API] $\to$ [Local .env] $\to$ [Processing] $\to$ [Result]`
*   **New Flow (Good):** `[Sync Agent] $\xrightarrow{\text{API Call}}$ [API Gateway] $\to$ [Vault/KMS] $\xrightarrow{\text{Credential}}$ [GitHub API] $\to$ [Raw Data Stream] $\to$ [Data Pipeline (SOP 통과)] $\to$ [Data Catalog]`

**2. 토큰 관리 아키텍처 확립 (PoLP 구현)**
*   **핵심:** `Sync Agent`는 토큰을 직접 보유하지 않습니다. 오직 `API Gateway`를 통해 Vault/KMS에 '토큰 사용 요청'을 보내고, 게이트웨이가 인증된 토큰을 받아 임시로 API 호출에 사용한 후, 사용 기록(Audit Log)을 남깁니다.
*   **기술 스택:** API Gateway (예: Kong, AWS API Gateway), Secret Manager (Vault/KMS), Sync Service.

**3. 에러 핸들링 및 로깅 강화**
*   모든 API 호출 로직은 반드시 `try...catch` 블록으로 감싸야 합니다.
*   **필수 로그 항목:** 호출 시도 시간, 실패 사유(Error Code), 시도한 자격 증명(Credential ID), **실패 원인 분류 (권한 부족/네트워크 오류/잘못된 파라미터)**.

### 🚀 기술적 구현 단계 (코드 레벨 가이드)

실제 코드는 Python을 기준으로 설명하며, 외부 라이브러리 사용을 전제로 합니다.

**1. 자격 증명 관리 모듈 (Credential Manager)**
*   **역할:** 실제 토큰을 절대 코드에 하드코딩하지 않고, Vault(예: HashiCorp Vault)에서 동적으로 가져옵니다.
*   **기능:** `get_token(service_name)` $\rightarrow$ Vault API 호출 $\rightarrow$ 만료 시간 체크 $\rightarrow$ 토큰 반환.

**2. API 호출 모듈 (API Client)**
*   **역할:** 실제 API 호출을 담당하며, 요청 시점에 토큰을 받아와 사용합니다.
*   **예시 (Python Pseudocode):**
    ```python
    from credential_manager import get_token
    import requests

    def fetch_github_data(repo_owner, repo_name):
        # 1. 토큰 획득 (Vault에서)
        token = get_token("github_api") 
        if not token:
            raise AuthenticationError("Token acquisition failed.")

        headers = {"Authorization": f"token {token}"}
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() # HTTP 에러 코드 발생 시 예외 처리
            return response.json()
        except requests.exceptions.HTTPError as e:
            # 2. 에러 코드 기반의 로깅 및 분류
            if response.status_code == 401:
                print("ERROR: 401 Unauthorized - Token 만료 또는 권한 부족.")
            elif response.status_code == 403:
                print("ERROR: 403 Forbidden - API Rate Limit 또는 Scope 부족.")
            else:
                print(f"ERROR: {response.status_
