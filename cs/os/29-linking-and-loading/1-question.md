# os/29-linking-and-loading — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고, 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> ⚠️ 이 질문 목록은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 질문

1. (왜) 링커가 하는 두 가지 일은 무엇인가? `nm main.o`의 `U add`와 `readelf -r main.o`의 `R_X86_64_PLT32 add`는 각각 그중 무엇의 재료인가?
2. (예측) `gcc -L. -Wl,-Bstatic -ladd -Wl,-Bdynamic main.o`는 실패하고, `main.o`를 앞에 두면 성공한다. 링커가 정적 라이브러리를 읽는 방식으로 설명하라.
3. (그림) `./app`을 실행했을 때 `execve`부터 `main`까지 커널과 동적 로더가 각각 하는 일을 순서대로 그려라. `PT_INTERP`와 `AT_ENTRY`는 어디에 나오나?
4. (경계) 빌드 때 `-L./lib`을 줬는데 실행하면 `cannot open shared object file`이 난다. 왜 빌드 때 경로가 실행 때 쓰이지 않나? 로더의 탐색 순서를 적고, 폴더째 배포할 때 쓰는 방법을 말하라.
5. (그림) PIC 코드가 `add`를 부를 때 PLT·GOT를 거치는 경로를 그려라. 왜 코드에 주소를 바로 박지 않고 한 단계를 더 두나? 지연 바인딩과 `BIND_NOW`의 차이는?
6. (장애 진단) CI에서 빌드한 바이너리가 운영 서버에서 `version 'GLIBC_2.34' not found`로 안 뜬다. 무엇을 확인하고 어떻게 고치나? 반대 방향(옛 곳에서 빌드 → 새 곳에서 실행)은 왜 대개 괜찮나?
7. (장애 진단) alpine 이미지에 복사한 바이너리가 `ls`로는 보이는데 실행하면 `not found`다. `strace`로 무엇이 보이고, 원인은 무엇인가?
8. (연결) Java의 `UnsatisfiedLinkError`, Node의 `ERR_DLOPEN_FAILED`는 OS의 어느 단계 실패가 드러난 것인가? 원인을 좁히는 데 쓸 환경 변수 하나를 들어라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
