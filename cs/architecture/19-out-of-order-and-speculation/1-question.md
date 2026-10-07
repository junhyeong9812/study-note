# architecture/19-out-of-order-and-speculation — 질문

## 질문

1. (왜) 순서대로만 실행하는 CPU는 메모리 읽기 하나 뒤에서 왜 노나? 비순차 실행은 실행 순서와 확정 순서를 각각 어떻게 다루나? 재정렬 버퍼(ROB)의 역할은?
2. (경계) 아키텍처 상태와 마이크로아키텍처 상태는 무엇이 다른가? 틀린 투기 실행 뒤 각각 어떻게 되나?
3. (예측) 같은 개수의 `double` 덧셈을 누적 변수 1개로 할 때와 4개로 나눠 할 때 시간이 어떻게 다를까? gcc가 `-O2`에서 1개짜리를 스스로 4개로 바꾸지 않는 이유는?
4. (그림) Spectre 변형 1의 흐름을 네 단계로 그려라(코드 아닌 그림으로). 변형 2는 무엇을 오염시키나?
5. (경계) Meltdown과 Spectre는 무엇이 다른가? Meltdown의 대표 완화책 PTI는 무엇을 바꾸고, 왜 시스템 콜마다 비용이 드나?
6. (장애 진단) 커널·마이크로코드 업데이트 뒤 프록시 서버의 `sys` CPU가 올랐다. 무엇을 보고 어떤 순서로 판단하나? `mitigations=off`는 언제 고려할 수 있나?
7. (그림) 이 호스트의 `/sys/devices/system/cpu/vulnerabilities/meltdown`과 `spectre_v2` 값은? 그 값이 [os/02](../../os/02-system-calls/2-summary.md)의 시스템 콜 비용 측정과 어떻게 이어지나?
8. (예측) 프로세스가 `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_DISABLE, 0, 0)`을 부르기 전후로 `/proc/self/status`의 `Speculation_Store_Bypass` 줄은 어떻게 바뀌나? 컨테이너(seccomp 적용) 안의 셸은 왜 `thread vulnerable`인가?
9. (연결) "신뢰하지 않는 코드를 컨테이너로 격리하면 CPU 취약점과 무관하다"는 주장이 틀린 이유와, 격리 수준을 높이는 선택지는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
