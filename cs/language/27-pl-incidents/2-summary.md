# language/27-pl-incidents — 실사건: Cloudbleed(2017, 생성된 파서 버퍼 오버런) · Heartbleed(2014, 경계 검사 누락) · left-pad(2016, 의존성 제거로 빌드 연쇄 실패) — 언어·런타임 관점 — 정리 (힌트)

## 해결하는 문제

세 사건은 모두 **언어나 생태계가 "검사하지 않기로 한 것"** 이 오래 숨어 있다가 조건이 바뀌자 드러난 경우다.

```text
  Cloudbleed 2017   생성된 C 스캐너의 끝 검사가 ==  ── 새 파서 도입으로 버퍼 경계가 바뀜 ──▶ 포인터가 끝을 건너뜀 → 남의 요청 메모리를 응답에
  Heartbleed 2014   요청이 말한 길이만큼 memcpy류 복사 ── 길이를 부풀린 하트비트 요청 ────────▶ 경계 밖 읽기(최대 64KB/회) → 프로세스 메모리 누출
  left-pad 2016     정확한 판(0.0.3)을 요구하는 사슬 ── 작가가 레지스트리에서 패키지를 내림 ───▶ 설치 실패가 의존자의 의존자까지 → 2.5시간 중단
```

쉬운 예: 택배 상자의 송장이다.\
송장에 "10kg"라고 적혀 있으면 기사는 저울에 올리지 않고 10kg로 처리한다. 실제로 1kg이면 9kg어치의 다른 짐까지 같이 실어 보낸다(Heartbleed).\
송장의 "마지막 칸" 표시가 칸 사이에 찍혀 있으면, 기사는 마지막 칸을 지나쳐 옆 집 짐까지 계속 싣는다(Cloudbleed).\
"그 가게의 그 상품 번호만 받는다"는 주문서는, 가게가 문을 닫으면 같은 물건이 다른 가게에 있어도 전부 실패한다(left-pad).

똑같은 구조다.\
C는 배열 경계를 검사하지 않는다. 경계를 넘은 읽기는 미정의 동작이라 언어가 결과를 보장하지 않는데, 이 사건들에서는 그 읽기가 **오류가 아니라 정상 응답**이 됐다.\
레지스트리는 "판 번호 → 내용"을 약속하지만, 그 판이 계속 있다는 것은 2016년 당시 약속하지 않았다.\
검사가 없는 자리는 평소에는 비용이 0이다. 조건이 바뀌는 날 한꺼번에 비용을 낸다.

실무 예:
- 백엔드에도 같은 모양이 있다. 직접 짠 바이너리 프로토콜 파서, 길이 필드를 가진 메시지 처리, 버퍼 풀을 쓰는 네트워크 코드, 레지스트리에서 바로 받는 CI 빌드다.
- Cloudbleed·Heartbleed는 **서버 로그에 이상이 남지 않았다** — 누출은 정상 응답 안에 있었다. left-pad의 설치 실패는 빌드 로그에 바로 보였지만, "내 코드·락파일은 그대로"인 채로 났다. 그래서 이 노트는 "발견 방법"과 "검사를 어디에 둘 것인가"를 함께 본다.

  - *1차 출처*: 당사자나 기관이 직접 쓴 문서 — Cloudflare 사고 보고서, NVD·OpenSSL 권고, npm 블로그. 이 노트는 날짜·수치를 원문 그대로 옮기고, 원문에 없는 연결은 "해석"이라고 표시한다.
  - *증상 → 사건*: 이 노트의 사건은 [26-pl-symptom-index](../26-pl-symptom-index/2-summary.md)의 증상(9절 누출, 11절 설치 실패)이 실제 사고가 된 모습이다.
  - *보안 관점과의 경계*: Heartbleed의 공격·대응(키 회전, 자산 목록)은 [security/30-security-incidents](../../security/30-security-incidents/2-summary.md) 사건 1이 정본이다. 이 노트는 "어떤 언어·런타임 원리가 깨졌나"만 본다. 공격 절차는 쓰지 않는다.

## 동작·원리

### 사건 1 — Cloudbleed: 생성된 파서의 등호 끝 검사 (신고 2017-02-18 · 보고서 2017-02-23)

출처
- John Graham-Cumming, "Incident report on memory leak caused by Cloudflare parser bug", Cloudflare 블로그, 2017-02-23 <https://blog.cloudflare.com/incident-report-on-memory-leak-caused-by-cloudflare-parser-bug/>(2026-10-08 열람, 본문 끝 "This post was updated to reflect updated information").
- Ragel 공식 페이지 <https://www.colm.net/open-source/ragel/>(2026-10-08 열람) — Ragel이 무엇을 생성하는지.
- "Cloudbleed"라는 이름은 보고서 본문에 없다. 보고서를 부르는 통칭으로 쓴다.

#### 사실 (원문)

| 항목 | 원문 |
|---|---|
| 신고 | Google Project Zero의 Tavis Ormandy가 "corrupted web pages being returned by some HTTP requests"를 보고 |
| 무엇이 샜나 | 엣지 서버가 "running past the end of a buffer and returning memory that contained private information such as HTTP cookies, authentication tokens, HTTP POST bodies, and other sensitive data". 일부는 검색엔진에 캐시됨 |
| 새지 않은 것 | 고객 SSL 개인 키 — SSL은 이 버그와 무관한 별도 NGINX 인스턴스가 종단 |
| 규모 | 영향이 가장 컸던 기간 2월 13~18일, "around 1 in every 3,300,000 HTTP requests"(약 0.00003%)가 누출 가능 |
| 근본 원인 | "reaching the end of a buffer was checked using the equality operator and a pointer was able to step past the end of the buffer". "Had the check been done using `>=` instead of `==` jumping over the buffer end would have been caught" |
| 생성 코드 | `if ( ++p == pe ) goto _test_eof;` — "The equality check is generated automatically by Ragel and was not part of the code that we wrote" |
| 직접 원인 | 오류 처리 블록(`$lerr`)에 `fhold`(= `p--`)가 빠짐. 버퍼 끝에서 오류가 나면 `p`가 `pe + 1`이 되고 끝 검사를 지나침 |
| 발현 조건 | 마지막 데이터 버퍼가 깨진 `script`·`img` 태그로 끝남, 버퍼가 4k 미만(넘으면 NGINX가 크래시), 옛 파서와 새 파서 cf-html이 같이 쓰이는 기능이 켜짐. 깨진 태그로 끝나는 HTML은 사이트의 약 0.06% |
| 잠복 | 버그는 Ragel 기반 옛 파서에 "for many years" 있었다. cf-html 도입이 NGINX 필터 사이 버퍼링을 바꿔(`last_buf` 값) 누출이 시작됨. 누출 가능 최초일 2016-09-22 |
| 완화 | 기능마다 있는 "global kill" 플래그로 Email Obfuscation을 세부 정보 수신 47분 뒤(01:19), Automatic HTTPS Rewrites를 그 3h05m 뒤(04:24) 끔. kill 스위치가 없던 Server-Side Excludes는 따로 만들어 배포(약 3시간). 전 세계 완료 7시간 미만, 첫 완화 47분 |
| 검색엔진 정리 | 누출 메모리를 담고 캐시된 고유 URI 770개, 고유 도메인 161개를 검색엔진과 함께 삭제 |
| 후속 | 생성 코드를 퍼징, 실제 깨진 페이지로 테스트, 모든 포인터 접근에 명시적 검사(`SAFE_CHAR` — `p < pe`가 아니면 로그를 남기고 오류 반환) |

타임라인(원문, UTC)

```text
  2016-09-22        Automatic HTTP Rewrites 켜짐 (누출 가능 최초일)
  2017-01-30        Server-Side Excludes가 새 파서로 이전
  2017-02-13        Email Obfuscation 일부가 새 파서로 이전 ← 영향이 가장 큰 기간의 시작
  2017-02-18 00:11  Tavis Ormandy가 Cloudflare 연락처를 묻는 트윗
             00:32  Google로부터 버그 세부 수신
             01:19  Email Obfuscation 전 세계에서 끔          (수신 47분 뒤)
             04:24  Automatic HTTPS Rewrites 전 세계에서 끔
             07:22  cf-html 파서 kill switch 패치 전 세계 배포
  2017-02-20 21:59  SAFE_CHAR 수정 전 세계 배포
  2017-02-21 18:03  세 기능 다시 켬
```

#### 원리 1 — 정규 언어를 DFA 코드로 생성했고, 그 코드는 C의 포인터 규칙을 따른다

```text
  Ragel 소스(.rl)  ── 정규 언어 + 전이에 붙인 C 동작 ──▶  Ragel  ──▶  생성된 C (상태마다 goto)
                                                                    st1266:
                                                                      if ( ++p == pe ) goto _test_eof1266;   ← 끝 검사 = 등호
                                                                      switch (*p) { ... }

  버퍼   [ ... < s c r i p t   t y p e = ]  [ 옆 메모리: 다른 요청의 헤더·쿠키 ... ]
                                         pe
  정상 경로:   p 가 pe−1 에서 ++p → p == pe → EOF 처리로 감
  $lerr 경로:  fhold(p--) 없이 다음 상태로 → 이미 p == pe 인 채 ++p → p == pe+1
               → ++p == pe 는 영원히 거짓 → 끝을 못 알아채고 옆 메모리를 계속 "파싱"해 응답에 씀
  >= 였다면:   p >= pe 에서 멈춤
```

- Ragel 공식 페이지: "Ragel compiles executable finite state machines from regular languages." 사용자의 정규식은 결정적 상태 기계로 컴파일되고, 동작은 전이에 붙는다. 같은 페이지의 생성 코드 예시에도 `if ( ++p == pe ) goto out0;`가 있다. 즉 **등호 끝 검사는 생성기의 관용구**이고, "포인터는 한 번에 한 칸씩만 움직인다"는 가정 위에서만 맞다.
  - *DFA 스캐너*: 정규 언어를 상태 하나만 들고 한 글자씩 읽는 기계로 바꾼 것([02-lexing-and-regular-languages](../02-lexing-and-regular-languages/2-summary.md) 3·6절). 상태 기계 자체는 메모리 안전과 무관하다. 생성된 코드가 C의 포인터로 입력을 읽는 순간 C의 규칙을 따른다.
- 사용자가 전이 동작 안에서 포인터를 직접 움직일 수 있었다(`fhold`·`fgoto`). 보고서: "Ragel itself gives the user a lot of control of the movement of those pointers." 한 칸 규칙을 깨는 길이 사용자 코드에 열려 있었다.
- C에서 배열(버퍼) 끝을 지나 역참조하는 것은 미정의 동작이다. 언어는 검사하지 않고, 이 경우 실제 동작은 "옆 메모리를 읽는다"였다([20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md) 3·4절의 공간 안전, N1570 부록 L의 critical UB).

#### 원리 2 — 결함 위치와 발현 조건이 따로 논다

- 보고서: 결함은 옛 파서에 수년간 있었다. 누출을 연 것은 결함이 없는 새 파서 cf-html이었다. 두 파서가 함께 있을 때 마지막 데이터 버퍼의 `last_buf`가 1이 되어 `eof = pe`가 설정되고, 그때만 `$lerr` 경로가 실행됐다.
- 해석: 단위 테스트가 "옛 파서 혼자"를 검증했다면 이 경로는 실행되지 않았다. 증상의 조건(버퍼 크기·순서·기능 조합)은 결함이 있는 함수 밖에 있었다. 같은 모양이 [01](../01-compile-interpret-jit/2-summary.md)·[23](../23-jit-tiered-compilation-and-warmup/2-summary.md)의 "같은 코드인데 실행 조건이 바뀌자 다르게 동작"과 [20-5](../20-undefined-behavior-and-memory-safety/2-summary.md)의 "빌드 조건에 따라 다른 UB 결과"다.
- 해석: 크래시 대신 누출이 된 것도 조건 때문이다. 보고서는 버퍼가 4k를 넘으면 NGINX가 크래시했다고 적는다. 작은 버퍼에서는 옆 메모리가 읽을 수 있는 같은 프로세스의 힙이었다.

#### 실험: 등호 끝 검사 장난감 (다른 노트의 실험)

[20](../20-undefined-behavior-and-memory-safety/2-summary.md) 실험 3(`e20/overrun.c`, 자기 로컬 코드·합성 데이터, 읽기 40바이트 제한)을 옮긴다. 새로 돌리지 않았다.

```text
  -O0/-O2, 한 풀 안에 두 요청:  check p == pe   read 40 bytes: "<>hi<p><.....user_002 cookie=FAKE-SESSIO"
  수정판:                        check p >= pe   read  8 bytes: "<>hi<p><"
  ASan, 따로 malloc:  ERROR: AddressSanitizer: heap-buffer-overflow ... READ of size 1   (exit 1)
  ASan, 한 풀 안:     check p == pe   read 40 bytes: "...user_002 cookie=FAKE-SESSIO"   (exit 0, 보고 없음)
```

- `==` → `>=` 한 글자가 이 빌드의 누출을 막았다. 다만 20이 적듯 배열 끝 바로 뒤(`pe`)를 넘는 포인터를 계산하는 것 자체가 C 표준상 UB다(N1570 §6.5.6 ¶8). 표준상 올바른 수정은 증가·역참조 **전에** `p < pe`를 확인하는 것이고, Cloudflare의 `SAFE_CHAR`도 역참조 전에 `p < pe`를 검사했다. 그리고 **메모리 풀 안의 넘침은 ASan도 못 잡았다.** NGINX처럼 풀을 쓰는 서버에서 새니타이저만 믿을 수 없는 이유다(20의 해석). Cloudflare의 후속 `SAFE_CHAR`가 풀이 아닌 **논리적 버퍼 끝(`pe`)** 을 기준으로 검사한 것과 같은 방향이다(해석).

#### 막았을 장치 (해석 — 원문 후속 조치에 기댐)

| 층 | 장치 | leaf |
|---|---|---|
| 생성 코드 | 모든 포인터 접근 전에 `p < pe` 검사(원문 `SAFE_CHAR`). `>=` 끝 검사는 원문이 든 대안이지만 끝을 넘은 포인터 계산 자체는 표준상 UB로 남는다(20 실험 3) | [20](../20-undefined-behavior-and-memory-safety/2-summary.md) 적용 |
| 생성기 사용 | 전이 동작 안의 포인터 이동(`fhold`·`fgoto`)을 오류 경로까지 같은 규칙으로 검토 | [02](../02-lexing-and-regular-languages/2-summary.md) |
| 테스트 | 생성 코드 퍼징 + 실제 깨진 HTML 말뭉치 + **기능 조합**(옛·새 파서 동시) 테스트 | [20-1](../20-undefined-behavior-and-memory-safety/2-summary.md) |
| 언어 | 파서를 경계 검사가 있는 언어·API로(넘으면 누출 대신 예외) — 아래 사건 2의 실험 참조 | [21](../21-language-choice-tradeoffs/2-summary.md) |
| 운영 | 기능마다 kill 플래그 — 원문은 이것으로 47분 만에 주 누출원을 끔. 가장 오래된 기능(Server-Side Excludes)에는 없어 따로 만들어 배포 | [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md) |

### 사건 2 — Heartbleed: 요청이 말한 길이를 믿은 복사 (CVE-2014-0160, 2014-04-07 공개)

출처
- NVD CVE-2014-0160 <https://nvd.nist.gov/vuln/detail/CVE-2014-0160>(NVD API로 2026-10-08 조회 — 게시 2014-04-07T22:55, 마지막 수정 2026-06-17)
- OpenSSL Security Advisory [07 Apr 2014] "TLS heartbeat read overrun (CVE-2014-0160)" <https://www.openssl.org/news/secadv/20140407.txt>(2026-10-08 열람)
- OpenSSL 수정 커밋 96db9023 "Add heartbeat extension bounds check."(2014-04-06) <https://github.com/openssl/openssl/commit/96db9023b881d7cd9f379b0c154650d6c108e9a3> · 1.0.1f `ssl/t1_lib.c`의 `memcpy(bp, pl, payload)`(2026-10-08 열람)
- 사건 전체(노출 기간·흔적·발견·대응)는 [security/30](../../security/30-security-incidents/2-summary.md) 사건 1이 정본이다. 아래 사실은 그 노트와 같은 원문에서 이 노트에 필요한 것만 옮겼다.

#### 사실 (원문)

| 항목 | 원문 |
|---|---|
| 결함 | OpenSSL 권고: "A missing bounds check in the handling of the TLS heartbeat extension can be used to reveal up to 64k of memory to a connected client or server." |
| 영향 판 | NVD: "OpenSSL 1.0.1 before 1.0.1g". 권고: "Only 1.0.1 and 1.0.2-beta releases of OpenSSL are affected including 1.0.1f and 1.0.2-beta1." |
| 무엇이 샜나 | NVD: Heartbeat Extension 패킷을 제대로 처리하지 않아 "obtain sensitive information from process memory via crafted packets that trigger a buffer over-read, as demonstrated by reading private keys" |
| 위치 | NVD: "related to d1_both.c and t1_lib.c" |
| 분류 | NVD 약점 CWE-125(Out-of-bounds Read), CVSS 3.1 7.5(`AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`), CISA KEV 등재 2022-05-04 |
| 수정 | 권고: 1.0.1g로 올리거나, 바로 못 올리면 `-DOPENSSL_NO_HEARTBEATS`로 재컴파일 |

#### 원리 — 길이 필드는 입력이고, C의 복사는 길이를 검사하지 않는다

```text
  하트비트 요청:  [선언 길이 N] [실제 payload k 바이트]       (N > k 이면 거짓말)
  응답 만들기:    payload 시작에서 N 바이트를 복사해 되돌려 줌
                  └ C: memcpy(dst, src, N) — src에 N 바이트가 있는지 언어도 함수도 모른다
  결과:           payload 뒤 (N − k) 바이트의 프로세스 메모리가 정상 응답에 실림
  수정(1.0.1g):   1 + 2 + N + 16(유형·길이·최소 패딩) 이 실제 레코드 길이를 넘으면 조용히 버린다 — 선언 길이 ≤ 실제 길이 대조
```

- 언어 관점의 핵심: C에는 "배열"과 "그 길이"를 함께 들고 다니는 타입이 없다. 포인터와 정수 길이가 따로 다니므로, 둘이 맞는지는 **프로그래머가 매번 대조해야 하는 불변식**이다. 대조를 빠뜨리면 언어는 그 위반을 오류로 만들지 않는다([20](../20-undefined-behavior-and-memory-safety/2-summary.md) 3절의 공간 안전).
  - *경계 검사(bounds check)*: 인덱스·길이가 배열의 실제 범위 안인지 접근마다 확인하는 것. Java·Go·Rust(safe)·Python은 언어·런타임이 넣는다(안전이 증명되면 컴파일러가 비교를 지운다 — 경계 검사 제거, [20](../20-undefined-behavior-and-memory-safety/2-summary.md)). C·C++의 원시 배열과 포인터는 넣지 않는다.
- 해석: 이 결함이 "크래시 없이, 로그 없이" 지나간 것은 경계 밖 읽기가 이 빌드·이 메모리 배치에서 정상 연산처럼 실행됐기 때문이다(C에서는 UB라 크래시 등 다른 결과도 언어가 배제하지 않는다). 같은 실수가 경계 검사 언어에서는 **예외**로 바뀐다. 다만 아래 실험처럼, 경계 검사는 **배열 단위**라 큰 버퍼 하나를 여러 요청이 나눠 쓰면 다시 새어 나간다.

#### 실험: 같은 "선언 길이 에코"를 Java로 (`echo/Echo.java`)

선언 길이 40, 실제 payload 5바이트(`ping!`). 요청 2의 합성 데이터 `user_002 cookie=FAKE-SESSION-0002`가 같은 풀의 8번 칸부터 들어 있다. 자기 로컬 코드이며 네트워크를 쓰지 않는다.

```java
static byte[] echoOwnArray(byte[] payload, int claimed) {          // (a) 요청마다 자기 배열
    byte[] out = new byte[claimed];
    System.arraycopy(payload, 0, out, 0, claimed);                 // JVM이 배열 경계를 검사
    return out;
}
static byte[] echoFromPool(int off, int len, int claimed) {         // (b) 공유 풀의 [off, off+len) 구간
    return Arrays.copyOfRange(POOL, off, off + claimed);            // 검사는 POOL 전체 경계뿐
}
static byte[] echoChecked(int off, int len, int claimed) {          // (c) 선언 길이를 실제 길이와 대조
    if (claimed > len) throw new IllegalArgumentException("claimed " + claimed + " > actual " + len);
    return Arrays.copyOfRange(POOL, off, off + claimed);
}
```

(실험, `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`, 2회 + 사실 점검 재실행 2회 모두 같은 출력, 2026-10-08)

```text
(a) own array : java.lang.ArrayIndexOutOfBoundsException: arraycopy: last source index 40 out of bounds for byte[5]
(b) pool      : "ping!...user_002 cookie=FAKE-SESSION-000"
(c) checked   : java.lang.IllegalArgumentException: claimed 40 > actual 5
(c) honest    : "ping!"
```

- 관찰 1 — (a) 요청마다 배열을 따로 쓰면, Java는 같은 실수를 **누출이 아니라 예외**로 바꿨다. 실패가 드러나고 옆 데이터는 나가지 않는다.
- 관찰 2 — (b) 풀(큰 `byte[]` 하나)을 나눠 쓰면 Java에서도 옆 요청의 데이터가 응답에 실렸다. 경계 검사는 "그 배열 안인가"만 보고, "그 요청의 구간 안인가"는 모른다. 20 실험 3의 "ASan이 풀 안 넘침을 못 잡음"과 같은 구조다.
- 관찰 3 — (c) 선언 길이를 실제 길이와 대조하는 한 줄이 언어와 무관한 수정이다. Heartbleed의 1.0.1g 수정과 같은 방향이다.
- 해석: 메모리 안전 언어는 **공간 안전의 기본값**을 바꾼다(기본이 예외). 그러나 프로그램이 스스로 만든 하위 구간(풀·슬랩·`ByteBuffer.slice` 없이 offset으로 나눈 버퍼)의 경계는 여전히 프로그래머 몫이다.

#### 막았을 장치 (해석)

| 층 | 장치 | leaf |
|---|---|---|
| 코드 | 신뢰 못 할 길이 필드는 실제 길이와 대조한 뒤 사용 | [20-2](../20-undefined-behavior-and-memory-safety/2-summary.md) |
| 언어·API | 길이를 함께 가진 타입(Java 배열·`ByteBuffer`의 `limit`, Rust 슬라이스)으로 복사 — 하위 구간도 `slice`처럼 경계를 가진 뷰로 | [21-4](../21-language-choice-tradeoffs/2-summary.md) |
| 테스트 | 퍼징 + AddressSanitizer 빌드(풀 안 넘침은 별도 검사 모드) | [security/24](../../security/24-memory-safety-exploits/2-summary.md) |
| 보안 대응 | 새었다고 보고 키 회전, 판 자산 목록 | [security/30](../../security/30-security-incidents/2-summary.md) 사건 1 |

### 사건 3 — left-pad: 레지스트리에서 사라진 정확한 판 (2016-03-22)

출처
- npm Blog, "kik, left-pad, and npm", 2016-03-23 <https://blog.npmjs.org/post/141577284765/kik-left-pad-and-npm>(2026-10-08 열람 — 현재 "npm Blog (Archive)" 페이지, 서명 `@izs`, "March 23rd, 2016 6:21pm").
- npm Docs, "npm Unpublish Policy" <https://docs.npmjs.com/policies/unpublish>(2026-10-08 열람) — 현재 정책.

#### 사실 (원문)

| 항목 | 원문 |
|---|---|
| 배경 | 작가와 Kik이 패키지 이름 `kik`을 두고 합의하지 못했다. npm은 이름 분쟁 정책에 따라 이름을 Kik 쪽에 두기로 하고 양쪽에 알렸다 |
| 사건 | 작가가 의존 프로젝트 개발자에게 경고 없이 `kik`과 "272 other packages"를 unpublish했다. 그중 하나가 `left-pad` |
| 영향 | "This impacted many thousands of projects." 태평양 시 3월 22일(화) 오후 2:30 직후부터 "hundreds of failures per minute" — 의존 프로젝트와 그 의존자들, 그 의존자들이 사라진 패키지를 요청하며 실패 |
| 첫 대응 | 10분 안에 다른 사용자가 기능이 같은 `left-pad`를 1.0.0으로 공개(버려진 이름은 같은 판 번호만 아니면 누구나 쓸 수 있었음) |
| 그래도 실패 | "a number of dependency chains, including babel and atom, were bringing it in via line-numbers, which explicitly requested 0.0.3" |
| 복구 | npm이 백업에서 원래 0.0.3을 다시 공개(평소에는 재공개 불가라 "unprecedented"). 4:05 PM 계획 발표, 4:55 PM 완료 |
| 중단 시간 | "The duration of the disruption was 2.5 hours." |
| npm의 평가 | "Unrestricted un-publishing caused a lot of pain." 다른 패키지를 깨뜨리는 unpublish를 어렵게 하겠다고 적음 |
| 현재 정책 | 공개 72시간 안에는 레지스트리의 다른 패키지가 의존하지 않으면 unpublish 가능. 72시간이 지나면 의존자 없음 + 지난주 다운로드 300 미만 + 소유자 1명일 때만. 한 번 쓴 `패키지@판`은 unpublish해도 다시 쓸 수 없다 |

#### 원리 — 의존 그래프의 역방향 도달, 그리고 판 번호는 이름일 뿐이다

```text
  정방향(설치):      app ──▶ babel ──▶ line-numbers ──"0.0.3"──▶ left-pad
  역방향(영향 범위):  left-pad 가 사라지면, left-pad 에 "도달하는" 노드가 (사본이 없으면) 설치 실패
                     = 역방향 간선으로 BFS 했을 때 닿는 집합 (의존자의 의존자의 …)

  요구 방식별로 "다른 판"이 구해 주나:
    "0.0.3" (정확)     → 1.0.0 공개로 안 풀림 → 공용 레지스트리만 쓰면 0.0.3 자체가 돌아와야 풀림   ← 원문의 babel·atom 사슬
    ">=0.0.3" (범위)   → 1.0.0 공개로 풀림
    락파일 + 해시       → 판·내용을 고정하지만, 레지스트리에 그 판이 없으면 여전히 실패
    사내 미러·벤더링     → 원천이 사라져도 받아 둔 사본으로 설치
```

- 언어·생태계 관점의 핵심: 패키지 관리자는 이름과 판 번호로 **내용을 찾는 함수**다([19-modules-and-dependency-resolution](../19-modules-and-dependency-resolution/2-summary.md)). 해석기·락파일은 "어느 판"을 정할 뿐, 그 판의 내용이 레지스트리에 **계속 있는가**는 레지스트리의 정책에 달려 있었다. 2016년 당시에는 작가가 그것을 언제든 지울 수 있었다.
- 범위 요구는 대체 판으로 풀린다. 정확한 판 요구는, 기존 제약을 그대로 두고 공용 레지스트리만 쓰는 한 원래 판이 돌아와야만 풀린다(사용자 쪽에서는 미러 사본이나 `overrides`로 제약을 바꿔 피할 수 있다 — 장애 3). 원문의 "1.0.0을 공개했는데도 오류가 계속됐다"가 이 차이다.
- 해석: 크기가 작은 패키지일수록 깊은 사슬의 아래쪽에 들어가기 쉽다. 그 노드의 역방향 도달 집합(영향 범위)은 패키지 크기와 무관하게 커질 수 있다.

#### 실험: left-pad 모형 — 판이 사라지면 어디까지 실패하나 (`leftpad/model.py`)

합성 의존 그래프에서 `pad`(left-pad 역할)를 지우고, 대체 판 공개·원래 판 복구·사내 미러의 효과를 본다. 그래프는 원문의 모양(정확한 판을 요구하는 중간 패키지 `numbers`)만 따랐고, 노드 이름과 수는 합성이다.

```python
deps = {
    'pad':      [],
    'numbers':  [('pad', '0.0.3')],     # 정확한 판 요구 (원문: line-numbers가 0.0.3을 명시)
    'fmt_lib':  [('pad', '>=0.0.3')],   # 범위 요구
    'compiler': [('numbers', '1.0.0')], 'editor': [('numbers', '1.0.0')],
    'app_001':  [('compiler', '1.0.0')],
    'app_002':  [('editor', '1.0.0'), ('fmt_lib', '1.0.0')],
    'app_003':  [('fmt_lib', '1.0.0')],
}
# install(app): BFS로 전이 의존을 풀다가, 요구를 만족하는 판이 레지스트리(+미러)에 없으면 FAIL
```

(실험, 호스트 Python 3.12.3 표준 라이브러리, 2회 + 사실 점검 재실행 2회 모두 같은 출력, 2026-10-08)

```text
t0 정상                        app_001:ok   app_002:ok   app_003:ok
t1 pad 전 판 삭제              app_001:FAIL (numbers -> pad@0.0.3)  app_002:FAIL (fmt_lib -> pad@>=0.0.3)  app_003:FAIL (fmt_lib -> pad@>=0.0.3)
t2 다른 사람이 pad 1.0.0 공개   app_001:FAIL (numbers -> pad@0.0.3)  app_002:FAIL (numbers -> pad@0.0.3)   app_003:ok
t3 레지스트리가 0.0.3 복구      app_001:ok   app_002:ok   app_003:ok
t1 + 사내 미러(삭제 전 사본)     app_001:ok   app_002:ok   app_003:ok
```

- 관찰 1 — `pad`를 직접 쓰지 않는 앱 셋이 모두 실패했다. 실패는 의존 그래프의 역방향 도달 집합 전체로 번졌다.
- 관찰 2 — 대체 판 1.0.0 공개 뒤에는 범위 요구만 있는 `app_003`만 살아났다. 정확한 판을 요구하는 사슬(`numbers`)을 거치는 앱은 계속 실패했다. 원문의 "1.0.0 공개 뒤에도 babel·atom 사슬 오류"와 같은 모양이다(모형 — 원문 규모·시간을 재현한 것은 아니다).
- 관찰 3 — 삭제 전에 받아 둔 사본(사내 미러)이 있으면 같은 시점에도 모두 설치됐다. 레지스트리를 고칠 수 없는 사용자 쪽에서 가능한 대처다.

#### 막았을 장치 (해석)

| 층 | 장치 | leaf |
|---|---|---|
| 레지스트리 | 의존자가 있는 판의 unpublish 제한(현재 npm 정책), 쓴 `이름@판` 재사용 금지 | — |
| 빌드 | 락파일 + 무결성 해시로 판·내용 고정, CI는 락을 따르는 설치만 | [19-3](../19-modules-and-dependency-resolution/2-summary.md) |
| 공급 | 사내 미러·프록시 캐시·벤더링으로 원천이 사라져도 설치 | [19-4](../19-modules-and-dependency-resolution/2-summary.md) · [security/25](../../security/25-supply-chain-security/2-summary.md) |
| 설계 | 작은 기능은 직접 쓰거나 표준 라이브러리로 — 의존 그래프 노드 수를 줄임 | [data-structure/34](../../data-structure/34-dependency-resolver/2-summary.md) |

### 같은 원리의 다른 사건 — Cloudflare WAF 정규식(2019-07-02)

- 커리큘럼 27 행에는 없지만, 같은 언어 원리(백트래킹 정규식 엔진)가 전 세계 CPU 100%가 된 사건이다. Cloudflare 원문은 "27분" 장애, 문제 정규식 끝부분 `.*(?:.*=.*)`, PCRE에 폭주 방지 장치가 없었다고 적는다([02-1](../02-lexing-and-regular-languages/2-summary.md)).
- 사건의 정본은 [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md) 사건 3(알고리즘 관점)과 [engineering-practice/20-practice-incidents](../../engineering-practice/20-practice-incidents/2-summary.md)(배포 절차 관점)다. 이 노트는 되풀이하지 않는다.
- 언어 관점 한 줄(해석): 정규식은 정규 언어라 선형 시간 엔진(Thompson NFA 시뮬레이션·DFA)으로 돌릴 수 있는데, 역참조 같은 확장을 지원하는 백트래킹 엔진을 썼다. Cloudbleed가 쓴 Ragel도 같은 이론(정규 언어 → DFA) 위에 있다. 이론이 같아도 **어떤 엔진·어떤 생성 코드**인지가 장애를 갈랐다.

### 세 사건을 나란히 (해석)

| | Cloudbleed 2017 | Heartbleed 2014 | left-pad 2016 |
|---|---|---|---|
| 검사하지 않은 것 | 포인터가 끝을 **지나쳤나**(`==`만 봄) | 선언 길이 ≤ 실제 길이 | 그 판이 **아직 있나** |
| 왜 검사가 없었나 | 생성기 관용구가 "한 칸씩만 이동"을 가정, 사용자 동작이 그 가정을 깸 | C의 포인터 + 길이 분리, 대조는 프로그래머 몫 | 레지스트리가 unpublish를 제한하지 않음 |
| 숨어 있던 기간 | 옛 파서에 "for many years", 누출 가능 2016-09-22 ~ 2017-02-18 | security/30 기준 2012-03-14 릴리스 ~ 2014-04-07 공개 | 패키지가 공개된 뒤 삭제될 때까지 — 삭제 전에는 증상이 없음 |
| 드러난 조건 | 새 파서가 버퍼 경계(`last_buf`)를 바꿈 | 길이를 부풀린 요청 | 작가의 일괄 unpublish |
| 보인 형태 | 정상 응답 안의 남의 데이터, 검색엔진 캐시 | 정상 응답 안의 프로세스 메모리, 로그 흔적 없음 | 설치 실패, 내 코드는 그대로 |
| 원리 leaf | [20](../20-undefined-behavior-and-memory-safety/2-summary.md) · [02](../02-lexing-and-regular-languages/2-summary.md) | [20](../20-undefined-behavior-and-memory-safety/2-summary.md) · [21](../21-language-choice-tradeoffs/2-summary.md) | [19](../19-modules-and-dependency-resolution/2-summary.md) |
| 고친 한 줄 | `>=` 또는 접근마다 `p < pe` | 길이 대조 | 0.0.3 복구(사고), unpublish 정책(재발 방지) |

- 공통 1 — **검사 비용 0의 기본값**이 사고를 키웠다. C의 무검사 접근, 생성기의 등호 검사, 레지스트리의 무제한 삭제. 평소에는 빠르고 편했다.
- 공통 2 — 세 사건 모두 **결함 위치와 증상 위치가 달랐다**. 옛 파서 vs 새 파서 도입, 하트비트 처리 vs 응답 내용, `left-pad` vs `babel`을 쓰는 앱. 26의 「하지 말 것」(증상이 보인 자리만 고치지 말 것)이 여기서 나온다.
- 공통 3 — Cloudbleed·Heartbleed는 **크래시가 아니라 누출**로 끝났다. 메모리 안전 언어는 이것을 예외로 바꾸지만, 프로그램이 만든 하위 구간(풀)의 경계는 바꾸지 못한다(사건 2 실험 (b)).

## 쓰이는 자료구조·알고리즘

- **유한 오토마타(DFA) 생성**: Ragel은 정규 언어를 결정적 상태 기계로 컴파일하고 전이에 동작을 붙인다([02](../02-lexing-and-regular-languages/2-summary.md) 3·6절 부분집합 구성). 생성된 코드의 안전성은 생성기의 가정(포인터 한 칸 이동)과 사용자 동작이 그 가정을 지키는지에 달렸다.
- **경계 검사**: 접근마다 `0 ≤ i < length`(또는 `p < pe`). 길이를 함께 가진 타입이 이것을 언어 기본값으로 만든다([20](../20-undefined-behavior-and-memory-safety/2-summary.md)·[21](../21-language-choice-tradeoffs/2-summary.md)).
- **역방향 그래프 도달(BFS)**: 패키지 하나가 사라질 때 영향받을 수 있는 범위 = 역방향 간선으로 BFS한 도달 집합([algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)). 실제 실패는 그 부분집합이다 — 선택 의존(`optionalDependencies`)이거나 범위를 만족하는 다른 판이 있으면 도달해도 설치된다(위 실험 t2의 `app_003`). 설치 자체는 정방향 전이 폐포·위상정렬([data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md)).
- **버전 제약 만족**: 정확한 판·범위·최소 판 요구를 레지스트리의 판 집합에 대응시키는 일([19](../19-modules-and-dependency-resolution/2-summary.md) 2·3·6절).

## 적용 — 풀어나가는 법

### 1. 내 코드로 옮길 점검 목록

| 질문 | 사건 | 걸리면 | leaf |
|---|---|---|---|
| 끝 검사가 `==`인 포인터·인덱스 루프가 있나? 오류 경로에서도 포인터가 한 칸씩만 움직이나? | Cloudbleed | `>=`·`<`로, 접근마다 경계 검사 | [20-1](../20-undefined-behavior-and-memory-safety/2-summary.md) |
| 생성된 코드(파서·스캐너·직렬화)를 퍼징·리뷰 대상에 넣었나? | Cloudbleed | 생성 코드 퍼징, 기능 조합 테스트 | [02](../02-lexing-and-regular-languages/2-summary.md) |
| 외부에서 온 길이 필드로 복사·할당하기 전에 실제 길이와 대조하나? | Heartbleed | 대조 후 사용, 상한 | [20-2](../20-undefined-behavior-and-memory-safety/2-summary.md) |
| 버퍼 풀·큰 배열 하나를 요청들이 offset으로 나눠 쓰나? | 둘 다 | 경계를 가진 뷰(`ByteBuffer.slice`·슬라이스)로, 반납 시 지우기 | [12](../12-object-layout-and-allocation-reduction/2-summary.md) |
| 기능마다 즉시 끌 수 있는 플래그가 있나? 오래된 기능도? | Cloudbleed | kill 플래그 | [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md) |
| CI가 공용 레지스트리에서 바로 받나? 정확한 판 고정에 기대나? | left-pad | 락파일 + 미러·캐시·벤더링 | [19-4](../19-modules-and-dependency-resolution/2-summary.md) |
| 작은 유틸 패키지가 깊은 사슬 아래에 몇 개나 있나? | left-pad | 역방향 영향 범위 점검, 표준 라이브러리 대체 | [19](../19-modules-and-dependency-resolution/2-summary.md) |

### 2. 코드 — Java 21: 길이 필드 메시지를 안전하게 읽기

```java
import java.nio.ByteBuffer;

final class LengthPrefixed {
    static final int MAX_PAYLOAD = 16 * 1024;

    /** [2바이트 길이][payload] 레코드 하나를 읽는다. 선언 길이를 믿지 않는다. */
    static ByteBuffer readRecord(ByteBuffer record) {
        if (record.remaining() < 2) throw new IllegalArgumentException("short header");
        int declared = Short.toUnsignedInt(record.getShort());
        int actual = record.remaining();
        if (declared > actual) {                      // Heartbleed 수정과 같은 방향: 선언 ≤ 실제
            throw new IllegalArgumentException("declared " + declared + " > actual " + actual);
        }
        if (declared > MAX_PAYLOAD) throw new IllegalArgumentException("too large");
        // slice(): [position, position+declared) 경계를 가진 새 뷰 — 단 record의 limit이 이 레코드 끝으로
        //          먼저 제한돼 있어야 레코드 밖(풀의 옆 구간)을 못 읽는다. 풀 전체를 넘기면 actual도 부풀어 검사가 통과한다
        ByteBuffer payload = record.slice(record.position(), declared);
        record.position(record.position() + declared);
        return payload.asReadOnlyBuffer();
    }

    /** 스캐너 루프의 끝 검사는 "같다"가 아니라 "넘었나"로. */
    static int countTags(byte[] buf, int start, int end) {
        int tags = 0;
        for (int p = start; p < end; p++) {           // == 가 아니라 <
            if (buf[p] == '<') {
                tags++;
                p++;                                   // 한 번에 두 칸 이동해도 p < end 가 잡는다
            }
        }
        return tags;
    }
}
```

- `ByteBuffer.slice(int, int)`(JDK 13+)는 원래 버퍼의 구간을 경계가 있는 새 뷰로 만든다. 사건 2 실험 (b)의 "풀 안 offset" 대신 요청마다 그 요청 구간으로 자른 뷰를 넘기면, 뷰 밖 접근은 `IndexOutOfBoundsException`·`BufferUnderflowException`이 된다. `readRecord`의 대조(`declared > actual`)도 입력 버퍼가 이 레코드 끝까지로 제한돼 있을 때만 의미가 있다 — 풀 전체를 넘기면 `remaining()`이 옆 요청까지 세어 부풀린 선언 길이가 통과한다.
- `p < end`는 포인터가 두 칸 뛰어도 끝을 지나치지 않는다. Cloudbleed의 `++p == pe`가 놓친 경우다.

### 3. 사고 보고서를 읽는 순서 — 언어 관점

```text
  ① 무엇이 보였나      정상 응답 안의 남의 데이터 / 설치 실패 / CPU 100%
  ② 어디서 검사가 없었나  경계(공간), 길이 필드, 판의 존재, 엔진의 시간 상한
  ③ 왜 오래 숨었나      결함 위치 ≠ 발현 조건 (버퍼링 변경, 특정 요청, 삭제 시점)
  ④ 고친 한 줄         원문의 수정(>=, 길이 대조, 판 복구)과 재발 방지(정책·검사 모드)
  ⑤ 내 코드의 같은 자리  위 점검 목록
```

## 장애 시나리오와 대처

### 1. 응답에 다른 사용자의 데이터가 섞인다는 외부 신고 — Cloudbleed형

- **현상**: 보안 연구자·사용자가 "응답 끝에 알 수 없는 헤더·쿠키 조각이 붙어 온다"고 신고한다. 서버 오류율·로그는 평소와 같다.
- **보이는 형태**: 일부 응답의 본문 끝이 깨져 있고, 그 뒤에 다른 요청의 헤더 조각이 있다. 특정 기능(HTML 재작성 등)이 켜진 사이트에서만, 그리고 깨진 입력으로 끝나는 응답에서만 난다.
- **원인**: 네이티브 코드(생성된 스캐너 포함)의 끝 검사가 포인터의 건너뛰기를 놓쳐 버퍼 밖을 읽었다([20-1](../20-undefined-behavior-and-memory-safety/2-summary.md)). 최근 바뀐 것은 그 코드가 아니라 버퍼링을 바꾼 **다른** 구성 요소일 수 있다.
- **대처**: 해당 기능을 kill 플래그로 즉시 끈다(원문은 47분). 끝 검사를 `>=`·접근마다 검사로 바꾸고, 생성 코드를 퍼징한다. 캐시된 누출(검색엔진·CDN)을 찾아 지우고, 샌 비밀(내부 키)을 회전한다.

### 2. 길이 필드를 가진 프로토콜에서 메모리가 샌다 — Heartbleed형

- **현상**: 자체 바이너리 프로토콜의 에코·핑 응답에 요청보다 긴 데이터가 돌아온다.
- **보이는 형태**: 응답 길이가 요청 payload보다 길다. C 서비스는 오류 없이, Java 서비스는 풀 버퍼를 쓰는 경로에서만 같은 증상(사건 2 실험 (b)).
- **원인**: 선언 길이를 실제 길이와 대조하지 않고 복사했다. Java라도 큰 풀을 offset으로 나눠 쓰면 배열 경계 검사가 구간 경계를 대신하지 못한다.
- **대처**: 선언 ≤ 실제 대조, 상한. 하위 구간은 경계를 가진 뷰(`slice`)로 넘긴다. 공격 관점의 대응(키 회전·자산 목록)은 [security/30](../../security/30-security-incidents/2-summary.md) 사건 1.

### 3. 코드 변경 없이 모든 빌드가 설치 단계에서 실패 — left-pad형

- **현상**: 아침부터 모든 CI가 `npm install`(또는 다른 패키지 관리자)에서 실패한다. 로컬도 캐시를 지우면 실패한다.
- **보이는 형태**: 설치 로그의 "패키지·판을 찾을 수 없음". 실패한 패키지는 우리가 직접 쓰지 않는 깊은 전이 의존이다.
- **원인**: 그 판이 레지스트리에서 사라졌다. 락파일은 판을 고정하지만 존재를 보장하지 않는다([19-4](../19-modules-and-dependency-resolution/2-summary.md)).
- **대처**: 사내 미러·캐시에 사본이 있으면 그쪽으로 설치한다(실험 마지막 줄). 없으면 `overrides`로 대체 판을 강제하되, 정확한 판을 요구하는 사슬이 있는지 먼저 본다(실험 t2). 재발 방지는 미러·벤더링·아티팩트 보관이다.

### 4. "메모리 안전 언어니까 누출은 없다"고 가정한 버퍼 풀

- **현상**: 성능을 위해 Java 서버에 직접 만든 바이트 풀을 넣은 뒤, 드물게 응답에 남의 데이터가 섞였다는 신고.
- **보이는 형태**: 예외 로그 없음. 풀 크기보다 작은 요청에서만.
- **원인**: 경계 검사는 배열 단위다. 풀 하나를 여러 요청이 나눠 쓰면 구간 경계는 프로그래머의 대조에 달린다(사건 2 실험 (b)). 반납한 칸을 지우지 않으면 이전 요청의 데이터도 남는다(해석 — [20](../20-undefined-behavior-and-memory-safety/2-summary.md) 3절의 초기화 축).
- **대처**: 구간마다 경계를 가진 뷰를 넘긴다. 반납할 때 지운다. 풀이 정말 필요한지 측정으로 먼저 확인한다(풀링의 GC 쪽 비용은 [12-3](../12-object-layout-and-allocation-reduction/2-summary.md)).

## 핵심 문장

- Cloudbleed의 근본 원인은 생성된 C 스캐너의 등호 끝 검사(`++p == pe`)였다. 오류 경로가 포인터를 한 칸 더 밀자 끝을 지나쳤고, C는 경계 밖 읽기를 막지 않아 남의 요청 메모리가 응답에 실렸다. `>=`였다면 잡혔다(원문).
- Heartbleed는 요청이 말한 길이를 실제 길이와 대조하지 않은 over-read였다(NVD CWE-125). C에서 포인터와 길이가 따로 다니므로 대조는 프로그래머의 몫이었다.
- 경계 검사 언어는 같은 실수를 누출 대신 예외로 바꾼다. 하지만 큰 버퍼 하나를 offset으로 나눠 쓰면 배열 경계 검사가 구간 경계를 대신하지 못해 다시 샌다(실험 (b)).
- left-pad는 정확한 판(0.0.3)을 요구하는 사슬 때문에 대체 판(1.0.0) 공개로 풀리지 않았고, 원래 판 복구까지 2.5시간 중단이 이어졌다(npm 원문). 락파일은 판을 고정할 뿐 그 판의 존재를 보장하지 않는다.
- 세 사건 모두 결함 위치와 증상 위치가 달랐다. Cloudbleed·Heartbleed는 서버 로그에 이상이 남지 않았고, left-pad는 내 코드가 그대로인 채 설치가 실패했다. 증상이 보인 자리가 아니라 "검사가 없던 자리"를 찾는다.

## 관련 주제·근거

- 선행·같은 영역
  - [26-pl-symptom-index](../26-pl-symptom-index/2-summary.md) — 이 사건들의 증상(9절 누출, 11절 설치 실패, 6절 정규식 CPU)
  - [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md) — 공간 안전·UB, Cloudbleed 모양 실험(이 노트가 옮긴 실험 3), 장애 1·2
  - [02-lexing-and-regular-languages](../02-lexing-and-regular-languages/2-summary.md) — 정규 언어·DFA(Ragel의 이론), ReDoS
  - [19-modules-and-dependency-resolution](../19-modules-and-dependency-resolution/2-summary.md) — 해석·락파일·장애 4(left-pad)
  - [21-language-choice-tradeoffs](../21-language-choice-tradeoffs/2-summary.md) — "틀렸을 때 어떻게 틀리나"로 언어 고르기
  - [09-memory-management-models](../09-memory-management-models/2-summary.md) — use-after-free가 크래시 대신 남의 데이터가 되는 모양
- 다른 영역
  - [security/30-security-incidents](../../security/30-security-incidents/2-summary.md) 사건 1 — Heartbleed의 보안 관점(정본)
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md) — Heartbleed형 over-read ASan 실험, 완화책
  - [security/25-supply-chain-security](../../security/25-supply-chain-security/2-summary.md) — 락파일·해시·SBOM·미러
  - [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md) · [engineering-practice/20-practice-incidents](../../engineering-practice/20-practice-incidents/2-summary.md) — Cloudflare 2019 정규식 사건
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — kill 플래그
  - [architecture/23-arch-incidents](../../architecture/23-arch-incidents/2-summary.md) · [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md) — 다른 관점의 실사건 노트
- 근거
  - Cloudflare, "Incident report on memory leak caused by Cloudflare parser bug", 2017-02-23 <https://blog.cloudflare.com/incident-report-on-memory-leak-caused-by-cloudflare-parser-bug/>
  - Colm Networks, "Ragel State Machine Compiler" <https://www.colm.net/open-source/ragel/>
  - NVD CVE-2014-0160 <https://nvd.nist.gov/vuln/detail/CVE-2014-0160> · OpenSSL Security Advisory [07 Apr 2014] <https://www.openssl.org/news/secadv/20140407.txt> · 수정 커밋 <https://github.com/openssl/openssl/commit/96db9023b881d7cd9f379b0c154650d6c108e9a3>
  - npm Blog, "kik, left-pad, and npm", 2016-03-23 <https://blog.npmjs.org/post/141577284765/kik-left-pad-and-npm> · npm Docs "npm Unpublish Policy" <https://docs.npmjs.com/policies/unpublish>
  - Cloudflare, "Details of the Cloudflare outage on July 2, 2019" <https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/> — 수치는 [02](../02-lexing-and-regular-languages/2-summary.md)·[algorithm/43](../../algorithm/43-alg-incidents/2-summary.md)에서 옮김
  - Java SE 21 API `ByteBuffer.slice(int index, int length)` — "Since: 13", 공유 부분 구간의 새 버퍼(용량·limit = length) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/ByteBuffer.html>
  - C 표준 초안 N1570 부록 L(critical UB) — [20](../20-undefined-behavior-and-memory-safety/2-summary.md) 5절에서 옮김
- 이 노트의 실험
  - `echo/Echo.java` — 선언 길이 에코: 자기 배열(예외)·공유 풀(옆 구간 누출)·대조(거부). `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`, 2회 + 사실 점검 재실행 2회(같은 출력), 2026-10-08
  - `leftpad/model.py` — 합성 의존 그래프에서 판 삭제·대체 판·복구·미러의 설치 결과. 호스트 Python 3.12.3, 2회 + 사실 점검 재실행 2회(같은 출력), 2026-10-08
  - 적용 2의 `LengthPrefixed` — `javac -Xlint:all` 경고 없이 컴파일, 작은 테스트에서 정상 레코드 `remaining=5`, 뷰 밖 `get(5)` → `IndexOutOfBoundsException`, 선언 40 > 실제 5 거부, `countTags("<a<")` = 2(같은 컨테이너, 사실 점검 재실행도 같은 결과, 2026-10-08)
  - 옮긴 실험(새로 돌리지 않음): [20](../20-undefined-behavior-and-memory-safety/2-summary.md) 실험 3 `e20/overrun.c`
