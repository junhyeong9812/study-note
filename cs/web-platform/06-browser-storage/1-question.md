# web-platform/06-browser-storage — 질문

## 질문

1. (왜) 쿠키·localStorage·IndexedDB·Cache Storage를 고를 때 따져야 할 네 가지 축은? 세션 식별자·테마 설정·오프라인 초안을 각각 어디에 두나?
2. (예측) 서버가 `sid=secret; HttpOnly`와 `theme=dark`를 주고, 페이지가 `localStorage.access_token`을 저장했다. 페이지 스크립트에서 `document.cookie`와 `localStorage.getItem('access_token')`은 각각 무엇을 돌려주나? 이것이 토큰 저장 위치에 주는 교훈은?
3. (예측) Chrome 151에서 localStorage에 1Mi 문자짜리 값을 계속 넣으면 몇 번째에서 어떤 예외가 나나? 값이 한글이면 달라지나? 이 결과로 볼 때 쿼터는 무엇을 센다고 해석할 수 있나?
4. (계산) 실험에서 4MiB 문자열 `setItem`이 42~54ms 걸렸다. 60Hz 화면의 한 프레임 예산과 비교하면? 왜 IndexedDB로 옮기면 이 문제가 줄어드나?
5. (예측) IndexedDB 객체 저장소에 키 `10, 'b', 2, 'a', new Date(0), [1]`을 넣고 `getAllKeys()`를 하면 순서는? 같은 readwrite 트랜잭션에서 `add({id:'new1'})` 다음 이미 있는 키로 `add({id:10})`를 하면 `new1`은 남나?
6. (경계) 다른 포트의 페이지(127.0.0.1:A vs 127.0.0.1:B)는 서로의 localStorage를 볼 수 있나? 쿠키는? 둘이 다른 이유는?
7. (경계) best-effort와 persistent 저장소의 차이는? 공간이 모자랄 때 브라우저는 무엇을 어떤 단위로 지우나(MDN 기준)?
8. (장애 진단) iPhone 사용자가 "며칠 안 들어갔더니 오프라인 초안이 사라졌다"고 한다. 오류 로그는 없다. 가능한 원인과 대처는?
9. (연결) IndexedDB 트랜잭션 안에서 `await fetch(...)`를 한 뒤 같은 트랜잭션으로 `put`하면 무엇이 잘못되나? 올바른 순서는?
10. (연결) Chromium의 IndexedDB 저장 엔진은 무엇에서 무엇으로 바뀌는 중인가? 그 두 자료구조의 차이를 한 줄씩 말하고, 이 노트 실험의 디스크 프로필에서는 무엇이 보였나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
