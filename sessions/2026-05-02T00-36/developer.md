# 💻 Developer — 기술적 검증 계획을 수립하라. 연결 검증은 단순히 '연결 여부'가 아닌, '보안 아키텍처 적합성'에 초점을 맞춰야 한다. 다음 3가지 포인트를 포함하여 검증 절차를 설계할 것: 1) 모든 자격 증명은 Vault/KMS 기반의 최소 권한 토큰으로만 접근하는지 확인. 2) 모든 API 호출은 API Gateway를 통해 전용 서비스 계층(Data Fetcher Service)으로 격리되는지 확인. 3) 모든 요청/응답/실패는 중앙 로깅 시스템(ELK Stack)에 기록되는지 테스트할 것.

💻 Developer: 작업 시작합니다.

# 🛡️ 기술적 검증 계획 (Technical Validation Plan)
**목표:** 단순 기능 연동 여부 확인이 아닌, **최소 권한 원칙(PoLP)**을 준수하고 **보안 아키텍처의 적합성**을 검증하는 데 초점을 맞춥니다.

## 1. 아키텍처 검증 흐름도 (Conceptual Flow)

요청하신 3가지 포인트를 만족하는 이상적인 데이터 흐름(Data Flow)은 다음과 같아야 합니다.

`Client/Calling Service` $\xrightarrow{\text{Request}}$ `API Gateway` $\xrightarrow{\text{Auth Check}}$ `Data Fetcher Service` $\xrightarrow{\text{Token Request}}$ `Vault/KMS` $\xrightarrow{\text{Token Use}}$ `External API` $\xrightarrow{\text{Response}}$ `Data Fetcher Service` $\xrightarrow{\text{Logging}}$ `Central Logging (ELK)` $\xrightarrow{\text{Response}}$ `Client/Calling Service`

## 2. 필수 검증 시나리오 및 테스트 코드 (Executable Test Plan)

다음 3가지 핵심 포인트를 검증하기 위한 구체적인 테스트 시나리오와 검증 로직을 설계합니다.

### 🧪 Test Case 1: 자격 증명 관리 및 최소 권한 원칙(PoLP) 검증
**목표:** 토큰이 Vault/KMS를 통해 발급되고, 필요한 Scope만 가지는지 확인합니다.
**검증 항목:**
1.  **성공 시나리오:** 유효한 Scope를 가진 토큰을 획득하고 API 호출 성공 여부.
2.  **실패 시나리오 (권한 부족):** 존재하지 않거나, 현재 비즈니스 목적에 불필요한 Scope를 가진 토큰으로 API 호출 시도 $\rightarrow$ **반드시 403 Forbidden (권한 부족) 에러 코드 반환.**
3.  **실패 시나리오 (만료/미존재):** 만료된 토큰을 사용하여 API 호출 시도 $\rightarrow$ **반드시 401 Unauthorized (인증 실패) 에러 코드 반환.**

**[Pseudo-Code: Token Validation Layer]**
```python
def validate_api_call(api_endpoint: str, required_scope: list):
    """Vault/Secret Manager를 통해 토큰을 요청하고, 유효성을 검증하는 함수"""
    try:
        # 1. 토큰 획득 시도 (Secret Manager API 호출)
        token = secret_manager.get_token(required_scope=required_scope)
        
        # 2. Scope 검증 (가장 중요)
        if not token.has_scope(required_scope):
            log.error("토큰에 필수 Scope 누락. 접근 거부.")
            raise PermissionError("Insufficient Scope")
            
        # 3. 실제 API 호출 시도
        response = http_client.call(endpoint, headers={"Authorization": f"Bearer {token}"})
        return response
        
    except PermissionError as e:
        log.critical(f"권한 오류 발생: {e}")
        return None
    except Exception as e:
        log.error(f"네트워크/인증 오류 발생: {e}")
        return None
```

### 📊 에러 핸들링 및 로깅 (필수)
모든 실패 시, 단순 에러 메시지 대신, **어떤 종류의 권한 오류(Scope Error, Expiration Error 등)**가 발생했는지 구분하여 로그를 남겨야 합니다.

---

### 🚧 API Gateway/서비스 레이어 (실제 호출 지점)
실제 서비스 로직은 위 함수를 호출하여 결과를 받고, 받은 결과에 대해 비즈니스 로직상의 예외 처리를 수행합니다.

```python
def execute_business_logic(user_input):
    # 1. 필수 Scope 정의 (예: 'read:data', 'write:report')
    required_scope = "read:data" 
    
    # 2. 토큰을 통해 데이터 접근 시도
    data_response = validate_and_call_api(required_scope)
    
    if data_response is None:
        # 3. 실패 처리 (권한 문제로 인한 비즈니스 로직 중단)
        return {"status": "Failed", "reason": "권한 부족 또는 시스템 오류"}
        
    # 4. 성공 로직 수행
    return {"status": "Success", "data": data_response.get("data")}
```

---

### 📝 요약 및 결론 (제출 문서용)

| 단계 | 컴포넌트 | 책임 (책임 소재) | 검증 항목 (Checklist) |
| :--- | :--- | :--- | :--- |
| **1. 인증/권한** | Secret Manager | 토큰 발급 및 Scope 검증 | **[필수]** 요청된 Scope와 실제 토큰 Scope 일치 여부 검증. |
| **2. 호출/전달** | API Gateway/Client | 토큰을 헤더에 포함하여 요청 전달 | **[필수]** 토큰 만료 여부 체크 및 재발급 로직 구현. |
| **3. 비즈니스 로직** | Service Layer | API 응답을 받아 비즈니스 규칙 적용 | **[필수]** API 응답 코드(4xx, 5xx)에 따른 적절한 사용자 피드백 제공. |
| **4. 모니터링** | Logging System | 모든 단계의 성공/실패 기록 | **[필수]** 권한 오류(Permission Error)와 시스템 오류(System Error)를 분리하여 기록. |
