# architecture/04-character-encoding-unicode — 코드 포인트·UTF-8/UTF-16·서로게이트·정규화: 글자를 바이트로 — 정리 (힌트)

## 해결하는 문제

메모리·디스크·네트워크에는 바이트만 있다. "글자"라는 것은 저장되지 않는다.\
그래서 두 가지를 약속해야 한다. **글자 ↔ 번호**, 그리고 **번호 ↔ 바이트**다.

```text
  글자          번호(코드 포인트)        바이트(UTF-8)
  'é'    ──→    U+00E9          ──→    C3 A9
         문자 집합(Unicode)       인코딩(UTF-8·UTF-16·…)
```

- 쓰는 쪽과 읽는 쪽의 약속이 하나라도 다르면 글자가 깨진다. 오류 없이 깨지는 경우가 많다.

쉬운 예: 모스 부호표가 두 종류 있다고 하자.
- 보낸 사람은 영문 표로 `·−`(A)를 쳤다. 받은 사람은 다른 나라 표로 읽었다. 신호는 그대로인데 글자가 바뀐다.

똑같은 구조다.\
`café`의 UTF-8 바이트 `63 61 66 C3 A9`를 ISO-8859-1로 읽으면 `cafÃ©`가 된다. 바이트는 하나도 안 바뀌었다(실험 2).

실무 예:
- 외부 API 응답의 `é`가 화면에 `Ã©`로 나온다.
- 이모지가 든 닉네임을 MySQL `utf8`(= `utf8mb3`) 컬럼에 넣자 `Incorrect string value`로 실패한다.
- 맥에서 올린 파일 `한글.txt`와 서버에서 만든 `한글.txt`가 같은 폴더에 둘 다 있다.
- 미리보기를 자른 문자열 끝에 `?`나 `�`가 붙는다.

## 동작·원리

### 1. 두 단계 — 코드 포인트와 인코딩 형식

```text
  Unicode 코드 공간: 0 ~ 10FFFF(16진) = 1,114,112개 번호
  ┌────────── 평면 0 (BMP) ──────────┐┌ 평면 1 ┐┌ 평면 2 ┐ ... ┌ 평면 16 ┐
  0000                          FFFF 10000   20000          10FFFF
   A=0041  é=00E9  가=AC00  €=20AC     😀=1F600  𠜎=2070E
                  └ D800~DFFF: 서로게이트 전용 구간(글자 없음)
```

- *코드 포인트(code point)*: 글자에 붙인 번호. `U+` 뒤에 16진수로 쓴다. 코드 공간은 0~10FFFF다(Unicode 18.0 핵심 명세 2장, 3장 D9).
- *평면(plane)*: 코드 공간을 64K(65,536)개씩 나눈 묶음. 17개다.
  - *BMP(Basic Multilingual Plane)*: 평면 0(U+0000~FFFF). 한글 음절 11,172자(U+AC00~D7A3)가 여기 있다(Python `unicodedata` 15.0으로 셈).
  - *보조 평면 문자(supplementary character)*: U+10000 이상. 이모지 대부분과 한자 확장 B가 여기 있다.
- *인코딩 형식(encoding form)*: 코드 포인트를 *코드 유닛* 나열로 바꾸는 규칙. UTF-8(8비트 단위), UTF-16(16비트 단위), UTF-32(32비트 단위)가 있다(핵심 명세 §3.9 D90~D92).
  - *코드 유닛(code unit)*: 인코딩 형식이 쓰는 최소 비트 묶음. UTF-8은 1바이트, UTF-16은 2바이트.
    - 흔한 오해: "유니코드 = 2바이트." 2바이트는 UTF-16의 코드 유닛 크기일 뿐이다.
- ASCII 기초와 Python `encode` 예는 원고 [foundations/data-representation](../../foundations/data-representation/README.md) §3.1~3.2에 있다.
  - 참고: 원고 §3.2의 "16비트로 65,536개 … 유니코드는 2바이트로 문자 하나"는 지금 표준과 맞지 않는다. 코드 공간은 0~10FFFF이고, 2바이트에 안 들어가는 글자는 UTF-16에서 4바이트(서로게이트 쌍), UTF-8에서 4바이트가 된다(핵심 명세 2장, RFC 3629 §3, 실험 1).

### 2. UTF-8 — 앞 바이트가 길이를 말한다

```text
  코드 포인트 범위       바이트 틀 (x = 코드 포인트 비트)                 길이
  0000 0000-0000 007F   0xxxxxxx                                       1
  0000 0080-0000 07FF   110xxxxx 10xxxxxx                              2
  0000 0800-0000 FFFF   1110xxxx 10xxxxxx 10xxxxxx                     3
  0001 0000-0010 FFFF   11110xxx 10xxxxxx 10xxxxxx 10xxxxxx            4
                        └ 시작 바이트     └ 이어지는 바이트(모두 10으로 시작)
  RFC 3629 §3 표 — 3바이트 범위 중 D800~DFFF(서로게이트)는 인코딩하지 않는다(같은 절)
```

예: `가` = U+AC00 = `1010 1100 0000 0000`(16비트) → 3바이트 틀.

```text
  1110 1010   10 110000   10 000000
     1010       110000      000000      ← 코드 포인트 비트를 뒤에서부터 채운다
  = EA          B0          80
```

- 성질(RFC 3629 §1)
  - ASCII 바이트(00~7F)는 여러 바이트 글자 안에 나타나지 않는다. 그래서 `/`·`\0`을 찾는 옛 C 코드가 UTF-8에서도 동작한다.
  - 첫 바이트가 길이를 알려 준다. 어디서 읽기 시작하든 `10xxxxxx`를 건너뛰면 글자 경계가 나온다(실험 7).
  - 올바른 UTF-8에는 C0, C1, F5~FF 바이트가 나오지 않는다.
  - UTF-8 바이트열의 사전식 순서 = 코드 포인트 순서다.
- 한 코드 포인트를 나타내는 방법은 하나뿐이다. 더 긴 틀로 쓴 것(*과잉 길이*, overlong)은 형식 위반이다(RFC 3629 §3).

### 3. UTF-16 — 16비트 두 칸으로 보조 평면을 쓴다

```text
  😀 U+1F600
   − 0x10000        = 0x0F600 = 0000 1111 0110 0000 0000 (20비트)
   위 10비트 0000111101 = 0x03D  → D800 + 03D = D83D  (상위 서로게이트)
   아래 10비트 1000000000 = 0x200 → DC00 + 200 = DE00  (하위 서로게이트)
   UTF-16: D83D DE00          UTF-8: F0 9F 98 80
```

- *서로게이트 쌍(surrogate pair)*: 보조 평면 문자 하나를 UTF-16 코드 유닛 두 개로 나타낸 것. 상위는 D800~DBFF, 하위는 DC00~DFFF(핵심 명세 3장 D71~D75).
  - 짝 없이 하나만 있으면(*외톨이 서로게이트*) 어떤 UTF에서도 형식 위반이다. UTF-8은 D800~DFFF를 인코딩하지 않는다(RFC 3629 §3).
- Java `String`은 UTF-16이다. `length()`와 인덱스는 코드 유닛(`char`)을 센다(Java SE 21 `String` 문서). JS 문자열도 같다.
  - 그래서 `"a😀b".length()`는 4, 코드 포인트는 3이다(실험 3).
- *UTF-16BE·LE*: 16비트 단위를 바이트로 놓을 때의 순서(엔디안, [06](../06-byte-order-and-alignment/2-summary.md)). `iconv -t UTF-16`은 앞에 BOM `FF FE`를 붙이고 LE로 썼다(실험 9).
  - *BOM(byte order mark)*: 파일 맨 앞의 U+FEFF. UTF-16에서는 바이트 순서를 알린다. UTF-8에서는 순서가 없으니 "UTF-8이라는 표식" 노릇만 한다(RFC 3629 §6). UTF-8 BOM은 `EF BB BF`다.

### 4. 잘못된 바이트열 — 바꿔 넣거나, 거부하거나

```text
  입력 바이트          왜 틀렸나                       관대한 디코더    엄격한 디코더
  C0 AF               '/'(2F)의 과잉 길이 표현         � �             예외
  ED A0 BD            서로게이트를 UTF-8로 씀(CESU-8식)  �               예외
  F4 90 80 80         10FFFF 초과                     � � � �         예외
  "한글" CP949 바이트   UTF-8로 읽음                    � ѱ �           예외
  (Java 21 실험 4·2)
```

- 표준은 형식이 틀린 코드 유닛 나열을 **오류로 다루라**고 한다(핵심 명세 §3.9 C10). 오류를 다루는 방법 중 하나가 U+FFFD(`�`, 대체 문자)로 바꾸는 것이다.
  - *관대한 디코더*: 틀린 부분을 `�`로 바꾸고 계속 간다. Java `new String(bytes, UTF_8)`가 이렇다(문서: "always replaces malformed-input").
  - *엄격한 디코더*: 틀린 부분에서 예외를 던진다. Java `CharsetDecoder`에 `CodingErrorAction.REPORT`를 건다.
- CP949 바이트 `C7 D1 B1 DB` 중 `D1 B1`은 우연히 올바른 UTF-8(U+0471 `ѱ`)이다. 관대한 디코더는 이것을 다른 글자로 살려 낸다. 그래서 "오류 없음"이 "올바름"을 뜻하지 않는다.
- 보안: 과잉 길이 표현을 받아 주는 파서는 `/../` 검사를 우회당할 수 있다. RFC 3629 §10은 `2F C0 AE 2E 2F` 사례를 들고, 2001년 웹 서버를 공격한 바이러스가 실제로 썼다고 적는다.

### 5. 정규화 — 눈에 같은 글자, 다른 코드 포인트

```text
  "한é"   NFC  U+D55C U+00E9                      2 코드 유닛 / UTF-8 5바이트
          NFD  U+1112 U+1161 U+11AB U+0065 U+0301  5 코드 유닛 / UTF-8 12바이트
               ㅎ     ㅏ     ㄴ     e      ́(결합 악센트)
  화면에서는 같다. equals 는 false (실험 5)
```

- *정준 동등(canonical equivalence)*: 보이는 글자와 뜻이 같은 서로 다른 코드 포인트 나열. 완성형 `é`(U+00E9)와 `e`+결합 악센트(U+0065 U+0301)가 그렇다(UAX #15 §1).
- *정규화 형식*(UAX #15)
  - *NFD*: 정준 분해. 완성형을 기본 글자 + 결합 문자로 푼다. 한글 음절은 자모로 풀린다.
  - *NFC*: 정준 분해 뒤 다시 조합. 완성형 글자가 있으면 완성형으로 남는다.
  - *NFKC·NFKD*: *호환 분해*까지 한다. 반각 `ｶ`·원문자 `①`·합자 `ﬁ` 같은 "모양만 다른 변형"을 기본 글자로 바꾼다. 실험에서 `ｶﾞ①ﬁ` → NFKC `ガ1fi`. 정보가 사라지므로 표시용 원문에는 쓰지 않는다.
- 같은 정규화를 두 번 해도 결과는 같다. `toNFC(toNFC(x)) = toNFC(x)`(UAX #15 §7 설계 목표). 이 성질이 05에서 다룰 "식별자 정규화"의 바탕이다.
- 파일 이름: Linux ext4는 이름을 바이트 그대로 저장한다. 보통의(대소문자 구분, casefold를 켜지 않은) 디렉터리에서 NFC 이름과 NFD 이름으로 각각 만들면 **두 파일**이 된다(실험 9). casefold(`+F`) 디렉터리는 비교할 때 정준 분해로 맞추므로 같은 이름으로 본다(커널 ext4 관리 문서). NFD 이름은 macOS에서 만든 파일 등으로 들어온다고 알려져 있다 [?].
- DB 쪽 비교(정규화와 collation)는 [database/10-collation-and-text-comparison](../../database/10-collation-and-text-comparison/2-summary.md) §5에 있다.

### 실험: 같은 글자의 세 표현, 모지바케, 절단, 정규화

환경: i7-13700HX, Linux 7.0.0-34, Docker `eclipse-temurin:21-jdk`(OpenJDK 21.0.12) `--cpus=2 --network none`, 호스트 glibc 2.39 `iconv`·`xxd`(2023-10-25)·`file` 5.45, ext4. 2026-10-07. 시간 측정이 없는 결정적 실험이다.

```java
// Enc04.java 핵심
s.getBytes(StandardCharsets.UTF_8);                         // 1. UTF-8 바이트
new String("café".getBytes(UTF_8), ISO_8859_1);             // 2. 모지바케
"a😀b".substring(0, 2).getBytes(UTF_8);                     // 3. 외톨이 서로게이트 인코딩
UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
     .decode(ByteBuffer.wrap(bytes));                       // 4. 엄격한 디코딩
Normalizer.normalize("한é", Normalizer.Form.NFD);            // 5. 정규화
static int charStart(byte[] b, int off) {                   // 7. 바이트 경계 탐색
    while (off > 0 && (b[off] & 0xC0) == 0x80) off--;      //    10xxxxxx 면 한 칸 뒤로
    return off;
}
```

```text
== 1. 같은 글자, 세 가지 표현 ==
 A | U+0041 | 41           | 00 41       | true      ← 마지막 열: RFC 표대로 쓴 손 인코더와 일치
 é | U+00E9 | C3 A9        | 00 E9       | true
 가 | U+AC00 | EA B0 80     | AC 00       | true
 😀 | U+1F600 | F0 9F 98 80  | D8 3D DE 00 | true
 𠜎 | U+2070E | F0 A0 9C 8E  | D8 41 DF 0E | true
== 2. 모지바케 ==
  "café" UTF-8 63 61 66 C3 A9
  ISO-8859-1로 읽음         → cafÃ©   (길이 5)
  복구: latin1로 되돌려 UTF-8로 읽기 → café
  "한글" UTF-8 ED 95 9C EA B8 80 / MS949 C7 D1 B1 DB
  UTF-8 바이트를 MS949로 읽음 → �븳湲�
  MS949 바이트를 UTF-8로 읽음 → �ѱ�  U+FFFD U+0471 U+FFFD
== 3. 서로게이트 쌍 중간 절단 ==
  "a😀b" length()=4 codePointCount=3 UTF-16 단위 0061 D83D DE00 0062
  substring(0,2) 단위 0061 D83D → getBytes(UTF-8) 61 3F
  같은 문자열을 엄격 인코더로 → 예외 java.nio.charset.MalformedInputException: Input length = 1
  "😀" UTF-8 F0 9F 98 80 를 3바이트에서 자름 → new String = "�" U+FFFD
== 7. 바이트 경계 탐색 ==  "A가😀" = 41 EA B0 80 F0 9F 98 80
  off 2 (0xB0) → 시작 1     off 3 (0x80) → 시작 1     off 6 (0x98) → 시작 4
== 8. 정렬 순서 ==  x=U+FF61 y=U+1F600
  x.compareTo(y) = 10020  (양수 = x가 뒤)      코드포인트 비교 = -1      UTF-8 바이트 무부호 비교 = -1
```

```text
== 9. 호스트 (bash, LANG=C.UTF-8) ==
$ printf 'A가😀' | xxd                         → 41ea b080 f09f 9880
$ printf 'A가😀' | iconv -f UTF-8 -t UTF-16 | xxd → fffe 4100 00ac 3dd8 00de   (BOM + LE)
$ printf 'café' | iconv -f latin1 -t UTF-8      → cafÃ©
$ printf '한글' | iconv -f UTF-8 -t CP949 | iconv -f UTF-8 -t UTF-8
iconv: illegal input sequence at position 0    (exit 1)
$ ls   (NFC·NFD 이름으로 각각 만든 뒤)       → 한글.txt / 한글.txt  (두 줄)
$ ls | xxd   → e184 92e1 85a1 e186 ab… (NFD, 자모 6개) / ed95 9c ea b8 80 … (NFC)
$ file t-*.txt
t-cp949.txt: ISO-8859 text                     ← CP949를 알아보지 못한다
t-utf16.txt: Unicode text, UTF-16, little-endian text
t-utf8.txt:  Unicode text, UTF-8 text
```

관찰과 해석
- 1: UTF-8과 UTF-16의 길이가 글자마다 다르다. ASCII는 UTF-8이 짧고, 한글은 UTF-16이 짧고, 보조 평면 문자는 둘 다 4바이트다.
- 2: 모지바케는 디코딩 단계의 잘못이다. 한 번만 잘못 읽었고 ISO-8859-1처럼 256개 바이트 값 각각을 글자 하나로 받는 문자셋이었다면, 역방향으로 되돌려 원문을 살릴 수 있다. `�`로 바뀐 바이트는 되살릴 수 없다.
- 3: 같은 외톨이 서로게이트를 Java `getBytes`는 `?`(3F)로, JS `TextEncoder`는 `EF BF BD`(U+FFFD)로 바꿨다(Node 22.23.2 실험, [05](../05-text-length-segmentation-and-case/2-summary.md)). 둘 다 예외는 없다.
- 8: Java `compareTo`는 UTF-16 코드 유닛 값으로 비교한다. 서로게이트(D800~DFFF)가 E000~FFFF보다 작아서 보조 평면 문자가 앞에 온다. UTF-8 바이트 비교·코드 포인트 비교와 순서가 다르다. 앱 정렬과 DB의 코드 값 순 정렬(PostgreSQL `C`, MySQL `utf8mb4_bin` — 문자 코드 값 순이고 끝 공백은 무시하는 PAD SPACE, MySQL 8.0 매뉴얼 12.8.5)이 이런 문자에서 어긋날 수 있다.
- 9: `file`은 내용으로 추측할 뿐이다. CP949를 ISO-8859로 잘못 말했다. 인코딩은 메타데이터(HTTP `Content-Type`의 `charset`, DB 연결 설정)로 받아야 한다.

## 쓰이는 자료구조·알고리즘

- **가변 길이 부호화(접두 부호)**: UTF-8의 시작 바이트 꼴(`0`, `110`, `1110`, `11110`)은 어느 것도 다른 것의 앞부분이 아니다. 그래서 구분자 없이 이어 써도 한 가지로만 끊어 읽힌다. 허프만 부호와 같은 성질이다 — [algorithm/33-lossless-compression-lz77-huffman](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md), [math/14-information-theory-basics](../../math/14-information-theory-basics/2-summary.md).
- **바이트 경계 탐색(자기 동기화)**: 이어지는 바이트는 모두 `10xxxxxx`다. 임의 위치에서 많아야 3바이트 물러나면 글자 시작이다. 바이트 제한 자르기·역방향 탐색은 [05](../05-text-length-segmentation-and-case/2-summary.md).
- **비트 연산**: 인코딩·디코딩은 마스크(`& 0x3F`)와 시프트뿐이다 — [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md).
- **해시·트라이 키의 정규화**: 해시 맵·트라이는 키를 정규화하지 않고 받은 단위 그대로 다룬다(Java `String.hashCode`는 UTF-16 `char` 나열로 계산). NFC와 NFD 키는 다른 칸에 들어간다. 넣기와 찾기에서 같은 정규화를 해야 한다 — [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [data-structure/09-trie](../../data-structure/09-trie/2-summary.md).
- **정렬 키**: UTF-8 바이트 사전식 순서 = 코드 포인트 순서(RFC 3629 §1). 사람이 기대하는 순서는 collation이 만든다 — [database/10](../../database/10-collation-and-text-comparison/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 원인

| 화면에 보이는 것 | 무슨 일이 있었나 | 먼저 볼 곳 |
|---|---|---|
| `Ã©`, `Ã¤`, `ì•ˆ` 같은 라틴 문자 무더기 | UTF-8 바이트를 ISO-8859-1·Windows-1252로 읽었다 | 응답 헤더 `charset`, 소비자의 디코딩 문자셋 |
| `�`(U+FFFD) | 틀린 바이트열을 관대한 디코더가 바꿨다(인코딩 불일치, 바이트 중간 절단) | 원본 바이트 `xxd`, 자른 위치 |
| `?`(3F) | 인코더가 표현 못 하는 글자(외톨이 서로게이트, 대상 문자셋에 없는 글자)를 바꿨다 | 인코딩 직전 문자열의 코드 유닛 |
| 한글이 엉뚱한 한자·키릴 문자로 | CP949 ↔ UTF-8 혼동 | 파일 앞 바이트(한글 음절의 UTF-8 시작 바이트는 `EA`~`ED`) |
| 같은 이름인데 검색·중복 검사가 안 맞음 | NFC/NFD 차이 | 코드 포인트 덤프, 길이 비교 |

### 2. 바이트로 확인한다

```bash
printf '%s' "$value" | xxd                     # 실제 바이트
iconv -f UTF-8 -t UTF-8 file.csv > /dev/null   # 올바른 UTF-8인가 (틀리면 위치를 찍고 exit 1)
file file.csv                                  # 추측일 뿐 — CP949를 ISO-8859로 말한 예(실험 9)
```

```java
// Java 21 — 받는 경계에서는 엄격하게
static String decodeStrict(byte[] in) throws CharacterCodingException {
    return StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(in)).toString();
}
static boolean fitsUtf8mb3(String s) {          // MySQL utf8mb3 컬럼에 들어가나
    return s.codePoints().allMatch(c -> c <= 0xFFFF
            && (c < 0xD800 || c > 0xDFFF));     // 외톨이 서로게이트는 UTF-8로 못 쓴다
}
```

### 3. 코드에서 지킬 것

- 문자셋을 코드에 적는다. `new String(bytes, UTF_8)`, `getBytes(UTF_8)`.
  - JDK 18부터 표준 API의 기본 문자셋이 UTF-8이다(JEP 400). JDK 17 이하나 `-Dfile.encoding=COMPAT`에서는 OS·로캘에 따라 달라진다(같은 JEP). 기본값에 기대지 않는 편이 안전하다.
- 입력 경계(HTTP 본문, 파일 업로드, 메시지)에서 엄격하게 디코딩한다. 관대하게 받으면 `�`가 DB까지 들어가고, 원본 없이는 되돌릴 수 없다.
- 식별자(아이디·파일 이름·태그)는 들어올 때 NFC로 맞춰 저장한다. 사람에게 보일 원문은 따로 둘 수 있다. 대소문자·호환 문자까지 맞추는 식별자 정규화는 [05](../05-text-length-segmentation-and-case/2-summary.md).
- MySQL은 `utf8mb4`를 쓴다. `utf8mb3`는 BMP만 담고 최대 3바이트이며 폐기 예정이다(MySQL 8.0 매뉴얼 12.9.1·12.9.2). 클라이언트 연결 문자셋도 맞춘다(Connector/J 속성은 [database/10](../../database/10-collation-and-text-comparison/2-summary.md) 적용 2).
- CSV처럼 사람이 엑셀로 여는 파일의 BOM 문제는 [database/35-bulk-file-import-export](../../database/35-bulk-file-import-export/2-summary.md) 장애 1·2.

## 장애 시나리오와 대처

### 1. 모지바케 `cafÃ©` (⚠ 커리큘럼)

- **현상**: 외부 시스템에서 받은 이름의 `é`가 `Ã©`로 저장·표시된다. 오류 로그는 없다.
- **보이는 형태**: DB 값의 길이가 한 글자씩 늘어 있다(`café` 4 → `cafÃ©` 5, 실험 2). 두 번 거치면 `Ã`·`Â`가 더 붙는다.
- **원인**: 쓰는 쪽은 UTF-8, 읽는 쪽은 ISO-8859-1·Windows-1252였다. HTTP 응답에 `charset`이 없어 클라이언트 라이브러리 기본값으로 읽은 경우가 흔하다.
- **대처**
  - 디코딩하는 지점을 찾아 문자셋을 명시한다.
  - 이미 저장된 값은 "한 번, 1:1 문자셋으로 잘못 읽은 것"이 확실할 때만 역변환으로 복구한다(latin1로 인코딩 → UTF-8로 디코딩). 섞여 있으면 원본에서 다시 받는다.

### 2. 서로게이트 쌍 중간 절단 → `?`·`�` (⚠ 커리큘럼)

- **현상**: 닉네임을 20자로 잘라 저장했더니 끝의 이모지가 `?`로 바뀌어 있다. 다른 서비스에서는 `�`로 보인다.
- **보이는 형태**: Java `substring(0, n)` 뒤 `getBytes(UTF_8)`에서 `3F`가 나온다. JS `TextEncoder`에서는 `EF BF BD`. 바이트 배열을 n바이트에서 잘라 `new String`하면 끝이 U+FFFD(실험 3).
- **원인**: UTF-16 단위나 바이트 단위로 잘라 서로게이트 쌍·UTF-8 시퀀스의 가운데가 끊겼다. 인코더·디코더가 예외 대신 대체 문자를 넣었다.
- **대처**: 자르는 함수를 하나로 모은다. 코드 포인트(`offsetByCodePoints`)나 그래핌 경계(`BreakIterator`)로 자른다. 자세한 것은 [05](../05-text-length-segmentation-and-case/2-summary.md). 엄격한 인코더(`REPORT`)로 바꾸면 이런 버그가 예외로 드러난다.

### 3. NFC/NFD 불일치 → 같은 파일 이름 두 개 (⚠ 커리큘럼)

- **현상**: 업로드한 `한글.txt`를 이름으로 찾으면 없다고 나온다. 폴더에는 같은 이름이 두 개 보인다.
- **보이는 형태**: 두 이름의 `length()`가 6 대 10으로 다르다(`.txt` 4자 포함). `ls | xxd`에서 한쪽은 `e1 84 92`(자모 ㅎ)로 시작한다(실험 9).
- **원인**: 한쪽은 NFD, 다른 쪽은 NFC로 만들었다. ext4(실험 9)와 Java `equals`는 코드 포인트(바이트)를 그대로 비교한다.
- **대처**: 파일 이름·검색 키를 들어오는 순간 NFC로 맞춘다(`Normalizer.normalize(s, NFC)`). 이미 쌓인 데이터는 정규화한 값으로 묶어 중복을 찾는다. 검색 인덱스 쪽은 [data-structure/09-trie](../../data-structure/09-trie/2-summary.md) 장애 2.

### 4. MySQL `utf8` 컬럼에 이모지 → `Incorrect string value` (⚠ 커리큘럼)

- **현상**: 특정 사용자의 프로필 저장만 실패한다. 이모지나 희귀 한자가 든 입력이다.
- **보이는 형태**: `ERROR 1366 (HY000): Incorrect string value: '…' for column '…' at row 1`. 오류 참조의 틀은 `Incorrect %s value: '%s' for column '%s' at row %ld`(ER_TRUNCATED_WRONG_VALUE_FOR_FIELD)다. 값 자리에 들어가는 바이트 표기 모양은 이 문서에서 확인하지 못했다 [?].
- **원인**: MySQL의 `utf8`은 `utf8mb3`의 별칭이고, BMP 문자만 최대 3바이트로 담는다. 4바이트 UTF-8(보조 평면 문자)은 담을 수 없다(MySQL 8.0 매뉴얼 12.9.1·12.9.2). 실험 6에서 `😀`·`𠜎`·`🇰🇷`가 이 조건에 걸렸다. 이 실험은 MySQL을 띄우지 않고 코드 포인트만 검사한 것이다.
- **대처**: 테이블·컬럼·연결을 `utf8mb4`로 바꾼다. 선언한 `VARCHAR(n)`의 n(글자 수)은 그대로다. 인덱스 키 길이와 행 크기(65,535바이트) 한도는 바이트로 그대로라서, 인덱싱할 수 있는 글자 수와 선언 가능한 최대 길이가 줄어든다(매뉴얼 13.3.2 `CHAR`·`VARCHAR`). 예: InnoDB COMPACT·REDUNDANT 행 형식의 767바이트 인덱스는 `utf8mb3` 255자, `utf8mb4` 191자다. DYNAMIC·COMPRESSED 행 형식은 3072바이트까지라 각각 1024자, 768자다(같은 절). 변환 전에 인덱스 정의를 확인한다(매뉴얼 12.9.8 "Converting Between 3-Byte and 4-Byte Unicode Character Sets"). 당장 바꿀 수 없으면 `fitsUtf8mb3` 같은 검사로 입력 단계에서 명확한 오류를 낸다.

### 5. 관대한 디코딩이 보안 검사를 우회

- **현상**: 경로 검사(`..` 금지)를 통과한 요청이 상위 디렉터리 파일을 읽는다.
- **보이는 형태**: 요청 바이트에 `C0 AE` 같은 과잉 길이 시퀀스가 있다.
- **원인**: 검사는 바이트 단계에서 하고, 그 뒤의 디코더가 과잉 길이 표현을 `.`로 해석했다. RFC 3629 §10의 예(`2F C0 AE 2E 2F`)다. Java 21 디코더는 같은 꼴의 과잉 길이 `C0 AF`를 `�`로 바꾸거나 예외를 던졌다(실험 4). 문제는 그렇지 않은 파서가 끼어 있을 때다.
- **대처**: 먼저 엄격하게 디코딩하고 정규화한 **뒤에** 검사한다. 검사한 값과 실제로 쓰는 값이 같은 단계의 값이어야 한다. 입력 검증 일반은 [security/18-injection](../../security/18-injection/2-summary.md).

## 핵심 문장

- 글자는 두 번 바뀐다. 글자 → 코드 포인트(Unicode), 코드 포인트 → 바이트(UTF-8·UTF-16). 깨짐은 둘째 단계의 약속이 다를 때 생긴다.
- UTF-8은 1~4바이트 가변 길이이고, 시작 바이트가 길이를 말하며, 이어지는 바이트는 모두 `10xxxxxx`라 경계를 되찾을 수 있다.
- UTF-16은 U+10000 이상을 서로게이트 쌍(코드 유닛 2개)으로 쓴다. Java·JS의 `length`는 이 코드 유닛 수다.
- 틀린 바이트열을 `�`로 바꾸는 관대한 디코딩, 표현 못 하는 글자를 `?`로 바꾸는 관대한 인코딩(Java `getBytes`)은 오류를 숨긴다. 입력 경계에서는 엄격하게 디코딩한다.
- NFC와 NFD는 눈에 같아도 다른 코드 포인트다. 식별자는 들어올 때 한 형식으로 맞춘다.
- MySQL `utf8`은 3바이트 `utf8mb3`라 보조 평면 문자를 못 담는다. `utf8mb4`를 쓴다.

## 관련 주제·근거

- 선행: [01-number-systems-twos-complement](../01-number-systems-twos-complement/2-summary.md)(16진·비트)
- 원고: [foundations/data-representation](../../foundations/data-representation/README.md) §3(ASCII·유니코드·Python 문자열)
- 후속(이 영역): [05-text-length-segmentation-and-case](../05-text-length-segmentation-and-case/2-summary.md) · [06-byte-order-and-alignment](../06-byte-order-and-alignment/2-summary.md)(UTF-16 바이트 순서)
- 연결
  - [database/10-collation-and-text-comparison](../../database/10-collation-and-text-comparison/2-summary.md) — 정규화와 collation, MySQL `utf8mb4` 기본 collation
  - [database/35-bulk-file-import-export](../../database/35-bulk-file-import-export/2-summary.md) — CSV BOM, CP949 파일 적재
  - [web-platform/12-internationalization-and-localization](../../web-platform/12-internationalization-and-localization/2-summary.md) — 브라우저 쪽 길이·로캘
  - [languages/js/syntax/04-strings-and-utf16](../../../languages/js/syntax/04-strings-and-utf16/2-summary.md) · [languages/go/syntax/10-strings-bytes-runes-and-utf8-iteration](../../../languages/go/syntax/10-strings-bytes-runes-and-utf8-iteration/2-summary.md) — 언어별 문자열 표현
  - [security/18-injection](../../security/18-injection/2-summary.md) · [security/19-xss-and-csp](../../security/19-xss-and-csp/2-summary.md) — 검사 전 정규화, 문맥별 인코딩
- 근거
  - RFC 3629 "UTF-8, a transformation format of ISO 10646"(2003) — §1 성질, §3 바이트 틀·서로게이트 금지·과잉 길이, §6 BOM, §10 보안 <https://www.rfc-editor.org/rfc/rfc3629.txt>
  - The Unicode Standard 18.0 핵심 명세 — 2장(코드 공간 1,114,112, 평면), 3장 D9·D71~D75·§3.9 D90~D92·C10·표 3-7·U+FFFD 대체 <https://www.unicode.org/versions/latest/core-spec/chapter-3/>. 커리큘럼 칸의 "Unicode Standard 2·3장"은 이 두 장이다.
  - UAX #15 "Unicode Normalization Forms"(18.0.0, rev. 58) — 정준·호환 동등, NFC/NFD/NFKC/NFKD, §7 멱등성 <https://www.unicode.org/reports/tr15/>
  - CS:APP 3판 2.1.4 "Representing Strings"(절 번호는 저자 사이트 머리말 PDF 목차로 확인 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>)
  - Java SE 21 API — `String`(UTF-16, 코드 유닛 인덱스, `getBytes`·생성자의 대체 동작), `Character`(Unicode 15.0), `java.text.Normalizer`, `java.nio.charset.CharsetDecoder` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html>
  - JEP 400 "UTF-8 by Default"(JDK 18) <https://openjdk.org/jeps/400>
  - MySQL 8.0 Reference Manual 12.9.1 utf8mb4, 12.9.2 utf8mb3(BMP만, 3바이트, 폐기 예정) <https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-utf8mb4.html> (Internet Archive 사본으로 열람) · MySQL 8.0 Error Reference 1366 ER_TRUNCATED_WRONG_VALUE_FOR_FIELD
  - MySQL 8.0 매뉴얼 12.8.5(`_bin`은 문자 코드 값 순, PAD SPACE) <https://dev.mysql.com/doc/refman/8.0/en/charset-binary-collations.html> · 13.3.2 `CHAR`·`VARCHAR`(n은 글자 수, 행 크기 65,535바이트) <https://dev.mysql.com/doc/refman/8.0/en/char.html> (둘 다 Internet Archive 사본으로 열람)
  - Linux 커널 ext4 관리 문서 — casefold 디렉터리는 정준 분해 뒤 바이트 비교, 디스크에는 원래 이름 보존 <https://docs.kernel.org/admin-guide/ext4.html>
- 실험 목록
  - `Enc04.java` — 1. 글자별 코드 포인트·UTF-8·UTF-16 바이트와 손 인코더 일치, 2. 모지바케(ISO-8859-1·MS949)와 역변환, 3. 외톨이 서로게이트 인코딩·바이트 절단 디코딩, 4. 과잉 길이·CESU-8·범위 초과·BOM의 관대/엄격 디코딩, 5. NFC/NFD/NFKC, 6. utf8mb3 적합 검사, 7. 바이트 경계 탐색, 8. `compareTo` vs 코드 포인트 순서. OpenJDK 21.0.12, Docker `--cpus=2 --network none`.
  - 호스트 셸 — `xxd`, `iconv`(UTF-16 BOM, latin1 모지바케, CP949를 UTF-8로 엄격 변환 실패, UCS-2로 이모지 변환 실패), ext4에서 NFC·NFD 이름 파일 두 개, `file` 판정. glibc 2.39, Linux 7.0.0-34.
  - Node 22.23.2 `TextEncoder`의 외톨이 서로게이트 처리는 05 실험(`len05.js`)에서 함께 확인.
  - 파일 위치: scratchpad `arch/05/`(Enc04.java, out-enc04.txt, out-host04.txt).
