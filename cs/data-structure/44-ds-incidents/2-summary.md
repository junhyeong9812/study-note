# data-structure/44-ds-incidents — 실사건: HashDoS(28C3, 2011) → JDK 7u6 대체 해시·JEP 180 트리화·Python 해시 랜덤화·SipHash · JDK 7 이하 HashMap 동시 resize 무한 루프 — 정리 (힌트)

## 해결하는 문제

자료구조의 "평균 O(1)"과 "스레드 안전하지 않음"은 교과서 문장으로는 가볍다.\
두 사건은 그 두 문장이 운영에서 어떤 모양으로 터지는지 보여 준다.

```text
  HashDoS 2011        웹 프레임워크가 POST 파라미터를 해시 맵에 넣는다 -> 공격자가 같은 해시의 키를 수만 개 보낸다
                      -> 삽입 1+2+...+n = O(n^2) -> 요청 하나가 CPU 한 코어를 오래 점유 (advisory: "up to several hours")
  JDK 7 HashMap 순환   여러 스레드가 동기화 없이 같은 HashMap에 put -> 두 스레드가 동시에 resize
                      -> 머리 삽입이 버킷 순서를 뒤집다 A.next = B, B.next = A -> get()이 끝나지 않음 -> CPU 100%
```

쉬운 예: 우편함 백 개짜리 아파트에서 모든 편지를 "1호" 우편함에만 넣으면, 집배원은 편지 한 통을 넣을 때마다 그 우편함 안의 편지를 다 뒤져야 한다. 나머지 99개는 비어 있다.\
첫째 사건은 공격자가 주소를 일부러 전부 "1호"로 적은 것이다.\
둘째 사건은 두 집배원이 같은 우편함 줄을 동시에 다시 꿰다가 줄 끝을 처음에 묶어 버린 것이다.

똑같은 구조다.\
해시 맵의 비용 계약은 "키가 고르게 퍼진다"는 가정과 "한 번에 한 스레드만 구조를 바꾼다"는 가정 위에 있다. 첫째 사건은 앞 가정을, 둘째 사건은 뒤 가정을 깬다([02-adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md)).

실무 예:
- 외부 입력(쿼리 파라미터·폼 필드·JSON 키·HTTP 헤더)을 그대로 해시 맵의 키로 쓰는 코드는 지금도 흔하다. 웹 서버는 요청 파싱 단계에서 이미 그렇게 한다.
- "캐시니까 조금 틀려도 괜찮다"며 `HashMap`을 공유하는 코드도 흔하다. 틀리는 것이 아니라 **멈출** 수 있다.

  - *HashDoS*: 해시가 같은 키를 대량으로 보내 해시 테이블을 사실상 연결 리스트로 만드는 서비스 거부 공격.
  - *1차 출처*: 사건 당사자·발견자·유지보수자가 직접 쓴 문서(권고문, 발표, 버그 보고, 소스, 설계 문서). 이 노트는 시각·수치·버전을 1차 출처 원문대로 옮기고, 원문에 없는 연결은 "해석"이라고 표시한다.

## 동작·원리

### 사건 1 — HashDoS: 예측 가능한 해시로 웹 서버 CPU 고갈 (2011-12-28)

출처
- oCERT-2011-003 "multiple implementations denial-of-service via hash algorithm collision" <https://ocert.org/advisories/ocert-2011-003.html>(2026-10-05 열람).
- Alexander Klink, Julian Wälde, "Effective Denial of Service attacks against web application platforms", 28C3, 2011-12-28 <https://media.ccc.de/v/28c3-4680-en-effective_dos_attacks_against_web_application_platforms>. SipHash 논문(Aumasson–Bernstein 2012) 참고문헌은 이 발표를 "Efficient …"로 적지만, 발표 페이지의 실제 제목은 "Effective …"다.
- Crosby, Wallach, "Denial of Service via Algorithmic Complexity Attacks", USENIX Security 2003 — advisory가 "practically identical"이라고 인용한 선행 연구.

#### 사실 — 무엇이 보고됐나 (advisory 원문)

- 원인: 해시 자료구조에 키/값을 저장하는 함수가 해시 알고리즘의 **예측 가능한 충돌**로 서비스 거부에 빠진다. 특히 웹 서버 애플리케이션·프레임워크에서 POST 요청 파라미터 수에 충분한 제한이 없는 것과 겹친다.
- 영향: 특수 제작한 HTTP 요청으로 "100% of CPU usage which can last up to several hours"(대상과 서버 성능에 따라). 공격자 쪽은 적은 대역폭과 시간만 쓴다.
- 28C3 발표 소개문: 단일 HTTP 요청으로 웹 애플리케이션 서버가 "99% of CPU for several minutes to hours"를 쓰게 할 수 있다.
- 보고된 언어 구현: Java, JRuby, PHP, Python, Rubinius, Ruby. Ruby 1.9.x는 해시 함수를 이미 랜덤화해 영향이 없었다.

| 날짜 (advisory 타임라인) | 사건 |
|---|---|
| 2011-09-25 | 보고 접수. 보고자가 공개일(embargo)을 12월 27일로 정함 |
| 2011-10-18 | Apache Tomcat·Geronimo·Jetty·Java·Plone·Zope·V8 유지보수자에게 연락 |
| 2011-11-01 | Ruby on Rails·Ruby·Python·PHP와 배포판에 연락 |
| 2011-12-28 | advisory 공개 (28C3 발표도 이날) |
| 2012-02-27 | Python 수정 판 정보 갱신 |

| 대상 (advisory 원문) | 영향 판 | 수정 판 |
|---|---|---|
| Java | all versions | N/A |
| Python | <= 2.6.7, <= 2.7.3, <= 3.1.4, <= 3.2.2 | >= 2.6.8, >= 2.7.3, >= 3.1.5, >= 3.2.3 (hash randomization disabled by default, use -R flag to enable it) |
| PHP | <= 5.3.8, <= 5.4.0RC3 | >= 5.3.9, >= 5.4.0RC4 |
| Ruby | <= 1.8.7-p356 | >= 1.8.7-p357, 1.9.x |
| Apache Tomcat | <= 5.5.34, <= 6.0.34, <= 7.0.22 | >= 5.5.35, >= 6.0.35, >= 7.0.23 |
| Jetty | <= 7.5.4 | >= 7.6.0.RC3 |
| V8 JavaScript Engine | all versions | N/A |

(표는 advisory 목록의 일부다. 원문에는 JRuby·Rubinius·Geronimo·Glassfish·Plone·Rack도 있다. Python 행의 "2.7.3"이 영향·수정 양쪽에 있는 것은 원문 그대로다.)

#### 원리 — 같은 칸에 n개를 넣으면 n²

```text
  체이닝 해시 테이블, 키 n개가 전부 같은 해시 h
  ┌────┐
  │ 0  │
  │ .. │
  │ h  │──▶ k1 ──▶ k2 ──▶ k3 ──▶ ... ──▶ k(i-1)      i번째 키를 넣을 때: 중복인지 보려고 앞의 i-1개와 equals 비교
  │ .. │
  └────┘
  총 비교 = 0 + 1 + 2 + ... + (n-1) = n(n-1)/2  →  O(n²)
```

- Java `String.hashCode`는 Javadoc에 공식이 정해져 있다(`s[0]*31^(n-1) + ... + s[n-1]`). 시드가 없다. `"Aa"`와 `"BB"`의 해시는 둘 다 2112다. 이 두 블록을 k번 이어 붙인 2^k개 문자열은 모두 해시가 같다(아래 실험 A 첫 줄).
- 공격 비용은 요청 하나다. 서버 비용은 n²이다. 이 비대칭이 "amplification effect"다.
  - *증폭(amplification)*: 공격자가 쓴 자원 대비 피해자가 쓰게 되는 자원의 비율.

#### 언어·런타임은 어떻게 막았나 — 두 갈래

```text
  (가) 해시를 예측 불가능하게:  비밀 시드를 섞는다      Python(3.3 기본), Ruby 1.9
                               └ 시드가 새면 끝 → 시드를 못 뽑게 키 있는 해시(SipHash)로   Python 3.4 (PEP 456)
  (나) 최악 비용을 줄인다:       긴 버킷을 균형 트리로    Java 8 HashMap (JEP 180)
  (공통) 입력 상한:              요청당 파라미터 수 제한   Tomcat maxParameterCount 등
```

| 런타임 | 조치 (1차 출처) |
|---|---|
| Java 7u6 | `HashMap`·`Hashtable`·`HashSet`·`LinkedHashMap`·`LinkedHashSet`·`WeakHashMap`·`ConcurrentHashMap`에 대체 해시 함수 도입. 기본 임계값 -1 = **꺼짐**(-1은 2147483647과 같은 뜻 — jdk7u 소스의 `ALTERNATIVE_HASHING_THRESHOLD_DEFAULT`는 `Integer.MAX_VALUE`). `jdk.map.althashing.threshold`로 켬, 권장값 512 (Oracle "Collections Framework Enhancements in Java SE 7") |
| Java 8 | JEP 180 "Handle Frequent HashMap Collisions with Balanced Trees": 버킷 항목 수가 임계를 넘으면 연결 리스트 대신 균형 트리. 최악 O(n) → O(log n). `Comparable`을 구현한 키 타입에 효과. 대체 문자열 해시(`String`의 private `hash32` 필드 포함)는 제거(JEP 원문은 "can then be removed" — jdk8u `HashMap.java`·`String.java`에 `hash32`·althashing이 없는 것을 소스로 확인). `Hashtable`·`WeakHashMap`은 트리화 대상 아님(대체 해시 이전 상태로 되돌림) |
| Python 2.6.8 / 2.7.3 / 3.1.5 / 3.2.3 | 해시 랜덤화를 넣되 기본 꺼짐, `-R`로 켬 (advisory) |
| Python 3.3 | "Changed in version 3.3: Hash randomization is enabled by default." (Python 언어 레퍼런스 `__hash__`) |
| Python 3.4 | PEP 456: `str`·`bytes` 기본 해시를 SipHash(SipHash-2-4)로(64비트 정수형이 있고 정렬 접근 제약이 없는 보통 플랫폼 기준 — 그런 형이 없는 플랫폼·SPARC 등은 FNV를 유지). 이유: 기존 수정 FNV 해시와 그 랜덤화는 공격에 견디지 못하고, 암호학적 해시만 비밀 랜덤화 키의 추출을 막는다(29C3 발표, Aumasson–Bernstein의 시드 복구 시연을 인용) |
| Python 3.11 | `str`·`bytes` 기본 해시를 SipHash-1-3(`siphash13`)으로 (What's New in Python 3.11, bpo-29410: siphash24와 비슷한 보안 성질, 긴 입력에서 조금 빠름) |
| Apache Tomcat 7 | `maxParameterCount` — 컨테이너가 자동 파싱하는 파라미터 쌍(GET+POST) 상한, 기본 10000, 넘는 것은 무시 (Tomcat 7.0 HTTP 커넥터 문서) |

- 해석: Java가 `String.hashCode`를 랜덤화하지 않은 이유를 JEP 180은 직접 쓰지 않는다. `String.hashCode`의 값이 API 명세에 공식으로 고정돼 있어 바꾸기 어려웠다는 것이 흔한 설명이다 [?] (1차 출처 미확인). JEP 180이 고른 길은 해시 대신 **버킷의 최악 비용**을 바꾸는 것이었다.
- 두 갈래의 한계가 다르다.
  - (가)는 시드가 비밀인 동안만 막는다. 재현성을 이유로 운영에서 `PYTHONHASHSEED=0`처럼 시드를 고정하면 방어가 꺼진다.
  - (나)는 키가 `Comparable`이 아니면 효과가 약하다(아래 실험 A). 그리고 O(log n)도 공짜는 아니므로 입력 상한은 여전히 필요하다.

#### 실험 A: JDK 21에서 같은 공격 키 — `String` vs 비`Comparable` (`HashDos.java`)

`"Aa"`·`"BB"` 블록 k개 조합(2^k개, 해시는 전부 하나)을 `HashMap`에 넣는다. 같은 문자열을 `hashCode`만 위임하고 `Comparable`이 아닌 래퍼로 감싸 넣은 경우, 해시가 고른 보통 키(`"k0"`, `"k1"`, …)와 비교한다.

```java
static final class Opaque {            // 같은 hashCode, Comparable 아님 → 트리는 만들지만(동률 깨기) 찾을 때 방향을 못 정한다
    final String s; Opaque(String s) { this.s = s; }
    @Override public int hashCode() { return s.hashCode(); }
    @Override public boolean equals(Object o) { return o instanceof Opaque p && p.s.equals(s); }
}
static List<String> keys(int k) {      // "Aa"/"BB" 블록 k개 → 2^k 개
    List<String> out = new ArrayList<>(List.of(""));
    for (int i = 0; i < k; i++) {
        List<String> nx = new ArrayList<>(out.size() * 2);
        for (String p : out) { nx.add(p + "Aa"); nx.add(p + "BB"); }
        out = nx;
    }
    return out;
}
// k = 11..15 마다: new HashMap<>() 에 전부 put 하는 시간(ms)을 String / Opaque / 보통 키로 잰다
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-05 — 시간은 실행마다 다르다. 첫 실행)

```text
"Aa".hashCode()=2112  "BB".hashCode()=2112  "AaBB"=2031744  "BBAa"=2031744
n= 2,048 (서로 다른 hashCode 1개)  충돌 String     13 ms | 충돌 비Comparable     257 ms | 보통 키    1 ms
n= 4,096 (서로 다른 hashCode 1개)  충돌 String     15 ms | 충돌 비Comparable     591 ms | 보통 키    1 ms
n= 8,192 (서로 다른 hashCode 1개)  충돌 String     18 ms | 충돌 비Comparable   1,053 ms | 보통 키    4 ms
n=16,384 (서로 다른 hashCode 1개)  충돌 String     32 ms | 충돌 비Comparable   6,354 ms | 보통 키    8 ms
n=32,768 (서로 다른 hashCode 1개)  충돌 String     68 ms | 충돌 비Comparable  32,101 ms | 보통 키   13 ms
```

두 번째 실행(같은 명령): 비`Comparable`은 279 · 541 · 1,068 · 6,433 · 31,737 ms, 충돌 `String`은 15 · 20 · 15 · 26 · 51 ms, 보통 키는 1 · 2 · 3 · 7 · 11 ms.

사실 점검 재실행 두 번(같은 코드·같은 명령): 비`Comparable`은 66 · 193 · 924 · 6,111 · 32,688 ms와 363 · 203 · 1,050 · 6,438 · 35,324 ms, 충돌 `String`은 n=32,768에서 46 ms·64 ms, 보통 키는 12 ms·17 ms.

- 관찰
  - n = 32,768에서 키 전부가 해시 하나로 모였다. 그래도 `String` 키는 46~68 ms(네 번)로 보통 키(11~17 ms)의 수 배에 머물렀다. 트리화(JEP 180)가 공격 키를 O(log n) 조회로 막은 모양이다.
  - 같은 해시의 비`Comparable` 키는 31.7~35.3초(네 번)였다. 보통 키의 2천 배가 넘는다. 큰 n(8,192→16,384→32,768)에서 n이 두 배일 때 시간은 네 번 모두 약 5~6.6배였다. 작은 n(2,048~8,192)의 비율은 실행마다 크게 달랐다(집필 두 번은 약 2배씩, 점검 두 번은 2.9~4.8배와 0.6~5.2배 — 2,048이 4,096보다 느린 실행도 있었다). 첫 측정의 JIT 워밍업이 섞인 것으로 보이므로(해석) 작은 n의 비율은 쓰지 않는다. 삽입 하나가 버킷 전체를 훑는 O(n)이면 전체는 O(n²), 즉 두 배에 4배가 예상된다. 큰 n에서 4배를 넘은 것은 캐시 미스 등 상수의 영향으로 보인다(해석 — 따로 재지 않았다).
  - 같은 모양을 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) 실험(삽입 + 조회, n=8,192→16,384에서 약 6배)도 보였다. 코드가 달라 절대값은 다르다.
- 해석: 2011년의 Java(JDK 7 이하, 대체 해시 꺼짐)는 버킷이 연결 리스트라 `String` 키도 비`Comparable` 열과 같은 O(n²) 쪽이었다. JDK 7 이미지가 없어 직접 재현하지 않았다. 대신 jdk7u `HashMap.java`의 `put`이 버킷 리스트를 처음부터 `equals`로 훑는 구조임을 소스로 확인했다.

#### 실험 B: Python 3.12의 해시 랜덤화 (`pyhash.sh`)

```bash
for i in 1 2 3; do python3 -c 'import sys; print(sys.version.split()[0], "hash(\"Aa\")=", hash("Aa"), sys.hash_info.algorithm)'; done
for i in 1 2; do PYTHONHASHSEED=0 python3 -c 'print("PYTHONHASHSEED=0 hash(\"Aa\")=", hash("Aa"))'; done
```

(실험, python:3.12-slim = CPython 3.12.14, docker `--network none --cpus=1`, 2026-10-05)

```text
3.12.14 hash("Aa")= 5457046695198189700 siphash13
3.12.14 hash("Aa")= 2645493569435583083 siphash13
3.12.14 hash("Aa")= 6210981154125699700 siphash13
PYTHONHASHSEED=0 hash("Aa")= -3747738680037904767
PYTHONHASHSEED=0 hash("Aa")= -3747738680037904767
```

- 관찰: 같은 문자열의 해시가 프로세스마다 달랐다. 공격자는 서버 프로세스의 해시를 미리 계산할 수 없다. `PYTHONHASHSEED=0`이면 두 번 다 같은 값이다. 이 상태로 운영하면 (가) 방어가 꺼진다.
- 관찰: 3.12.14의 `sys.hash_info.algorithm`은 `siphash13`이었다. PEP 456은 SipHash-2-4(`siphash24`)를 도입했다. 1-3 변형이 기본이 된 것은 Python 3.11부터다(What's New in Python 3.11, bpo-29410).

### 사건 2 — JDK 7 이하 `HashMap` 동시 resize 무한 루프

출처
- JDK-6423457 "(coll) High cpu usage in HashMap.get()", 2006-05-09 등록, 영향 판 1.4.2_09, 2006-05-11 "Not an Issue"로 종료 <https://bugs.openjdk.org/browse/JDK-6423457>(2026-10-05 열람).
- jdk7u `HashMap.java` — `transfer()` 598~614행, 클래스 Javadoc "Note that this implementation is not synchronized." <https://github.com/openjdk/jdk7u/blob/master/jdk/src/share/classes/java/util/HashMap.java>
- Paul Tyma, "A Beautiful Race Condition", 2009-06-09 <https://mailinator.blogspot.com/2009/06/beautiful-race-condition.html> — resize 루프를 그림으로 풀어 쓴 글.
- OpenJDK 21 `HashMap.java` `resize()` — "preserve order" 주석과 `loHead`/`hiHead` 분할 <https://github.com/openjdk/jdk21u/blob/master/src/java.base/share/classes/java/util/HashMap.java>

#### 사실 — 버그 보고의 모양

- 보고 내용(JDK-6423457): WS6.0(원문 표기) + JDK 1.4.2_09. 시작할 때 동기화된 코드에서 `HashMap`에 200개를 넣고, 이후 여러 스레드가 높은 빈도로 **동기화 없이** 접근했다. 몇 주 뒤 CPU를 다 쓰는 스레드들이 `HashMap.get()` 안에 있었다.
- 처리: "Not an Issue". 버그의 평가(EVALUATION) 기록: 코어 파일을 HSDB로 열어 보니 `HashMap.get` 프레임의 `HashMap$Entry`가 순환이었다. Doug Lea의 평가 인용 "This is a classic symptom of an incorrectly synchronized use of HashMap … it's not a JDK or JVM bug." 즉 JDK 결함이 아니라 사용법 결함으로 판정됐다(`HashMap` Javadoc: 여러 스레드가 구조를 바꾸면 외부 동기화가 필요하다). 평가 기록은 bugs.sun.com의 Internet Archive 사본(2013년 수집)으로 읽었다 — 2026-10-05에는 bugs.openjdk.org가 오류 페이지를 돌려줬다.
- 해석: "읽기만 했는데 멈췄다"는 보고가 흔한 이유는, 순환을 **만든** 쓰기(동시 resize)와 순환에 **갇힌** 읽기(`get`)가 다른 시점·다른 스레드이기 때문이다.

#### 원리 — 머리 삽입이 순서를 뒤집는다

jdk7u `transfer()`의 핵심(598~614행 발췌):

```java
while(null != e) {
    Entry<K,V> next = e.next;               // ① 다음을 기억
    ...
    int i = indexFor(e.hash, newCapacity);
    e.next = (Entry<K,V>)newTable[i];       // ② 새 버킷의 머리에 붙인다 (머리 삽입)
    newTable[i] = e;
    e = next;                               // ③ 기억한 다음으로
}
```

```text
  옛 표 버킷:      A -> B -> null
  한 스레드가 다 옮기면 (머리 삽입 → 순서 뒤집힘):   새 버킷: B -> A -> null

  두 스레드가 겹치면
  T1: ① e=A, next=B 를 읽고 선점됨
  T2: 끝까지 옮김.  공유 객체가 B.next = A, A.next = null 이 됨
  T1 재개: A 를 자기 새 버킷 머리에          A -> null
           e = B (기억해 둔 next), next = B.next = A  ← T2 가 바꿔 놓은 값
           B 를 머리에                       B -> A -> null
           e = A, next = A.next = null
           A 를 머리에: A.next = B          A -> B -> A -> B -> ...   ← 순환
```

- 엔트리 객체는 두 스레드가 **공유**한다. 새 표는 스레드마다 따로 만들어도 `next` 포인터는 같은 객체의 필드다.
- 순환이 생긴 버킷에서 없는 키를 찾는 `get()`은 `null`을 만나지 못한다. 덤프마다 같은 `get` 루프에 머무는 `RUNNABLE` 스레드로 보인다.

#### 실험 C: 두 스레드의 겹침을 단계별로 재연 (`Jdk7Transfer.java`, 시뮬레이션)

실제 경쟁은 타이밍에 달려 재현이 어렵다. 그리고 이 환경에는 JDK 7 이미지가 없다(이미지 받기 금지). 그래서 위 `transfer()`의 머리 삽입을 그대로 옮기고, 두 "스레드"의 실행 순서를 한 스레드 안에서 **정해 놓고** 재연했다. 실제 스레드·실제 JDK 7이 아니다.

```java
// 옛 표 2칸, 버킷 1 에 A(hash 3) -> B(hash 7). 새 표 4칸에서 둘 다 3번 칸.
Entry t1e = old[1], t1next = t1e.next;                  // 스레드1: e=A, next=B 읽고 멈춤
for (Entry e = old[1]; e != null; ) {                    // 스레드2: 끝까지 transfer
    Entry nx = e.next; int i = indexFor(e.hash, 4);
    e.next = t2tab[i]; t2tab[i] = e; e = nx; }
Entry e = t1e, nx = t1next;                               // 스레드1 재개 (기억한 값으로)
while (e != null && steps < 10) {
    int i = indexFor(e.hash, 4);
    e.next = t1tab[i]; t1tab[i] = e;
    e = nx; nx = (e == null) ? null : e.next;
}
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-05 — 결정적, 실행마다 같다)

```text
옛 표 버킷1: A -> B -> null
스레드1: e=A, next=B 를 읽고 선점됨
스레드2 완료: 새 표 버킷3: B -> A -> null
  스레드1 단계1: A 를 머리에, 버킷3 = A -> null
  스레드1 단계2: B 를 머리에, 버킷3 = B -> A -> null
  스레드1 단계3: A 를 머리에, 버킷3 = A -> B -> A -> B -> A -> B -> ... (6칸 넘게 계속)
A.next=B, B.next=A
없는 키 조회: 100만 칸 상한에서 멈춤 = true
```

- 관찰: 세 단계 만에 `A.next = B`, `B.next = A`가 됐다. 상한(100만 칸)을 두지 않은 순회라면 끝나지 않는다.
- 이것은 "이런 순서가 가능하다"를 보인 것이다. 실제 운영에서 이 순서가 얼마나 자주 나는지는 보이지 않는다.

#### JDK 8 이후 — 순서는 보존, 그래도 스레드 안전하지 않다

- OpenJDK 21 `resize()`는 버킷을 `lo`/`hi` 두 리스트로 나누며 "preserve order" 주석대로 원래 순서를 지킨다(꼬리에 붙임). 위의 "뒤집힘 → 순환" 경로는 없어졌다.
- 그래도 `HashMap` Javadoc은 여전히 "not synchronized"다. [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) 3절 실험(OpenJDK 21.0.12, 스레드 4개가 서로 다른 키 10만 개씩)에서 `HashMap`은 집필 16번 중 14번 `size()`가 기대보다 작았고(그 leaf의 전체 범위 15만~34만, 기대 40만 — 키마다 다시 센 점검에서도 키가 실제로 사라졌다) 2번은 10초 안에 끝나지 않았다(점검 8번 중 1번도 멈춤). 멈춘 스레드는 `HashMap$TreeNode.root`·`putTreeVal`, 또는 `balanceInsertion` ← `treeify` ← `split`에 있었다.
- 해석: JDK 8의 변경은 "한 가지 순환 경로"를 없앴을 뿐이다. 공유 `HashMap`의 결함 부류(유실·손상·멈춤)는 남았다.

### 두 사건을 나란히 (해석)

| | HashDoS 2011 | JDK 7 HashMap 순환 |
|---|---|---|
| 깨진 가정 | 키가 고르게 퍼진다 | 한 번에 한 스레드만 구조를 바꾼다 |
| 누가 깨나 | 외부 공격자(입력) | 내부 코드(공유) |
| 보이는 것 | 특정 요청만 CPU 100%, 덤프가 진행 중 | 특정 스레드가 CPU 100%, 덤프가 같은 줄 |
| 예외 | 없음 | 없음 |
| 판정 | 여러 구현의 취약점, CVE 부여(advisory의 CVE 목록에 Java·Python 행은 없음) | "Not an Issue" — 사용법 결함 |
| 처방 | 입력 상한 + 키 있는 해시 또는 트리 버킷 | `ConcurrentHashMap` 등 동시 컬렉션 |

- 둘 다 **예외 없이 CPU만 쓴다**. 그래서 [43-ds-symptom-index](../43-ds-symptom-index/2-summary.md) 2절은 "덤프 여러 장에서 프레임이 진행하나, 멈췄나"를 첫 질문으로 둔다.
- 둘 다 평소에는 보이지 않는다. HashDoS는 공격 입력이 올 때, 순환은 드문 타이밍이 겹칠 때만 터진다. 정상 부하 테스트로는 잡히지 않는다.

## 쓰이는 자료구조·알고리즘

- **체이닝 해시 테이블**: 버킷 = 연결 리스트. 최악(모든 키가 한 버킷) 삽입 O(n) → n개 O(n²) — [05-hashmap](../05-hashmap/2-summary.md).
- **레드-블랙 트리(트리 버킷)**: JDK 8 `HashMap.TreeNode`. 키 순서는 해시 → `compareTo` → 동률 깨기. 비`Comparable`이면 양쪽을 뒤짐 — [16-red-black-tree](../16-red-black-tree/2-summary.md).
- **개방 주소 해시(CPython `dict`)**: 충돌하면 다른 칸을 탐사한다. 같은 해시의 키가 몰리면 탐사가 길어져 같은 n² 공격 면이 있다. Python 문서는 해시 랜덤화가 dict 삽입 최악 O(n²)을 노린 입력을 막기 위한 것이라고 적는다 — [29-open-addressing](../29-open-addressing/2-summary.md).
- **키 있는 해시(SipHash)**: 128비트 비밀 키를 섞는 짧은 입력용 PRF. 키를 모르면 충돌 키를 미리 계산하기 어렵다 — [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).
- **연결 리스트 머리 삽입**: O(1)이지만 순서를 뒤집는다. 동시 수정과 만나면 순환 — [02-linked-list](../02-linked-list/2-summary.md) 장애 2.
- **쓰이는 곳(🔧)**: 웹 서버의 파라미터·헤더 파싱, JSON 파서의 객체 맵, 언어 런타임의 기본 맵(`dict`·`Hash`·`HashMap`), 로컬 캐시.

## 적용 — 풀어나가는 법

### 1. 내 시스템으로 옮길 점검 목록

| 점검 질문 | 사건 근거 | 처방 | leaf |
|---|---|---|---|
| 외부 입력이 해시 맵의 **키**가 되는 곳은? 요청당 키 수에 상한이 있나? | HashDoS (advisory: 파라미터 수 제한 부족) | 서버·파서의 개수 상한(Tomcat `maxParameterCount` 기본 10000 등), 본문 크기 상한 | [05-hashmap](../05-hashmap/2-summary.md) |
| 그 맵의 키 타입이 `Comparable`인가? 자체 키라면 `hashCode`가 `equals`에 쓰는 필드를 모두 섞나? | 실험 A (비`Comparable` 31.7초) | `record`·`Objects.hash`, `Comparable` 구현 | [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) |
| Python 서비스에서 `PYTHONHASHSEED`를 고정했나? | 실험 B | 운영은 기본(`random`) 유지. 재현이 필요하면 테스트에서만 고정 | — |
| 필드·static으로 둔 `HashMap`을 여러 스레드가 쓰나? | JDK-6423457, 실험 C | `ConcurrentHashMap`, 불변 맵(`Map.copyOf`)으로 발행 | [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) |
| "읽기 전용"이라던 공유 맵을 처음 채운 뒤 안전하게 발행했나? | JDK-6423457(초기화는 동기화, 이후 무동기 접근) | 다 채운 뒤 `final` 필드·불변 맵으로 발행하고 이후 쓰지 않음 | [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) |

### 2. 진단 — 덤프로 두 사건 가르기

```bash
for i in 1 2 3; do jcmd <pid> Thread.print > dump.$i.txt; sleep 3; done
grep -A6 '"http-nio' dump.*.txt | grep -E 'HashMap|TreeNode' | sort | uniq -c | sort -rn | head
```

- 세 장에서 같은 스레드의 맨 위 프레임이 **같은 줄**이면 순환·손상(사건 2형)을 의심한다. 그 맵이 공유되는지 코드에서 찾는다.
- 프레임이 `putVal` ↔ `TreeNode.find` ↔ `getNode`로 **바뀌며** 진행하고, 그 요청의 파라미터·키 수가 비정상이면 사건 1형이다. 접근 로그에서 요청 본문 크기·파라미터 수를 본다.
- `"http-nio`는 Tomcat 기본 스레드 이름의 예시다. 서버마다 다르다.

### 3. 코드 — 공격 면을 줄인다 (Java 21)

```java
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

// ① 외부 키의 개수 상한: 파싱 단계에서 거부한다
static Map<String, String> parseParams(List<Map.Entry<String, String>> raw) {
    final int MAX = 1_000;                                  // 예시 값 — API 계약으로 정한다
    if (raw.size() > MAX) throw new IllegalArgumentException("too many parameters: " + raw.size());
    Map<String, String> m = HashMap.newHashMap(raw.size()); // JDK 19+: 기대 원소 수로 용량 계산
    for (var e : raw) m.putIfAbsent(e.getKey(), e.getValue());
    return m;
}

// ② 자체 키는 record(전 필드로 hashCode·equals) + Comparable
record OrderKey(long tenantId, String orderNo) implements Comparable<OrderKey> {
    public int compareTo(OrderKey o) {
        int c = Long.compare(tenantId, o.tenantId);
        return c != 0 ? c : orderNo.compareTo(o.orderNo);
    }
}

// ③ 공유 캐시는 동시 컬렉션 — "조금 틀려도 되는 캐시"도 HashMap 이면 멈출 수 있다
static final Map<OrderKey, Object> CACHE = new ConcurrentHashMap<>();
```

- `HashMap.newHashMap(int)`은 JDK 19에서 추가됐다(OpenJDK 21 `HashMap.java`에 있음).
- 상한 1,000은 예시다. 정상 요청의 최대 키 수를 재서 여유를 두고 정한다.

## 장애 시나리오와 대처

### 1. 외부 입력을 키로 받는 맵 — HashDoS형

- **현상**: 요청률·트래픽은 평소 수준인데 몇 개 요청만으로 서버 CPU가 100%가 되고 응답이 멈춘다.
- **보이는 형태**: 요청 처리 스레드의 덤프가 `HashMap.putVal`·`TreeNode.find`(JDK 8+) 또는 버킷 순회(JDK 7 이하), Python이면 dict 삽입 안. 느린 요청의 본문이 크고 파라미터·키가 수만 개다. 예외 없음.
- **원인**: 예측 가능한 해시(시드 없음, 또는 시드 고정) + 키 개수 상한 없음. 삽입 n개가 O(n²).
- **대처**: 요청당 파라미터·키 수와 본문 크기 상한. 런타임의 방어(Java 8+ 트리 버킷, CPython 해시 랜덤화)를 끄지 않는다. 런타임 업그레이드만으로는 충분하지 않다 — 상한을 함께 둔다.

### 2. 자체 키 클래스에서 트리화가 안 통한다

- **현상**: 공격도 없는데 특정 고객 데이터의 배치만 수십 배 느리다.
- **보이는 형태**: 프로파일 상위에 `HashMap$TreeNode.find`(재귀). 키 수가 두 배면 시간이 4배 이상(실험 A: 8,192 → 16,384에서 약 6배).
- **원인**: 몇 필드만 더한 `hashCode`로 해시 값이 좁고, 키가 `Comparable`이 아니다. JEP 180의 개선은 `compareTo`로 키를 가를 수 있는 키를 전제로 한다.
- **대처**: `record`나 `Objects.hash`로 `equals`에 쓰는 필드를 모두 섞는다. 충돌하는 서로 다른 키를 `compareTo`가 구별하게(0은 같은 키일 때만) `Comparable`을 구현한다. 테스트에서 키 집합의 서로 다른 `hashCode` 수를 확인한다.

### 3. 재현을 위해 해시 시드를 고정한 채 운영

- **현상**: Python 서비스가 특정 요청에 CPU를 오래 쓴다. 같은 코드의 다른 배포에서는 괜찮다.
- **보이는 형태**: 문제 배포의 환경 변수에 `PYTHONHASHSEED=0`(또는 고정 정수). 실험 B처럼 프로세스마다 `hash("Aa")`가 같다.
- **원인**: 테스트 재현성이나 여러 프로세스의 해시 공유를 위해 시드를 고정했고, 그 설정이 운영까지 갔다. `0`은 해시 랜덤화(갈래 가)를 끈다. 0이 아닌 고정 정수는 랜덤화를 끄지는 않지만 시드가 설정 파일에 드러나 모든 프로세스가 같으므로, 그 값이 새면 (가) 방어가 없는 것과 같다(해석 — Python 명령줄 문서 `PYTHONHASHSEED`).
- **대처**: 운영은 기본값(`random`)으로 둔다. 순서가 필요하면 해시 순서에 기대지 말고 정렬한다. 설정 검사에 이 변수를 넣는다.

### 4. "캐시니까 괜찮다"며 공유한 `HashMap`이 멈춘다

- **현상**: 몇 주 잘 돌던 서버 하나가 CPU 한 코어 100%로 해당 기능이 응답하지 않는다. 재시작하면 한동안 괜찮다.
- **보이는 형태**: 덤프 여러 장에서 같은 스레드가 `HashMap.get` 루프(JDK 7 이하) 또는 `HashMap$TreeNode.root`·`balanceInsertion`(JDK 8+)의 같은 줄에 있다. 예외·로그 없음.
- **원인**: 여러 스레드가 동기화 없이 `put`했다. 동시 resize가 버킷을 순환시키거나(JDK 7 이하 머리 삽입, 실험 C) 트리 구조를 망가뜨렸다(JDK 21 실험).
- **대처**: `ConcurrentHashMap`으로 바꾼다. 처음 채운 뒤 안 바뀌는 맵이면 불변 맵으로 안전하게 발행한다. 멈춘 프로세스는 재시작 외에 풀 방법이 없으므로, 재발 방지는 코드에서 한다.

### 5. "JDK 8로 올렸으니 해결됐다"

- **현상**: JDK 7의 무한 루프 사례를 보고 JDK 8+로 올린 뒤 공유 `HashMap`을 그대로 뒀다. 순환 루프는 사라졌는데 캐시 항목이 가끔 사라지고, 드물게 여전히 멈춘다.
- **보이는 형태**: 기대 크기보다 작은 `size()`(JDK 21 실험: 40만 기대에 15만~34만). 드물게 `TreeNode` 프레임에서 멈춤.
- **원인**: JDK 8은 resize의 순서 뒤집기만 없앴다. `HashMap`은 여전히 동기화되지 않는다.
- **대처**: 버전 업그레이드를 동시성 수정으로 여기지 않는다. 공유 여부를 코드 리뷰 항목으로 둔다.

## 핵심 문장

- HashDoS(2011)는 "해시가 고르게 퍼진다"는 가정을 공격자가 깬 사건이다. 같은 해시의 키 n개가 삽입 O(n²)을 만들고, 요청 하나가 CPU를 오래 점유한다(advisory: "up to several hours").
- 런타임의 처방은 두 갈래였다. 해시를 예측 불가능하게(Python 3.3 랜덤화 기본, 3.4 SipHash), 또는 최악 비용을 줄이기(Java 8 JEP 180 트리 버킷). 둘 다 입력 상한을 대신하지 않는다.
- JEP 180의 트리 버킷은 `Comparable` 키에서 효과가 있다. 실험에서 같은 해시 키 32,768개가 `String`이면 46~68 ms, 비`Comparable` 래퍼면 약 32~35초였다.
- JDK 7 이하 `HashMap`의 resize는 머리 삽입으로 버킷 순서를 뒤집어, 두 스레드가 겹치면 `A.next = B, B.next = A` 순환을 만들 수 있다. JDK 버그 보고는 이를 "Not an Issue"(사용법 결함)로 닫았다.
- JDK 8+는 순서를 보존하지만 `HashMap`은 여전히 스레드 안전하지 않다. JDK 21에서도 원소 유실과 멈춤이 재현됐다.

## 관련 주제·근거

- 선행: [43-ds-symptom-index](../43-ds-symptom-index/2-summary.md) 2절(해시 성능 절벽) · [05-hashmap](../05-hashmap/2-summary.md) · [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) · [02-linked-list](../02-linked-list/2-summary.md) 장애 2
- 같은 원리의 알고리즘 쪽: [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)(SipHash·유니버설 해싱·HashDoS 재현) · [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md) 장애 3(평균 O(1)을 최악 보장으로 착각)
- 알고리즘 실사건: [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md)(이진 탐색 오버플로·정규식 백트래킹 — 같은 "입력이 가정을 깬다" 모양)
- 다른 영역: [os/15-race-conditions](../../os/15-race-conditions/2-summary.md)(경쟁 조건 일반) · [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)(입력 상한·부하 차단)
- 1차 출처
  - oCERT-2011-003 <https://ocert.org/advisories/ocert-2011-003.html> — 설명·영향/수정 판·타임라인·CVE 목록
  - Klink, Wälde, 28C3 (2011-12-28) 발표 페이지 <https://media.ccc.de/v/28c3-4680-en-effective_dos_attacks_against_web_application_platforms>
  - Crosby, Wallach, "Denial of Service via Algorithmic Complexity Attacks", USENIX Security 2003 (advisory 참고 문헌)
  - Oracle, "Collections Framework Enhancements in Java SE 7" — 7u6 대체 해시, `jdk.map.althashing.threshold` 기본 -1, 권장 512 <https://docs.oracle.com/javase/7/docs/technotes/guides/collections/changes7.html>
  - JEP 180 "Handle Frequent HashMap Collisions with Balanced Trees"(Release 8, Created 2013/02/08) <https://openjdk.org/jeps/180>
  - PEP 456 "Secure and interchangeable hash algorithm"(Python-Version 3.4, Created 27-Sep-2013) <https://peps.python.org/pep-0456/>
  - Python 언어 레퍼런스 `object.__hash__` — "Changed in version 3.3: Hash randomization is enabled by default." <https://docs.python.org/3/reference/datamodel.html> · 명령줄 문서 `-R`·`PYTHONHASHSEED` <https://docs.python.org/3/using/cmdline.html>
  - Apache Tomcat 7.0 HTTP 커넥터 문서 `maxParameterCount`(기본 10000) <https://tomcat.apache.org/tomcat-7.0-doc/config/http.html>
  - JDK-6423457 <https://bugs.openjdk.org/browse/JDK-6423457>
  - jdk7u `HashMap.java`(`transfer()` 598~614행, 대체 해시 `ALTERNATIVE_HASHING_THRESHOLD_DEFAULT`) · jdk21u `HashMap.java`(`resize()` "preserve order", `TREEIFY_THRESHOLD = 8`, `MIN_TREEIFY_CAPACITY = 64`, `newHashMap`)
  - Paul Tyma, "A Beautiful Race Condition", 2009-06-09 <https://mailinator.blogspot.com/2009/06/beautiful-race-condition.html>
- 실험 목록
  - A. 같은 해시 키 삽입 시간: `scratchpad/dsa/syn/e2/HashDos.java`, `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <dir>:/w -w /w eclipse-temurin:21-jdk java HashDos.java` 집필 두 번 + 사실 점검 두 번(OpenJDK 21.0.12). 시간은 실행마다 다르다.
  - B. Python 해시 랜덤화: `scratchpad/dsa/syn/e2/pyhash.sh`, `docker run --rm --pull never --network none --cpus=1 … python:3.12-slim sh pyhash.sh`(CPython 3.12.14).
  - C. JDK 7 `transfer()` 겹침 재연(시뮬레이션): `scratchpad/dsa/syn/e2/Jdk7Transfer.java`, A와 같은 명령. 결정적 출력. 실제 JDK 7·실제 스레드 경쟁이 아니다 — 실제 경쟁 재현은 하지 않았고 JDK-6423457 보고와 jdk7u 소스로 대신했다.
  - 공유 `HashMap`의 JDK 21 유실·멈춤 수치는 [29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) 실험에서 옮겼다.
