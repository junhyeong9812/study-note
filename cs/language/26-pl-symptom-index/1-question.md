# language/26-pl-symptom-index — 질문

## 질문

1. (왜) 커리큘럼의 일곱 증상(`NoSuchMethodError`·`ClassCastException`·`NullPointerException`·`StackOverflowError`·`GC overhead`·정규식 CPU 100%·async 정지)을 각각 "깨진 가정" 하나에 대응시켜라. 첫 질문이 "그 줄을 실행한 것이 정확히 무엇이었나"인 이유는?
2. (예측) 이 노트 실험에서 Caller를 money 2.0에 맞춰 컴파일한 뒤 money 1.0으로, 그리고 money 없이 실행하면 각각 어떤 예외가 나왔나? `NoSuchMethodError` 문구에서 무엇을 읽을 수 있나?
3. (예측·경계) 실험의 CCE·NPE·SOE는 메시지와 맨 위 프레임이 어떻게 나왔나? 운영의 CCE 트레이스만 보고 꺼낸 줄을 고치면 안 되는 이유는?
4. (장애 진단) 로그에 `java.lang.NullPointerException` 한 줄만 수천 개, 스택 0줄, 메시지 `null`이다. 원인은 무엇이고, 무엇부터 찾나? 같은 NPE가 드물게 x86이 아닌 서버에서만 나면 어느 갈래를 의심하나?
5. (장애 진단) `StackOverflowError`를 받았다. 이 영역 leaf에서 원인 갈래 셋을 들고, 각각을 가르는 첫 확인을 말하라. `-Xss`를 키우는 처방의 한계는?
6. (장애 진단) `OutOfMemoryError: GC overhead limit exceeded` 뒤 수집기를 G1으로 바꿨더니 `Java heap space`로 죽었다. 10번 실험을 근거로 이 현상을 설명하고, 먼저 봐야 할 지표를 말하라.
7. (구분) CPU 한 코어 100%를 받았다. 스레드 덤프 맨 위가 `Pattern$Loop.match` 무리인 경우, 새 파드에서만 1~몇 분 나는 경우, 기능 플래그를 켠 시점에만 잠깐 튀는 경우를 각각 어느 원인·leaf로 보내나?
8. (장애 진단) 외부 API 하나가 느려진 날, 무관한 API까지 모두 느려졌다. 공유 실행 자원 세 가지 갈래와 각각의 첫 확인을 말하라. 인스턴스 증설이 답이 아닌 이유는?
9. (연결) 9절(UB)·11절(설치 실패)의 증상은 27-pl-incidents의 어느 사건과 이어지나? 「하지 말 것」 표 왼쪽 항목들이 공통으로 하는 일은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
