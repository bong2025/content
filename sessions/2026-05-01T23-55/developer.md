# 💻 Developer — 기술 구현 단계로 넘어가기 위해, 가장 먼저 **'SOP(표준 운영 절차) 이행 추적 시스템'**의 아키텍처를 설계해야 함을 제안합니다. 이 시스템은 비즈니스팀이 정의한 '사용 목적'과 '승인 단계'를 추적하는 자동화된 워크플로우(Workflow)여야 합니다.

💻 Developer: 작업 시작합니다.

## ⚙️ SOP 이행 추적 시스템 아키텍처 설계 (SOP Execution Tracking System Architecture)

CEO님의 지시에 따라, 단순한 데이터 연동 재시도 대신, 시스템의 근본적인 거버넌스 문제를 해결하기 위한 **'SOP 이행 추적 시스템'**의 아키텍처를 설계합니다. 이 시스템은 모든 데이터 접근 및 기능 구현이 반드시 거쳐야 하는 **워크플로우 게이트(Workflow Gate)** 역할을 수행합니다.

### 1. 시스템 개요 및 목표

*   **시스템명:** SOP Workflow Orchestrator (SOWO)
*   **목표:** 모든 프로젝트의 데이터 사용 목적 정의(Business Use Case) $\to$ 최소 권한 Scope 정의 $\to$ 전사적 승인(Sign-off) 과정을 자동화하고, 각 단계의 이행 여부를 불변의 로그(Immutable Log)로 추적합니다.
*   **핵심 원칙:** 모든 기술적 작업(Code Commit)은 SOWO에서 '승인 완료'된 트래킹 ID와 연결되어야 합니다.

### 2. 아키텍처 다이어그램 (Conceptual Flow)

```mermaid
graph TD
    A[1. 비즈니스 요청 (Business Request)] --> B{2. Use Case 정의서 제출};
    B --> C[SOP Workflow Orchestrator (SOWO)];
    C --> D{3. 권한 Scope 정의 및 검토};
    D -- 실패/재검토 --> B;
    D -- 통과 --> E{4. 승인 워크플로우 실행 (Approval Gate)};
    E -- 승인 필요 --> F[Signatory 1: CDO];
    E -- 승인 필요 --> G[Signatory 2: Legal/Compliance];
    F --> H{5. 최종 승인 (Final Sign-off)};
    G --> H;
    H -- 최종 승인 --> I[6. Credential Vault 등록 (PoLP 적용)];
    I --> J[7. 데이터 파이프라인/API 구현 (Code Execution)];
    J --> K[8. Audit Log 기록 및 배포];
    K --> L(SOP Tracking Dashboard);
```

### 3. 컴포넌트 상세 설계 및 기술 스택

| 컴포넌트 | 역할 및 기능 | 기술 스택 (제안) | 보안/거버넌스 고려 사항 |
| :--- | :--- | :--- | :--- |
| **Workflow Orchestrator (SOWO)** | 전체 워크플로우의 상태 관리 및 순서 제어. 비동기적 상태 전이(State Transition)를 담당. | Apache Airflow (또는 Prefect) | **상태 전이 로깅:** 모든 단계 진입/종료 시 타임스탬프와 담당자 ID를 필수 기록. |
| **Use Case Repository** | 비즈니스 사용 목적 정의서, KPI, 기대 효과를 구조화하여 저장. (기술 문서가 아님) | Notion/Confluence API 연동 $\to$ DB (PostgreSQL) | **Version Control:** 사용 목적 정의서의 버전 관리를 필수화. |
| **Approval Gate** | 승인 주체별(CDO, Legal 등) 알림, 승인 상태 추적, 승인 기한 관리. | Slack/Email API 연동 + SOWO 로직 | **승인 책임 소재:** 승인 주체별 로그 기록 및 자동 알림 실패 시 재시도 로직 구현. |
| **Credential Vault Connector** | SOWO가 최종 승인을 받은 후, Vault(HashiCorp Vault 권장)에 최소 권한의 API Credential을 요청하고 등록하는 게이트웨이. | Python (hvac library) | **PoLP 강제:** Credential 요청 시, SOWO의 **성공 상태(Success State)**가 전제되어야만 API 호출 가능. |
| **Audit Logging Service** | 모든 단계의 입력 데이터, 처리 로직, 출력 데이터, 사용 주체를 불변의 로그로 기록. | ELK Stack (Elasticsearch, Logstash, Kibana) | **불변성:** 데이터 위변조가 불가능하도록 WORM(Write Once Read Many) 원칙 준수. |

### 4. 구현 계획 (Pseudo-Code: Airflow DAG Skeleton)

다음은 Airflow를 사용하여 SOWO의 핵심 게이트를 구현하는 의사 코드(DAG)의 골격입니다.

```python
# airflow/dags/sop_workflow_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    dag_id='sop_governance_workflow',
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['governance', 'sop', 'mandatory']
) as dag:

    # 1. Use Case Definition Stage

