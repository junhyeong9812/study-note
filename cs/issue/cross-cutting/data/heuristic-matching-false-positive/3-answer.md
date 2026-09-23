# cs/issue/data/heuristic-matching-false-positive — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

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
