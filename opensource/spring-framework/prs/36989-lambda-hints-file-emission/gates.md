# PR #36989 — 이해 게이트 기록

> 출처: 세션 3a9337b2 (2026-07-02), 작업 폴더 docs/plans/2026-07-02/nativeconfig-lambda-hints. 답변은 원문 그대로(오타 포함) 옮기고, 판정·정답은 대화에 기록된 것만 쓴다.

## 게이트 목록

이 작업에서 통과한 이해 게이트는 계획 하나와 diff 둘, 모두 세 건이다.

| 번호 | 대상 | 시도 | 최종 판정 |
|---|---|---|---|
| G1 | 계획 게이트 — 버그가 왜 발생하나 / 왜 이 수정이 맞나 | 2 | 2회차 pass |
| G2 | diff 1 — 테스트 `lambdaConfig()` 추가 | 1 | pass |
| G3 | diff 2 — `hasAnyHint` OR 체인 1줄 fix | 1 | pass |

세 게이트 모두 독립 판정 워커가 실코드와 대조해 판정했다. 계획 게이트 앞에 트레이드오프 확정(T1 fix 위치, T2 테스트 강도, T3 입증 순서)이 있었으나 이는 선택 확인이지 이해 게이트가 아니다. 사용자 답변은 다음 한 줄이었다.

> 위 순서대로 가자.

## G1 — 계획 게이트: 버그 발생 원인과 수정 근거

게이트 순서에 한 번 사고가 있었다. Claude가 계획 게이트를 "첫 diff(테스트)의 게이트에서 실코드와 함께 받겠다"며 뒤로 미루고 테스트 import를 먼저 적용했고, gate-guard 훅이 `PENDING_GATE=1`로 다음 Edit를 막았다. Claude는 곧바로 자기 정정하고 코드를 되돌린 뒤 계획 게이트를 정식으로 다시 올렸다.

> 맞습니다. 제가 틀렸어요. lazy 모드의 핵심이 바로 그 이해 게이트를 건너뛰지 않는 건데, 제가 "첫 diff에서 받겠다"며 임의로 순서를 바꿔 진행한 게 자율주행입니다. 계획 게이트(설명 #2)를 통과하기 전엔 코드를 쓰면 안 됩니다.

**질문** (Claude가 낸 원문)

> 아래를 **본인 말로** 설명해 주세요. 독립 워커가 실코드와 대조해 판정합니다:
>
> 1. **이 버그가 왜 발생하나** — `hasAnyHint`가 무슨 역할이고, lambda hint만 있을 때 어떤 경로로 메타데이터가 drop되는가?
> 2. **왜 이 수정이 맞나** — OR 체인에 `lambdaHints().findAny().isPresent()` 한 줄을 넣는 게 왜 올바른 해법인가? (불변식 관점에서)

**시도 1 — 답변** (사용자 원문)

> hasAnyHint는 모든 hint에 대해서 이게 hint인지 체크를 하는데 현재는 lambda로 작성한 hint일 경우 오류가 발생될 수 있다. 그래서 이걸 lamba일 경우에도 제대로 json 출력이 가능하도록 수정한다.이거 task.md에 너가 변경할 before/after가 없어서 보기 힘드네. 리플랙션 객체로 hints의 객체중 람다로만 이뤄진 힌트들을 찾아서 이것도 넣으라고 추가해서 그냥 생성되는 불변객체에 해당 객체도 더해서 만들게 하는 거 아니야?

답변에 포함된 되묻기(task.md에 계획 diff의 before/after가 없어 이해가 어렵다는 지적)는 Claude가 받아들여, 판정 전에 계획된 before/after 스니펫을 task.md에 먼저 채워 넣었다.

**판정 1 — fail**

판정 워커 원문:

> 람다 힌트에서 "오류(error)가 발생한다"고 본 점과, 불변객체에 람다 데이터를 새로 더해 넣는 수정이라고 본 점을 다시 생각해 보라. hasAnyHint가 실제로 무엇을 "결정"하는지(무슨 일이 일어나는지/안 일어나는지)와, JSON 출력 자체는 이미 누가 만들고 있는지를 코드에서 재확인할 것.

Claude가 전달한 힌트(정답 비노출 원칙에 따라 답은 주지 않고 확인 지점만 제시):

> - `write()`: `if (hasAnyHint(hints)) { writeTo(...) }` — `hasAnyHint`가 false를 반환하면 그 다음에 뭐가 실행되나요/안 되나요?
> - `oneLambda` 테스트(RuntimeHintsWriterTests) — lambda hint의 JSON은 이미 잘 나옵니다. 그럼 lambda-only일 때 진짜 문제는 어디서 생기나요?

**시도 2 — 답변** (사용자 원문)

> 1. 람다온리일 경우 해당 인트를 인식못하고 false가 반환되고 그대로 사일런트 에러가 되는구나. 결국 람다 조건으로 해당 힌트를 찾아낼 수있어야되는구나. false면 실행안되지.

**판정 2 — pass**

판정 워커 원문:

> 람다온리 힌트 미인식으로 hasAnyHint가 false, write 미실행, 사일런트 no-op(예외 아님)까지 정확하고, 수정 방향을 "게이트가 람다 힌트를 인식/검출하게 만들기"로 잡은 것도 맞습니다. (최종 시도로 통과 처리됩니다.)

**정답 정리**

- `hasAnyHint`(`NativeConfigurationWriter.java` L46-53)는 proxies, reflection의 typeHints, resources의 patterns, resources의 bundles, jni의 typeHints, serialization 여섯 종만 OR로 검사하고 `reflection().lambdaHints()`를 빠뜨렸다.
- `write()`는 `if (hasAnyHint(hints)) { writeTo(...) }` 구조라, false가 나오면 `writeTo`가 아예 호출되지 않는다. 예외가 던져지는 게 아니라 `reachability-metadata.json`이 만들어지지 않는 조용한 no-op이다.
- JSON 출력 로직은 이미 완비돼 있다. `RuntimeHintsWriter`와 `ReflectionHintsAttributes`(L95)가 lambda 힌트를 정상 방출하고, `RuntimeHintsWriterTests`의 `oneLambda` 테스트가 그 출력을 증명한다. 따라서 이 fix는 데이터를 더 넣는 수정이 아니라, 파일을 쓸지 말지 결정하는 앞단 게이트 조건을 고치는 수정이다.
- 다운스트림 영향(Claude가 게이트 통과 후 별도로 설명): 파일이 없으므로 lambda 메타데이터가 native image 빌드에 들어가지 않는다. JVM에서는 리플렉션 제약이 없어 정상 동작하고, native image 런타임에서 그 lambda를 리플렉티브하게 다루거나 직렬화하는 경로에서만 깨진다.
- 트리거는 좁다. `RuntimeHints`가 오직 lambda 힌트만 가질 때에만 발생한다. 다른 종류 힌트가 하나라도 함께 있으면 `hasAnyHint`가 이미 true여서 lambda JSON도 같이 기록된다.

## G2 — diff 1: 테스트 `lambdaConfig()` 추가

첫 diff 게이트는 추가한 red 테스트가 무엇을 검증하는지를 물었고 1회차에 통과했다.

**질문** (Claude가 낸 원문)

> **본인 말로 설명해 주세요** (워커 판정):
> - 이 테스트가 **무엇을 검증**하나요? (왜 lambda hint를 "하나만" 등록하는 게 핵심인지)
> - 지금 `NoSuchFileException`으로 실패하는 게 왜 "버그가 있다"는 증거인가요?

**시도 1 — 답변** (사용자 원문)

> 실제 hints에 람다만 넣어서 람다에 대한 메타json을 생성하도록 해서 실제 생성되어야 하는 JSON과 같은지 비교하는데 이 과정에서 실제 파일이 드랍되서 생성이 안되니, 노서치파일예외가 발생한거고, 그렇다면 해당 파일을 읽는 네이티브 이미지에 데이터가 없으니 실제 리플렉션이나 시리얼라이즈에 대한지원을 그렝들 vm이 못해주니 런타임에 문제가 발생한다.

**판정 1 — pass**

판정 워커 원문:

> 람다만 등록해 기대 JSON과 비교한다는 점, 파일이 드랍되어 생성 안 됨, NoSuchFileException, 그리고 그것이 메타데이터 유실의 증거이며 네이티브 이미지에서 GraalVM 리플렉션/직렬화 지원 실패로 이어진다는 다운스트림까지 정확히 짚었습니다.

**정답 정리**

- `lambdaConfig()`는 lambda 힌트 하나만 등록한 `RuntimeHints`로 `generator.write(hints)`를 호출하고, `assertEquals` 헬퍼가 `reachability-metadata.json`을 읽어 `oneLambda`의 기대 JSON과 대조한다.
- 힌트를 하나만, 그것도 lambda만 등록하는 것이 핵심이다. 다른 종류 힌트가 섞이면 `hasAnyHint`가 이미 true라 파일이 써지고 버그가 가려진다.
- 수정 전 실행 결과는 `FileNativeConfigurationWriterTests.java:236`의 `Files.readString(jsonFile)`에서 `java.nio.file.NoSuchFileException`이었다. JSON 내용이 틀린 게 아니라 파일 자체가 없다는 것이므로, 실패 지점이 직렬화가 아니라 그 앞단 게이트임을 결정적으로 가리킨다.
- T3(입증 순서)대로 수정 전에 먼저 이 테스트를 돌려 FAIL을 확보했고, fix 후 PASS로 뒤집혀 결정적 회귀 테스트가 성립했다.

## G3 — diff 2: `hasAnyHint` OR 체인 1줄 fix

둘째 diff 게이트는 프로덕션 한 줄이 왜 결함을 고치고 왜 기존 판정을 깨지 않는지를 물었고, 역시 1회차에 통과했다.

**질문** (Claude가 낸 원문)

> **본인 말로 설명해 주세요** (워커 판정 — 마지막):
> - 이 1줄이 **왜 버그를 고치나요?** (`findAny().isPresent()`가 여기서 하는 역할)
> - 왜 이 위치·이 방식이 기존 코드와 **일관**되며, 다른 hint 종류의 판정을 **깨뜨리지 않나요?**

**시도 1 — 답변** (사용자 원문)

> 1번 저기서 실제람다로만 이뤄진 힌트의 경우도 true를 발생시키니, 이제 실제 해당 json문자열 자체도 메타json에 입력이 되고 이렇게 입력이되면 결국 메타분기를 생성하는 조건 1개만 추가한거라 기존 메타 생성에는 영향이 없고 새성만 되는거지

**판정 1 — pass**

판정 워커 원문:

> 람다 전용 힌트가 이제 true를 내 파일(람다 JSON)이 기록된다는 게이트 동작과, OR 체인에 조건 1개만 추가돼 기존 다른 힌트 타입의 메타 생성엔 영향이 없고 빠졌던 케이스만 새로 생성된다는 무회귀 논리를 정확히 짚었습니다.

**정답 정리**

- 추가된 한 줄은 `hasAnyHint`의 OR 체인에서 typeHints 뒤에 들어간 `hints.reflection().lambdaHints().findAny().isPresent()`다. `findAny().isPresent()`는 스트림에 원소가 하나라도 있는지만 보는 존재 검사이므로, lambda 힌트가 하나라도 있으면 게이트가 true가 된다.
- 게이트가 true가 되면 `write()`의 `if` 블록이 실행되고, 이미 존재하던 `RuntimeHintsWriter`의 lambda 방출 로직이 그대로 동작해 파일이 기록된다. 새 출력 로직을 만드는 게 아니다.
- OR 체인에 항 하나를 더한 것뿐이므로 나머지 다섯 종 힌트의 판정은 불변이고, 전부 비어 있는 `emptyConfig` 케이스도 여전히 false를 유지해 파일 미작성 계약이 깨지지 않는다. 빠져 있던 lambda-only 케이스만 새로 true가 된다.
- 검증: 수정 후 `FileNativeConfigurationWriterTests` 전체 통과, 이어서 nativex 전체 테스트와 `checkstyleMain`/`checkstyleTest`까지 BUILD SUCCESSFUL. self-review 결과 production 1줄과 테스트(import 1개 + 메서드 1개) 외 의도 밖 변경 없음.

## 반복된 오해 패턴 / 교훈

세 게이트를 통과하는 과정에서 반복된 오해와 그로부터 얻은 교훈은 다섯 가지다.

- **조용한 실패를 예외로 착각한다.** G1 시도 1의 첫 오답이 "오류가 발생될 수 있다"였다. 실제로는 아무 예외도 던져지지 않고 `if` 블록이 통째로 건너뛰어져 파일이 안 만들어지는 no-op이었다. 시도 2에서 사용자가 스스로 "사일런트 에러"로 고쳐 잡았다. 실패 형태를 "무엇이 던져지나"가 아니라 "무엇이 실행되지 않나"로 물으면 빨리 도달한다.
- **결함 위치를 출력 단계로 잘못 민다.** G1 시도 1의 두 번째 오답이 "불변객체에 람다 데이터를 더해 넣는 수정"이었다. 직렬화기는 처음부터 lambda를 잘 출력하고 있었고 (`ReflectionHintsAttributes` L95, `oneLambda` 테스트), 빠진 것은 그 앞의 게이트 조건뿐이다. 고장난 곳을 찾을 때 "이미 잘 되는 부분은 어디까지인가"를 먼저 확정하면 범위가 좁혀진다.
- **판정 워커의 힌트 방식이 유효했다.** 1회차 fail에서 정답을 노출하지 않고 확인할 코드 지점 두 곳(`write()`의 if 구조, `oneLambda` 테스트)만 제시했고, 사용자는 2회차에서 스스로 정정해 pass했다. 이후 G2와 G3는 1회차 pass였고, G2 답변에서는 묻지도 않은 다운스트림(native image 런타임 실패)까지 스스로 확장했다.
- **게이트 순서를 접으려는 관성은 훅이 잡았다.** Claude가 계획 게이트를 첫 diff 게이트에 합치려 했을 때 gate-guard의 `PENDING_GATE=1`이 다음 Edit를 차단했다. 자율주행 방지가 문서 규칙만이 아니라 훅으로 강제되는 지점이다.
- **테스트 격리 설계가 게이트 이해의 핵심이었다.** lambda 힌트를 "하나만" 등록해야 버그가 드러난다는 점은 G1과 G2 양쪽에서 반복해 확인됐다. 다른 힌트가 섞이면 게이트가 이미 true여서 버그가 통째로 가려진다.
