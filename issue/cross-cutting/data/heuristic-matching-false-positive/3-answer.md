# issue/data/heuristic-matching-false-positive — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **`indexOf` vs `startsWith` vs 구조 판정.**\
   접두사는 이름의 **시작**에서만 의미가 있는데 `indexOf`는 위치를 보지 않아 `budget`·`issue`·`history` 속의 `get`/`is`를 접두사로 오인한다(`budget()` → `""`, `issue()` → `"sue"`).\
   전에는 입력이 항상 `getX`/`isX` 꼴이라 `indexOf`와 `startsWith`의 결과가 같았다 — record 접근자처럼 **접두사 없는 이름**이 입력 영역에 들어오자 차이가 드러났다.\
   `startsWith`로만 바꾸면 `issue()`처럼 **접두사로 시작하는 평범한 이름**은 여전히 `is`+`sue`로 잘린다.\
   그래서 "접근자인가"를 이름이 아니라 **구조적 사실**(record 컴포넌트의 접근자와 같은 메서드인가 → 이후 "무인자·비void·비static·동명 인스턴스 필드 존재"로 일반화)로 먼저 판정하고, 그 외에만 `startsWith`를 쓴다. 검사 순서가 정확성을 보장한다.
   > **구조적 신호** — 이름 관례가 아니라 타입·문법·선언 관계처럼 언어가 보장하는 사실.

2. **선택지 포함 판정.**\
   `"autonomous".includes("auto")`도 참이라 `auto`와 `autonomous` **둘 다 ✓**로 보인다.\
   정확 일치의 구분자는 **실제 결과 포맷**에서 가져왔다 — 응답 안의 따옴표 라벨(`"label"`)로 찾거나, 줄 단위로 잘라 trim 후 `===` 비교.\
   포맷 가정이 깨질 때를 대비해 매칭 실패 시에도 응답 원문을 그대로 보여 준다(graceful).\
   같은 계열: 인터럽트 센티널을 prefix로 판정하면 그 문구로 **시작하는 정상 입력**을 삼키고(→ trim 정확 일치), 거부 판정을 substring으로 하면 실패 출력에 우연히 그 단어가 있을 때 오분류된다(→ 결과 **시작부** 고정 매칭).

3. **`sk-` ⊂ `task-`.**\
   단어 경계 없는 접두 패턴은 `task-` 같은 흔한 단어 속에서 걸린다(실측: 매칭 16건 전부 이 오탐). 경계 패턴으로 재스캔하면 CLEAN.\
   더 근본적으로, 명령 **문자열**을 보는 스캐너는 실제로 전송되는 **바이트**를 보지 못한다 — `$(cat file)`·간접 경로·인코딩·환경변수 확장·stdin/리다이렉트, 그리고 스캔 후 파일 교체(TOCTOU)까지 우회면이 열려 있다.\
   그래서 이런 훅은 **backstop**(보조 방어선)으로만 두고, 주 방어는 절차적 스캔에 둔다. 스캐너 로그에 매칭 값을 찍지 않는 것(redaction)도 함께.
   > **TOCTOU** — 검사 시점과 사용 시점 사이에 대상이 바뀌는 경쟁.

4. **소유권 판별.**\
   `contains("my-tool")`은 `not-my-tool-wrapper` 같은 **남의 항목**도 자기 것으로 오인해 덮어쓴다(수정 후 재검토에서 다시 잡힌 결함).\
   정확한 기준은 **command 경로의 basename이 정확히 `my-tool`** 인 경우만 "내 것". 아니면 덮어쓰지 않고 "이미 존재" 오류로 거부하고, 손상된 JSON은 건드리지 않고 보고한다.

5. **정적 분석의 판정 범위.**\
   classpath 전체를 모르는 도구가 "틀렸다"고 단정할 수 있는 곳은 **자기 인덱스가 실제로 아는 범위**뿐이다 — "인덱스에 실존하는 패키지의 대문자 클래스"로 한정하고, 외부·미지 서브패키지·와일드카드·소문자·잘린(truncated) 인덱스는 전부 침묵한다.\
   같은 조직 접두어의 외부 라이브러리를 "2-세그먼트 prefix가 같으니 우리 것"으로 추정하면 멀쩡한 import에 빨간 줄이 생긴다.\
   잘못된 경고는 사용자가 경고 자체를 무시하게 만들어 진짜 경고의 가치까지 깎으므로, 확신할 수 없으면 침묵이 낫다.

6. **ps 출력으로 active 판정.**\
   "실행 중 + 출력 줄에 포트 문자열" 조건은 **방금 띄운 standby도 만족**하고, 출력 순서(최신 먼저)에 의존해 standby를 active로 골랐다 → 배포 파이프라인이 active(실은 새 standby)를 stop → 로그는 "배포 완료", 실제로는 새 컨테이너가 사라지고 프록시가 upstream을 못 찾아 재시작 루프.\
   1차 가드: 판정에서 standby 포트를 제외(`skip_port`) + `active != standby` 검사.\
   근본 수정: ps 휴리스틱 삭제 → **라우팅 설정(프록시 conf)에서 색을 파싱**하는 함수 하나를 유일 진실 소스로(주석 제외, 정확히 한 색일 때만, 아니면 None), 판정 불가면 배포 중단(fail-closed), 모니터 쪽의 깨진 판정도 같은 함수로 교체, 상태 영속화(원자 쓰기 + 파일 락).

7. **교정 3종.**\
   **정확 일치**(구분자·위치 고정, basename ==, 단어 경계) — "경계 없음"을 제거한다.\
   **구조적 신호**(record 접근자 판정, `static` 키워드 캡처, 선언 클래스 하위타입 검사, 복수 신호 AND) — "관례 의존"을 제거한다.\
   **영속 상태**(마지막 성공 전환이 가리키는 쪽 = active) — 관측 신호가 전환 도중 모호해지는 "과도 상태"를 제거한다.

## 문제 구조 (추상화 코드)

### 변형 A — 위치·경계 없는 포함 검사
① 문제 코드
```java
int index = name.indexOf("get");          // budget → "", issue(is) → "sue"
if (index != -1) index += 3;
// ...
```
② 고친 코드
```java
if (isAccessorByStructure(method)) index = 0;               // 구조 판정 먼저 (순서가 정확성 보장)
else if (name.startsWith("get")) index = 3;
else if (name.startsWith("is")) index = 2;
```
무엇이 깨졌나: 접두사를 위치 무관 검색으로 찾아 흔한 단어 속 부분 문자열을 접두사로 오인했다.

같은 구조:
```ts
// 선택지 판정: includes → 구분자 기준 정확 일치
const isSelected = (label?: string) => {
  const l = label?.trim(); if (!l) return false;
  if (answer.includes(`"${l}"`)) return true;                       // 결과 포맷의 따옴표 라벨
  return answer.split(/\r?\n/).some((line) => line.trim() === l);   // 줄 단위 정확 일치
};
```
```rust
// 공유 설정의 소유권: contains → basename 정확 일치
let is_ours = entry.get("command").and_then(Value::as_str)
    .and_then(|c| Path::new(c).file_name())
    .map(|f| f == "my-tool").unwrap_or(false);
if !is_ours { return Err(AlreadyExists); }
```
```rust
// 텍스트 포함으로 부모 찾기: 자기 자신을 후보에서 제외
.find(|it| it.id != *child_id && it.text.as_deref().is_some_and(|t| t.contains(child_id.as_str())))
```
- 같은 구조: 시크릿 스캐너의 `sk-` 접두 패턴이 `task-`에 걸림 → 단어 경계 패턴(스캐너는 backstop으로 격하).
- 같은 구조: 인터럽트 센티널 prefix 판정 → trim 정확 일치 / 거부 판정 substring → 결과 시작부 고정.

### 변형 B — 이름 관례로 의미 추정
① 문제 코드
```ts
// 마지막 식별자가 대문자면 클래스로 간주, 2-세그먼트 prefix가 같으면 "우리 패키지"로 간주
if (/^[A-Z]/.test(last(spec))) flagIfUnresolved(spec);
```
② 고친 코드
```ts
const cls = m[1] /* static 키워드 캡처 */ ? spec.slice(0, spec.lastIndexOf(".")) : spec;
if (!/^[A-Z]/.test(cls.split(".").pop() ?? "")) continue;
const pkg = cls.slice(0, cls.lastIndexOf("."));
if (!pkg || !knownPackages.has(pkg)) continue;      // 모르는 영역 → 침묵
```
무엇이 깨졌나: 대소문자·접두어 관례를 의미로 믿어 상수를 클래스로, 외부 라이브러리를 미해석으로 판정했다.

```java
// 타입변수를 이름만으로 매칭 → 다른 선언의 동명 변수와 교차 매칭
if (var.getGenericDeclaration() instanceof Class<?> declaring
        && resolved.isAssignableFrom(declaring)) {         // 선언 클래스가 하위타입일 때만
    for (int i = 0; i < vars.length; i++)
        if (Objects.equals(vars[i].getName(), var.getName())) return forType(args[i]);
}
```
무엇이 깨졌나: 타입변수의 정체성은 (선언 + 이름)인데 이름 폴백은 문자열만 봐서, 두 인터페이스를 구현한 톱레벨 클래스에서 형제 인터페이스의 동명 변수로 해석됐다(폴백 자체 제거는 정당한 좁히기 경로가 의존해 선택하지 않음).

- 같은 구조: 컨테이너 이름 필터(부분 일치)에 넣은 패턴이 실제 이름과 달랐다 — 오케스트레이터가 이름을 `{프로젝트디렉터리}-{서비스}-{번호}`로 자동 생성해 디렉터리명(오타 포함)이 들어가 있었다 → 이름을 추정하지 말고 실제 생성 규칙대로 맞춤.

### 변형 C — 화면 텍스트 스크래핑
① 문제 코드
```ts
if (screen.text.includes(PERMISSION_PROMPT_TEXT)) showBadge("permission");   // 화면 전체에서 단일 문구
// 스크롤백의 과거 프롬프트·산문 속 번호 목록도 매칭
```
② 고친 코드
```ts
const tail = lastNonEmptyLines(screen, 20);                     // 관찰 창을 라이브 하단으로 한정
const SELECT_CURSOR   = /❯\s*\d+\.\s/;
const NUMBERED_OPTION = /(?:^|\s)\d+\.\s+\S/;
const isPermission = hasQuestionHeader(tail) && hasNumberedYes(tail);          // 복수 신호 AND
const isMenu = SELECT_CURSOR.test(tail) && countMatches(tail, NUMBERED_OPTION) >= 2;
// write/onData 300ms 트레일링 디바운스
```
무엇이 깨졌나: 화면은 과거 출력의 잔재를 포함하므로 단일 문자열 매칭은 오탐한다. 화면이 없는 백그라운드 탭에서는 원리적으로 감지 불가 — 복귀 시 재스캔으로 정합, 실시간화는 백엔드 감시로 남김.

### 변형 D — 토큰 분해·다의어로 매칭 확장
① 문제 코드
```python
results = set()
for tok in tokenize(query):                       # 다대일 매핑을 뒤집은 역인덱스를 토큰 단위로 조회
    results |= set(reverse_index.get(tok, []))    # 한 키에 모인 무관한 값들이 합성어 전체로 증폭
```
② 고친 코드
```python
results = list(reverse_index.get(str(query), []))   # 원문 단일 키 조회 (호출처 전부 동일 적용)
# 트레이드오프: 풀키가 없는 다단어 입력의 recall 감소
```
무엇이 깨졌나: 역인덱스의 한 키에 무관한 값들이 모여 있는데, 입력을 쪼개 부분 키로 조회·합성해 오염을 증폭했다(반대 방향 함수에는 이미 "부분 매칭 버림" 가드가 있었으나 대칭 적용 누락).

- 같은 구조: 문맥 없는 키워드 매칭이 다의어(일반 명사)를 구분하지 못해 다른 카테고리 결과가 섞임 → 상위 분류 필터를 AND로 결합해 분류 수준에서 차단.
```
bool.filter: [ terms(groupCodes), bool.should(keywords) ]
```
(주의: `should`를 `filter`/`must`와 **같은** bool에 두면 `minimum_should_match` 기본값이 0이 되어 키워드가 필수 조건이 아니게 된다 — 중첩 bool에 두거나 `minimum_should_match`를 명시한다.)

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

"지금 active 인스턴스는 무엇인가"(블루/그린 전환)라는 같은 질문에 대한 두 방안.

### 방안 1 — 부수 신호 추론 + 가드 (1차 대응)
```python
def find_active_port(skip_port=None):
    for line in run("docker ps").splitlines():            # 출력 순서에 의존
        if "service" in line.lower():
            if str(BLUE_PORT) in line and BLUE_PORT != skip_port: return BLUE_PORT
            if str(GREEN_PORT) in line and GREEN_PORT != skip_port: return GREEN_PORT

start(standby)
active = find_active_port(skip_port=idle_port)
if active != idle_port: stop(active)
```
(1차 수정 시점에는 standby 대기 시간·컨테이너 생성 시각 기반 판별도 함께 쓰였다.)

### 방안 2 — 영속된 단일 진실 소스 (근본 수정)
```python
def detect_active_color(cfg_path) -> Color | None:
    try: text = read(cfg_path)
    except (OSError, UnicodeDecodeError): return None    # 읽기 실패도 판정 불가
    colors = {c for c in parse_upstreams(strip_comments(text))}
    return colors.pop() if len(colors) == 1 else None      # 정확히 한 색일 때만

active = detect_active_color(PROXY_CONF)
if active is None: abort_deploy("active 판정 불가")           # fail-closed
# 상태(승인 대기 등)는 파일에 영속: tmp + rename 원자 쓰기 + file lock (자격증명 미저장)
# 프록시 reload 후 worker 프로세스 세대교체까지 확인해야 전환 완료
```

| | 방안 1 부수 신호 + 가드 | 방안 2 영속 단일 진실 소스 |
|---|---|---|
| 전제 | 두 인스턴스가 공존하는 순간이 짧고 드묾 | 트래픽을 실제로 가르는 설정이 존재(라우팅 conf) |
| 비용 | 한 줄 가드, 즉시 적용 | 판정 함수·영속화·락·시뮬 하네스(S1~S10 + 실패 주입) 필요 |
| 실패 모드 | 전환 과도 상태·출력 순서 변화·재시작 시 상태 증발·동시 요청 | conf 파싱 모호 → None → 배포 중단(시끄러운 실패) |
| 맞는 조건 | 긴급 복구, 원인 격리 전 임시 방어 | 운영 배포 경로의 정본 판정 |

**결론**: 방안 1은 "방금 띄운 것을 죽인다"는 한 증상만 막을 뿐, 부수 신호가 전환 도중 모호해지는 구조는 그대로라 같은 시스템에서 "green 기동 후 blue 미종료" 같은 결함이 다시 나왔다.\
active 여부는 **트래픽을 실제로 결정하는 곳**(라우팅 설정)에서 읽고, 읽을 수 없으면 추측하지 말고 멈추는 방안 2가 정본이다 — 수정 전에 시뮬 하네스로 버그를 먼저 재현(REPRO)해 두면 수정이 실제로 그 결함을 닫았는지 확인할 수 있다.

## 방안 비교 — 실행 모드를 부하에 따라 생기는 사건 줄로 판정하면, 그 사건이 없는 부하에서 거짓 불일치가 난다

같은 원리(부수 신호로 의미를 추정)의 **거짓 음성** 쪽 사례다.\
측정 하네스는 회차마다 "계획한 GC 모드(세대형 수집기)가 실제로 적용됐나"를 GC 로그로 대조하고, 다르면 회차를 하네스 실패로 처리한다.\
수집기 종류는 기동 시 한 번 찍히는 초기화 줄(`Using …`)로 읽었지만, **세대형인지**는 수집 사건 줄로 판정했다.\
세대형 모드는 수집을 `Minor Collection`(젊은 세대)·`Major Collection`(전체)으로 찍고, 비세대형은 `Garbage Collection`으로 찍는다.\
판정이 `Minor Collection` 줄만 찾았기 때문에, 할당이 적은 낮은 부하 회차(Minor 0회 · Major 170회 — 모드는 세대형이 맞음)가 "모드 불일치"로 실패 처리됐다.

```text
신호:  수집 사건 줄  ── 언제 생기나? ── 할당 속도·힙 상태에 따라 (부하 의존)
판정:  "Minor 줄 있음" ⇒ 세대형
        │
        ├─ 높은 부하: Minor 다수 → 세대형 ✓
        └─ 낮은 부하: Minor 0 · Major만 → "비세대형" ✗ (거짓 불일치 → 정상 회차를 실패 처리)
```

### 방안 1 — 모드의 사건 한 종류만 본다 (문제 코드)
```python
if "Minor Collection" in line:          # 세대형이면 "자주" 생기는 사건 하나
    out["generational"] = True
```

### 방안 2 — 그 모드만 찍는 사건 종류를 전부 본다 (이 사례에서 적용)
```python
# 세대형은 Minor·Major로 찍고, 비세대형은 "Garbage Collection"으로 찍는다 — 두 표기 모두 세대형의 증거
if "Minor Collection" in line or "Major Collection" in line:
    out["generational"] = True
```
고친 뒤 실패했던 낮은 부하 스모크와 이전 측정 단계의 로그 양쪽으로 판정이 맞는지 확인했다.

| | 방안 1 사건 한 종류 | 방안 2 모드 고유 사건 전부 |
|---|---|---|
| 전제 | 그 사건이 모든 부하에서 최소 한 번 생긴다 | 모드마다 찍는 사건 표기가 서로 겹치지 않는다(로그 형식이 그 런타임 버전에서 고정) |
| 비용 | 한 줄 | 한 줄 + 표기 목록을 런타임 버전에 맞춰 유지 |
| 실패 모드 | 사건이 생기지 않는 부하(낮은 할당)에서 거짓 불일치 — 정상 회차를 버리고 다시 잰다 | 수집이 한 번도 돌지 않은 회차는 여전히 판정 불가 · 로그 표기가 바뀌면 다시 깨진다 |
| 맞는 조건 | 없음 — 고부하 전용 판정이라는 범위를 스스로 밝힐 때만 | 사건 줄 외에 모드를 직접 말하는 신호가 로그에 없을 때 |

**결론**: 부하에 따라 생기거나 안 생기는 사건으로 설정을 판정하면, "사건 없음"이 "설정 아님"으로 읽힌다 — 판정 신호는 그 모드에서 **반드시** 나타나는 것이어야 한다.\
방안 2는 "어떤 수집이든 한 번은 돈다"까지만 가정을 줄인 것이고, 수집이 0회인 회차에는 여전히 답하지 못한다 — 그 경우를 불일치로 처리할지 판정 불가로 처리할지는 따로 정해야 한다.\
사건이 아니라 **기동 시 한 번 찍히는 설정 사실**(수집기 종류처럼)이 모드까지 말해 준다면 그쪽이 부하와 무관하다 — 이 사례는 그런 신호를 쓰지 않았으므로 비교하지 않았다.\
검증 기록: 2026-10-23 사건 기록 대조·추상화(Claude 초안).

## 방안 비교 — 활성 쪽을 설정 파일(의도)이 아니라 프록시 응답 표식(관측)으로 판정하고, reload 직후의 과도 구간은 기다렸다가 여러 번 본다

같은 질문("지금 트래픽은 어느 쪽으로 가나, 옛 쪽을 내려도 되나")에 대한 세 번째 방안이다.\
위 방안 2는 라우팅 설정 파일을 정본으로 읽는다 — 그런데 파일은 프록시에 **원하는 상태를 전하는 수단**이고, 프록시가 실제로 그렇게 동작하는지는 따로 사실이다.\
다른 블루/그린 전환 구현의 설계 검토에서 파일 정본이 틀리는 경우가 둘 나왔다.

```text
(a) 파일을 B로 바꾼 직후 전환 주체가 죽음      파일 = B · 프록시 = A  → 다음 실행이 "A는 비활성"으로 읽고 A를 내림
(b) reload가 조용히 적용되지 않음            파일 = B · 프록시 = A  → 외부 헬스는 A의 200으로 통과 → "전환 성공"
```

그리고 관측으로 바꾼 뒤에도, 실서버 시험에서 **reload 직후의 과도 구간**이 판정을 양방향으로 틀리게 했다(로컬 실험·리뷰에서는 드러나지 않았다).

```text
nginx reload:  새 worker 기동 ──▶ (틈) ──▶ 옛 worker에 종료 신호 ──▶ 옛 worker "shutting down" (남은 연결 처리)
                                 │
          틈 안에서는:  ps에 "shutting down" 없음   +   옛 worker가 요청을 한두 개 더 받음(응답 표식 = 옛 쪽)
                                 │
   정리 판정을 이 틈에 한 번만 하면
     ├─ 서비스 X:  "남은 연결 없음" + 응답 = 옛 쪽  → "아직 옛 쪽이 서비스 중" → 정지 보류 → 옛 인스턴스 방치
     └─ 서비스 Y:  "남은 연결 없음" + 응답 = 새 쪽  → 전환 1초 뒤 옛 쪽 정지 → 긴 스트림이 있었다면 절단
```
방치 쪽은 실제 채팅 부하를 건 서버 배포에서 정리 로그가 `stop deferred — proxy still routes to "blue"` 꼴로 남아 발견했다.\
반대쪽(일찍 내림)은 같은 원인을 되짚다가 다른 두 서비스의 배포 기록(전환 1초 뒤 옛 쪽 정리)에서 확인했다 — 그때는 긴 스트림이 없어 피해가 없었다.

### 방안 3 — 응답 표식을 정본으로, 과도 구간은 기다렸다 여러 번 (이 사례에서 적용)
```nginx
# 활성 쪽 파일 (전환 주체가 템플릿을 temp + rename으로 교체)
map "" $slot     { default blue; }
map "" $upstream { default svc-blue:8080; }

server {
    add_header X-Slot $slot always;          # 모든 응답(502 포함)에 "지금 어느 쪽으로 보냈나"
    location / { proxy_pass http://$upstream; }
}
```
```go
// 판정: 상태 코드가 아니라 표식 — 앱이 죽어 502여도 프록시가 어디로 보내는지는 안다
func observedSlot(url string) (string, error) {
    for i := 0; i < 3; i++ {                       // 일시적 시간 초과 한 번으로 "모름"이 되지 않게
        slot, _ := readSlotHeader(url)                      // 응답 헤더 X-Slot
        if slot == "blue" || slot == "green" { return slot, nil }
        sleep(probeInterval)
    }
    return "", errUnknown                          // 프록시 무응답·표식 없음 = 모름
}

// 전환 전: 파일과 관측이 다르면 관측을 따르고 파일을 고친다. 모르면 전환하지 않는다
active, err := observedSlot(publicURL)
if err != nil { return refuse("switch") }
if fileSlot != active { replaceSlotFile(slotTemplate(active)) }

// 전환 후 성공 판정: 200이어도 표식이 새 쪽이 아니면 성공이 아니다
waitUntil(func() bool { s, err := readSlotHeader(publicURL); return err == nil && s == target })

// 옛 쪽 정리: 과도 구간을 지나서 보고, 내리기 전에 여러 번 확인한다
func retireOld(old string) {
    announceRetire(old)
    sleep(settle)                                  // 2초 — 옛 worker가 "shutting down"이 될 시간
    for before(deadline) && proxyProcessListHas("shutting down") { sleep(pollInterval) }   // 남은 연결(상한 3분)
    s, err := observedSlot(publicURL)
    for i := 0; i < 5 && err == nil && s == old; i++ {   // 틈에 옛 worker가 받은 한두 요청에 단정하지 않는다
        sleep(probeInterval)
        s, err = observedSlot(publicURL)
    }
    if err != nil || s == old { logError("stop deferred"); return }   // 응답 중이거나 모르면 내리지 않는다
    stop(old)
}
```
고친 뒤 같은 서버에서 채팅 12건을 건 채 다시 배포해 12건 모두 완료, 옛 쪽은 전환 2초 뒤 정리되어 한 벌만 남았다.\
과도 구간 수정에는 "reload 직후 한동안 옛 쪽을 돌려주다가 새 쪽으로 바뀌는 프록시"를 흉내 낸 단위 테스트 둘을 함께 넣었다.

| | 방안 2 라우팅 설정 파일 정본 | 방안 3 응답 표식 정본 + 과도 구간 처리 |
|---|---|---|
| 전제 | 파일 내용 = 프록시가 실제로 쓰는 설정(쓰기와 적용 사이에 끊김이 없다) | 프록시가 모든 응답에 활성 쪽을 표시한다(설정 한 줄) · 외부에서 그 응답을 받아 볼 수 있다 |
| 비용 | 파서·영속화·락 | 표식 헤더 · probe 재시도 · 정착 대기(2초)와 재확인(최대 5회) — 정리가 그만큼 늦다 |
| 실패 모드 | 쓰기 뒤 중단·조용히 미적용인 reload에서 파일과 실제가 어긋나 운영 중인 쪽을 내릴 수 있다 | 정착 대기는 시간 추정이다 — 틈이 그보다 길면 다시 틀릴 수 있다(그때도 "모르면·응답 중이면 안 내림"이라 방치 쪽으로 기운다) · 프록시가 응답하지 않으면 판정 불가 → 전환 거절 |
| 맞는 조건 | 설정 쓰기와 적용이 한 주체 안에서 원자적으로 끝나고, 적용 여부를 따로 확인할 수 있을 때 | 전환 주체가 중간에 죽거나 reload가 실패할 수 있고, 운영 중인 쪽을 잘못 내리는 비용이 클 때 |

**결론**: 파일은 의도이고 응답이 사실이다 — 운영 중인 쪽을 내리는 판단처럼 틀리면 비싼 판단은 프록시가 실제로 돌려준 표식으로 한다(위 방안 2가 덧붙인 "worker 세대교체까지 확인"도 같은 방향이다).\
다만 관측에도 시간축이 있다 — reload 같은 비동기 전환 직후에는 옛 상태와 새 상태가 섞여 있으므로, 한 번 본 값으로 단정하지 말고 자리 잡을 시간을 준 뒤 여러 번 본다.\
그래도 정착 대기는 상한 있는 추정이므로, 판정이 애매할 때의 기본값을 "내리지 않는다"(남은 인스턴스는 다음 배포·재기동 정리가 치운다)로 두어 틀려도 절단이 아니라 방치가 되게 한다.\
같은 원리의 짧은 언급: [silent-failure-vs-artifact](../../reliability/silent-failure-vs-artifact/)의 "프록시 설정 파일은 의도일 뿐".\
검증 기록: 2026-11-20 사건 기록·수정 diff·서버 재시험 기록 대조·추상화(Claude 초안). 파일 정본의 실패 (a)(b)는 설계 검토의 지적이고 실서버에서 재현하지 않았다.
