# language/20-undefined-behavior-and-memory-safety — 정답

## 정답

### 1. 배열 밖 읽기 — 세 언어

- Java: `ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3`. 그 자리에서 멈춘다([language 21](../21-language-choice-tradeoffs/2-summary.md) 실험).
- JS: `undefined`. 정의된 값이 나오고 예외는 없다.
- C: 미정의 동작. 이 호스트 gcc 13 `-O0`에서는 아무 오류 없이 어떤 정수가 나왔고, 그 값은 실행마다 달랐다(`159879248`, `10266432`, `-432788448` 등) — 관찰된 값일 뿐이다.
- "쓰레기 값"만으로 부족한 이유
  - 그 "쓰레기"는 대개 **다른 살아 있는 데이터**다. 응답에 실려 나가면 누출이 된다(Cloudbleed·Heartbleed).
  - 표준이 아무것도 요구하지 않으므로, 컴파일러가 그 접근 주변의 검사를 지우는 등 **값 이상의 일**이 일어날 수 있다(3·5번).

### 2. 세 분류

| 분류 | 뜻(N1570 §3.4) | 예 |
|---|---|---|
| 구현 정의 | 구현이 고르고 문서화 | 부호 있는 정수의 오른쪽 시프트 |
| 미지정 | 여러 가능성 중 아무거나 | 함수 인자 평가 순서 |
| 미정의 | 아무 요구 없음 | 정수 넘침(§3.4.3 예), 배열 범위 밖 첨자, null 역참조 |

- 부호 있는 넘침
  - C: 미정의(§6.5 ¶5 "예외 조건", J.2).
  - Go: 정의됨 — 결과가 표현 방식으로 결정적이고, 컴파일러는 `x < x+1`이 항상 참이라 가정하면 안 된다(Go 명세 "Integer overflow").
  - Java: 정의됨 — 결과는 2의 보수 하위 비트(JLS §15.18.2).

### 3. null 검사 삭제 (실험 1)

- `-O2`: 남지 않는다. gcc·clang 모두 `mov (%rdi),%eax; ret` 두 명령이 됐다.
- `-O2 -fno-delete-null-pointer-checks`: 남는다(`test %rdi,%rdi` + `cmovne`).
- 추론: "①에서 역참조했다 → 그것이 UB가 아니었다면 p는 null이 아니다 → ② 분기는 죽은 코드다"(GCC 13.3 `-fdelete-null-pointer-checks` 설명).

### 4. `x + 1 > x` 결과 (실험 2)

| 컴파일 | 결과 |
|---|---|
| gcc -O0 | 1 (기계어 `mov $0x1,%eax` — -O0에서도 식을 접음) |
| gcc -O2 | 1 |
| clang -O0 | 0 (실제로 더하고 비교 → 감김) |
| clang -O2 | 1 |
| gcc·clang -O2 -fwrapv | 0 |

- 교훈: UB가 있는 프로그램에는 "맞는 출력"이 없다. 같은 소스가 컴파일러·최적화 수준마다 다른 값을 냈고, 그중 어느 것도 표준 위반이 아니다.
- 부가: gcc는 식을 미리 접어 UBSan이 이 함수에서 보고하지 못했다. clang UBSan은 `signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'`를 보고했다.

### 5. 넘친 뒤의 넘침 검사 (실험 2의 `guard.c`)

- 원인: `len + add`는 넘치는 순간 UB다. 컴파일러는 "넘침은 없다"로 `len + add < len`을 `add < 0`으로 바꿨다(gcc -O2 기계어 `test %esi,%esi / js`). 이 기계어에서는 `add`가 0 이상이면 -1을 내지 않는다.
- 관찰: `len = INT_MAX-10, add = 100`에서 gcc -O0/-O2·clang -O2는 `-2147483559`를 반환했고 clang -O0만 -1이었다.
- 고치기
  - 연산 **전에** 판정: `if (len > INT_MAX - add)`(add ≥ 0일 때). `add > INT_MAX - len`으로 쓰면 `len`이 음수일 때 `INT_MAX - len`이 넘친다.
  - `__builtin_add_overflow(len, add, &r)`(GCC·Clang) — 시험한 네 조합 모두 -1. C23 `ckd_add`도 같은 일을 한다(단 이 호스트 gcc 13.3에는 `<stdckdint.h>`가 없었다).
  - 크기·길이는 `size_t` + 상한 검사.

### 6. Cloudbleed

```text
  [ ... 버퍼 ... '<' ] [ 옆 메모리 ... ]
                    pe-1  pe   pe+1
  '<' 처리로 p가 pe에 닿은 뒤 ++p → pe+1
  if (++p == pe)   pe+1 ≠ pe → 끝을 못 봄 → 옆 메모리를 계속 파싱
  if (++p >= pe)   pe+1 ≥ pe → 끝으로 처리(보고서의 수정 — 단 pe+1 계산부터 C 표준상 UB)
  if (p < pe) ++p  증가 전에 확인 — 표준상 안전한 형태
```

- Cloudflare 보고서(2017-02-23): 생성 코드 `if ( ++p == pe )`가 근본 원인이며 "`>=`였다면 잡혔다". 포인터를 한 칸 되돌리는 처리(`fhold`)가 오류 경로에 없어 p가 pe를 지나쳤다.
- 잠복 이유: 같은 버그가 Ragel 기반 옛 파서에 수년간 있었지만 NGINX 내부 버퍼 사용 방식 때문에 누출이 없었다. 새 파서 cf-html 도입이 버퍼링을 바꿔 누출 조건이 열렸고, 2017-02-13 Email Obfuscation 일부 이관 뒤 영향이 커졌다.

### 7. ASan이 풀 안 넘침을 못 잡은 이유 (실험 3)

- ASan은 할당마다 앞뒤에 레드존(접근 금지)을 두고, 접근 전에 그림자 메모리를 조회한다. 범위 밖 접근은 **할당 경계**를 넘을 때만 안다(해제 후 사용·이중 해제 탐지는 별도).
- 한 번에 크게 할당한 풀 안에서는 "응답 A 영역"을 넘어도 같은 할당 안이라 합법 접근으로 보인다. 그래서 exit 0, 보고 없음이었다.
- 다른 못 잡는 경우: 실행되지 않은 경로, 구조체 안에서 배열이 옆 필드로 넘침(intra-object, [security/24](../../security/24-memory-safety-exploits/2-summary.md)), 레드존을 건너뛰어 다른 할당 안으로 바로 들어간 접근(해석 — 레드존 크기에 달림 [?]).

### 8. 네 축과 부록 L

| 축 | 예 |
|---|---|
| 공간 | 버퍼 오버플로·over-read(Cloudbleed·Heartbleed) |
| 시간 | use-after-free, double free |
| 타입 | 해제 후 같은 자리에 들어온 다른 타입 객체를 옛 타입으로 씀 |
| 초기화 | 쓰기 전에 읽어 이전 사용자의 데이터가 보임 |

- 부록 L(N1570, 선택 사항): **bounded UB**는 범위 밖 저장을 하지 않는 UB(트랩·불확정 값은 가능), **critical UB**는 그 밖 — 수명 밖 객체 참조, 잘못된 포인터 역참조 등.
- 실무 질문과 같다: "이 버그의 피해가 틀린 값에서 멈추나, 남의 메모리를 고쳐 번지나." 후자는 원인과 증상 위치가 멀어지고 보안 문제가 된다.

### 9. 릴리스에서만 틀림

- 먼저 UB를 의심한다. 최적화 수준마다 컴파일러가 다른 가정을 써서 결과가 갈린다(4번). printf가 배치·최적화를 바꿔 증상이 사라지는 것도 같은 신호다.
- 확인
  - `clang -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined`로 테스트를 돌려 보고 위치를 본다.
  - 의심 함수의 `objdump -d`/`-S`로 검사 분기가 남아 있는지 본다(3번).
  - `-fwrapv`·`-fno-delete-null-pointer-checks`로 다시 빌드해 증상이 바뀌면 그 계열의 UB다.
- "컴파일러 버그"는 이 확인을 다 한 뒤에 의심한다.
