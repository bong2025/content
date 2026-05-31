# 💻 Developer — 새로운 토큰 연동을 위한 기술 아키텍처를 설계하십시오. 이 아키텍처는 반드시 'API 게이트웨이'를 통해 접근을 제한하고, 모든 토큰 사용 시도와 성공/실패 여부를 기록하는 '감사 추적 시스템(Audit Logging)'을 의무적으로 포함해야 합니다.

💻 Developer: 작업 시작합니다.

CEO의 지시사항은 기존의 '토큰 직접 사용' 방식의 근본적인 문제(보안 취약점, 비가시적 사용 범위)를 해결하고, 엔터프라이즈급의 **'신뢰성'과 '투명성'**을 확보하는 핵심적인 아키텍처 설계입니다.

단순히 토큰을 등록하는 것이 아니라, 토큰을 **'서비스'**처럼 활용하고, 그 사용 과정 전체를 기록하는 구조가 필요합니다. 이를 위해 **'Secure API Proxy Pattern'**을 적용한 아키텍처를 설계합니다.

---

# 🛡️ Secure GitHub Integration 아키텍처 설계 (v1.0)

## 🎯 목표 및 원칙
1.  **최소 권한 원칙 (PoLP) 강제:** 모든 API 호출은 사전에 정의된 '비즈니스 목적(Why)'과 '최소 Scope'를 기반으로만 허용됩니다.
2.  **중앙 집중식 접근 제어:** 모든 외부 API 접근은 오직 API 게이트웨이를 통해서만 이루어지며, 직접적인 토큰 노출을 원천 차단합니다.
3.  **불변의 감사 기록:** 모든 요청 시도(성공/실패, 파라미터, 시간, 호출 주체)는 변조 불가능한 로그로 기록됩니다.

## 🧩 아키텍처 컴포넌트 다이어그램

```mermaid
graph LR
    A[Calling Service / 자동화 스크립트] -->|1. API 요청 (요청자 ID, 목적)| B(API Gateway);
    B -->|2. 요청 검증 및 Rate Limit 체크| C{Auth & Governance Service};
    C -->|3. 승인 여부 확인 (PoLP 체크)| D[Secret Manager / Vault];
    D -->|4. 임시 토큰 획득 (PoLP 기반)| C;
    C -->|5. 인증된 토큰과 요청 파라미터 전달| E(GitHub Adapter / Core Logic);
    E -->|6. API 호출 실행| F[GitHub API];
    F -->|7. 응답 데이터| E;
    E -->|8. 결과 전송| C;
    C -->|9. 감사 로그 기록 (성공/실패)| G[(Audit Log DB - 불변)];
    C -->|10. 응답 데이터| A;

    subgraph Backend Microservices Layer
        B; C; D; E;
    end
    subgraph External System
        F;
    end
```

## ⚙️ 컴포넌트별 상세 설계 및 기술 요구사항

### 1. API Gateway (접근 통제 및 필터링)
*   **역할:** 모든 외부 요청의 유일한 진입점(Single Entry Point).
*   **기술 요구사항:**
    *   **Rate Limiting:** 호출 주체(Calling Service)별/전체 API별 호출 횟수를 제한합니다. (예: 1분당 100회)
    *   **Request Validation:** 요청 헤더 및 바디에 필수 필드(요청자 ID, 비즈니스 목적 코드)가 누락되었는지 1차 검증합니다.
    *   **보안:** WAF(Web Application Firewall)를 적용하여 기본적인 SQL Injection 및 XSS 공격을 방어합니다.

### 2. Auth & Governance Service (핵심 게이트키퍼)
*   **역할:** 토큰 사용의 **'비즈니스적 적절성'**을 판단하는 핵심 로직입니다.
*   **작동 로직:**
    1.  **요청 분석:** `Calling Service`가 전송한 `요청자 ID`와 `비즈니스 목적 코드`를 받습니다.
    2.  **정책 매칭:** 내부 DB에 저장된 **'사용 승인서(Business Approval Form)'**와 비교하여, 현재 요청이 허용된 목적/Scope와 일치하는지 확인합니다.
    3.  **권한 매핑:** 목적에 맞는 최소 권한(Scope)을 정의하고, `Secret Manager`에 해당 Scope를 가진 토큰 발급을 요청합니다.

### 3. Secret Manager / Vault (토큰 관리)
*   **역할:** 모든 민감 토큰(PAT)을 저장하는 장치입니다. **절대 개발자나 서비스 코드에 직접 노출되어서는 안 됩니다.**
*   **기술 요구사항:**
    *   **암호화:** AES-256 또는 KMS(Key Management Service) 기반의 강력한 암호화를 적용합니다.
    *   **접근 통제:** `Auth & Governance Service`가 승인된 자격 증명(Credential)을 통해서만 토큰을 임시로 가져갈 수 있도록 합니다.
    *   **자동 만료:** 토큰 사용 후에는 즉시 세션 기반으로 토큰을 폐기(Revoke)하는 로직이 필수입니다.

### 4. GitHub Adapter / Core Logic (실제 호출 담당)
*   **역할:** `Secret Manager`로부터 임시 토큰을 받아 실제 GitHub API 엔드포인트를 호출하는 전용 모듈입니다.
*   **구현 원칙:** 이 모듈은 오직 `Auth & Governance Service`의 요청을 통해서만 호출되어야 하며, 토큰을 가지고 외부 네트워크에 접근하는 유일한 통로입니다.

### 5. Audit Log DB (감사 추적 시스템)
*   **역할:** 모든 요청의 메타데이터를 기록합니다. **이 데이터는 수정이 불가능해야 합니다.**
*   **기록 항목 (필수):
