# issue10 — 트리 prev 링크, 그리고 배포가 조용히 안 되고 있던 사건

- 이슈 #21 · PR: #23

## 1. 내용

front 뒤로가기가 경로 문자열을 잘라 계산하던 것을 — 트리 생성 시점에 **각 노드에
prev(상위 폴더 경로)를 넣어** 객체의 링크로 이동하게 변경(사용자 설계). 순수 함수
TreeBuilder에 한 줄 재귀 인자 추가라 구현은 작다:

```kotlin
buildNode(childName, childPath, prev = path, …)   // 자식의 prev = 나의 path
```

## 2. 구현 중 마주친 문제 — 머지했는데 운영에 안 나가고 있었다

**상황**: PR 머지 → Actions "success" → 그런데 운영 API에 prev가 없다(None).

**문제(증상)**: master 배포 이력에 이 배포가 아예 없음. Actions 로그를 열어보니:

```
{"error":{"code":"unauthorized"},"success":false}
http:401                    ← 그런데 Actions 결론은 "success"
```

두 겹의 결함: ① **DEPLOY_SECRET 오등록** — 시크릿 대장(md)에서 값을 꺼낼 때
`grep 첫 32-hex`가 표의 **첫 행(SYNC_SECRET)** 을 집어 backend·front 리포에 엉뚱한
값이 등록돼 있었다. ② **워크플로 curl에 -f가 없어** 401이 초록불로 위장 — 홈에서
"성공"을 믿는 동안 배포는 한 번도 안 나가고 있었다.

**접근**: 운영 API 실값(prev=None) → master 이력 조회(기록 없음) → Actions 로그의
http 코드 순서로 좁힘. "Actions 초록불"을 증거로 안 친 게 핵심.

**결론(수정)**: 시크릿을 **정본(master의 .env)에서 직접** 다시 등록(전 리포), 재실행
→ 202 → 75초 뒤 배포 ok·prev 라이브. curl `-f` 추가는 남은 수정 목록에.

**배경**: ① 시크릿의 정본은 문서가 아니라 **사용처** — 문서는 사람용 사본이다.
② 파이프라인의 "성공"은 각 단계가 실패를 **전파해야** 의미가 있다 — 실패를 삼키는
단계 하나가 전체 신호를 거짓으로 만든다(이슈3의 "202≠배포됨"과 같은 계열).
