# 💻 Developer — 정의된 '강력한 병합 정책'을 구현하기 위한 구체적인 기술적 단계를 설계하시오. 1. 깃허브의 '브랜치 보호 규칙(Branch Protection Rules)'을 설정하는 구체적인 절차를 설명하고, 2. PR이 생성될 때 자동으로 실행되는 CI/CD 파이프라인(예: GitHub Actions)의 워크플로우 파일(`main.yml`) 초안을 작성하여, 테스트 실행 및 Linting 검사를 필수화하시오.

💻 Developer: 작업 시작합니다.

제시된 `GH013` 오류는 근본적으로 **'프로세스(Process)의 부재'**에서 기인합니다. 단순히 코드를 고치는 것이 아니라, 코드가 `main` 브랜치에 합병(Merge)되기 전에 반드시 **검증(Verification)** 과정을 거치도록 시스템을 구축해야 합니다.

이 목표를 달성하기 위해, 다음 두 가지 계층적 방어 장치(Layered Defense)를 구현합니다.

1.  **[정책 계층]** GitHub의 **브랜치 보호 규칙**을 설정하여, 사람의 행동(Push)을 강제적으로 제한합니다.
2.  **[실행 계층]** **GitHub Actions**를 통해 PR이 생성될 때마다 자동화된 테스트/Linting 검사를 강제 실행합니다.

---

### 🛡️ 1. GitHub 브랜치 보호 규칙 설정 (Branch Protection Rules)

이 설정은 `main` 브랜치에 대한 모든 수동 푸시(Direct Push)를 원천 차단하는 핵심 단계입니다.

**[적용 대상 브랜치]** `main`
**[설정 절차]**

1.  **저장소 설정 진입:** GitHub 레포지토리 → **Settings** → **Branches**로 이동합니다.
2.  **브랜치 보호 규칙 추가:** `main` 브랜치에 대한 보호 규칙을 생성합니다.
3.  **필수 옵션 활성화 (Critical):**
    *   ✅ **Require pull request reviews before merging:** (필수) 병합 전에 반드시 PR을 요구합니다.
    *   ✅ **Require approvals:** (필수) 최소 1명 이상의 승인자(Reviewer)를 지정합니다. (최소 2명 권장)
    *   ✅ **Include administrators:** (선택) 관리자 계정 포함 여부를 설정합니다.
    *   ✅ **Require status checks to pass before merging:** (가장 중요) 이 옵션을 활성화하고, 여기에 아래에서 작성할 **CI/CD 워크플로우 이름**을 추가합니다. 이 게이트가 통과하지 못하면 Merge 버튼 자체가 비활성화됩니다.
4.  **직접 푸시 제한 (The Fix for GH013):**
    *   **Do not allow force pushes:** (필수) 강제 푸시를 막습니다.
    *   **Require linear history:** (권장) 히스토리가 깔끔하게 유지되도록 합니다.

**[효과]** 이 설정을 완료하면, 개발자가 로컬에서 코드를 수정하더라도 `main` 브랜치에 직접 `git push`를 시도하는 것은 원천적으로 차단됩니다. 모든 변경은 오직 PR을 통해서만 이루어져야 합니다.

---

### ⚙️ 2. CI/CD 워크플로우 파일 초안 (`.github/workflows/main.yml`)

이 워크플로우는 PR이 생성되거나 업데이트될 때마다 자동으로 실행됩니다. 테스트와 Linting을 실패 시키면, 브랜치 보호 규칙에 의해 Merge가 불가능해집니다.

**[파일 위치]** `.github/workflows/main.yml`

```yaml
# main.yml
name: 🚀 Code Quality & Test Gate

# 🎯 1. 언제 실행할 것인가? (Trigger)
# PR이 생성되거나 업데이트될 때만 실행하도록 제한합니다.
on:
  pull_request:
    branches: [ main ]

# 🛠️ 2. 어떤 Job을 실행할 것인가? (Job Definition)
jobs:
  build_and_test:
    # 🏃 병렬 실행 및 환경 설정
    runs-on: ubuntu-latest
    
    # 🚨 실패 시 전체 PR Merge를 차단하는 핵심 로직
    # 이 Job이 실패하면, 브랜치 보호 규칙의 Status Check가 실패합니다.
    
    steps:
      # 1. 코드 체크아웃
      - name: Checkout Code
        uses: actions/checkout@v4

      # 2. 환경 설정 (예시: Node.js 환경 가정)
      - name: Setup Node.js Environment
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      # 3. 의존성 설치
      - name: Install Dependencies
        run: npm ci # ci는 CI 환경에 최적화된 설치 명령입니다.

      # 4. Linting (코드 스타일 및 문법 검사)
      - name: Run Lint Check
        run: npm run lint # package.json에 "lint": "eslint ."가 정의되어 있어야 합니다.
        # 이 단계에서 에러가 발생하면, 워크플로우가 즉시 실패합니다.

      # 5. Unit & Integration Testing (핵심 테스트)
      - name: Run Unit & Integration Tests
        run: npm run test -- --ci # package.json에 "test": "jest --ci"가 정의되어 있어야 합니다.
        # 이 단계에서 테스트가 실패하면, 워크플로우가 즉시 실패합니다.
        
      # (추가 옵션: 보안 스캔을 추가할 수 있습니다.)
      # - name: Security Scan
      #   run: npm run security-scan
```

**[사용법]**
1.  위 코드를 프로젝트의 `.github/workflows/main.yml` 파일로 저장합니다.
2.  (필요한 경우) `package.json`에 `lint` 및 `test` 스크립트를 정의하고, Linting/Testing 라이브러리를 설치합니다.
3.  개발자는 반드시 Feature Branch에서 작업하고, PR을 생성하여 테스트가 통과하는지 확인합니다.

---
📊 평가: 완료 — 브랜치 보호 규칙 설정과 CI
