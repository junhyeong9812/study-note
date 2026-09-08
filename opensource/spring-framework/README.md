# spring-framework — 업스트림 기여 학습 아카이브

이 폴더는 Spring Framework 업스트림 기여(2026-06~) 과정에서 작성한 학습 문서의 아카이브다. 원본은 작업 repo(spring-framework-fork)의 `docs/study/`에서 작성됐고, 2026-09-08에 머지 17건 시점의 상태로 이곳에 복사됐다. **이후의 새 기여 문서는 이 폴더에 직접 작성한다.**

구성은 두 갈래다. `prs/`는 PR 하나당 주제 폴더 하나로, 표준 5종 문서(README 해설, tests 테스트 해설, structure 실구조, analysis 메서드 그래프·이름표 사전, gates 이해 게이트 기록)가 탭으로 배포된다. `concepts/`는 기여 중 배운 개념을 단일 문서 주제(폴더명 = md 파일명)로 담는다.

## 작성 규칙 (이 폴더의 계약)

- 배포 트리 규칙: 주제(리프) = 하위 폴더 없이 md만 있는 폴더. PR 주제 폴더 안에 하위 폴더를 만들지 않는다. 단일 문서 개념은 `<슬러그>/<슬러그>.md`.
- 폴더명은 영문 슬러그: PR은 `<번호>-<내용-kebab>`, 개념은 내용 kebab.
- 문체는 study-note 작성 방법론(`reference/writing/README.md`)을 따른다: 산문, 절마다 topic sentence, 결론 앞, 표는 고정 차원 비교 + lead-in, 이모지·유니코드 특수기호 금지(ASCII 다이어그램 허용).
- 새 PR마다 표준 5종을 채우고 아래 대장에 한 줄을 더한다.

## PR 대장

| 폴더 | 상태 | 한 줄 주제 |
|---|---|---|
| prs/36911-property-name-resolution | 머지 2026-08-19 (f067d40f0a6, main) | Property 이름 해석 — indexOf가 자른 record 접근자 |
| prs/36912-aot-reserve-method-names | 머지 2026-09-04 (2b5229ff8fa) | AOT 메서드 이름 예약 누락 |
| prs/36913-optional-to-object-converter | 머지 2026-08-20 (7.1.0-M2) | OptionalToObjectConverter canConvert 과대보고 |
| prs/36914-stax-gettextcharacters-offset | 머지 2026-09-04 (2b276311ebe, 7.0.x+main + 테스트 polish) | StAX getTextCharacters의 sourceStart 무시 |
| prs/36915-stax-require-validation | 리뷰 대기 | require()의 네임스페이스·로컬명 검증 누락 |
| prs/36916-async-executor-throttle-permits | 리뷰 대기 | SimpleAsyncTaskExecutor throttle permit 불균형 |
| prs/36917-classfile-array-attributes | 거절 (이후 upstream 자체 수정 7de2b24d81c) | 배열 어트리뷰트 파싱 — 의도 vs 버그 판별 교훈 |
| prs/36919-classfile-method-tostring | 머지 2026-09-03 (ad83d5ebd9e + polish) | ClassFileMethodMetadata 파라미터 타입 렌더링 |
| prs/36932-exponential-backoff-jitter | 머지 (7.0.x+main) | ExponentialBackOff jitter 0 나눗셈 |
| prs/36933-throwaway-classloader-stream-leak | 머지 | ThrowawayClassLoader InputStream 미해제 |
| prs/36938-throwaway-classloader-null-contract | 머지 | ThrowawayClassLoader null 반환 — 클래스로더 계약 |
| prs/36948-doctype-in-comment | 머지 (7.0.x+main) | 여러 줄 주석 안 DOCTYPE 오탐 |
| prs/36965-valuecodegen-nonfinite-doubles | 머지 2026-09-04 (4a803961bc5) | ValueCodeGenerator NaN/Infinity 컴파일 불가 코드 |
| prs/36967-async-executor-flaky-cancel-test | 머지 2026-07-12 (7.0.9) | flaky 취소 테스트 결정론화 |
| prs/36972-native-config-utf8 | 머지 (7.0.x+main) | 네이티브 설정 파일 UTF-8 인코딩 |
| prs/36989-lambda-hints-file-emission | 머지 (7.0.x+main) | lambda 힌트만 있을 때 설정 파일 누락 |
| prs/37008-mimetype-duplicate-parameters | 머지 2026-08-31 (bc6662234) | MIME 파라미터 대소문자 중복 거부 |
| prs/37014-jdbcinsert-generated-key-overlap | 머지 2026-09-07 (e06482ad519 — fail-fast 재작업 후) | 선언·생성 키 겹침 거부 (리뷰로 fail-fast 반전) |
| prs/37053-twobytematcher-state-reset | 머지 (7f1966f5f57, 7.0.x+main) | TwoByteMatcher 부분 일치 상태 미리셋 |
| prs/37082-typevariable-name-fallback | 리뷰 대기 | 타입 변수 이름 폴백의 과잉 매칭 |
| prs/37109-typedescriptor-serialization | 리뷰 대기 | TypeDescriptor 직렬화 회귀 복원 |
| prs/37139-property-setter-prefix | 머지 2026-08-19 (e8e293a7060, 수동 적용) | Property setter 판별 강화 |
| prs/37153-enum-array-annotation-probe | 리뷰 대기 | AttributeMethods enum 배열 probe 누락 |
| prs/37157-nested-annotation-probe | 리뷰 대기 | nested annotation 재귀 probe |
| prs/37186-resolvabletype-generics-serialization | 리뷰 대기 | forClassWithGenerics 직렬화 프록시 |
| prs/37206-callmetadata-return-lookup | 머지 2026-09-03 (ec6b9251916, 7.0.x+main + polish) | 함수 반환 파라미터 조회 정규화 |
| prs/37235-sqlerrorcodes-sort-duplicate-keys | 리뷰 대기 | duplicateKeyCodes 정렬 누락 — binarySearch 전제 |

상태는 2026-09-08 이전 시점 기준이다. 이후 변동은 각 폴더 README와 이 표를 함께 갱신한다.
