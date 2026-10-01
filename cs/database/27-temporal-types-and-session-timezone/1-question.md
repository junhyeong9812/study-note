# database/27-temporal-types-and-session-timezone — 질문

## 질문

1. (왜) "순간"과 "벽시계 값"은 무엇이 다른가? 결제 시각과 "매일 09:00 알림 시각"은 각각 PostgreSQL·MySQL·Java의 어떤 타입에 담아야 하나?
2. (예측) PostgreSQL 17에서 `SET TimeZone='Asia/Seoul'` 후 `timestamp` 컬럼 a와 `timestamptz` 컬럼 b에 똑같이 `'2026-10-01 00:30:00'`을 넣었다. 세션을 `UTC`로 바꿔 읽으면 a와 b는 각각 무엇으로 보이나? `timestamptz`는 시간대를 저장하나?
3. (그림) JVM은 Asia/Seoul, DB 세션은 UTC다. 앱이 서울 10시를 시간대 없는 글자로 보내 `timestamptz`에 저장했다. 저장된 순간은 서울 기준 몇 시인가? 흐름을 그림으로 그려라.
4. (경계) MySQL Connector/J 8.0.23+의 `preserveInstants`·`connectionTimeZone`·`forceConnectionTimeZoneToSession` 기본값은? 기본값 조합이 9시간 밀림을 막지 못하는 조건은?
5. (계산) 한국 시각 판매 4건(09-30 23:59 100원, 10-01 00:30 200원, 10-01 08:59 300원, 10-01 09:00 400원). UTC 세션에서 `date_trunc('day', sold_at)`로 일별 합계를 내면 결과는? 한국 기준으로 고친 쿼리와 결과는?
6. (경계) MySQL `TIMESTAMP`의 범위는? 상한 값은 어디서 나오나? 세션이 `+09:00`일 때 들어가는 마지막 글자는?
7. (연결) pgJDBC에서 `timestamptz`를 `Instant`로 바로 `setObject`하면? 어떤 Java 타입을 써야 하나? 읽어 온 `OffsetDateTime`의 오프셋은?
8. (장애 진단) 배포 후부터 새 주문의 생성 시각만 9시간 늦게 보인다. 에러는 없다. 무엇을 어떤 순서로 확인하고, 데이터는 어떻게 보정하나?
9. (장애 진단) MySQL에서 앱 기동 시 `ERROR 1298 (HY000): Unknown or incorrect time zone: 'Asia/Seoul'`이 난다. 원인과 대처 두 가지는? 오프셋 `'+09:00'`으로 대체할 때의 한계는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
