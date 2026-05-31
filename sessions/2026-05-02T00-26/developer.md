# 💻 Developer — 비즈니스팀에서 확정된 Scope와 PoLP 원칙을 전제로, 깃허브 연동을 위한 기술 아키텍처 변경 계획을 수립해주세요. 반드시 'API Gateway'를 통한 접근 제어와 'Vault/KMS'를 이용한 토큰 관리 자동화 과정을 포함해야 합니다.

💻 Developer: 작업 시작합니다.

## 🚀 GitHub 연동을 위한 기술 아키텍처 재설계 계획 (PoLP & 거버넌스 준수)

CEO 지시에 따라, 단순 재연동 시도가 아닌, **최소 권한 원칙(PoLP)**과 **강화된 보안 거버넌스**를 반영한 기술 아키텍처 변경 계획을 수립합니다. 이 아키텍처는 외부 자산(GitHub)에 대한 접근을 **최대한 격리(Isolation)**하고, 모든 데이터 흐름에 대한 **감사 추적(Audit Trail)**을 의무화합니다.

### 1. 아키텍처 개요: 3단계 접근 제어 모델

기존의 '앱 $\to$ GitHub' 직접 연결 방식은 폐기하고, 다음의 3단계 보안 게이트를 통과하는 **'서비스 계정 기반(Service Account)'** 접근 모델을 채택합니다.

**[핵심 원칙]**
1.  **Credential 관리:** GitHub Token은 개발 환경(.env)이나 코드 레포지토리에 절대 저장하지 않습니다.
2.  **접근 제어:** 모든 외부 호출은 API Gateway를 통해 강제합니다.
3.  **서비스 분리:** 데이터를 가져오는 로직을 전용 마이크로서비스(Data Sync Service)로 분리합니다.

### 2. 상세 아키텍처 다이어그램 (Conceptual Flow)

```mermaid
graph TD
    A[GitHub Repository] -- 1. Pull Request (PR) Trigger --> B(GitHub Webhook);
    B --> C[API Gateway];
    C -- 2. 인증 요청 (Scope 검증) --> D[Secret Manager / Vault (KMS)];
    D -- 3. 임시 토큰 발급 (PoLP 기반) --> C;
    C -- 4. Rate Limit 및 스코프 검증 --> E[Data Sync Service (Microservice)];
    E -- 5. 데이터 추출 (Read-Only API Call) --> F{Data Transformation / Validation};
    F -- 6. 감사 로깅 기록 --> G[Audit Log System];
    F --> H[Internal Data Lake / System];
```

**[데이터 흐름 설명]**
1.  **Trigger (A $\to$ B):** GitHub에 변경사항(예: `main` 브랜치 푸시)이 발생하면 Webhook이 발생합니다.
2.  **Authentication (B $\to$ D $\to$ C):** Webhook은 API Gateway로 전송되며, Gateway는 토큰 요청을 받아 Vault에서 필요한 최소 권한의 토큰을 받아옵니다.
3.  **Processing (E):** 전용 서비스(Data Fetcher Service)가 토큰을 사용하여 필요한 데이터만 가져와서 비즈니스 로직을 수행합니다.
4.  **Persistence (F):** 처리된 데이터는 안전한 내부 시스템으로 전송됩니다.

---

### ⚙️ 구현 계획 및 다음 단계 (Action Items)

이 아키텍처를 현실화하기 위해 다음 3가지 단계가 필수적이며, 각 단계별 담당자가 지정되어야 합니다.

| 단계 | 목표 | 기술적 요구사항 | 산출물 (Deliverable) | 담당 부서 |
| :--- | :--- | :--- | :--- | :--- |
| **Step 1: 인증 및 접근 제어** | 외부 자격 증명을 안전하게 관리하고, 최소 권한 원칙을 적용합니다. | HashiCorp Vault 또는 AWS Secrets Manager 도입. OAuth 2.0/JWT 기반 인증 구현. | **[Vault/Secrets Manager]** 구축 및 테스트 완료. | 보안/인프라팀 |
| **Step 2: 서비스 분리 및 API 게이트웨이** | 비즈니스 로직과 데이터 접근을 분리하고, 외부 접근을 통제합니다. | API Gateway 구축 (예: Kong, AWS API Gateway). 전용 마이크로서비스 (Data Fetcher Service) 개발. | **[API Gateway]** 설정 및 기본 `GET` 요청 테스트. | 백엔드 개발팀 |
| **Step 3: 데이터 흐름 및 로깅** | 데이터 흐름을 확정하고, 모든 접근 시도를 기록합니다. | Kafka 또는 메시지 큐 도입. 모든 요청/응답/실패를 기록하는 중앙 로깅 시스템(ELK Stack) 구축. | **[End-to-End]** 테스트 환경 구축 및 성공 로깅 검증. | 백엔드/DevOps팀 |

**요약:** 가장 먼저 보안 및 인증 시스템(Step 1)을 구축하여, 임시 계정이나 하드코딩된 자격 증명 없이 안전하게 외부 API에 접근하는 환경을 마련해야 합니다.
