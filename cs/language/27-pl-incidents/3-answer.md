# language/27-pl-incidents — 정답

## 정답

### 1. 검사하지 않기로 한 것

| 사건 | 검사하지 않은 것 | 누가 정한 기본값인가 |
|---|---|---|
| Cloudbleed 2017 | 포인터가 버퍼 끝을 **지나쳤는지**(`==`만 봄) | 생성기(Ragel)의 끝 검사 관용구 + C의 무검사 포인터 |
| Heartbleed 2014 | 요청이 선언한 길이 ≤ 실제 payload 길이 | C — 포인터와 길이가 따로 다니고, 대조는 프로그래머 몫 |
| left-pad 2016 | 요구한 판이 레지스트리에 **아직 있는지** | 당시 레지스트리 — 작가가 unpublish를 제한 없이 할 수 있었음 |

- Cloudbleed·Heartbleed가 로그에 남지 않은 이유: 프로그램 입장에서 "정상 처리"였다. 경계 밖 읽기는 C에서 미정의 동작이지만, 이 사건들에서는 정상 연산처럼 실행되어 결과가 정상 응답 안에 실렸다. 그래서 Cloudbleed는 외부 연구자의 신고(Tavis Ormandy)로 처음 알려졌다.
- left-pad: 설치 실패는 빌드 로그에 바로 보였다(npm은 분당 수백 건의 실패를 관측). 다만 우리 코드·락파일은 그대로였고, 원인은 레지스트리에서 사라진 깊은 전이 의존이었다.

### 2. Cloudbleed의 근본 원인

- 원문: 버퍼 끝 도달을 **등호 연산자**로 검사했고 포인터가 끝을 건너뛸 수 있었다. 생성 코드는 `if ( ++p == pe ) goto _test_eof;`다.
- 오류 처리 블록(`$lerr`)에 `fhold`(= `p--`)가 빠졌다. 마지막 버퍼 끝에서 속성 파싱이 실패하면 `p == pe`인 채로 다음 상태로 가서 `++p`가 되고, `p`는 `pe + 1`이 된다. 그 뒤 `++p == pe`는 계속 거짓이라 끝을 알아채지 못하고 옆 메모리를 파싱해 응답에 썼다.
- `>=`였다면 `p`가 `pe`를 넘는 순간 참이 되어 멈췄다. 원문: "Had the check been done using >= instead of == jumping over the buffer end would have been caught." 다만 끝을 넘은 포인터를 계산하는 것 자체가 C 표준상 UB라(20 실험 3, N1570 §6.5.6 ¶8), 표준상 올바른 형태는 Cloudflare의 후속 `SAFE_CHAR`처럼 역참조 전에 `p < pe`를 확인하는 것이다.
- Ragel: "Ragel compiles executable finite state machines from regular languages." 정규 언어를 결정적 상태 기계 C 코드로 생성하고 전이에 사용자 동작을 붙인다. 공식 페이지의 생성 예시에도 `if ( ++p == pe )`가 있다. 등호 검사는 "포인터는 한 칸씩만 움직인다"는 가정 위에서만 맞고, 사용자 동작(`fhold`·`fgoto`)이 그 가정을 깰 수 있었다.

### 3. 수년 잠복 뒤의 누출

- 원문: 결함은 Ragel 기반 옛 파서에 "for many years" 있었지만, NGINX 내부 버퍼 사용 방식 때문에 누출이 없었다. 새 파서 cf-html이 들어와 두 파서가 함께 쓰이자 마지막 데이터 버퍼의 `last_buf`가 1이 되어 `eof = pe`가 설정됐고, 그때만 `$lerr` 경로가 실행됐다. 누출 가능 최초일은 2016-09-22, 영향이 가장 큰 기간은 Email Obfuscation이 이전된 2017-02-13부터다.
- 결함 위치(옛 파서의 오류 경로)와 발현 조건(다른 구성 요소가 바꾼 버퍼링, 깨진 태그로 끝나는 4k 미만 버퍼, 기능 조합)이 따로 있었다. 결함이 없는 새 파서가 누출을 열었다.
- 같은 모양의 leaf(아무거나 하나): 20-5(같은 UB 코드가 빌드 최적화 수준에 따라 다른 결과), 01·23(같은 코드가 워밍업·역최적화 조건에 따라 다른 속도), 16-2(코어 수에 따라 공용 풀 크기가 달라 정지가 운영에서만).

### 4. Heartbleed의 언어 관점

- 결함: OpenSSL 권고 "A missing bounds check in the handling of the TLS heartbeat extension can be used to reveal up to 64k of memory". NVD는 "buffer over-read", CWE-125, 영향 판 1.0.1 ~ 1.0.1g 이전으로 적는다.
- 언어 관점: C에는 배열과 길이를 함께 들고 다니는 타입이 없다. 복사 함수는 원본에 그만큼의 바이트가 있는지 모른다. 선언 길이와 실제 길이의 대조는 프로그래머가 매번 지켜야 하는 불변식이고, 빠뜨려도 언어가 오류로 만들지 않는다. 이 사건에서는 그 경계 밖 읽기가 정상 연산처럼 실행되어 payload 뒤의 프로세스 메모리가 정상 응답에 실렸다(UB라 언어가 이 결과를 보장하지는 않는다).
- 정본: 공격·대응(노출 기간, 흔적 없음, 키 회전, 자산 목록)은 [security/30](../../security/30-security-incidents/2-summary.md) 사건 1이다. 이 노트는 그 노트와 같은 원문(NVD·OpenSSL 권고)에서 필요한 사실만 옮겼다.

### 5. `Echo.java` 결과

- (a) 자기 배열: `java.lang.ArrayIndexOutOfBoundsException: arraycopy: last source index 40 out of bounds for byte[5]` — 같은 실수가 누출이 아니라 예외가 됐다.
- (b) 공유 풀: `"ping!...user_002 cookie=FAKE-SESSION-000"` — 예외 없이 옆 요청의 합성 데이터가 응답에 실렸다.
- (c) 대조: `IllegalArgumentException: claimed 40 > actual 5`로 거부, 선언이 정직하면(5) `"ping!"`.
- 한계: Java의 경계 검사는 **배열 단위**다. 큰 `byte[]` 하나를 여러 요청이 offset으로 나눠 쓰면 "그 요청의 구간 안인가"는 검사하지 않는다. 20 실험 3에서 ASan이 메모리 풀 안 넘침을 못 잡은 것과 같은 구조다. 하위 구간은 경계를 가진 뷰(`ByteBuffer.slice`)로 넘기고, 길이는 언어와 무관하게 대조한다.

### 6. 1.0.0 공개로 안 풀린 이유

- 원문: "a number of dependency chains, including babel and atom, were bringing it in via line-numbers, which explicitly requested 0.0.3." 정확한 판 0.0.3을 요구하는 사슬은 1.0.0으로 만족되지 않았다.
- 중단: 태평양 시 2016-03-22(화) 오후 2:30 직후부터 분당 수백 건의 실패, "The duration of the disruption was 2.5 hours."
- 끝: npm이 평소에는 불가능한 재공개를 백업으로 해서 원래 0.0.3을 되살렸다. 4:05 PM 계획 발표, 4:55 PM 완료.

### 7. `model.py` 결과와 영향 범위

- t1(pad 전 판 삭제): `app_001`·`app_002`·`app_003` 모두 FAIL — `pad`를 직접 쓰지 않는 앱까지 실패.
- t2(다른 사람이 pad 1.0.0 공개): 범위 요구(`>=0.0.3`)만 거치는 `app_003`만 ok. 정확한 판을 요구하는 `numbers`를 거치는 `app_001`·`app_002`는 `numbers -> pad@0.0.3`으로 계속 FAIL.
- t3(0.0.3 복구): 모두 ok.
- 미러(삭제 전 사본): t1 시점에도 모두 ok.
- 영향받을 수 있는 범위는 사라진 노드에서 **역방향 간선으로 BFS한 도달 집합**이다(algorithm/11-bfs). 실제 실패는 그 부분집합이다 — t2의 `app_003`처럼 범위를 만족하는 다른 판이 있거나 선택 의존이면 도달해도 설치된다. 설치 자체는 정방향 전이 의존 풀기다. 모형은 원문의 모양만 따른 합성 그래프이고 규모·시간을 재현한 것은 아니다.

### 8. 모든 CI가 설치 단계에서 실패

- 락파일이 있어도 실패하는 이유: 락파일은 "무슨 판(과 해시)"을 고정할 뿐, 그 판이 레지스트리에 남아 있음을 보장하지 않는다(19-4).
- 즉시: 실패한 패키지가 어느 깊은 사슬에 있는지 본다(`npm ls <pkg>`). 사내 미러·캐시에 사본이 있으면 그쪽으로 설치한다. 없으면 `overrides`로 대체 판을 강제하되, 정확한 판을 요구하는 중간 패키지가 있는지 먼저 확인한다(t2처럼 대체 판으로 안 풀릴 수 있다).
- 재발 방지: 사내 미러·프록시 캐시, 벤더링, 빌드 아티팩트 보관. 작은 유틸 의존을 줄인다. 레지스트리 쪽은 현재 npm 정책이 의존자가 있는 패키지의 unpublish를 막는다(72시간 이후 조건: 의존자 없음, 지난주 다운로드 300 미만, 소유자 1명).

### 9. 26과의 연결, Cloudflare 2019

- Cloudbleed·Heartbleed → 26의 9절(UB와 최적화), 행 20-1·20-2("정상 응답 안의 남의 데이터").
- left-pad → 26의 11절(설치·재빌드 실패), 행 19-4.
- Cloudflare 2019 정규식 → 26의 6절(정규식 CPU 100%), 행 02-1.
- Cloudflare 2019는 커리큘럼 27 행에 없어 "같은 원리의 다른 사건"으로 언어 관점 한 단락만 둔다(백트래킹 엔진 선택 — 정규 언어는 선형 엔진으로 돌릴 수 있다). 정본은 [algorithm/43](../../algorithm/43-alg-incidents/2-summary.md) 사건 3(알고리즘)과 [engineering-practice/20](../../engineering-practice/20-practice-incidents/2-summary.md)(배포 절차)이다.
