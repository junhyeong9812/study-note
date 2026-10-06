# security/23-deserialization-and-parser-attacks — 정답

## 정답

### 1. 공통 구조

- 한 문장: **데이터 안에 지시문이 들어 있고, 파서가 그 지시문을 신뢰 경계 안쪽에서 실행한다.**
  - 역직렬화: 스트림이 만들 클래스를 정하고, 그 클래스의 `readObject`가 돈다.
  - XXE: 문서의 엔티티 선언이 파일·URL을 읽게 한다.
  - Log4Shell: 로그 메시지 안의 `${...}`가 lookup을 실행한다.
- 18번 인젝션과 같은 점: 데이터가 실행 문맥으로 샌다.
- 다른 점: 인젝션은 **내가 문자열을 이어 붙여** 코드 문맥을 만들었다. 여기서는 **파서의 정상 기능**이 실행 문맥이다. 그래서 파라미터 바인딩 같은 인젝션 방어가 통하지 않을 수 있다(5번).

### 2. 역직렬화 순서

1. `ObjectInputStream`이 스트림의 클래스 이름을 해석한다.
2. 인스턴스를 만든다. 필드는 아직 기본값이다.
3. 그 클래스에 `readObject`가 있으면 실행한다. 필드는 그 안의 `defaultReadObject()`·`readFields()`로 복원된다. 여기서 부작용이 난다.
4. 결과를 앱이 `(Order)`로 캐스트한다. 이때 `ClassCastException`.

- 실험(OpenJDK 21.0.12)에서 `[Job.readObject 실행]`이 먼저 찍히고, 그다음 `ClassCastException`이 났다.
- 캐스트는 3번 뒤에 온다. 그래서 방어가 아니다. 실제 공격은 클래스패스 라이브러리의 가젯을 이어 3번 단계에서 위험한 동작에 닿게 한다.

### 3. 필터 판정 흐름

```text
  스트림의 각 클래스·배열·깊이
     │
     ├─ 깊이 > 5 또는 배열 길이 > 1000 ──▶ REJECTED
     ├─ com.example.Order ──────────────▶ ALLOWED
     ├─ java.lang.* ────────────────────▶ ALLOWED
     └─ 그 밖의 모든 클래스 (!*) ─────────▶ REJECTED  → InvalidClassException: filter status: REJECTED
```

- 패턴은 앞에서부터 보고 처음 맞는 것이 결정한다(JEP 290).
- `!*`를 빼면 목록에 없는 클래스는 `UNDECIDED`가 된다. 그러면 거부되지 않는다. 사실상 **거부 목록 없는 허용**이 되어 새 가젯을 못 막는다.

### 4. XML 파싱 결과 (JDK 21.0.12 실험)

| | JDK 기본 | `disallow-doctype-decl=true` |
|---|---|---|
| `file:` 외부 엔티티 | **성공**, 파일 내용이 본문에 들어옴 | `DOCTYPE is disallowed ...`로 거부 |
| 엔티티 폭탄(641바이트 → 10^10) | `JAXP00010001 ... more than "64000" entity expansions`로 중단 | `DOCTYPE is disallowed ...`로 거부 |

- 이 실험에서 엔티티 폭탄을 멈춘 것은 확장 횟수 한도였다(JDK에는 엔티티 전체 크기 등 다른 기본 한도도 있다). 외부 엔티티는 풀었다.
- DTD 금지는 두 공격 모두 파싱 시작 단계에서 끊는다(OWASP XXE Prevention Cheat Sheet).

### 5. 바인딩해도 lookup이 돈 이유

- Log4j 2.0-beta9~2.14.1(보안 수정판 2.12.2 이상 2.12.x·2.3.1 이상 2.3.x 제외)은 `{}` 자리에 값을 넣어 메시지를 **완성한 뒤**, 그 문자열에서 다시 `${...}`를 찾아 lookup을 실행했다(message lookup).
- 그래서 사용자 값이 바인딩으로 들어와도 결국 lookup 대상이 됐다. 실험에서 `${sys:demo.secret}`가 가짜 비밀 값으로 바뀌어 찍혔다.
- `formatMsgNoLookups=true`: 메시지 lookup을 끈다. 실험에서 같은 2.14.1이 글자 그대로 남겼다.
- 못 막는 것: 설정 패턴 쪽 Context Lookup(`$${ctx:loginId}`) 경로. CVE-2021-45046이 이 경로였다(NVD). 그래서 답은 2.17.1 이상 업그레이드다.

### 6. 다른 형식의 같은 위험

| | 위험한 기능 | 안전한 쪽 |
|---|---|---|
| Jackson | 다형 타입(기본 타이핑) — JSON 안 타입 이름으로 클래스 선택 | 켜지 않기. 필요하면 2.10+ `activateDefaultTyping(PolymorphicTypeValidator, …)` 허용 목록 |
| SnakeYAML | `Constructor()`가 임의 타입 생성(CVE-2022-1471) | `SafeConstructor`, 2.0 이상 |
| Python `pickle` | 역직렬화 중 임의 호출 | 신뢰 못 할 입력에 쓰지 않기, JSON 등 데이터 형식 |

- 셋 다 "입력이 만들 타입을 고른다"는 점이 Java 기본 직렬화와 같다.

### 7. 389 포트 외부 연결

- 찾을 것: 접근 로그의 헤더·파라미터에서 `${`와 `jndi`·`lower:`·`upper:` 같은 문자열(`grep -F '${' access.log | grep -iE 'jndi|lower:|upper:'`).
- 순서
  1. 그 서버의 egress를 막아 추가 조회를 끊는다.
  2. `mvn dependency:tree -Dincludes=org.apache.logging.log4j:log4j-core`와 배포물 안 jar 목록으로 버전을 확인한다.
  3. 2.17.1 이상으로 올려 다시 배포한다.
  4. 연결이 실제로 일어났으므로 침해로 보고 범위를 조사한다(26번 로그, 30번 사고).

### 8. 필터 배포 뒤 세션 유실

- 로그: `java.io.InvalidClassException: filter status: REJECTED`.
- 원인: 세션 복제·캐시가 직렬화하는 클래스가 허용 목록에 없었다.
- 순서
  1. 거부 대신 **기록만** 하는 필터(JEP 415 필터 팩토리로 구성)로 먼저 돌려, 실제로 오가는 클래스 목록을 모은다.
  2. 목록을 허용 목록에 반영한다.
  3. 거부 기록이 정상 경로에서 0이 된 뒤 강제한다.
- 26번의 audit → enforce와 같은 순서다. 장기적으로는 세션·캐시도 데이터 형식(JSON)으로 바꾼다.
