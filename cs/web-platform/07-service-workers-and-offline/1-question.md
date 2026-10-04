# web-platform/07-service-workers-and-offline — 질문

## 질문

1. (왜) HTTP 캐시가 있는데도 서비스 워커가 필요한 이유는? 서비스 워커가 들어오면서 앱이 새로 떠안는 책임은?
2. (그림) 서비스 워커의 상태 값 여섯 개를 순서대로 쓰고, installed(waiting)에서 activating으로 넘어가는 조건 두 가지를 그림에 표시하라.
3. (예측) 처음 방문한 페이지에서 `register('/sw.js')`가 끝나고 워커가 activated가 됐다. 이 페이지의 `navigator.serviceWorker.controller`는? 새로고침 뒤에는? 이유는?
4. (예측) cache-first 워커가 `/`와 `/app.js`(v1)를 사전 캐시했다. 서버의 `/app.js`를 v2로 바꾸고 새로고침하면 화면은 v1인가 v2인가? network-first라면? 서버가 아예 응답하지 않으면 두 전략은 각각?
5. (예측) `sw.js`에 `Cache-Control: max-age=86400`을 줬다. 내용을 바꿔 배포하면 브라우저는 하루 동안 새 워커를 못 보나? 실험에서 확인 요청은 새로고침 후 언제 서버에 갔나?
6. (예측) 새 워커가 install을 마쳤다. 탭 하나를 열어 둔 채 새로고침을 한 번 더 하면 새 워커가 활성화되나? 탭을 닫고 새로 열면?
7. (경계) `skipWaiting()`+`clients.claim()`을 넣은 워커를 배포하고 새로고침했다. 그 새로고침 화면에는 새 버전 자원이 보이나? 한 번 늦는 이유는?
8. (경계) cache-first, network-first, stale-while-revalidate를 해시 파일명 JS, HTML, 아바타 이미지, 결제 API에 각각 어떻게 배정하나? 기준 한 문장은?
9. (장애 진단) 새 워커가 나타났다가 바로 `redundant`가 되고 옛 워커가 계속 제어한다. 콘솔에 `Failed to execute 'addAll' on 'Cache': Request failed`가 있다. 원인과 대처는? 이때 캐시에는 목록의 정상 URL이 들어가 있나?
10. (장애 진단) 배포 뒤 일부 사용자만 며칠째 옛 화면을 본다. 어디를 보면 서비스 워커 때문인지 알 수 있고, 지금 당장과 재발 방지 대처는 각각 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
