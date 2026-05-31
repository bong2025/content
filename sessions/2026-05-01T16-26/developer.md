# 💻 Developer — 연구 결과를 바탕으로, 이 오류를 해결하는 구체적인 기술 로드맵을 제시합니다. (1) 보호된 브랜치(main)에 직접 푸시하는 것을 금지하고, (2) 반드시 'Pull Request(PR)'를 통해서만 병합(Merge)할 수 있도록 워크플로우를 재설정하는 방법을 안내합니다. 필요한 설정 항목(예: CI/CD 트리거, 리뷰 승인자 설정)을 리스트업하여 실행 가능한 코딩/설정 가이드를 제공합니다.

💻 Developer: 작업 시작합니다.

제시된 오류(`GH013: Repository rule violations found`)는 코드가 잘못되었다는 문제가 아니라, **저장소의 보안 정책(Branch Protection Rules)**을 위반했기 때문에 발생한 구조적인 문제입니다. 이는 CI/CD 파이프라인 구축의 가장 기본적인 단계이며, 시스템 안정성을 확보하는 필수 과정입니다.

따라서, 이 오류를 해결하는 로드맵은 **'코드를 고치는 것'이 아니라 '워크플로우를 고치는 것'**입니다.

다음은 `main` 브랜치에 대한 보호 규칙을 설정하고, Pull Request(PR) 기반의 CI/CD 파이프라인을 구축하는 구체적인 기술 로드맵 및 설정 가이드입니다.

---

## 🚀 GitHub CI/CD 기반 워크플로우 재설정 로드맵

### 🎯 목표 요약
1.  **`main` 브랜치 보호:** 직접 푸시(Direct Push)를 시스템적으로 금지합니다.
2.  **PR 강제화:** 모든 변경 사항은 PR을 통해서만 병합(Merge)되도록 합니다.
3.  **자동화된 게이트:** PR이 생성될 때마다 자동 테스트(CI)가 실행되어 코드 품질을 검증합니다.

### 🛠️ 1단계: GitHub 설정 (Branch Protection Rules)

GitHub 웹 인터페이스에서 다음 설정을 반드시 적용해야 합니다.

**📍 경로:** `Settings` → `Branches` → `Branch protection rules`
**📍 규칙 대상:** `main` 브랜치
**📍 필수 활성화 설정 (체크박스):**

1.  ✅ **Require pull request reviews before merging:** (필수) PR 없이는 Merge 불가.
2.  ✅ **Require approvals:** (필수) 최소 1명 이상의 리뷰 승인자가 필요함.
3.  ✅ **Require status checks to pass before merging:** (필수) CI/CD가 성공해야만 Merge 가능.
4.  ✅ **Restrict who can push to matching branches:** (선택/보강) 이 규칙을 사용하면 `main` 브랜치에 대한 직접 푸시가 근본적으로 차단됩니다.

### 💻 2단계: CI/CD 자동화 코드 작성 (GitHub Actions)

PR이 생성될 때마다 자동으로 테스트를 실행하는 워크플로우를 정의합니다. 이 파일은 모든 코드가 커밋될 때마다 자동으로 실행되는 '자동 게이트' 역할을 합니다.

**📍 파일 경로:** `.github/workflows/ci.yml` (프로젝트 루트 디렉터리)

```yaml
# .github/workflows/ci.yml
name: CI - Code Quality Check

on:
  # 1. PR이 생성되거나 업데이트될 때마다 트리거 (가장 중요)
  pull_request:
    branches: [ main ]
  # 2. 메인 브랜치에 직접 푸시할 경우 (이 경우는 보호 규칙에 의해 막히지만, 예방적 설정)
  push:
    branches: [ main ]

jobs:
  build_and_test:
    runs-on: ubuntu-latest # 가상 환경 설정
    steps:
      # 1. 코드 체크아웃 (작업할 코드 다운로드)
      - name: Checkout repository
        uses: actions/checkout@v4

      # 2. 환경 설정 (예: Node.js 20 버전 사용)
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      # 3. 의존성 설치 (npm install)
      - name: Install dependencies
        run: npm install

      # 4. 테스트 실행 (npm test)
      # 이 단계가 실패하면 PR의 상태가 'Failed'로 표시되어 Merge가 차단됩니다.
      - name: Run unit tests
        run: npm test

      # 5. (선택) 코드 포맷 검사
      # - name: Run linter
      #   run: npm run lint
```

### ⚙️ 3단계: 개발자 워크플로우 변경 가이드 (The New Flow)

개발자가 가장 중요하게 숙지해야 할 새로운 업무 방식입니다. 이 단계를 따르지 않으면 여전히 `GH013` 오류를 만날 수 있습니다.

1.  **새로운 브랜치 생성 (Feature Branching):**
    *   `main` 브랜치에서 절대 직접 작업하지 않습니다.
    *   항상 `main`을 기반으로 새로운 브랜치를 생성합니다.
    *   **명령어 예시:** `git checkout -b feature/user-auth-login`
2.  **개발 및 커밋:**
    *   `feature/user-auth-login` 브랜치에서 코드를 개발하고 커밋합니다.
    *   **명령어 예시:** `git commit -m "feat: Add login form"`
3.  **원격 푸시:**
    *   자신이 만든 Feature Branch에만 푸시합니다.
    *   **명령어 예시:** `git push origin feature/user-auth-login`
4.  **Pull Request (PR) 생성:**
    *   GitHub 웹사이트로 이동하여, `feature/user-auth-login` $\rightarrow$ `main` 을 대상으로 PR을 생성합니다.
    *   **🔥 중요:** 이 순간 CI/CD (`.github/workflows
