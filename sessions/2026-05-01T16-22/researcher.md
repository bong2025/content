# 🔍 Researcher — 오류가 발생한 시점에 GitHub API의 최근 변경 사항(Breaking Changes)이나 인증 프로토콜(OAuth)에 변화가 있었는지 외부 정보를 조사합니다. 만약 외부 요인이 원인이라면, 이를 공식 문서와 대조하여 해결책을 찾고, 관련 정보를 개발팀에 즉시 전달합니다.

🔍 Researcher: 작업 시작합니다.

## 🌐 GitHub API 오류 원인 분석 및 외부 요인 조사 보고서 (가설 기반)

**[목표]**
GitHub API 연동 오류의 원인이 내부 시스템 문제인지, 아니면 GitHub 측의 **최근 변경 사항(Breaking Changes)** 또는 **인증 프로토콜(OAuth) 정책 변화**와 같은 외부 요인에 의한 것인지 조사하고, 개발팀에 전달할 선제적 해결책을 제시합니다.

**[연구 범위]**
*   **주요 API 영역:** Webhooks, REST API 호출 (특히 트렌드/데이터 수집 관련 엔드포인트).
*   **인증 영역:** OAuth 2.0 Flow, Access Token 관리, Scope 권한.

---

### 🔍 1. 외부 요인 변화 감지 체크리스트 (Investigative Hypothesis)

| 변화 유형 | 체크 필요 사항 (What to Check) | 발생 가능성 | 개발팀 전달 시 강조점 |
| :--- | :--- | :--- | :--- |
| **API Breaking Changes** | **API Versioning:** 사용 중인 엔드포인트가 Deprecated(사용 중단 예정) 버전이 아닌지, 또는 새로운 필수 파라미터가 추가되었는지 확인. | 높음 | `GET /repos/{owner}/{repo}/issues` 등 특정 엔드포인트의 요청/응답 스키마 변경 여부. |
| **OAuth/Token Scope 변화** | **필요 Scope 축소/확대:** 과거에는 충분했지만, 현재는 더 세분화된 권한(Scope)이 요구되는지 확인. (예: `read:user` -> `user:email`) | 중간 | 토큰 획득 시, 필요한 최소한의 Scope만 요청하도록 재검토 필요. |
| **Rate Limiting 정책 강화** | **Rate Limit 초과:** 특정 시간/사용자/API 호출당 할당량이 변경되거나, 할당량이 더욱 엄격해졌는지 확인. | 매우 높음 | 에러 로그에서 `403 Forbidden` 코드가 발생 시, Rate Limit 초과가 아닌지 우선 진단. |
| **보안 프로토콜 변화** | **Client Secret/Key 관리:** GitHub 측에서 보안 강화를 이유로 인증 키(Secret)의 주기적 갱신이나 특정 사용 방식을 강제하는지 확인. | 중간 | Secret Key의 만료 주기 및 갱신 프로세스를 공식 문서와 대조해야 함. |

### 🛠️ 2. 공식 문서 기반 해결책 제안 (Actionable Solutions)

만약 외부 요인(특히 API 변경)이 원인일 경우, 다음의 3단계 접근 방식을 통해 해결할 수 있습니다.

#### 💡 A. 문제 진단 단계 (Diagnosis)
1. **버전 명시 의무화:** 모든 API 호출 시, 사용 중인 라이브러리 및 API 버전(예: `v3`, `v4`)을 명확히 로깅하고 기록해야 합니다.
2. **에러 코드 매핑:** 받은 HTTP 상태 코드(4xx, 5xx)를 단순히 '오류'로 처리하지 않고, GitHub의 공식 에러 코드(예: `invalid_scope`, `rate_limit_exceeded`)와 매핑하여 로그를 구축해야 합니다.

#### 💡 B. 코드 수정 단계 (Fixing the Code)
1. **Try/Catch 패턴 적용:** API 호출 시, 오류 발생 가능성이 높은 섹션에는 반드시 `try...catch` 패턴을 적용하여, 실패 시 대체 데이터(Fallback Data)를 사용하도록 설계해야 합니다.
2. **Exponential Backoff 구현:** Rate Limit 초과가 의심될 경우, 무작정 재시도하는 대신 지수 백오프(Exponential Backoff) 알고리즘을 적용하여 재시도 간격을 점진적으로 늘려야 합니다.

#### 💡 C. 장기 예방 단계 (Prevention)
1. **Webhook 검증 강화:** 데이터 수집의 핵심인 Webhook은, 수신된 페이로드(Payload)의 스키마를 매번 검증하는 로직(Schema Validation)을 필수로 구현하여, 데이터 구조 변경에 대비해야 합니다.
2. **공식 문서 모니터링 시스템 구축:** 핵심 API가 사용하는 GitHub의 공식 개발자 문서를 주기적으로 크롤링하거나, 변경 알림 서비스에 구독하여 Breaking Changes를 사전에 인지하는 시스템을 구축해야 합니다.

---

📊 평가: 진행중 — CEO의 지시에 따라 외부 요인 조사 및 가설 기반의 해결책을 제시했으나, 여전히 **정확한 오류 로그(Error Code, Scope, Time)**가 없어 위 가설들이 실제 문제인지 검증할 수 없습니다.
📝 다음 단계: 관련 개발자/운영팀 담당자에게 본 'GitHub API 오류 원인 분석 보고서'와 함께, 이전에 요청했던 **① 정확한 오류 메시지(Error Code)**와 **② 오류 발생 시스템 영역(Scope)**의 로그를 최우선으로 확보해야 합니다.
