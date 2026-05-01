# 💻 Developer — Business 에이전트가 정의한 목표와 권한을 바탕으로, GitHub OAuth 인증 플로우를 설계합니다. 필요한 API 엔드포인트, 인증 토큰(Credential) 관리 방안, 그리고 연결 성공 후 데이터가 어떤 파이프라인을 거쳐야 하는지(데이터 흐름도)를 구체적으로 코드로 계획하고 문서화합니다.

💻 Developer: 작업 시작합니다.

요청하신 GitHub OAuth 인증 플로우 설계, 크리덴셜 관리 방안, 그리고 데이터 파이프라인을 아래와 같이 구체적인 기술 문서와 실행 가능한 스켈레톤 코드로 계획했습니다.

이 설계는 '읽기 전용(Read-Only)' 목표에 맞춰, 인증을 통해 토큰을 획득하고, 웹훅(Webhook)을 통해 변경 사항을 감지하며, 안전하게 데이터를 추출하는 구조를 따릅니다.

---

## ⚙️ 1. GitHub OAuth 인증 및 토큰 관리 설계

### 1.1. 인증 플로우 (Authentication Flow)
| 단계 | 주체 | 액션 | 엔드포인트/요소 | 설명 |
| :--- | :--- | :--- | :--- | :--- |
| **1. 요청** | 시스템 | OAuth 인증 요청 | `https://github.com/login/oauth/authorize` | `client_id`, `redirect_uri`, `scope` (Read: Contents, Metadata) 포함하여 사용자를 GitHub 인증 페이지로 리디렉션. |
| **2. 승인** | 사용자 | 승인 | N/A | 사용자가 권한을 승인하면, GitHub는 `code`를 포함하여 `redirect_uri`로 리디렉션. |
| **3. 교환** | 시스템 | 토큰 요청 (백엔드) | `https://github.com/login/oauth/access-token` | 획득한 `code`와 `client_secret`을 사용하여, **액세스 토큰(Access Token)**으로 교환. |
| **4. 저장** | 시스템 | 크리덴셜 저장 | `[SECRET_VAULT]` | 획득한 **액세스 토큰**과 **리프레시 토큰**을 암호화하여 안전하게 저장. |

### 1.2. 크리덴셜 관리 방안 (Credential Management)
*   **저장 위치:** 환경 변수 또는 전용 비밀 관리 시스템 (예: HashiCorp Vault, AWS Secrets Manager) 사용을 원칙으로 합니다.
*   **저장 항목:**
    1.  `GITHUB_CLIENT_ID`: (환경 변수)
    2.  `GITHUB_CLIENT_SECRET`: (환경 변수)
    3.  `GITHUB_ACCESS_TOKEN`: (DB/Vault에 암호화 저장)
    4.  `GITHUB_REFRESH_TOKEN`: (DB/Vault에 암호화 저장, 토큰 만료 시 재발급용)
*   **보안 원칙:** 절대 코드나 일반 로그에 토큰을 평문으로 기록하지 않습니다. 토큰 만료 시, `refresh_token`을 사용하여 자동으로 새 `access_token`을 갱신하는 로직을 구현해야 합니다.

---

## 🚀 2. 데이터 파이프라인 및 워크플로우 설계

### 2.1. 아키텍처 다이어그램 (Conceptual Flow)
`[GitHub Webhook] ➡️ [API Gateway/Trigger] ➡️ [Data Processor Service] ➡️ [Validation/Filtering] ➡️ [JAYCORP Data Lake (Postgres/S3)]`

### 2.2. 핵심 파이프라인 로직
1.  **트리거 감지:** GitHub Webhook이 `[JAYCORP-Content-Assets]` 저장소에 `push` 이벤트 발생을 감지합니다.
2.  **데이터 추출 (Read):** Data Processor Service는 Webhook Payload에 포함된 Commit SHA를 이용해, GitHub API (`/repos/{owner}/{repo}/contents/{path}`)를 호출하여 최신 자산 파일의 내용을 읽어옵니다.
3.  **유효성 검사 (Validate):** 추출된 파일 내용(예: 스크립트)이 필수 포맷(예: 마크다운, YAML)을 따르는지, 그리고 특정 키워드(예: `[DRAFT]`, `[FINAL]`)를 포함하는지 검사합니다.
4.  **저장 및 기록 (Store):** 유효성 검사를 통과한 데이터를 JAYCORP의 중앙 데이터 저장소(Data Lake)에 저장하고, 해당 데이터의 **Source Commit ID**, **Timestamp**, **Version** 정보를 메타데이터로 기록합니다.

---

## 💻 3. 구현 코드 스켈레톤 (Python 예시)

다음은 토큰을 이용해 데이터를 가져오고 파이프라인을 구동하는 핵심 로직의 스켈레톤 코드입니다.

```python
import os
import requests
from datetime import datetime

# --- 환경변수 설정 (보안을 위해 실제 값은 환경변수에서 로드) ---
REPO_OWNER = "jaycorp-dev"
REPO_NAME = "JAYCORP-Content-Assets"
GITHUB_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN")

# --- API 엔드포인트 상수 ---
GITHUB_API_BASE = "https://api.github.com/repos"

def get_latest_file_content(file_path: str, commit_sha: str) -> str | None:
    """
    특정 경로의 파일을 특정 커밋 SHA 기준으로 가져옵니다. (Read-Only)
    :param file_path: 파일 경로 (예: scripts/intro.md)
    :param commit_sha: 커밋 SHA (버전 추적용)
    :return: 파일 내용 (문자열) 또는 None
    """
    endpoint = f"{GITHUB_API_BASE}/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}?ref={commit_sha}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    print(f"Attempting to fetch content from: {file_path}...")
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # GitHub는 Base64 인코딩된 내용을 제공하므로 디코딩이 필요합니다.
        import base64
        decoded_content = base64.b64decode(data['content']).decode('utf-8')
        return decoded_content
    elif response.status_code == 404:
        print(f
