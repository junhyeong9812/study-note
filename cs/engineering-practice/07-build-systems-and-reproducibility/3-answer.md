# engineering-practice/07-build-systems-and-reproducibility — 정답

## 정답

### 1. 전부 vs 증분

| | 전부 다시 | 바뀐 것만 |
|---|---|---|
| 얻는 것 | 정확함(옛 산출물이 섞일 틈이 없다) | 속도 |
| 잃는 것 | 속도 | "바뀜" 판정이 틀리면 정확함 |

- 셋을 함께 얻으려면 **각 산출물이 어떤 입력(소스·의존 산출물·도구·플래그·환경)에서 나왔는지**를 빌드 시스템이 정확히 알아야 한다. 그래야 입력 해시로 재사용 여부를 판정하고(빠름·정확함), 같은 입력에서 같은 바이트를 만들 수 있다(재현성).

### 2. 위상정렬과 재빌드 범위

- 진입 차수(의존 개수): util 0, domain 1, api 1, service 2, app 2.
- Kahn: util → (domain 0) domain → (api 0, service 0) api → service → app. 실험 출력 `build order = [util, domain, api, service, app]`, Maven reactor 순서도 같았다.
- util이 바뀌면: util에서 역방향으로 도달하는 전부(다시 빌드할 후보) = util·domain·service·api·app(실험 `[util, service, domain, app, api]`).
- api가 바뀌면: api·app(실험 `[api, app]`).
- Maven: `-pl <모듈> -amd`(also-make-dependents). 실험에서 `-pl api -amd`는 api·app만 골랐다.

### 3. make의 시각 판정

- (a) `touch`만: `cp in.txt out.txt` — 내용이 같은데 다시 빌드했다(헛빌드).
- (b) 내용 변경 + 과거 mtime: `make: 'out.txt' is up to date.` → `out.txt = a`. 바뀐 내용을 놓쳤다.
- Docker `COPY` 캐시: 문서상 체크섬에 mtime을 넣지 않는다. 08 실험(레거시 빌더)에서 `touch`해도 캐시 적중이 그대로였다(5/5).

### 4. 키에서 입력이 빠진 캐시

- 운영 빌드가 스테이징 산출물을 받는다: `HIT key=70af500bf94e requested API_URL=https://prod.example.invalid artifact -> const API = "https://staging.example.invalid";`
- 로그에는 "HIT"만 보인다. 오류도 경고도 없다 — 성공처럼 보이는 오염이다.
- 키에 설정을 넣으면 운영 요청은 `MISS key=289c76ee06ca`로 새로 빌드돼 올바른 URL을 갖는다.

### 5. jar 해시와 타임스탬프

- `outputTimestamp` 없음: `bf0b98304c05ce73` / `aeeff60013ea9cfc` — 다르다. 실행마다 값도 달라진다.
- 고정: `f418ea6b2a18687e` 두 번(별도 실행·사실 점검 재실행에서도 같은 값).
- 차이는 zip 엔트리 시각이다: `Sun Oct 04 17:08:58 UTC 2026` vs `Thu Jan 01 00:00:00 UTC 2026`. 풀어서 비교하면 내용(클래스·MANIFEST·pom 파일)은 같다. JDK `jar --date`도 같은 효과(`535c9689be4535b0` 두 번).

### 6. 정의와 남는 차이

- 정의: "Given the same source code, build environment and build instructions, any party can recreate bit-by-bit identical copies of all specified artifacts."
- Maven 가이드가 꼽는 남는 차이: JDK 메이저 버전(바이트코드), 줄 끝(CRLF/LF), 의존성 버전 범위, 사용자 이름·현재 디렉터리 같은 환경 누출.
- `SOURCE_DATE_EPOCH`: 무언가(보통 소스)의 마지막 수정 시각을 Unix epoch 초로 나타낸 표준 환경 변수. 빌드 도구가 현재 시각 대신 쓴다.

### 7. SWE@G 18장의 분류

- Maven·Gradle(그리고 Ant·Grunt·Rake)을 **작업 기반(task-based)**으로 분류한다.
- 약점: 작업이 임의 스크립트라 도구가 입력·출력을 다 알 수 없다. 그래서 병렬화·신뢰할 만한 증분 빌드가 어렵고, 타임스탬프·다운로드 같은 비결정 요소가 숨어든다. 저자는 "the system can't have enough information to always be able to run builds quickly and correctly"라고 쓴다.
- 원격 캐시 조건: 같은 입력 집합이 어느 기계에서든 정확히 같은 출력을 내야 한다. 캐시 항목은 target과 입력 해시로 키를 단다.
- 성격: Google의 경험에 근거한 **저자 주장·회사 관례**다. 측정 연구가 아니다. Gradle도 입출력 선언·빌드 캐시를 갖고 있어 분류의 경계는 도구마다 정도 차이가 있다.

### 8. 환경 의존 테스트

- UTC CI: 기본 시간대가 UTC라 2026-10-04T20:00:00Z의 날짜가 `day=2026-10-04`(서울은 `2026-10-05`) → FAIL.
- de_DE: 소수점이 쉼표라 `amount=1,5` → FAIL.
- 고치는 코드: 입력을 드러낸다.

```java
LocalDate.ofInstant(t, ZoneId.of("Asia/Seoul"));
String.format(Locale.ROOT, "%.1f", 1.5);
```

- 실험에서 명시한 줄은 세 환경 모두 `day=2026-10-05 amount=1.5`였다.

### 9. 지운 클래스가 남는 이유

- maven-compiler-plugin 3.15.0: `Recompiling the module because of added or removed source files.` → jar에 `ex/Hello.class`만. 삭제를 감지했다.
- 손 스크립트(`javac -d out`, out 유지): `Hello.class`·`Legacy.class` — 지운 소스의 클래스가 남는다.
- 플러그인의 증분 단위(기본 설정 `useIncrementalCompilation=true`): 모듈. Hello.java 하나만 고쳐도 `Compiling 2 source files`로 모듈 전체를 다시 컴파일했다. `false`로 바꾸면 `Compiling 1 source file`이지만 문서가 권하지 않는 모드다(바뀐 클래스를 쓰는 클래스는 다시 컴파일하지 않는다).
- 대처: 릴리스는 `clean` 빌드, 산출물 목록과 소스 목록 대조.

### 10. 순환 의존

- 순환 안의 모듈은 진입 차수가 0이 되지 않는다. Kahn 알고리즘이 그 모듈들을 꺼내지 못해 순서를 정할 수 없다(실험 `CYCLE: not orderable …`).
- Maven 출력: `… introduces to cycle in the graph ex:app:1 --> ex:service:1 --> ex:util:1 --> ex:app:1`.
- 고치기: 하위 모듈(util)이 상위(app)를 의존하지 않게 한다. 공유할 부분을 새 하위 모듈로 빼거나, 인터페이스를 하위에 두고 구현을 상위에 둬서(의존성 역전) 방향을 한쪽으로 맞춘다.
