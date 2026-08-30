# issue9 — 자동 배포 호출 편입 (+ 바인딩과 헬스체크의 충돌)

- 이슈 #18 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/19

## 1. 내용

llm과 동일한 호출-전용 Actions(main push → www/api/deploy, `{service: backend, commit_sha}`).
빌드는 .158 에이전트가 git pull 후 수행 — gradle이라 걱정했지만 **도커 레이어 캐시
덕에 증분 38초**(의존성 레이어는 build.gradle이 안 바뀌면 재사용).

## 2. 첫 자동 배포가 unhealthy로 실패한 사건

backend만의 특이점: 이 리포는 보안 리뷰 때 `${BIND_ADDR:?}` **fail-closed 바인딩**을
도입해 앱이 LAN IP에만 열린다. 에이전트의 배포 후 헬스 확인이 127.0.0.1을 두드리자
connection refused — **배포는 정상인데 헬스 URL이 틀린** 상황을 헬스체크가 "실패"로
정직하게 보고했다. 전말과 의미는 ci-cd issue3 §3에 정리(두 검증 장치가 서로를 검증한
사례). 교정: DEPLOY_HEALTH_BACKEND를 LAN 주소로.

## 3. 결론

backend도 push→자동 배포(38s). 특이 설정(BIND_ADDR)이 있는 서비스는 헬스 URL도 그
설정을 따라야 한다는 운영 지식 한 줄을 얻었다. PR: #19
