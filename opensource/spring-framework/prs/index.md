# prs 인덱스

PR별 주제 폴더 목록이다. 상태는 2026-09-08 이전 시점 기준이며 갱신은 각 폴더 README와 상위 README 대장에서 한다.

| 주제 | 상태 | 한 줄 주제 |
|------|------|------|
| [36911-property-name-resolution](36911-property-name-resolution/) | 머지 2026-08-19 (f067d40f0a6, main) | Property 이름 해석 — indexOf가 자른 record 접근자 |
| [36912-aot-reserve-method-names](36912-aot-reserve-method-names/) | 머지 2026-09-04 (2b5229ff8fa) | AOT 메서드 이름 예약 누락 |
| [36913-optional-to-object-converter](36913-optional-to-object-converter/) | 머지 2026-08-20 (7.1.0-M2) | OptionalToObjectConverter canConvert 과대보고 |
| [36914-stax-gettextcharacters-offset](36914-stax-gettextcharacters-offset/) | 머지 2026-09-04 (2b276311ebe, 7.0.x+main + 테스트 polish) | StAX getTextCharacters의 sourceStart 무시 |
| [36915-stax-require-validation](36915-stax-require-validation/) | 리뷰 대기 | require()의 네임스페이스·로컬명 검증 누락 |
| [36916-async-executor-throttle-permits](36916-async-executor-throttle-permits/) | 리뷰 대기 | SimpleAsyncTaskExecutor throttle permit 불균형 |
| [36917-classfile-array-attributes](36917-classfile-array-attributes/) | 거절 (이후 upstream 자체 수정 7de2b24d81c) | 배열 어트리뷰트 파싱 — 의도 vs 버그 판별 교훈 |
| [36919-classfile-method-tostring](36919-classfile-method-tostring/) | 머지 2026-09-03 (ad83d5ebd9e + polish) | ClassFileMethodMetadata 파라미터 타입 렌더링 |
| [36932-exponential-backoff-jitter](36932-exponential-backoff-jitter/) | 머지 (7.0.x+main) | ExponentialBackOff jitter 0 나눗셈 |
| [36933-throwaway-classloader-stream-leak](36933-throwaway-classloader-stream-leak/) | 머지 | ThrowawayClassLoader InputStream 미해제 |
| [36938-throwaway-classloader-null-contract](36938-throwaway-classloader-null-contract/) | 머지 | ThrowawayClassLoader null 반환 — 클래스로더 계약 |
| [36948-doctype-in-comment](36948-doctype-in-comment/) | 머지 (7.0.x+main) | 여러 줄 주석 안 DOCTYPE 오탐 |
| [36965-valuecodegen-nonfinite-doubles](36965-valuecodegen-nonfinite-doubles/) | 머지 2026-09-04 (4a803961bc5) | ValueCodeGenerator NaN/Infinity 컴파일 불가 코드 |
| [36967-async-executor-flaky-cancel-test](36967-async-executor-flaky-cancel-test/) | 머지 2026-07-12 (7.0.9) | flaky 취소 테스트 결정론화 |
| [36972-native-config-utf8](36972-native-config-utf8/) | 머지 (7.0.x+main) | 네이티브 설정 파일 UTF-8 인코딩 |
| [36989-lambda-hints-file-emission](36989-lambda-hints-file-emission/) | 머지 (7.0.x+main) | lambda 힌트만 있을 때 설정 파일 누락 |
| [37008-mimetype-duplicate-parameters](37008-mimetype-duplicate-parameters/) | 머지 2026-08-31 (bc6662234) | MIME 파라미터 대소문자 중복 거부 |
| [37014-jdbcinsert-generated-key-overlap](37014-jdbcinsert-generated-key-overlap/) | 머지 2026-09-07 (e06482ad519 — fail-fast 재작업 후) | 선언·생성 키 겹침 거부 (리뷰로 fail-fast 반전) |
| [37053-twobytematcher-state-reset](37053-twobytematcher-state-reset/) | 머지 (7f1966f5f57, 7.0.x+main) | TwoByteMatcher 부분 일치 상태 미리셋 |
| [37082-typevariable-name-fallback](37082-typevariable-name-fallback/) | 리뷰 대기 | 타입 변수 이름 폴백의 과잉 매칭 |
| [37109-typedescriptor-serialization](37109-typedescriptor-serialization/) | 리뷰 대기 | TypeDescriptor 직렬화 회귀 복원 |
| [37139-property-setter-prefix](37139-property-setter-prefix/) | 머지 2026-08-19 (e8e293a7060, 수동 적용) | Property setter 판별 강화 |
| [37153-enum-array-annotation-probe](37153-enum-array-annotation-probe/) | 리뷰 대기 | AttributeMethods enum 배열 probe 누락 |
| [37157-nested-annotation-probe](37157-nested-annotation-probe/) | 리뷰 대기 | nested annotation 재귀 probe |
| [37186-resolvabletype-generics-serialization](37186-resolvabletype-generics-serialization/) | 리뷰 대기 | forClassWithGenerics 직렬화 프록시 |
| [37206-callmetadata-return-lookup](37206-callmetadata-return-lookup/) | 머지 2026-09-03 (ec6b9251916, 7.0.x+main + polish) | 함수 반환 파라미터 조회 정규화 |
| [37235-sqlerrorcodes-sort-duplicate-keys](37235-sqlerrorcodes-sort-duplicate-keys/) | 리뷰 대기 | duplicateKeyCodes 정렬 누락 — binarySearch 전제 |
| [37259-mutiny-uni-empty-value](37259-mutiny-uni-empty-value/) | 리뷰 대기 | Mutiny Uni empty-value가 완료하지 않는 Uni - 응답 행 |
| [37268-lru-cache-double-decrement](37268-lru-cache-double-decrement/) | 리뷰 대기 | ConcurrentLruCache 이중 size 감산 - capacity 영구 초과 |
