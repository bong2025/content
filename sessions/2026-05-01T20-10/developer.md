# 💻 Developer — 기술팀 주도로 'Vault/KMS 기반 3단계 비밀 관리 아키텍처'의 PoC(개념 증명)를 즉시 착수합니다. PoC의 목표는 '기술적 실현 가능성' 입증이므로, 필요한 최소한의 범위(Scope)와 테스트 환경 구축 계획을 구체적인 로드맵으로 작성해 주세요.

💻 Developer: 작업 시작합니다.

# 🔒 Vault/KMS 기반 비밀 관리 아키텍처 PoC 로드맵 (MVP Scope)

**수신:** CEO
**작성:** Developer (Lead Engineer)
**목표:** 비밀 자산(Secrets)을 코드나 환경 변수에 직접 노출하지 않고, 중앙 집중식 시스템을 통해 안전하게 관리하고 접근하는 기술적 실현 가능성(PoC) 입증.
**전제:** PoC는 기술적 검증에 초점을 맞추며, 비즈니스 승인(Governance) 절차는 병행 진행됨을 전제로 합니다.

---

## 🎯 1. PoC 목표 및 최소 범위 (MVP Scope Definition)

**핵심 목표:** 외부 서비스(Client)가 API Gateway를 통해 중앙 비밀 저장소(Vault)에서 특정 비밀(Secret)을 요청하고, 성공적으로 받아와 사용하는 End-to-End 흐름을 구축합니다.

**MVP가 증명할 것:**
1.  **보안성:** 민감 자산(API Key, Token)이 코드 레벨이나 환경 변수에 직접 저장되지 않음.
2.  **접근 통제:** 모든 접근이 정의된 Scope와 최소 권한 원칙(PoLP)에 따라 통제됨.
3.  **신뢰성:** 접근 실패 시, 정확한 오류 코드와 감사 로그(Audit Log)가 기록됨.

**MVP Scope (최소 구현 항목):**
*   **비밀 종류:** 더미 API Key (예: `test_service_api_key`) 1개.
*   **기능:** 비밀 저장(Write), 비밀 조회(Read), 비밀 삭제(Delete)의 3가지 기본 CRUD 흐름 구현.
*   **연동:** 개발된 테스트 서비스가 Vault API를 호출하는 최소한의 코드 통합.

---

## 🏛️ 2. 아키텍처 설계 (3-Layer Architecture)

| 레이어 | 역할 (Role) | 기술적 기능 | 보안 원칙 |
| :--- | :--- | :--- | :--- |
| **1. Client Service** (요청자) | 실제 비즈니스 로직을 수행하는 애플리케이션 (예: 데이터 동기화 서비스). | **Vault Client SDK**를 사용하여 API Gateway에 요청. | **최소 권한 원칙 (PoLP):** 오직 필요한 Scope의 Secret만 요청. |
| **2. API Gateway** (접근점) | 클라이언트와 Vault 사이에 위치하여, 요청을 검증하고 라우팅하는 통로. | **Rate Limiting, JWT/OAuth 검증, 로깅** 기능을 수행. | **접근 통제:** 클라이언트가 유효한 인증/권한을 가졌는지 1차 검증. |
| **3. Secret Manager** (저장소) | 모든 비밀 자산을 암호화하여 중앙 관리하는 시스템 (Vault/KMS). | **암호화 저장, 접근 기록 (Audit Log) 강제, 만료 정책 적용.** | **데이터 암호화:** 모든 데이터는 전송 및 저장 시 암호화됨. |

---

## 🛣️ 3. PoC 실행 로드맵 (Phased Implementation Plan)

**총 예상 기간:** 1주 (전담 인력 기준)

### Phase 0: 준비 및 환경 구축 (Day 1)
**목표:** PoC를 위한 격리되고 통제된 환경을 마련하고, 기본 인프라를 설정합니다.

**필수 선행 조건 (Pre-requisites):**
1.  **Vault/KMS 인스턴스 확보:** 테스트용 Vault 또는 클라우드 KMS 계정 확보.
2.  **개발 환경 격리:** `dev-vault-poc`와 같은 전용 환경 구축.
3.  **인증 자격 증명:** Gateway와 Vault 간 통신에 사용할 임시 인증서/토큰 준비.

**Action Item:**
*   Vault/KMS의 기본 API 엔드포인트 확인 및 인증 방식(e.g., AppRole, Kubernetes Auth) 결정.

### Phase 1: 코어 기능 구현 (Day 2-3)
**목표:** 비밀 자산의 저장 및 조회 기본 기능을 완성하고, 3단계 아키텍처의 핵심 흐름을 구축합니다.

**Task:**
1.  **Vault 초기 설정:** 테스트용 Secret (예: `test_service_api_key`)를 Vault에 저장하는 API 호출 스크립트 작성.
2.  **API Gateway Stub 구현:** 요청을 받아 Vault로 전달하는 최소한의 게이트웨이 로직(Python/Node.js)을 작성. (실제 인증 로직은 MVP에서는 단순화)
3.  **Client Service 구현:** `requests` 라이브러리 등을 사용하여 Gateway를 호출하고, Secret 값을 받아오는 클라이언트 로직 구현.

**산출물:** `vault_write_test.py` (비밀 저장), `api_gateway_stub.py` (라우팅), `client_read_test.py` (읽기 테스트).

### Phase 2: 오류 처리 및 거버넌스 강화 (Day 4)
**목표:** 기술적 안정성과 보안 표준을 강화합니다.

**Task:**
1.  **Try/Catch 로직 추가:** Secret 조회 실패(401/403/500) 시, 일반적인 에러 메시지 대신 **구체적인 에러 코드와 원인**을 반환하도록 Client Service에 로직 추가.
2.
