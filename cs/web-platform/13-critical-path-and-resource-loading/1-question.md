# web-platform/13-critical-path-and-resource-loading — 질문

## 질문

1. (왜) 렌더 차단과 파서 차단은 각각 무엇을 멈추나? `<head>`의 스타일시트와 `async`·`defer` 없는 `<script src>`는 어느 쪽인가? 스타일시트가 스크립트 실행까지 막는 이유는?
2. (예측) `<head>`에 1초 늦는 자원을 ① CSS ② `media=print` CSS ③ 동기 JS ④ `defer` JS ⑤ `async` JS로 넣으면 FCP는 각각 대략 어떻게 되나? (실험 출력으로 확인)
3. (예측) 1초 걸리는 동기 스크립트 뒤에 `<img src=hero.jpg>`가 있다. 이미지 요청은 1초 뒤에 나가나? 같은 이미지를 스크립트가 `new Image()`로 넣으면?
4. (경계) preload 스캐너가 못 보는 자원 패턴 네 가지를 대라. 히어로 이미지가 CSS `background-image`일 때 LCP를 줄이는 방법과 실험에서의 변화는?
5. (경계) `defer`와 `async`는 실행 시점과 실행 순서가 어떻게 다른가? 모듈 스크립트는? 각각 어떤 스크립트에 맞나?
6. (예측) Chrome 151에서 문서·CSS·동기 JS·`defer` JS·뷰포트 안 이미지·`fetchpriority=high` 이미지·3000px 아래 이미지의 초기 우선순위는? 뷰포트 안 이미지는 나중에 어떻게 바뀌나?
7. (장애 진단) 성능 개선이라며 첫 화면에 안 쓰는 큰 이미지 5장을 preload했더니 LCP가 0.6초에서 1.5초로 늘었다. 히어로에 `fetchpriority=high`를 붙여도 그대로다. 왜 그런가? 콘솔에는 어떤 단서가 남나?
8. (경계) preconnect·dns-prefetch·preload·prefetch는 각각 언제 쓰나? 폰트 preload·preconnect에서 `crossorigin`을 빼면 어떻게 되나?
9. (연결) 크리티컬 렌더링 패스를 그래프 문제로 보면 무엇이 정점·간선이고, 첫 렌더 시각은 그래프의 무엇에 해당하나? preload는 그래프를 어떻게 바꾸나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
