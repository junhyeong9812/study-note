# cs/issue/infra/git-pitfalls — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
공통 렌즈: git의 기본값은 "사람이 공유 머신에서 안전하게" 쓰라고 맞춰져 있다.
           배포/CI 자동화는 그 전제(사람·공유·눈으로 봄)와 어긋나 부딪힌다.

① dubious ownership   (ci-cd/issue2 ④)
   컨테이너 root(uid 0)가 호스트 jun(uid 1000) 소유 repo에 git 실행
   → git 2.35.2+ 가 "소유자≠실행자"면 거부 (도커가 아니라 git 자신)
   왜? CVE-2022-24765: 남이 심어둔 악성 설정(core.fsmonitor 등)이 내 권한으로 실행될 위험
   판단: 배포 전용 컨테이너 + 마운트 3개 고정 + 명령 allowlist → 위협 전제 불성립
   fix: Dockerfile  git config --global --add safe.directory '*'

② 빈 디렉토리 미추적   (front/issue3)
   git은 빈 디렉토리를 추적 안 함 → 새 checkout에서 src/app/api 소멸
   `> src/app/api/search/route.ts` (리다이렉션은 없는 디렉토리를 안 만듦) → 쓰기 실패
   Next 빌드는 "없는 라우트"를 오류로 안 봄 → 초록불 (조용한 실패)
   fix: mkdir -p 먼저 + 빌드 라우트 표에서 grep 확인 (.gitkeep로 디렉토리 유지도 가능)

③ quotepath 8진수     (backend/issue2 시도5)
   git ls-files/diff 기본값(core.quotepath=true) → 한글 경로를 "\352\267\270…" 로 이스케이프
   이 "사람용 안전 출력"을 파일 경로로 그대로 쓰면 → No such file or directory
   fix: git -c core.quotepath=off ...  (기계용 입력엔 이스케이프 끔)
```

## 핵심 문장
- dubious ownership은 **git이** 막는다(도커 아님). 도커는 기본적으로 uid를 격리 안 하므로 소유자≠실행자 비교가 컨테이너 안에서도 성립한다.
- 보안 가드에 걸리면 "끄는 법"보다 "**무엇을 막으려던 가드인지**"를 먼저 이해하고, 우리 상황에서 그 위협이 성립하는지로 판단한다.
- git은 빈 디렉토리를 추적하지 않는다 → 디렉토리 존재를 전제한 스크립트는 새 클론/checkout에서 조용히 깨진다.
- 도구의 "사람용 출력"을 "기계용 입력"으로 쓸 때가 고전 함정 — 기계가 읽을 거면 출력 이스케이프(quotepath)부터 끈다.
- "성공 로그"가 아니라 **산출물 목록**(빌드 라우트 표·실제 파일)을 확인 항목으로 삼는다.
