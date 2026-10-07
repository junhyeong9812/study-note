# language/13-language-memory-model — 질문

## 질문

1. (왜) 하드웨어 메모리 순서(architecture/14)를 알면 되는데, 왜 언어 차원의 메모리 모델이 따로 필요한가? 순서를 바꾸는 주체 셋을 들어라.
2. (그림) `data = 42; ready = true;`(A) / `if (ready) r = data;`(B)에서 `ready`가 volatile일 때 happens-before 간선을 그리고, B가 42를 보는 것이 왜 보장되는지 설명하라. JLS 17.4.4의 synchronizes-with 간선 종류를 네 가지 이상 들어라.
3. (경계) "A happens-before B면 A가 실제로 B보다 먼저 실행된다"는 맞나? JLS 17.4.5는 무엇이라고 하나?
4. (경계) data race의 정의를 Java와 C11에서 각각 말하고, race가 있을 때 두 언어가 주는 보장이 어떻게 다른지, 왜 다른지 설명하라.
5. (예측) Java 21, x86에서 SB 리트머스(`x=1; r1=y` ∥ `y=1; r2=x`)를 plain·volatile·acquire/release·opaque·(release + `fullFence` + acquire)로 2백만 번씩 돌렸다. 각 모드에서 (0,0)은 나오나? `-Xint`에서 plain은?
6. (왜) 메시지 전달(MP)에는 release/acquire로 충분한데 SB에는 왜 부족한가? `VarHandle` 문서의 모드 정의로 답하라.
7. (예측) C에서 plain `int ready`를 깃발로 기다리는 루프를 `gcc -O0`, `gcc -O2`, `clang -fsanitize=thread`로 각각 빌드해 돌리면 어떻게 되나? `-O2` 결과를 objdump로 설명하라.
8. (연결) 모든 필드가 `final`인 불변 객체를 `volatile` 없이 다른 스레드에 넘겨도 되는 조건은? DCL을 고치는 세 가지 방법과 연결하라.
9. (장애 진단) `volatile`을 `setRelease`/`getAcquire`로 바꿔 "최적화"한 뒤, 직접 만든 상호 배제에서 두 스레드가 동시에 임계 구역에 들어간다. 원인과 대처는?
10. (장애 진단) 공유 변수 하나를 보고 무엇으로 동기화할지 고르는 결정 순서를 말하라. 카운터에 `volatile`만 쓰면 왜 안 되나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
