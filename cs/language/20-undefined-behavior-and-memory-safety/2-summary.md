# language/20-undefined-behavior-and-memory-safety — 미정의 동작·경계 검사·메모리 안전 — 정리 (힌트)

## 해결하는 문제

프로그램이 틀린 일을 했을 때 언어가 무엇을 약속하느냐가 장애의 모양을 정한다.

```text
  arr[5] (길이 3) 를 읽었다
  ┌ Java·Go·Python ─ 그 자리에서 예외/panic        → 안 잡으면 크래시(서버면 보통 500), 로그에 위치
  ├ JS               ─ undefined (정의된 값)         → 조용히 틀린 값
  └ C·C++            ─ 미정의 동작(UB) — 아무 요구 없음 → 옆 메모리를 읽고 정상 응답에 실어 보낼 수도
                                                        (Cloudbleed·Heartbleed)
```

- *미정의 동작(undefined behavior, UB)*: 언어 표준이 "이 경우 아무 요구사항도 두지 않는다"고 정한 동작. 크래시할 수도, 엉뚱한 값을 낼 수도, 아무 일 없어 보일 수도 있다.
  - 흔한 오해: "C에서 null 역참조는 segfault로 죽는다." 표준은 트랩을 약속하지 않는다. 죽는 것은 운영체제가 0번 페이지를 매핑하지 않았을 때의 결과일 뿐이다(Lattner 2011).
- *메모리 안전(memory safety)*: 할당받은 범위·수명·타입 안에서만 메모리를 읽고 쓴다는 보장. 언어가 보장하느냐, 프로그래머에게 맡기느냐가 갈린다.

쉬운 예: 자판기 설명서에 "없는 버튼 번호를 누르면?"이 어떻게 적혀 있나.
- A사: "경고음을 내고 동전을 돌려준다."(예외)
- B사: "1번 상품이 나온다."(정의된 엉뚱한 값)
- C사: "그런 일은 없다고 가정하고 설계했다." 그래서 정비사는 버튼 번호 검사 회로를 빼서 기계를 싸게 만든다(최적화).

똑같은 구조다.\
C 컴파일러는 "UB는 일어나지 않는다"를 전제로 코드를 줄인다. 그래서 UB가 실제로 일어나면 소스에 적은 검사조차 사라져 있을 수 있다.

실무 예:
- 2017-02, Cloudflare 엣지의 HTML 파서가 버퍼 끝을 지나 읽어, 쿠키·인증 토큰·POST 본문이 다른 사이트의 응답에 섞여 나갔다(Cloudflare 사고 보고서).
- 2014-04, OpenSSL Heartbeat 처리의 경계 검사 누락으로 프로세스 메모리(개인 키 포함)를 읽어 갈 수 있었다(NVD CVE-2014-0160).
- 2009, Linux 커널 TUN 드라이버에서 "먼저 역참조, 그다음 null 검사" 코드의 검사를 GCC가 최적화로 지웠고, 이것이 커널 익스플로잇 사슬의 한 고리가 됐다(LWN 2009-07-20).

## 동작·원리

### 1. 틀린 프로그램에 대한 세 가지 약속 — C11 표준의 분류

```text
  구현 정의 (implementation-defined)  ─ 구현이 고르고 문서화한다      예: 부호 있는 정수의 오른쪽 시프트
  미지정    (unspecified)              ─ 여러 가능성 중 아무거나       예: 함수 인자의 평가 순서
  미정의    (undefined)                ─ 아무 요구사항 없음            예: 부호 있는 정수 넘침
```

- N1570(C11 위원회 초안) §3.4.3: UB는 "이 국제 표준이 아무 요구사항도 부과하지 않는" 동작이다. NOTE: "상황을 완전히 무시해 예측할 수 없는 결과를 내는 것"부터 "진단과 함께 번역·실행을 끝내는 것"까지. 예: 정수 넘침.
- 부록 J.2가 UB 목록이다. 이 노트와 관련된 항목(N1570 J.2)
  - 식 평가 중 예외 조건(결과가 수학적으로 정의되지 않거나 그 타입으로 표현 불가) — §6.5. 부호 있는 정수 넘침이 여기다.
  - 배열 첨자가 범위 밖 — "객체에 접근 가능해 보이더라도"(`int a[4][5]`에서 `a[1][7]`) — §6.5.6(N1570). C23 초안 N3220에서는 J.2의 46번 항목(§6.5.7)이다.
  - 단항 `*`의 피연산자가 잘못된 값 — §6.5.3.2. 각주 102: 잘못된 값에는 **null 포인터**, 정렬이 안 맞는 주소, **수명이 끝난 객체의 주소**가 있다.
  - 수명이 끝난 객체를 가리키는 포인터 값을 사용 — §6.2.4(use-after-free의 표준 쪽 이름).
- 대비: Go 명세 "Integer overflow"는 부호 있는 넘침이 "합법적으로 넘칠 수 있고 결과가 결정적으로 정의된다", "컴파일러는 넘침이 없다고 가정해 최적화하면 안 된다. 예컨대 `x < x + 1`이 항상 참이라고 가정할 수 없다"고 적는다. Java JLS §15.18.2도 정수 덧셈 넘침 결과를 "2의 보수 하위 비트"로 정의한다.

### 2. 컴파일러는 "UB는 없다"로 추론한다

```text
  int v = *p;          ① p를 역참조했다
  if (p == NULL)       ② "①이 UB가 아니었다면 p는 null이 아니다"
      return -1;          → 이 분기는 죽은 코드 → 삭제
  return v;

  return x + 1 > x;    "부호 있는 넘침은 없다" → x+1 > x 는 항상 참 → return 1
  if (len + add < len) "넘침은 없다" → 이 식은 add < 0 과 같다 → 넘침 검사가 사라짐
```

- GCC 13.3 문서 `-fdelete-null-pointer-checks`: "역참조한 뒤 검사한 포인터는 null일 수 없다"고 가정하는 전역 데이터 흐름 분석이 쓸모없는 null 검사를 지운다. 대부분 대상에서 기본으로 켜져 있다.
- Lattner(LLVM 블로그 2011): 부호 있는 넘침이 UB라서 `X+1 > X`를 참으로, `X*2/2`를 `X`로 바꿀 수 있고, `for (i = 0; i <= N; ++i)`가 정확히 N+1번 돈다고 가정해 루프 최적화를 켤 수 있다. 넘침을 정의(`-fwrapv`)하면 이 최적화들을 잃는다.

### 실험 1: null 검사 삭제 (`e20/nullcheck.c`, 호스트 gcc 13.3.0·clang 18.1.3, `objdump -d`)

```text
  == gcc -O0                              == gcc -O2                == gcc -O2 -fno-delete-null-pointer-checks
  mov (%rax),%eax      ; ① 역참조           mov (%rdi),%eax           test   %rdi,%rdi
  cmpq $0x0,-0x18(%rbp); ② 검사 남아 있음    ret                      mov    $0xffffffff,%eax
  jne ...                                  ← 검사 사라짐             cmovne (%rdi),%eax   ← 검사 남음
  mov $0xffffffff,%eax
  == clang -O2: mov (%rdi),%eax / ret      (같이 사라짐)
```

- `-O2`에서 함수가 "읽고 반환" 두 명령이 됐다. 소스의 `if (p == NULL)`은 기계어에 없다.
- `-Wnull-dereference`를 켜도 이 파일에서 gcc 13은 경고하지 않았다.
- Linux 커널 최상위 Makefile은 `-fno-delete-null-pointer-checks`와 `-fno-strict-overflow`를 붙여 빌드한다(torvalds/linux master `Makefile`). 0번 주소가 실제로 매핑될 수 있는 환경에서 이 가정이 틀리기 때문이다(GCC 문서 "some environments this assumption is not true").

### 실험 2: 부호 있는 넘침 (`e20/overflow.c`, `overflow2.c`, `guard.c`)

`will_grow(x) = (x + 1 > x)`를 `x = INT_MAX`로 부른다. 이 컴파일러·옵션에서 관찰된 결과다.

```text
  gcc   -O0: will_grow=1      gcc   -O2: 1      gcc   -O2 -fwrapv: 0
  clang -O0: will_grow=0      clang -O2: 1      clang -O2 -fwrapv: 0
  gcc -O0의 기계어: mov $0x1,%eax   ← -O0에서도 식 자체를 1로 접었다
  clang -O0의 기계어: add $0x1 / cmp / setg   ← 실제로 더하고 비교 → 감겨서 0

  넘침 검사 guard.c (len = INT_MAX-10, add = 100)
  gcc -O0/-O2, clang -O2: bad_guard=-2147483559   ← 검사가 통과돼 음수 길이 반환
  clang -O0:              bad_guard=-1
  네 조합 모두:            good_guard=-1           ← __builtin_add_overflow
  gcc -O2 bad_guard 기계어: test %esi,%esi / js → "add < 0" 만 본다
```

- 같은 소스가 컴파일러·최적화 수준에 따라 0과 1을 냈다. UB 프로그램에는 "맞는 출력"이 없다.
- "넘친 뒤 결과를 보고 판단"하는 검사는 넘침 자체가 UB라서 지워질 수 있다. 넘치기 **전에** 판정하는 `__builtin_add_overflow`(GCC 13.3 "Integer Overflow Builtins": 무한 정밀도로 계산해 결과가 들어맞는지 반환)는 시험한 네 조합 모두에서 -1을 냈다.
- C23은 같은 일을 `<stdckdint.h>`의 `ckd_add`로 표준화했다. 이 호스트의 gcc 13.3에는 그 헤더가 없었다(컴파일 오류로 확인). clang 18에는 있었다.
- UBSan: clang `-fsanitize=undefined`는 `will_grow`에서 `runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'`를 보고했다. gcc는 식을 미리 1로 접어 같은 파일에서 보고가 없었고, 더하기만 하는 `add1(x)`(overflow2.c)에서는 같은 문구를 보고했다. 기본은 보고하고 계속 실행(exit 0), `-fno-sanitize-recover=undefined`면 exit 1로 멈췄다.

### 3. 메모리 안전의 네 축

```text
  공간(spatial)    : 범위 밖 접근        — 버퍼 오버플로·over-read
  시간(temporal)   : 수명 밖 접근        — use-after-free·double free
  타입(type)       : 다른 타입으로 해석   — 해제 후 재할당된 다른 객체를 옛 타입으로 씀
  초기화(init)     : 쓰기 전 읽기        — 이전 사용자의 데이터가 남은 메모리
```

- 네 축 분류는 Google "Secure by Design: Google's Perspective on Memory Safety"(2024)를 따른 원고 [languages/c-cpp-csharp.md](../../../languages/c-cpp-csharp.md) 「C의 실패 계급」 절에 있다. 기초(C가 검사를 넣지 않은 설계 이유, RAII가 지우는 것과 못 지우는 것)는 원고를 본다.
- 공격 관점(스택 스매싱·ASLR·NX·카나리)과 Heartbleed형 over-read·UAF의 ASan 실험은 [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md)에 있다. 이 노트는 언어 의미론 쪽만 다룬다.
- 메모리 안전 언어의 대가: 경계 검사·GC·소유권 규칙. 언어별로 틀렸을 때 어떻게 틀리는지의 실측 비교는 [language 21](../21-language-choice-tradeoffs/2-summary.md).

### 4. 오버런이 크래시가 아니라 누출이 되는 이유 — Cloudbleed 모양

```text
  버퍼  [ < p > h i < / p > < ]  |  옆 메모리: [ user_002 cookie=FAKE-SESSION ... ]
                               pe
  스캐너: '<' 를 만나면 p를 한 칸 더 민다 → 끝 바로 앞 '<' 에서 p 가 pe 에 닿고, ++p 로 pe+1
  끝 검사:  if (++p == pe)  → pe+1 ≠ pe → 끝을 못 알아채고 계속 읽는다
            if (++p >= pe)  → 잡힌다(보고서의 수정. 단 C 표준상 pe+1을 만드는 것부터 UB)
            if (p < pe) ++p → 증가 전에 확인 — 표준상으로도 안전한 형태
```

- Cloudflare 보고서(2017-02-23): 근본 원인은 "버퍼 끝 도달을 **등호 연산자**로 검사했고 포인터가 끝을 건너뛸 수 있었다", "`==` 대신 `>=`였다면 잡혔다". 생성된 코드 `if ( ++p == pe ) goto _test_eof;`가 원문에 있다.
- 같은 보고서: 버그는 Ragel 기반 옛 파서에 수년간 있었지만 NGINX 내부 버퍼 사용 방식 때문에 누출이 없었다. 새 파서 cf-html 도입이 버퍼링을 바꾸면서 누출이 시작됐다. 즉 **결함 위치와 증상 발현 조건이 따로 논다.**

### 실험 3: 등호 끝 검사 장난감 (`e20/overrun.c`, 자기 로컬 코드·합성 데이터, 읽기는 40바이트로 제한)

```text
  -O0/-O2, 한 풀 안에 두 요청:  check p == pe   read 40 bytes: "<>hi<p><.....user_002 cookie=FAKE-SESSIO"
  -O0/-O2, 따로 malloc:         check p == pe   read 40 bytes: "<>hi<p><.............1.......user_002 co"
  수정판:                        check p >= pe   read  8 bytes: "<>hi<p><"
  ASan, 따로 malloc:  ERROR: AddressSanitizer: heap-buffer-overflow ... READ of size 1
                      ... is located 1 bytes after 10-byte region      (exit 1)
  ASan, 한 풀 안:     check p == pe   read 40 bytes: "...user_002 cookie=FAKE-SESSIO"   (exit 0, 보고 없음)
```

- 일반 빌드는 오류 없이 옆 데이터를 "응답"으로 담았다. 따로 할당한 경우에도 이 glibc에서는 다음 할당이 가까이 있어 옆 요청 데이터가 섞였다(관찰, 배치 보장은 없음).
- ASan은 **할당 경계**를 넘는 순간 잡았다. 그러나 한 번에 크게 할당한 풀 안에서 넘친 경우는 같은 할당 안이라 잡지 못했다. 웹 서버처럼 메모리 풀을 쓰는 코드에서 새니타이저만 믿을 수 없는 이유다(해석).
- `>=` 한 글자로 이 빌드의 증상은 고쳐졌다. 다만 N1570 §6.5.6 ¶8상 배열 끝 바로 뒤(pe)를 넘는 포인터를 계산하는 것 자체가 UB다. 표준상 올바른 수정은 증가 **전에** `p < pe`를 확인하는 것이다.

### 5. 표준이 스스로 그은 선 — 부록 L "bounded vs critical UB"

- N1570 부록 L(선택, `__STDC_ANALYZABLE__`): UB를 둘로 나눈다.
  - *bounded UB*: 범위 밖 저장(out-of-bounds store)을 하지 않는 UB. 트랩하거나 값이 불확정할 수 있지만 남의 메모리는 안 고친다.
  - *critical UB*: 그렇지 않은 UB. 수명 밖 객체 참조, 잘못된 포인터 역참조(단항 `*`), 배열 끝 바로 뒤를 가리키는 포인터 역참조 등이 L.3 목록에 있다.
- 이 구분이 실무 질문과 같다: "이 버그가 틀린 값에서 멈추나, 남의 메모리까지 번지나."

### 6. 메모리 안전 언어로의 이동

- CISA·NSA·FBI와 호주·캐나다·영국·뉴질랜드 기관의 공동 문서 "The Case for Memory Safe Roadmaps"(2023-12): 메모리 안전 언어(MSL)는 메모리 안전 취약점을 없앨 수 있다. 근거로 Microsoft CVE의 약 70%(2006~2018), Chromium 취약점의 약 70%, 2021년 Project Zero가 분석한 제로데이의 67%가 메모리 안전 취약점이라는 업계 보고를 든다. 제조사에 단계·날짜가 있는 전환 로드맵을 공개하라고 권한다.
- 같은 문서 결론: 메모리 비안전 언어로 보고된 취약점의 3분의 2가 여전히 메모리 문제다.

## 쓰이는 자료구조·알고리즘

- **데이터 흐름 분석·값 범위 전파** — "역참조했으니 non-null", "넘침은 없으니 `x+1>x`" 같은 사실을 제어 흐름 그래프 위로 퍼뜨려 분기를 지운다. IR·최적화 일반은 [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md).
- **그림자 메모리 + 레드존** — ASan은 할당마다 앞뒤에 접근 금지 영역을 두고, 메모리 접근 전에 그림자 표를 조회한다. 그래서 범위 밖 접근은 "할당(힙·스택·전역 객체) 경계" 단위로만 안다(실험 3의 풀 사례). 해제 후 사용·이중 해제는 따로 잡는다(Clang AddressSanitizer 문서). [security/24](../../security/24-memory-safety-exploits/2-summary.md) 「쓰이는 자료구조」.
- **경계 = 포인터 + 길이** — 안전한 언어의 배열·슬라이스는 길이를 같이 들고 다니며 접근마다 범위를 확인한다(안전이 증명되면 컴파일러가 비교를 지운다 — 경계 검사 제거). C 포인터에는 길이가 없다(원고 [c-cpp-csharp.md](../../../languages/c-cpp-csharp.md) 「C」 절).

## 적용 — 풀어나가는 법

1. **증상에서 UB를 의심하는 신호**
   - `-O0`·디버그 빌드에서는 맞고 `-O2`·릴리스에서만 틀린다(실험 2).
   - 로그·printf를 넣으면 증상이 사라진다(배치·최적화가 바뀜).
   - 응답에 다른 요청·사용자의 바이트가 섞인다(실험 3).
   - 크래시 위치가 매번 다르고, 크래시 지점 코드에는 잘못이 없다.
2. **CI에서 계측 빌드로 테스트를 돈다.**

```bash
clang -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=undefined app.c -o app_san
./app_san < test_inputs        # 보고가 하나라도 나오면 CI 실패
```

   - ASan 문서: 일반적 감속은 약 2배다. 운영이 아니라 테스트·퍼징에서 켠다.
   - 새니타이저는 **실행된 경로만** 본다. 퍼징으로 경로를 늘린다.
3. **코드에서 UB를 만들지 않는다.**
   - 넘침 검사는 연산 전에: `__builtin_add_overflow`(GCC·Clang), C23 `ckd_add`.
   - 길이는 받은 값이 아니라 버퍼 크기로 자른다. 끝 검사는 `==`가 아니라, 포인터를 밀기 **전에** `p < pe`로(실험 3의 `>=`는 증상만 막는 실무 수정 — pe+1 계산이 C 표준상 UB).
   - 역참조 전에 검사한다(실험 1의 순서를 뒤집는다).
4. **컴파일 옵션으로 위험을 줄인다(대신 최적화를 일부 잃는다).**
   - `-fwrapv`: 부호 있는 덧셈·뺄셈·곱셈의 넘침을 감김으로 정의(GCC 문서의 범위). `-fno-delete-null-pointer-checks`: null 검사 유지. 커널처럼 0번 주소가 의미를 가질 수 있는 코드.
   - `-ftrapv`: 부호 있는 덧셈·뺄셈·곱셈 넘침 시 트랩(GCC 문서상 `-fwrapv`와 서로 덮어쓴다).
5. **새 코드는 메모리 안전 언어로**, 기존 C/C++은 경계를 받는 API와 계측 빌드로 감싼다(CISA 로드맵의 방향).

## 장애 시나리오와 대처

### 1. 버퍼 오버런이 크래시 대신 다른 요청의 데이터 누출 (Cloudbleed형)

- **현상**: 일부 응답에 다른 사용자의 쿠키·토큰·본문 조각이 섞인다. 서버는 오류를 내지 않는다.
- **보이는 형태**: 외부 신고나 검색엔진 캐시로 처음 알게 된다. Cloudflare 보고서: 2017-02-13~18이 영향이 가장 컸고 약 3,300,000건 중 1건(약 0.00003%)의 요청이 메모리 누출 가능성이 있었다. 2017-02-18 00:32(UTC)에 Google로부터 세부를 받았고, 01:19에 Email Obfuscation을 전 세계에서 껐다(보고서 본문은 "47분" 만의 첫 완화로 적는다).
- **원인**: 생성된 파서의 끝 검사가 `==`라 포인터가 끝을 건너뛰자 계속 읽었다. 버그는 수년간 잠복했고, 새 파서가 버퍼링을 바꾸면서 드러났다.
- **대처**: 기능 플래그로 경로를 즉시 끈다(보고서의 "global kill"). 끝 검사를 `>=`로(표준상으로는 증가 전 `p < pe` 확인), 파서를 메모리 안전 언어나 경계 검사 API로. 메모리 풀을 쓰는 코드는 ASan이 풀 안 넘침을 못 잡는다는 점을 감안해 퍼징 + 풀 경계 검사 모드를 둔다.

### 2. 길이 필드를 믿은 over-read (Heartbleed형)

- **현상**: 정상 응답 안에 프로세스 메모리(키·비밀번호)가 실려 나간다. 로그에 이상이 안 남는다.
- **보이는 형태**: NVD CVE-2014-0160(게시 2014-04-07): OpenSSL 1.0.1 ~ 1.0.1f의 TLS·DTLS가 Heartbeat 패킷을 제대로 처리하지 않아 "프로세스 메모리에서 민감한 정보를" 읽어 갈 수 있다. 개인 키 읽기가 시연됐다.
- **원인**: 요청이 주장한 길이만큼 복사하고 실제 길이와 대조하지 않았다.
- **대처**: 선언 길이와 실제 길이를 대조한다(1.0.1g의 수정). 재현·ASan 보고는 [security/24](../../security/24-memory-safety-exploits/2-summary.md) §4.

### 3. 소스에 있는 null 검사가 기계어에 없다

- **현상**: 코드 리뷰로는 null을 막는데, 운영에서 null 경로로 들어간 동작이 일어난다(커널이면 권한 상승까지).
- **보이는 형태**: `objdump -d`나 `-S` 출력에 검사 분기가 없다(실험 1). 디버그 빌드에서는 재현되지 않는다.
- **원인**: 검사 전에 역참조가 있었다. 컴파일러는 "역참조가 UB가 아니었다면 non-null"로 추론해 검사를 지운다. LWN(2009-07-20)이 설명한 TUN 드라이버 사례가 이 모양이다.
- **대처**: 검사를 역참조 앞으로 옮긴다. 0번 주소가 의미를 가질 수 있는 저수준 코드는 `-fno-delete-null-pointer-checks`. UBSan `-fsanitize=null`로 테스트.

### 4. 넘침 검사가 통과돼 음수 길이가 흘러간다

- **현상**: 큰 입력에서 할당 크기가 음수·아주 작은 값이 되고, 이후 복사가 범위를 넘는다.
- **보이는 형태**: 실험 2 `bad_guard`가 -1 대신 `-2147483559`를 냈다. `-O0`(clang)에서는 막히고 `-O2`에서 뚫리는 식으로 빌드마다 다르다.
- **원인**: `if (len + add < len)`은 넘침이 일어난 **뒤** 결과를 본다. 넘침이 UB라 컴파일러가 `add < 0`으로 바꿨다.
- **대처**: `__builtin_add_overflow`·`ckd_add`, 또는 `if (len > INT_MAX - add)`(add ≥ 0일 때 — `INT_MAX - add`는 넘치지 않는다)처럼 연산 전에 판정. 크기에는 부호 없는 `size_t`와 상한 검사.

### 5. 디버그 빌드에서는 맞고 릴리스에서만 틀린 값

- **현상**: 같은 입력에 디버그 빌드는 0, 릴리스는 1(실험 2의 clang -O0 vs -O2).
- **보이는 형태**: 버그 리포트를 디버거로 재현하려 하면 사라진다.
- **원인**: UB가 있는 프로그램에 대해 컴파일러가 최적화 수준마다 다른 가정을 썼다. 어느 쪽도 "틀린 컴파일"이 아니다.
- **대처**: UBSan으로 UB 위치를 찾는다. "릴리스만 이상하다"면 컴파일러 버그보다 UB를 먼저 의심한다.

## 핵심 문장

- 미정의 동작은 표준이 아무 요구도 두지 않은 동작이라, 크래시·틀린 값·정상처럼 보이는 실행이 모두 허용된다.
- 컴파일러는 UB가 일어나지 않는다고 가정해 최적화하므로, 역참조 뒤의 null 검사나 넘친 뒤의 넘침 검사는 기계어에서 사라질 수 있다.
- 같은 UB 소스가 컴파일러·최적화 수준마다 다른 결과를 내므로, UB 프로그램에는 "맞는 출력"이 없다.
- 경계 밖 읽기가 크래시가 아니라 다른 요청의 데이터 누출이 되는 것은, 옆 메모리가 대개 다른 살아 있는 데이터이고 언어가 그 접근을 막지 않기 때문이다.
- 새니타이저는 실행된 경로만 보고 범위 밖 접근은 할당 경계 단위로 보므로, 메모리 풀 안의 넘침이나 실행 안 된 경로는 놓친다.
- 메모리 안전 언어는 이 계열을 언어 층에서 없애고, 대가로 경계 검사·GC·소유권 규칙의 비용을 낸다.

## 관련 주제·근거

- 선행
  - [09-memory-management-models](../09-memory-management-models/2-summary.md) — 수동·참조 카운팅·GC·소유권(원고 [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md))
  - 원고 [languages/c-cpp-csharp.md](../../../languages/c-cpp-csharp.md) — C가 검사를 넣지 않은 설계(C99 Rationale "Keep the spirit of C"), C의 실패 계급, RAII의 한계, Chromium·Android 통계
- 후속·연결
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md) — 공격 관점, 완화책(카나리·ASLR·NX), Heartbleed형 실험
  - [21-language-choice-tradeoffs](../21-language-choice-tradeoffs/2-summary.md), [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md), [27-pl-incidents](../27-pl-incidents/2-summary.md)
  - [os/11-heap-allocation](../../os/11-heap-allocation/2-summary.md) — 할당기 배치(옆 메모리가 무엇인가) · [os/09-address-space](../../os/09-address-space/2-summary.md)
  - [languages/c/syntax/15-pointer-arithmetic-and-indexing](../../../languages/c/syntax/15-pointer-arithmetic-and-indexing/2-summary.md) · [languages/c/syntax/19-void-pointer-null-pointer-and-null](../../../languages/c/syntax/19-void-pointer-null-pointer-and-null/2-summary.md) · [languages/rust/언어-특성](../../../languages/rust/언어-특성/README.md)
- 표준·문서
  - ISO/IEC 9899 위원회 초안 N1570(C11) — §3.4.1·3.4.3·3.4.4, §6.5 ¶5, §6.5.3.2 ¶4·각주 102, 부록 J.2, 부록 L <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf> · C23 초안 N3220 J.2 (46) <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf>
  - GCC 13.3 — Optimize Options `-fdelete-null-pointer-checks`, Code Gen Options `-fwrapv`·`-ftrapv`, Integer Overflow Builtins <https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html>
  - Clang 문서 — UndefinedBehaviorSanitizer, AddressSanitizer("Typical slowdown … is 2x") <https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html>
  - Chris Lattner, "What Every C Programmer Should Know About Undefined Behavior #1/3"(LLVM Blog, 2011-05) <https://blog.llvm.org/2011/05/what-every-c-programmer-should-know.html>
  - Go 명세 "Integer overflow" <https://go.dev/ref/spec#Integer_overflow> · JLS SE21 §15.18.2
  - Linux 커널 최상위 `Makefile`(`-fno-delete-null-pointer-checks`, `-fno-strict-overflow`) <https://github.com/torvalds/linux/blob/master/Makefile>
  - Jonathan Corbet, "Fun with NULL pointers, part 1"(LWN, 2009-07-20) <https://lwn.net/Articles/342330/>
  - CISA 외, "The Case for Memory Safe Roadmaps"(2023-12) <https://www.cisa.gov/resources-tools/resources/case-memory-safe-roadmaps>(직접 접속이 거부돼 Internet Archive 사본으로 읽음)
- 사고 원문
  - Cloudflare, "Incident report on memory leak caused by Cloudflare parser bug"(2017-02-23) <https://blog.cloudflare.com/incident-report-on-memory-leak-caused-by-cloudflare-parser-bug/>
  - NVD CVE-2014-0160 <https://nvd.nist.gov/vuln/detail/CVE-2014-0160>(NVD API로 게시일·설명 확인)
- 실험(호스트 Ubuntu 24.04, gcc 13.3.0·clang 18.1.3, x86-64)
  - `e20/nullcheck.c` — `-O0`/`-O2`/`-fno-delete-null-pointer-checks`, gcc·clang `objdump -d`
  - `e20/overflow.c`·`overflow2.c` — `x+1>x` 결과 gcc/clang × -O0/-O2/-fwrapv, UBSan 보고 문구·recover 여부
  - `e20/guard.c` — 넘친 뒤 검사 vs `__builtin_add_overflow`, gcc -O2 기계어(`add < 0`), gcc 13.3에 `<stdckdint.h>` 없음
  - `e20/overrun.c` — 등호 끝 검사 장난감(합성 데이터, 40바이트 제한): 풀·분리 할당 × 일반·ASan, `>=` 수정판
