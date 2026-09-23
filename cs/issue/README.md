# cs/issue — 실전 이슈에서 뽑은 CS 패턴 아카이브

여러 프로젝트에서 실제로 겪은 이슈를 **원리 단위로 추상화**해 모은 곳이다.\
이슈 하나가 카드 하나가 아니다 — 같은 근본원인·같은 대응을 공유하는 이슈들을 **패턴 카드 하나**로 묶고, 각 사건 유형은 카드 안에서 **추상화 코드**(일반 이름·축약 로직)로 보인다.\
카드에는 출처(프로젝트명·파일·라인)를 적지 않는다 — 문제 코드의 구조 자체가 문서에 드러나므로 그것으로 충분하다.\
현재 카드 154개.

## 분류 두 축

1. **소속(폴더)** — 이슈가 뿌리내린 곳:
   - **언어별** (프레임워크·크레이트는 언어 하위 중첩): `java/` · `kotlin/` · `python/` · `rust/` · `shell/` · `typescript/`
   - **cross-cutting** — 언어 무관 시스템 계층: `concurrency` · `data` · `database` · `distributed` · `document-rendering` · `gui-platform` · `infra` · `network` · `os` · `reliability` · `search-engine` · `security` · `testing`
2. **메타 태그** — 폴더를 가로지르는 반복 주제(각 카드 본문 상단 `태그:`). 12종:

| 태그 | 뜻 | 카드 수 |
|------|----|---------|
| [`silent-failure`](#silent-failure) | 성공 표시 ≠ 산출물 — 실패가 정상처럼 보인다 | 25 |
| [`resource-bounding`](#resource-bounding) | 입력에 비례해 커지는 자원의 상한 | 21 |
| [`least-privilege`](#least-privilege) | 최소 권한·최소 노출·비밀 관리 | 14 |
| [`fail-closed`](#fail-closed) | 판정 불가·조회 실패를 거부로 처리 | 3 |
| [`race-condition`](#race-condition) | 순서·동시성에 따라 결과가 달라짐 | 9 |
| [`contract-drift`](#contract-drift) | 선언한 계약과 실제 동작의 어긋남 | 5 |
| [`test-reliability`](#test-reliability) | 초록불이 결함 유무를 말해 주는가 | 7 |
| [`parser-differential`](#parser-differential) | 검사하는 쪽과 실행하는 쪽의 해석 차이 | 3 |
| [`environment-drift`](#environment-drift) | 실행 환경·채널마다 값·동작이 달라짐 | 3 |
| [`encoding`](#encoding) | 바이트·문자·인코딩 경계 | 3 |
| [`identity`](#identity) | 같은 대상인가 — 식별자·정체성 판정 | 1 |
| [`single-source-of-truth`](#single-source-of-truth) | 같은 사실은 한 곳에서 파생 | 2 |

태그는 선택이다 — 12종 어느 주제에도 해당하지 않는 카드(58개)는 폴더 축으로만 분류한다.

## 포맷

각 패턴 = 폴더 하나(`1-question.md` / `2-summary.md` / `3-answer.md`) — 기존 cs 리프와 같은 인출 퀴즈 방식.\
질문에서 출발해 기억으로 답하고, 막히면 정리(ASCII 흐름도·핵심 문장), 최후에 정답(추상화 코드·방안 비교).\
하위 폴더가 있는 폴더는 `README.md`가 추상화 + 링크 인덱스, 리프(패턴)는 1/2/3.

> **작성 규약 정본**: [authoring-guide.md](authoring-guide.md) — 무엇을 한 카드로 묶나·폴더 분류 2축·파일 형태·서술 규칙(추상화 코드·도식화·출처 금지). 새 패턴을 추가할 땐 이 가이드를 따른다.

## 폴더 트리

숫자 = 그 폴더 아래 패턴 카드 수.

```
cs/issue/  (154)
├─ cross-cutting/               112
│  ├─ concurrency/               10
│  ├─ data/                      18
│  ├─ database/                   3
│  ├─ distributed/                2
│  ├─ document-rendering/         2
│  ├─ gui-platform/               2
│  ├─ infra/                     10
│  ├─ network/                   11
│  ├─ os/                         6
│  ├─ reliability/               23
│  ├─ search-engine/              8
│  ├─ security/                  12
│  └─ testing/                    5
├─ java/                          3
│  ├─ spring/                     1
│  └─ (언어 레벨 카드)            2
├─ kotlin/                        6
│  ├─ spring/                     4
│  └─ (언어 레벨 카드)            2
├─ python/                        6
│  ├─ fastapi/                    4
│  └─ (언어 레벨 카드)            2
├─ rust/                          6
│  ├─ cargo/                      1
│  ├─ serde/                      1
│  ├─ tauri/                      2
│  ├─ tokio/                      1
│  └─ (언어 레벨 카드)            1
├─ shell/                         2
└─ typescript/                   19
   ├─ browser/                    1
   ├─ next/                       4
   ├─ react/                     13
   └─ (언어 레벨 카드)            1
```

## 계층·언어별 카드 목록

### [cross-cutting/](cross-cutting/) — 언어 무관 시스템 패턴

#### [cross-cutting/concurrency/](cross-cutting/concurrency/) — 순서·공유·취소

- [aba-reusable-identifier](cross-cutting/concurrency/aba-reusable-identifier/) — 재사용되는 식별자(pid·세션 id·재시작마다 리셋되는 카운터·txId)로 수명 조작을 키잉하면 늦게 도착한 정리가 같은 이름의 다음 세대를 건드린다 — 세대(epoch)를 포함한 재사용 불가 키를 쓴다.
- [cancellation-reachability](cross-cutting/concurrency/cancellation-reachability/) — 취소 신호를 확인하지 않는 블로킹·await 지점이 하나라도 있으면 취소가 전파되지 않아 스레드·자식 프로세스가 영구 대기로 샌다.
- [capture-context-at-request-time](cross-cutting/concurrency/capture-context-at-request-time/) — 대상·출처·귀속을 실행 시점의 전역 "현재" 상태에서 다시 읽으면 발행~실행 사이 상태 변화에 오염된다 — 요청 시점에 값으로 캡처해 메시지와 함께 운반한다.
- [critical-section-design](cross-cutting/concurrency/critical-section-design/) — 하나의 불변식은 하나의 임계구역에서 원자적으로 갱신하고(check-then-act 금지), 락 안에서는 느린 I/O·join을 하지 않으며, 중복 작업은 single-flight로 합친다.
- [event-loop-head-of-line-blocking](cross-cutting/concurrency/event-loop-head-of-line-blocking/) — 단일 수신 루프에서 처리·송신을 직접 await하면 가장 느린 작업·구독자가 루프 전체를 막아(HOL) 무관한 메시지까지 지연·타임아웃된다.
- [out-of-order-completion](cross-cutting/concurrency/out-of-order-completion/) — 비동기 응답·이벤트의 완료 순서는 발행 순서와 무관하다 — 세대 토큰·CAS·단조 전이로 늦게 도착한 옛 결과가 최신 상태를 덮지 못하게 한다.
- [single-slot-handoff-loss](cross-cutting/concurrency/single-slot-handoff-loss/) — 용량 1 슬롯·전역 요청 버스에 요청을 두면 동시·버스트 생산자가 서로를 덮어 무음 유실된다 — 큐·id 맵·ACK 후 소비·소비자 단일화로 정확히 1회 전달한다.
- [single-writer-ownership](cross-cutting/concurrency/single-writer-ownership/) — 여러 writer가 락 없이 같은 저장 단위를 read-modify-write하면 lost update가 난다 — 저장소를 writer별로 분리하거나 원자 갱신(조건부 UPDATE·upsert·CAS)으로 단일 소유를 강제한다.
- [snapshot-stream-cursor](cross-cutting/concurrency/snapshot-stream-cursor/) — 스냅샷과 라이브 스트림을 이을 때는 먼저 구독하고 원자적 커서(epoch:seq) 이후만 적용해야 무손실·무중복이며, 커서는 짝이 되는 로컬 상태와 함께만 의미가 있다.
- [thread-affine-object-confinement](cross-cutting/concurrency/thread-affine-object-confinement/) — 특정 스레드·이벤트 루프에 묶인 객체는 그 소유자 안에 가두고 외부에는 채널·threadsafe 진입점만 노출한다(actor 패턴).

#### [cross-cutting/data/](cross-cutting/data/) — 값의 표현·해석·키

- [absent-vs-empty](cross-cutting/data/absent-vs-empty/) — "없음(absent)·비어 있음(empty)·손상·기본값·로딩 중·실패"를 같은 값(null·[]·0·"")으로 뭉개면 결함이 정상 데이터로 위장된다 — 상태를 구분해 표현하고 필수 필드는 필수로 받는다.
- [ad-hoc-parsing-of-structured-text](cross-cutting/data/ad-hoc-parsing-of-structured-text/) — 주석·문자열·중첩 괄호처럼 상태가 있는 문법은 정규식·양끝 슬라이스로 파싱할 수 없다 — 틀려도 예외 없이 과대·과소 매칭하므로 상태 기계·실파서를 쓴다.
- [aggregation-semantics](cross-cutting/data/aggregation-semantics/) — 집계는 의미(누적 vs 게이지, DISTINCT의 비가산성, 차원에 맞는 집계 함수)를 맞춰야 한다 — 틀려도 오류 없이 그럴듯한 수치가 나온다.
- [append-only-over-snapshot](cross-cutting/data/append-only-over-snapshot/) — 시간축 없는 현재값을 복사·재전송하는 대신 append-only 이동 기록을 적재하고 소비 단계에서 합산·최신 선택하면 순서·재전송에 무관하게 구성적이다.
- [boundary-arithmetic](cross-cutting/data/boundary-arithmetic/) — 오프셋·길이·0 분모·정수 overflow·비교 경계(==의 방향)·인덱스 좌표계 혼용은 대부분 입력에서 정상이다가 경계에서만 터진다 — 경계 산술을 명시 계산·검증한다.
- [byte-stream-framing](cross-cutting/data/byte-stream-framing/) — 스트림·파일 읽기 경계는 줄·문자·이스케이프 시퀀스 경계와 무관하다 — 완성된 프레임만 디코드하고 상한 절단도 프레임 경계에서 한다.
- [discriminator-not-shape](cross-cutting/data/discriminator-not-shape/) — 다형 레코드는 모양(shape)이 아니라 명시적 판별자(role·type·층)로 해석해야 한다 — 같은 모양의 다른 의미를 오분류한다.
- [float-nan-semantics](cross-cutting/data/float-nan-semantics/) — IEEE-754 NaN은 자기 자신과 같지 않아 전동치(Eq)·== 탐지·리터럴 생성 가정을 깨뜨린다.
- [graph-traversal-invariants](cross-cutting/data/graph-traversal-invariants/) — 외부 데이터로 만든 그래프·트리는 자기참조·사이클·부재 노드가 있을 수 있다 — visited 가드·깊이/개수 예산·레인 중복 방지 없이 순회·배치하면 무한 재귀·오배치가 난다.
- [heuristic-matching-false-positive](cross-cutting/data/heuristic-matching-false-positive/) — 부분 문자열·접두어·이름 관례·부수 신호(ps 출력·포트)로 의미를 추정하는 휴리스틱은 경계가 없어 오탐한다 — 정확 일치·구조적 신호·영속 상태로 판정한다.
- [identifier-ownership-and-scope](cross-cutting/data/identifier-ownership-and-scope/) — 식별자는 유일한 범위(네임스페이스)와 정본·발급 주체가 정해져야 키가 된다 — 외부 규칙 예측·축약·해시·상수 fallback·넓은 키는 충돌·오귀속을 만든다.
- [in-band-signaling-collision](cross-cutting/data/in-band-signaling-collision/) — 구분자·마커·센티널을 데이터와 같은 채널에 두면 데이터에 등장하는 순간 경계·의미가 깨진다 — NUL 구분·이스케이프 왕복 계약·nonce·별도 채널을 쓴다.
- [input-format-detection](cross-cutting/data/input-format-detection/) — 수집·렌더 대상의 형식(RSS vs Atom·구분자·다중값·코드 vs 마크다운)을 가정하지 말고 판정해야 한다 — 틀린 가정은 예외 없이 그럴듯한 잘못된 결과를 낸다.
- [key-normalization-consistency](cross-cutting/data/key-normalization-consistency/) — 검사·저장·조회·조인이 같은 값을 다룰 때 정규화 규칙(대소문자·trim·콜레이션·유니코드 정규형·표기)이 한 곳이라도 다르면 매칭이 조용히 실패하거나 검사가 우회된다.
- [lookup-cost-and-indexing](cross-cutting/data/lookup-cost-and-indexing/) — 조회 비용은 자료구조·인덱스가 결정한다 — 인덱스 없는 조인·upsert·선행 와일드카드·역방향 선형 탐색·해시 군집화는 입력 크기에 따라 O(n²)로 붕괴한다.
- [ordering-total-order](cross-cutting/data/ordering-total-order/) — 결과 순서는 ORDER BY·전순서 키가 없으면 보장되지 않는다(동점·Set 순회·사전식 비교·분할 컷) — 결정성이 필요하면 전순서를 명시한다.
- [pagination-cursor-integrity](cross-cutting/data/pagination-cursor-integrity/) — 커서 페이징은 이어받기 쿼리가 첫 쿼리와 같은 집합을 가리키고 종료·전진이 스캔한 키 윈도우에서 나와야 한다 — 아니면 가지·꼬리가 무음 유실된다.
- [time-semantics](cross-cutting/data/time-semantics/) — 벽시계는 단조 ID가 아니고 날짜는 타임존에 종속되며 구간 경계는 반열린이어야 한다 — 서로 다른 시계·타임존·해상도를 섞으면 조용히 틀린다.

#### [cross-cutting/database/](cross-cutting/database/) — 스키마 이력·방언·트랜잭션

- [migration-discipline](cross-cutting/database/migration-discipline/) — 마이그레이션은 적용된 순간 불변(append-only) 이력이며 순번은 공유 번호공간이다 — 제자리 수정·병렬 브랜치 채번·빌드 산출물 잔존·미생성 리비전이 기동 실패와 누락을 만든다.
- [sql-dialect-and-driver-traps](cross-cutting/database/sql-dialect-and-driver-traps/) — SQL 방언·드라이버·엔진 설정(NULL 유니크·세션 변수·패킷 상한·collation·MDL·SQLite 단일 writer)은 실 DB에서만 드러난다 — 대체 DB·ORM 추정이 아니라 실제 엔진으로 검증한다.
- [transaction-boundary-scope](cross-cutting/database/transaction-boundary-scope/) — 트랜잭션 경계가 곧 원자성 단위다 — 너무 넓으면 한 건 실패가 전부를 되돌리고, 쪼개면 부분 성공이 생기며, 트랜잭션 밖 부수효과(캐시·발행)는 커밋 결과와 따로 논다.

#### [cross-cutting/distributed/](cross-cutting/distributed/) — 원격 결과와 권리의 단조성

- [monotonic-fencing](cross-cutting/distributed/monotonic-fencing/) — 권리(lease·fencing token)의 최고수위는 단조 증가만 해야 하며 검증은 자원(sink) 측에서 단일 시계로 한다 — 유일성 제약은 단조성을 보장하지 않는다.
- [three-state-rpc-outcome](cross-cutting/distributed/three-state-rpc-outcome/) — 원격 호출의 타임아웃·유실은 "실패"가 아니라 "결과 모름"이다 — 미실행 보증·UNKNOWN·성공의 3상태로 다루고 늦은 성공 신호를 버리지 않는다.

#### [cross-cutting/document-rendering/](cross-cutting/document-rendering/) — 텍스트·인쇄 레이아웃

- [cjk-vs-western-text-rules](cross-cutting/document-rendering/cjk-vs-western-text-rules/) — 서구 기준 텍스트 규칙(폰트 메트릭·monospace 폴백·고정폭=1칸·CommonMark 구분자 규칙)은 CJK에서 깨진다 — 한글의 폭·폰트·문장부호 경계를 명시적으로 다룬다.
- [print-layout-traps](cross-cutting/document-rendering/print-layout-traps/) — 문서 레이아웃(인쇄 CSS·HTML 파서 자동 복구·docx/xlsx 기본 크기)은 에러 없이 조용히 무너진다 — 독립적으로 정한 값들의 관계를 명시하고 실물로 확인한다.

#### [cross-cutting/gui-platform/](cross-cutting/gui-platform/) — 좌표계·웹뷰 엔진

- [coordinate-space-consistency](cross-cutting/gui-platform/coordinate-space-consistency/) — 좌표계(논리 px vs 물리 px, 좌표축 부호)를 섞으면 한 지점 보정이 다른 지점의 보상 오류와 충돌한다 — 하나의 좌표계로 통일한 뒤 변환한다.
- [webview-engine-platform-gaps](cross-cutting/gui-platform/webview-engine-platform-gaps/) — 데스크톱 웹뷰 엔진·OS는 크롬이 보장하던 동작(DnD·PDF 뷰어·z-order API·문서 간 드래그)을 보장하지 않는다 — 대상 엔진에서 실측한다.

#### [cross-cutting/infra/](cross-cutting/infra/) — 플랫폼·툴·배포

- [bottleneck-identification](cross-cutting/infra/bottleneck-identification/) — 처리량 설정(병렬도·스레드풀·힙)은 실제 병목(디스크 IOPS·코어·요청 지연)에 상대적이다 — 병목을 실측하지 않고 늘리거나 이식하면 경합·기동 실패가 난다.
- [compose-variable-resolution-timing](cross-cutting/infra/compose-variable-resolution-timing/) — compose의 변수·설정은 파싱 채널과 런타임 채널, 명령별 로드 범위가 다르다 — 값이 어느 채널로 누구에게 도달하는지 확인해야 한다.
- [dependency-and-toolchain-compat](cross-cutting/infra/dependency-and-toolchain-compat/) — 의존성·툴체인은 선언·버전·런타임 호환(JDK·Node·Docker API·shade·peer deps·전이 의존)이 맞아야 동작한다 — 게시된 메타데이터·실제 해석 트리·대상 런타임으로 확인한다.
- [effective-uid-file-access](cross-cutting/infra/effective-uid-file-access/) — 파일 접근 권한은 실제로 여는 주체(컨테이너 uid·리다이렉트를 여는 셸·기동 시 확정된 보조 그룹)의 것이다 — "존재"가 아니라 그 주체의 읽기·쓰기 가능성으로 판단한다.
- [firewall-and-network-policy-layers](cross-cutting/infra/firewall-and-network-policy-layers/) — 패킷 필터·MAC·클라우드 보안목록·Docker 체인은 계층마다 따로 동작한다 — 한 계층(ufw)의 설정이 다른 계층(Docker publish·SELinux)을 보장하지 않는다.
- [git-pitfalls](cross-cutting/infra/git-pitfalls/) — git은 인덱스·ref·시퀀서 상태·출력 인용·소유권·ignore 규칙을 암묵 입력으로 쓰므로, 이름에서 떠올리는 직관과 실제 정의가 다른 지점을 명시적으로 다뤄야 한다.
- [llm-serving-vram-and-backend](cross-cutting/infra/llm-serving-vram-and-backend/) — LLM 서빙은 VRAM 예산(가중치+KV cache×동시 시퀀스)과 GPU 아키텍처별 백엔드 지원이 결정한다 — 기동 성공은 추론 성공을 보장하지 않는다.
- [nginx-broadband-defense-friendly-fire](cross-cutting/infra/nginx-broadband-defense-friendly-fire/) — 출처를 구분하지 않는 광역 방어(UA 차단·단일 버킷 레이트리밋)는 자기 자동화·검증 트래픽·정상 사용자를 오사한다 — allowlist·정확한 키로 범위를 좁힌다.
- [path-derived-key-on-move](cross-cutting/infra/path-derived-key-on-move/) — 가변 속성(절대 경로)에서 파생한 키·캐시는 폴더 이동 순간 고아가 된다 — 이동은 키 재계산·캐시 무효화를 동반해야 한다.
- [state-drift-delete-propagation](cross-cutting/infra/state-drift-delete-propagation/) — 같은 사실의 사본(설정·배포본·파생 상태·인덱스)은 삭제·변경이 전파되지 않으면 원본과 어긋난다 — 정본 단일 채널과 명시적 삭제(tombstone)로 수렴시킨다.

#### [cross-cutting/network/](cross-cutting/network/) — 프로토콜·연결·프록시

- [api-contract-evolution](cross-cutting/network/api-contract-evolution/) — 광고한 capability·버전·문서 보장은 실제 구현과 일치해야 하고, 계약 변경은 소비자·제공자의 배포 순서와 함께 진화해야 한다 — 상대 구현은 소스·스모크로만 확정한다.
- [bind-address-loopback-vs-lan](cross-cutting/network/bind-address-loopback-vs-lan/) — 바인드 주소(loopback vs LAN/wildcard)와 헬스체크·프로브가 보는 주소·도구가 어긋나면 정상 서비스가 unhealthy·접속 불가로 보인다.
- [chunked-vs-content-length](cross-cutting/network/chunked-vs-content-length/) — chunked 전송과 Content-Length 기대가 어긋나면 본문이 0바이트·절단된다 — 송수신 양쪽의 길이 채널을 맞춰야 한다.
- [container-network-addressing](cross-cutting/network/container-network-addressing/) — 컨테이너 네트워크에서 127.0.0.1은 자기 자신이고 호스트 매핑 포트·docker0·내장 DNS·광고 주소는 네트워크 범위에 따라 다르다 — 목적지 주소를 같은 네트워크 기준으로 정한다.
- [half-open-liveness-watchdog](cross-cutting/network/half-open-liveness-watchdog/) — 출력 전용·장기 스트리밍 연결은 상대가 사라져도 TCP 에러가 오지 않는다 — liveness는 앱이 의미 단위(완성 프레임·하트비트) 도착 시각으로 판정한다.
- [http-cache-policy](cross-cutting/network/http-cache-policy/) — immutable·장기 캐시는 콘텐츠 주소화된 URL에만 쓰고, 상태 엔드포인트·버전 없는 정적 자원에는 캐시 정책을 명시해야 배포와 클라이언트가 어긋나지 않는다.
- [http-streaming-status-locked](cross-cutting/network/http-streaming-status-locked/) — 응답 헤더가 커밋되는 순간 status는 확정되므로, 최종 상태를 보려면 커밋 이후가 아니라 가장 바깥 계층에서 확정 시점을 기준으로 관측해야 한다.
- [payload-transfer-cost](cross-cutting/network/payload-transfer-cost/) — 전송 비용은 크기×빈도다 — 바뀌지 않는 대형 본문을 매 틱 재전송하거나 필터 없이 통째로 반환하면 메모리·지연이 누적되므로 메타만 싣고 본문은 요청 시 회수한다.
- [proxy-passthrough](cross-cutting/network/proxy-passthrough/) — 프록시·BFF 계층마다 헤더(XFF·쿠키·prefix·상관 ID)·status·스트림을 명시적으로 왕복시켜야 하며, 전달받은 헤더는 신뢰 홉 기준으로만 믿는다.
- [reverse-tunnel-nat-traversal](cross-cutting/network/reverse-tunnel-nat-traversal/) — NAT·서브넷 단절로 inbound가 불가하면 연결 방향을 역전(outbound 유지형 역터널·브로커)한다.
- [uri-encoding-rules](cross-cutting/network/uri-encoding-rules/) — URI는 ASCII와 예약문자 규칙을 따른다 — 비ASCII·경로 속 슬래시·표준 Base64·이중 인코딩은 도구·컨테이너마다 다르게 처리되므로 경계에서 올바르게 인코딩한다.

#### [cross-cutting/os/](cross-cutting/os/) — 프로세스·경로·터미널

- [execution-context-inheritance](cross-cutting/os/execution-context-inheritance/) — 자식 프로세스·서비스·훅은 실행 방식(셸·GUI 런처·systemd·영속 cd·플랫폼 주입)에 따라 env·PATH·cwd·TERM을 다르게 물려받는다 — 필요한 실행 문맥을 명시적으로 결정·정화한다.
- [os-api-limits-and-semantics](cross-cutting/os/os-api-limits-and-semantics/) — OS API에는 고정 한계와 미정의 동작(UDS 경로 108바이트·소유하지 않은 디렉토리 chmod·순회 중 수정)이 있다 — 설계 전에 전제를 확인한다.
- [path-canonical-identity](cross-cutting/os/path-canonical-identity/) — 같은 파일을 가리키는 경로 표기는 여러 개다(`./`·구분자·대소문자·빈 문자열=cwd) — 비교·키·잠금 전에 모든 진입점이 같은 정규형을 거쳐야 한다.
- [process-group-and-tree-termination](cross-cutting/os/process-group-and-tree-termination/) — 부모만 죽이면 손자·다른 세션 자식은 고아로 남고, `pgrep/pkill -f`는 자기 명령줄도 매칭하며, SIGHUP·SIGKILL은 정리 경로를 건너뛴다 — 프로세스 그룹·신원 단위로 종료한다.
- [pty-semantics](cross-cutting/os/pty-semantics/) — PTY에 쓴 바이트는 수신 TUI의 현재 모드(raw·canonical·bracketed paste)로 해석된다 — CR≠LF, write 성공≠전달, EIO=EOF를 명시적으로 다룬다.
- [subprocess-lifecycle-and-pipes](cross-cutting/os/subprocess-lifecycle-and-pipes/) — spawn한 자식은 wait로 회수하고, 파이프는 양쪽 모두 드레인하며, stdio 프로토콜은 순수해야 하고 stdin은 닫아야 한다 — 아니면 좀비·교착·영구 대기가 된다.

#### [cross-cutting/reliability/](cross-cutting/reliability/) — 실패가 삼켜지는 곳

- [atomic-file-replace](cross-cutting/reliability/atomic-file-replace/) — 덮어쓰기는 원자적이지 않다 — 같은 파일시스템의 유니크 temp에 완성한 뒤 rename으로 게시하고(디렉토리는 displaced rename+복원), 교체 창의 동시 writer·옛 fd·내구성(fsync)까지 다룬다.
- [change-detection-key-design](cross-cutting/reliability/change-detection-key-design/) — 변경 감지·캐시 키는 결과에 영향을 주는 입력 전부를 반영해야 하고(mtime·길이·합산값은 불완전), 잠금·정체성 키에는 가변값을 넣지 않는다 — 한쪽이면 갱신 누락, 반대면 무한 루프.
- [cleanup-on-every-exit-path](cross-cutting/reliability/cleanup-on-every-exit-path/) — 종료 경로가 여럿이면 경로마다 정리를 흩어 두지 말고 스코프 소멸(RAII·try/finally·trap)에 묶어 모든 경로(에러·취소·spawn 실패·예외)에서 정확히 한 번 해제한다.
- [closed-state-model](cross-cutting/reliability/closed-state-model/) — 상태 공간을 타입·전이 규칙으로 닫아라 — 불법 상태·누락된 조합·종단 재전이·검사 없는 set·비단조 guard는 오보고와 교착을 만든다.
- [debounce-trailing-contract](cross-cutting/reliability/debounce-trailing-contract/) — 디바운스·보류 전송은 "마지막 변경 뒤 반드시 한 번 더"와 종결 이벤트와의 순서라는 새 계약을 만든다 — 지키지 못하면 마지막 변경이 무음 유실되거나 순서가 뒤집힌다.
- [derived-cache-staleness](cross-cutting/reliability/derived-cache-staleness/) — 파생 캐시·사본·비동기 로그는 원본보다 늦으며 실패 결과를 캐시하면 일시 장애가 영구화된다 — 완결성·최신성이 필요한 판정은 정본(이벤트 페이로드·원본)을 직접 읽는다.
- [deserialization-trust-boundary](cross-cutting/reliability/deserialization-trust-boundary/) — 역직렬화 경계에서 타입 보장이 끊긴다 — 영속·외부 데이터는 로드 시 검증·정규화하고, 부분 손상은 격리하되 드롭은 관측하며, 모르는 값·깊이 공격·스키마 진화를 명시 처리한다.
- [edge-detection-on-raw-signals](cross-cutting/reliability/edge-detection-on-raw-signals/) — 여러 신호를 스칼라로 접거나 매 tick 덮어쓰거나 주기 샘플링하면 사건(edge)이 사라진다 — 기저 신호별 edge 판정·래치·세대 ID·지속 조건으로 감지한다.
- [event-before-subscriber-loss](cross-cutting/reliability/event-before-subscriber-loss/) — 보관·replay가 없는 이벤트 채널(pub/sub·fire-and-forget)에서는 구독 완료 전·구독자 부재 중 발생한 사건이 영구히 사라진다 — 구독 먼저·backfill·내구성 있는 스트림을 쓴다.
- [fail-closed-guard](cross-cutting/reliability/fail-closed-guard/) — 안전 판정에서 "모름·조회 실패·설정 누락·default 분기"를 통과로 삼키면 장애가 곧 우회가 된다 — 판정 불가는 거부하고, 허용은 양성 증명(allowlist)으로만 부여하며, 폴백은 특정 오류에만 건다.
- [idempotent-retry-design](cross-cutting/reliability/idempotent-retry-design/) — 재시도·재처리 가능한 연산은 멱등으로 설계하고(at-least-once+멱등 키), 진행 표지(워터마크)는 전량 성공 후에만 전진시켜 재시도가 자동 복구 루프가 되게 한다.
- [lifecycle-signal-contract](cross-cutting/reliability/lifecycle-signal-contract/) — 준비·완료·종결 신호는 부수 사건(첫 출력·EOF·started·무활동 시간)에서 추론하지 말고 명시적 계약으로 모든 경로에서 정확히 한 번 보낸다.
- [non-transactional-multi-step](cross-cutting/reliability/non-transactional-multi-step/) — 트랜잭션 없는 다단계 변경은 순서로 실패를 격리한다 — 새것 확보·성공 확인 뒤에 파괴하고, 실패 가능한 쪽을 먼저 하며, 중간 잔해는 보상·회수한다.
- [process-memory-scope](cross-cutting/reliability/process-memory-scope/) — 프로세스 메모리 상태(세션 저장소·in-flight future·락)는 재시작·다중 워커·스케일아웃 경계를 넘지 못한다 — 수명·공유 범위가 필요한 상태는 영속·공유 저장소에 둔다.
- [reference-graph-not-text](cross-cutting/reliability/reference-graph-not-text/) — 삭제·이동 범위는 이름·문자열 치환이 아니라 실제 참조 그래프(컴파일러·빈 이름·FQCN·문자열 참조 전수)로 결정한다.
- [resource-bounding-last-defense](cross-cutting/reliability/resource-bounding-last-defense/) — 클라이언트 타임아웃·취소는 서버측 작업을 멈추지 못하므로, 외부 입력에 비례해 커지는 자원(메모리·큐·연결·시간)은 서버 쪽 상한이 최후 방어선이다.
- [retry-policy-design](cross-cutting/reliability/retry-policy-design/) — 재시도는 실패를 영구/일시로 정확히 분류해야 한다 — 영구 실패·poison 메시지를 재시도하면 무한 루프·아군 차단이 되고, 백오프는 실패 시점 기준이어야 한다.
- [self-feedback-loop](cross-cutting/reliability/self-feedback-loop/) — 처리기가 자기 입력 공간에 산출물을 남기거나(부산물 재처리), 측정 대상이 측정 결과로 바뀌거나, 브로드캐스트가 보낸 쪽에도 돌아오면 양의 피드백 루프가 생긴다.
- [shutdown-backstop-independence](cross-cutting/reliability/shutdown-backstop-independence/) — 종료 경로는 정상 정리(unmount·close 이벤트·이벤트 루프)를 보장받지 못한다 — 최후 백스톱은 고장 지점과 독립된 층에 best-effort·비블로킹으로 둔다.
- [sibling-path-invariant-drift](cross-cutting/reliability/sibling-path-invariant-drift/) — 같은 불변식을 지켜야 하는 형제 경로(분기·setter·오버로드·모듈 N벌 복사본·포팅 원본) 중 하나만 가드가 빠지는 비대칭이 결함이 된다 — 형제 전수를 대조한다.
- [silent-failure-vs-artifact](cross-cutting/reliability/silent-failure-vs-artifact/) — 성공 로그·exit 0·2xx·"완료" 표시는 산출물이 아니다 — 성공은 실제 산출물(저장소·파일·화면·행 수)로 검증해야 한다.
- [silent-truncation-marker](cross-cutting/reliability/silent-truncation-marker/) — 상한·예산·링버퍼로 자른 결과를 완전한 결과와 같은 모양으로 반환하면 호출자는 절단을 모른다 — 절단 표식을 동반하고, 절단은 표시 경계에서만 하며, 단계 간 상한을 정렬한다.
- [value-binding-time](cross-cutting/reliability/value-binding-time/) — 값은 해석·고정되는 시점(빌드·import·컨테이너 생성·프로세스 기동·작업 생성)에 박제된다 — 이후 변경은 그 시점을 다시 거치지 않으면 반영되지 않는다.

#### [cross-cutting/search-engine/](cross-cutting/search-engine/) — 색인·쿼리·점수

- [cluster-ops-traps](cross-cutting/search-engine/cluster-ops-traps/) — 검색엔진 클러스터는 운영 조건(디스크 워터마크 read-only·단일 노드 replica·세그먼트 병합·alias 이름공간·라이선스 게이팅)에 따라 조용히 다른 모드로 들어간다.
- [document-model-quirks](cross-cutting/search-engine/document-model-quirks/) — ES 문서 모델(메타필드 `_id`·nested 숨은 문서·missing의 빈 문자열·스크립트의 값 부재·`_id` last-write-wins)은 일반 JSON 직관과 다르다.
- [mapping-is-schema](cross-cutting/search-engine/mapping-is-schema/) — 검색 인덱스 매핑은 생성 시점에 고정되는 스키마다 — 제자리 변경·소급 적용이 안 되므로 정의 단일화·명시 매핑·재색인+alias 스왑으로 관리한다.
- [multilingual-analysis-chain](cross-cutting/search-engine/multilingual-analysis-chain/) — 분석기 체인은 순서가 있는 파이프라인이고 문자체계마다 토큰화 전제가 다르다 — 필터 순서·비대상 스크립트 fallback·혼합 입력을 명시 처리한다.
- [query-and-index-cost-limits](cross-cutting/search-engine/query-and-index-cost-limits/) — 엔진 상한(절 수·max_expansions·circuit breaker·bulk 큐·힙)과 변형 폭증(cartesian)은 쿼리·색인 비용을 입력 분포에 따라 폭발시킨다 — 조합·요청 크기에 상한을 둔다.
- [query-index-representation-mismatch](cross-cutting/search-engine/query-index-representation-mismatch/) — 쿼리가 인덱스의 실제 표현(분석 여부·search_analyzer·normalizer·필드 존재·index:false·nested)과 어긋나면 ES는 에러 없이 0건·오매칭을 낸다 — 색인측과 질의측 변환을 대칭으로 맞추고 매핑과 대조한다.
- [query-matching-breadth](cross-cutting/search-engine/query-matching-breadth/) — full-text match의 토큰 OR·토큰별 fuzzy·ngram 부분문자열·위치 정보 없는 자질 합집합은 매칭을 과도하게 넓힌다 — 쿼리 종류와 토큰화 단위를 의도에 맞춘다.
- [score-semantics-and-composition](cross-cutting/search-engine/score-semantics-and-composition/) — 점수는 상대값이다 — should 합산·TF 누적·길이 정규화·근사(PQ) 점수에 고정 임계를 걸면 순위·재현율이 조용히 왜곡된다.

#### [cross-cutting/security/](cross-cutting/security/) — 비밀·권한·신뢰 경계

- [authorization-freshness-binding](cross-cutting/security/authorization-freshness-binding/) — 인증·승인 신호는 "지금 이 행위"에 결속돼야 한다 — 서명은 신선도가 아니고, 신선도가 다른 소스를 OR로 합치면 과거 승인이 현재를 통과시키며, stateless 토큰은 명시 폐기해야 한다.
- [authorization-gate-placement](cross-cutting/security/authorization-gate-placement/) — 인가는 모든 경로가 지나는 단일 지점에서, 부작용 이전에, 런타임이 보증하는 신원으로 판정해야 한다 — 클라이언트 주장·두 번째 입력 경로·앞단 필터의 조기 확정은 우회를 만든다.
- [browser-credential-policy](cross-cutting/security/browser-credential-policy/) — 브라우저 자격(쿠키) 정책 — 자동 첨부되는 쿠키 인증은 CSRF 방어가 필요하고, `*`+credentials CORS는 금지되며, Secure 쿠키는 HTTPS에서만 전송된다.
- [complete-mediation](cross-cutting/security/complete-mediation/) — 강제 지점이 쓰기·원격 변경 경로 일부(특정 API·명령 이름)에만 있으면 같은 효과를 내는 다른 경로가 보호 밖에 남는다(complete mediation 위반).
- [data-interpreted-as-syntax](cross-cutting/security/data-interpreted-as-syntax/) — 데이터가 하위 인터프리터(argv 옵션·pathspec·셸·SQL·LIKE·템플릿·eval·로그 줄)의 문법으로 해석되면 인젝션이 된다 — 옵션 종결자·바인딩·리터럴 모드·화이트리스트로 데이터 채널을 분리한다.
- [local-endpoint-hardening](cross-cutting/security/local-endpoint-hardening/) — 루프백·유닉스 소켓 바인드만으로는 같은 호스트의 다른 프로세스·브라우저 오리진을 막지 못한다 — 로컬 끝점도 인증·Origin 검증·입력 검증·자원 상한이 필요하다.
- [regex-is-not-a-shell-parser](cross-cutting/security/regex-is-not-a-shell-parser/) — 셸 명령·자연어를 문자열 패턴으로 검사하면 셸의 실제 토큰화·리다이렉트·경로 해석과 desync된다 — 우회(false-allow)와 오탐(false-block)이 동시에 생기므로 보안 경계는 구조화된 신호로 세운다.
- [searchable-encryption-blind-index](cross-cutting/security/searchable-encryption-blind-index/) — salt·IV를 쓰는 가역 암호화는 의도적으로 비결정적이라 동등 조회가 불가하다 — 조회용 키는 비밀 키 기반 HMAC 결정적 해시 컬럼으로 분리한다.
- [secret-ownership-least-privilege](cross-cutting/security/secret-ownership-least-privilege/) — 비밀은 단일 소유·정본은 실사용처·최소 노출 경로여야 한다 — argv·URL·로그·git 히스토리·예시 파일·평문 사본처럼 지우기 어려운 곳으로 새지 않게 한다.
- [symlink-following-escape](cross-cutting/security/symlink-following-escape/) — 검사와 사용의 링크 추종 의미가 다르면(exists vs open, 최종 성분만 검사, 폴백 copy) 심볼릭 링크로 경계를 탈출한다 — lstat·전체 경로 resolve·생성/읽기 모든 분기에 같은 링크 정책.
- [trust-on-first-use](cross-cutting/security/trust-on-first-use/) — 호스트 신뢰는 일치·불일치·미지 세 상태이며, 신뢰 결정의 영속·판독이 실패하면 신뢰로 진행하지 않는다(fail-closed TOFU).
- [verify-what-you-use](cross-cutting/security/verify-what-you-use/) — 검증한 것과 사용하는 것이 같은 객체·같은 해석이어야 한다 — 정규화·파서 차이, 문자열 vs 실제 전송 hop, 재열람 TOCTOU, 승인 표시 vs 실제 대상이 어긋나면 검증이 무의미해진다.

#### [cross-cutting/testing/](cross-cutting/testing/) — 초록불의 증거력

- [green-masking](cross-cutting/testing/green-masking/) — 초록불은 테스트가 실패할 수 있었을 때만 증거다 — 무단언·약한 단언·수집 누락·캐시된 결과·표현 못 하는 픽스처·버그를 고정한 기대값은 결함을 통과시키므로 뮤테이션·대조군으로 이빨을 확인한다.
- [performance-measurement-validity](cross-cutting/testing/performance-measurement-validity/) — 측정값이 유효하려면 생존자 편향·JIT 워밍업·수렴 전 캐시·생성기 자체의 자원 한계·데이터 부재를 배제해야 한다.
- [test-isolation-and-determinism](cross-cutting/testing/test-isolation-and-determinism/) — 테스트 결과가 코드가 아니라 환경(공유 상태 디렉토리·재사용 컨테이너·시드 상수·스레드 스케줄링)에 좌우되지 않게 격리하고 happens-before를 보장한다.
- [test-tool-default-semantics](cross-cutting/testing/test-tool-default-semantics/) — 테스트 도구의 기본 의미(비선점 타임아웃·중첩 클래스 섀도잉·mock 패치 경로·호이스팅·lifespan 미실행·로거 비활성화)는 직관과 달라 테스트가 소실·무한 대기·무효화된다.
- [verification-environment-parity](cross-cutting/testing/verification-environment-parity/) — 검증 환경(헤드리스 모드·jsdom·H2·standalone MockMvc·빌드 스테이지·curl)이 실행 환경을 재현하지 않으면 테스트는 결함 유무와 무관한 결과를 낸다 — 실제 경로·실 DB로 검증한다.

### [java/](java/) — Java 언어·JVM·Spring

- [language-semantics-traps](java/language-semantics-traps/) — Java 언어 규칙(Error≠Exception·정적 초기화 순서·제네릭 불변성·소거·오버로드 모호성·주석 렉싱·인자 평가 순서)이 직관과 달라 컴파일은 통과하고 런타임에서 틀린다.
- [serializable-capture-contract](java/serializable-capture-contract/) — Serializable을 선언한 객체·람다가 비직렬화 객체(리플렉션 타입·TypeVariable)를 캡처하면 직렬화 계약이 조용히 깨진다.

#### [java/spring/](java/spring/) — Spring·JPA 기본 동작

- [framework-default-contracts](java/spring/framework-default-contracts/) — Spring·JPA의 기본 동작(프록시 self-invocation·자동설정 back-off·빈 이름 파생·정적 전체 UPDATE·save=merge·필터 자동등록·조건 평가 순서)은 명시하지 않으면 조용히 다르게 동작한다.

### [kotlin/](kotlin/) — Kotlin/JVM·Spring

- [charset-and-length-defaults](kotlin/charset-and-length-defaults/) — 언어·런타임·클라이언트의 기본 인코딩과 길이 단위(바이트·UTF-16 코드유닛·코드포인트)가 값을 조용히 왜곡한다 — charset과 길이 단위를 명시한다.
- [language-semantics-traps](kotlin/language-semantics-traps/) — Kotlin 언어 규칙(블록 주석 중첩·backtick 식별자 제약·배열 참조 동등성·코루틴 취소 예외)이 Java 직관과 달라 컴파일 오류·취소 파괴를 만든다.

#### [kotlin/spring/](kotlin/spring/) — Spring·Jackson·아키텍처

- [dip-port-ownership](kotlin/spring/dip-port-ownership/) — 도메인이 포트를 소유하고(DIP) 모듈 의존 방향을 지키며, 리팩토링은 특성 테스트 안전망 위에서 한다.
- [graceful-degradation-fault-isolation](kotlin/spring/graceful-degradation-fault-isolation/) — 보조 기능(헬스 집계·통계·네이티브 라이브러리)의 장애가 핵심 경로를 인질로 잡지 못하게 격리·강등한다.
- [path-traversal-and-data-reality](kotlin/spring/path-traversal-and-data-reality/) — 외부 입력을 경로로 결합하면 트래버설로 경계를 벗어난다(검증은 canonical 경로·단일 검증 함수로) — 그리고 버그의 절반은 코드가 아니라 데이터 실태다.
- [serialization-contract-leak](kotlin/spring/serialization-contract-leak/) — 내부 필드명·네이밍 전략·디버그 표현이 직렬화를 통해 외부 계약이 된다 — 와이어 이름을 명시 매핑하고 양쪽 실제 직렬화 결과로 교차 검증한다.

### [python/](python/) — Python 언어·FastAPI

- [language-and-stdlib-traps](python/language-and-stdlib-traps/) — Python 언어·표준 라이브러리 규칙(bool⊂int·`"" in s`·except 중 traceback 프레임 보유·import 시점 바인딩·truthiness·csv 필드 상한·버퍼링)이 직관과 달라 드문 경로에서만 터진다.
- [module-resolution-and-accidental-pass](python/module-resolution-and-accidental-pass/) — 실행 경로(pytest vs python -m, 클래스패스 순서, import 시점 부작용)에 따라 모듈 해석이 갈려 초록불이 우연히 켜지거나 꺼진다.

#### [python/fastapi/](python/fastapi/) — 실행 모델·응답 경계

- [handler-execution-model](python/fastapi/handler-execution-model/) — FastAPI에서 `def`는 스레드풀 병렬, `async def`는 이벤트 루프 단일 스레드에서 실행되고 미들웨어는 LIFO다 — 실행 모델에 맞춰 동기 I/O·check-then-act·요청 스코프를 배치한다.
- [response-normalization-framework-boundary](python/fastapi/response-normalization-framework-boundary/) — 프레임워크가 핸들러 밖에서 만드는 응답(검증 오류·필터 예외·미처리 예외)이 계약의 구멍이다 — 구체 예외 타입별 핸들러로 봉투를 정규화한다.
- [websocket-api-contract](python/fastapi/websocket-api-contract/) — Starlette/FastAPI WebSocket은 타입 특화 수신·타입 힌트 DI·비이터레이터 프로토콜이라 다른 라이브러리 관용구가 그대로 통하지 않는다(TestClient는 이 경로를 우회).
- [yagni-dead-contract](python/fastapi/yagni-dead-contract/) — 예측으로 예약한 계약은 유지비만 든다 — YAGNI로 제거하고 결정 흔적만 남긴다.

### [rust/](rust/) — Rust 언어·크레이트 생태계

- [language-semantics-traps](rust/language-semantics-traps/) — Rust 표준 동작(랜덤 시드 해셔·debug panic/release wrap·eager `or`·임시값 수명의 MutexGuard·take 1회 취득)이 직관과 달라 영속 키·교착·오버플로를 만든다.

#### [rust/cargo/](rust/cargo/) — 크레이트·모듈 경계

- [crate-module-boundary-rules](rust/cargo/crate-module-boundary-rules/) — Rust 빌드 단위 경계(링크 의존 크레이트의 헤드리스 테스트 불가·extern prelude 이름 충돌·module privacy)는 코드 구조를 강제하므로 순수 core 분리·이름 회피로 대응한다.

#### [rust/serde/](rust/serde/) — 데이터 모델

- [serde-data-model-traps](rust/serde/serde-data-model-traps/) — serde internally-tagged enum은 내용을 문자열 키로 버퍼링해 정수 키 맵 역직렬화가 실패한다(쓰기는 성공) — 비문자열 키 맵은 명시 코덱으로 변환한다.

#### [rust/tauri/](rust/tauri/) — 커맨드 경계·등록

- [command-boundary-execution-model](rust/tauri/command-boundary-execution-model/) — Tauri 동기 커맨드는 메인(UI) 스레드에서 실행되고 커맨드 경계의 panic은 구조화된 에러가 되지 않는다 — 블로킹은 async·별도 스레드로, 실패는 Result로 전파한다.
- [registration-mismatch-runtime-failure](rust/tauri/registration-mismatch-runtime-failure/) — 정적 capability ACL·TypeId 키 DI처럼 "선언과 사용의 불일치"는 컴파일·테스트를 통과하고 런타임에만 조용히 throw한다 — 선언을 사용처와 함께 검증한다.

#### [rust/tokio/](rust/tokio/) — 비동기 런타임

- [select-loop-semantics](rust/tokio/select-loop-semantics/) — tokio `select!`는 분기 본문의 await 동안 다른 분기를 poll하지 않고 닫힌 채널은 영원히 준비 상태이며 런타임 드라이버는 명시적으로 켜야 한다 — 읽기·쓰기를 독립 future로 분리하고 종료 조건을 모든 분기에서 처리한다.

### [shell/](shell/) — 셸 스크립트

- [exit-status-semantics](shell/exit-status-semantics/) — 파이프라인·그룹 리다이렉트·`&&`의 종료 코드는 마지막 명령의 것이고 errexit·명령별 비0 의미(grep 1·iconv)가 계약을 흔든다 — pipefail과 단계별 rc를 명시한다.
- [quoting-expansion-layers](shell/quoting-expansion-layers/) — 셸은 텍스트를 인용·확장·word-split·glob·heredoc 계층마다 다시 해석한다 — 중첩 인용·dotenv source·빈 매칭 glob·heredoc 종료 태그가 의도와 다른 명령을 만든다.

### [typescript/](typescript/) — TS/JS·브라우저·React·Next

- [js-language-traps](typescript/js-language-traps/) — JS 언어 규칙(TDZ·객체 리터럴 즉시 평가·중복 키 무음 덮어쓰기·try 안 await 없는 return·구조화 에러의 String 변환)이 직관과 달라 조용히 오동작한다.

#### [typescript/browser/](typescript/browser/) — 브라우저 입력

- [input-event-model](typescript/browser/input-event-model/) — 브라우저 입력 이벤트(IME 조합·키 전파·포커스 소유·DnD 생명주기)는 라이브러리 "처리됨" 반환·단일 이벤트 가정과 다르게 흐른다 — 조합 중 값 덮어쓰기 금지·전파 차단·창 단위 백스톱.

#### [typescript/next/](typescript/next/) — BFF·라우팅·모듈 해석

- [absolute-imports-and-per-tool-resolver](typescript/next/absolute-imports-and-per-tool-resolver/) — 상대 경로·모듈 해석은 파일 위치·도구(번들러·테스트 러너·로더)마다 기준이 달라 이동·도구 교체에 깨진다 — 절대 경로 정책과 도구별 리졸버 설정을 맞춘다.
- [bff-envelope-single-gate](typescript/next/bff-envelope-single-gate/) — 응답 봉투·래핑 검사를 소비처마다 하면 누락돼 오류가 정상 데이터(빈 배열)로 렌더된다 — 형태 변환·검증 책임을 한 계층(BFF)으로 모은다.
- [single-source-of-truth-routing](typescript/next/single-source-of-truth-routing/) — 같은 사실(판정식·파이프라인·상태·변환 코드)을 두 곳에서 따로 관리·계산하면 반드시 어긋난다 — 단일 출처에서 파생시킨다.
- [ssr-hydration-parity](typescript/next/ssr-hydration-parity/) — 하이드레이션 첫 렌더는 서버 HTML과 같아야 한다 — 브라우저 전용 값·HTML 파서가 재구성하는 중첩 위반은 불일치를 만든다.

#### [typescript/react/](typescript/react/) — 렌더링·상태·CSS

- [async-subscription-cleanup](typescript/react/async-subscription-cleanup/) — 해제 핸들이 비동기로 도착하는 구독은 cleanup 시점에 핸들이 없을 수 있다 — disposed·세대 플래그로 도착 즉시 해제하고 등록 실패도 처리한다.
- [css-containing-context](typescript/react/css-containing-context/) — 요소의 크기·스크롤·클리핑·위치는 조상 컨텍스트(flex min-size·overflow·containing block·stacking·container query·cascade)가 결정한다 — 문제의 소유 조상을 찾아 고친다.
- [css-negative-margin-overflow](typescript/react/css-negative-margin-overflow/) — 부모 패딩을 상쇄하는 음수 마진·overflow 클리핑 경계가 여백 소유권과 어긋나면 가로 스크롤·이웃 노출이 생긴다 — 여백 소유권을 한쪽에 둔다.
- [dependent-state-reset](typescript/react/dependent-state-reset/) — 상위 데이터·컨텍스트가 바뀌면 거기서 파생된 종속 상태(선택·스크롤 앵커·실패 표시·기본 선택)를 재검증·리셋해야 유령 참조가 되지 않는다.
- [effect-dependency-and-timing](typescript/react/effect-dependency-and-timing/) — effect는 커밋 후 deps 값 동등성으로만 재실행된다 — 의도(정체성·액션)를 deps에 담고, 렌더에서 파생 가능한 상태를 effect로 동기화하지 않는다.
- [instance-scope-of-global-state](typescript/react/instance-scope-of-global-state/) — "전역 = 내 것" 가정(모듈 싱글턴·전역 버스·DOM id·창별 스토어·SSR 모듈 상태)은 인스턴스·창·요청이 둘이 되는 순간 누출된다 — 상태를 인스턴스 스코프로 내린다.
- [remount-lifecycle-state-loss](typescript/react/remount-lifecycle-state-loss/) — 가시성 전환·조건부 래퍼·DOM 재생성은 곧 리마운트다 — 컴포넌트에 둔 상태·구독·포커스 대상은 사라지므로 수명이 긴 상태는 밖에 두고 명시적으로 정리한다.
- [render-and-subscription-cost](typescript/react/render-and-subscription-cost/) — 렌더·구독 비용이 전체 데이터 크기×갱신 빈도에 비례하지 않게 한다 — 가상화·셀렉터·참조 동일성 유지·메모로 비용을 뷰포트·변경분에 묶는다.
- [separation-structure-vs-style](typescript/react/separation-structure-vs-style/) — 렌더러는 구조만, 표시는 CSS가 맡아야 한다(관심사 분리).
- [stale-render-state](typescript/react/stale-render-state/) — 핸들러·클로저는 생성 시점 렌더의 state 스냅샷을 본다 — 같은 틱의 연속 이벤트·async 콜백은 가변 ref로 최신 값을 읽어야 한다.
- [theming-token-reach](typescript/react/theming-token-reach/) — CSS 변수 테마는 우리 DOM 캐스케이드에만 닿는다 — canvas·JS 위젯·네이티브 컨트롤은 각자 API로 주입하고, 한 시각 단위의 색은 모두 같은 토큰에서 파생한다.
- [tree-position-semantics](typescript/react/tree-position-semantics/) — React는 DOM이 아니라 컴포넌트 트리 위치로 인스턴스 동일성·Context 공급·합성 이벤트 전파를 결정한다(포털 포함) — DOM 기반 판정과의 어긋남을 명시 처리한다.
- [xss-escape-then-assemble](typescript/react/xss-escape-then-assemble/) — 신뢰 불가 텍스트를 HTML·스크립트 위치에 삽입하면 XSS가 된다 — 전체를 이스케이프(또는 데이터 채널·sanitizer)한 뒤 필요한 마커만 조립한다.

## 태그 역인덱스

태그 → 그 태그가 붙은 카드. 폴더가 달라도 같은 반복 주제를 한 번에 훑을 때 쓴다.

### silent-failure

성공 표시 ≠ 산출물 — 실패가 정상처럼 보인다 — 25개

- [single-slot-handoff-loss](cross-cutting/concurrency/single-slot-handoff-loss/) · `cross-cutting/concurrency`
- [absent-vs-empty](cross-cutting/data/absent-vs-empty/) · `cross-cutting/data`
- [ad-hoc-parsing-of-structured-text](cross-cutting/data/ad-hoc-parsing-of-structured-text/) · `cross-cutting/data`
- [aggregation-semantics](cross-cutting/data/aggregation-semantics/) · `cross-cutting/data`
- [in-band-signaling-collision](cross-cutting/data/in-band-signaling-collision/) · `cross-cutting/data`
- [input-format-detection](cross-cutting/data/input-format-detection/) · `cross-cutting/data`
- [key-normalization-consistency](cross-cutting/data/key-normalization-consistency/) · `cross-cutting/data`
- [pagination-cursor-integrity](cross-cutting/data/pagination-cursor-integrity/) · `cross-cutting/data`
- [print-layout-traps](cross-cutting/document-rendering/print-layout-traps/) · `cross-cutting/document-rendering`
- [state-drift-delete-propagation](cross-cutting/infra/state-drift-delete-propagation/) · `cross-cutting/infra`
- [chunked-vs-content-length](cross-cutting/network/chunked-vs-content-length/) · `cross-cutting/network`
- [half-open-liveness-watchdog](cross-cutting/network/half-open-liveness-watchdog/) · `cross-cutting/network`
- [http-streaming-status-locked](cross-cutting/network/http-streaming-status-locked/) · `cross-cutting/network`
- [pty-semantics](cross-cutting/os/pty-semantics/) · `cross-cutting/os`
- [change-detection-key-design](cross-cutting/reliability/change-detection-key-design/) · `cross-cutting/reliability`
- [debounce-trailing-contract](cross-cutting/reliability/debounce-trailing-contract/) · `cross-cutting/reliability`
- [deserialization-trust-boundary](cross-cutting/reliability/deserialization-trust-boundary/) · `cross-cutting/reliability`
- [event-before-subscriber-loss](cross-cutting/reliability/event-before-subscriber-loss/) · `cross-cutting/reliability`
- [lifecycle-signal-contract](cross-cutting/reliability/lifecycle-signal-contract/) · `cross-cutting/reliability`
- [silent-failure-vs-artifact](cross-cutting/reliability/silent-failure-vs-artifact/) · `cross-cutting/reliability`
- [silent-truncation-marker](cross-cutting/reliability/silent-truncation-marker/) · `cross-cutting/reliability`
- [query-index-representation-mismatch](cross-cutting/search-engine/query-index-representation-mismatch/) · `cross-cutting/search-engine`
- [registration-mismatch-runtime-failure](rust/tauri/registration-mismatch-runtime-failure/) · `rust/tauri`
- [exit-status-semantics](shell/exit-status-semantics/) · `shell`
- [bff-envelope-single-gate](typescript/next/bff-envelope-single-gate/) · `typescript/next`

### resource-bounding

입력에 비례해 커지는 자원의 상한 — 21개

- [cancellation-reachability](cross-cutting/concurrency/cancellation-reachability/) · `cross-cutting/concurrency`
- [event-loop-head-of-line-blocking](cross-cutting/concurrency/event-loop-head-of-line-blocking/) · `cross-cutting/concurrency`
- [byte-stream-framing](cross-cutting/data/byte-stream-framing/) · `cross-cutting/data`
- [graph-traversal-invariants](cross-cutting/data/graph-traversal-invariants/) · `cross-cutting/data`
- [lookup-cost-and-indexing](cross-cutting/data/lookup-cost-and-indexing/) · `cross-cutting/data`
- [bottleneck-identification](cross-cutting/infra/bottleneck-identification/) · `cross-cutting/infra`
- [llm-serving-vram-and-backend](cross-cutting/infra/llm-serving-vram-and-backend/) · `cross-cutting/infra`
- [payload-transfer-cost](cross-cutting/network/payload-transfer-cost/) · `cross-cutting/network`
- [process-group-and-tree-termination](cross-cutting/os/process-group-and-tree-termination/) · `cross-cutting/os`
- [subprocess-lifecycle-and-pipes](cross-cutting/os/subprocess-lifecycle-and-pipes/) · `cross-cutting/os`
- [cleanup-on-every-exit-path](cross-cutting/reliability/cleanup-on-every-exit-path/) · `cross-cutting/reliability`
- [resource-bounding-last-defense](cross-cutting/reliability/resource-bounding-last-defense/) · `cross-cutting/reliability`
- [retry-policy-design](cross-cutting/reliability/retry-policy-design/) · `cross-cutting/reliability`
- [self-feedback-loop](cross-cutting/reliability/self-feedback-loop/) · `cross-cutting/reliability`
- [shutdown-backstop-independence](cross-cutting/reliability/shutdown-backstop-independence/) · `cross-cutting/reliability`
- [query-and-index-cost-limits](cross-cutting/search-engine/query-and-index-cost-limits/) · `cross-cutting/search-engine`
- [handler-execution-model](python/fastapi/handler-execution-model/) · `python/fastapi`
- [command-boundary-execution-model](rust/tauri/command-boundary-execution-model/) · `rust/tauri`
- [select-loop-semantics](rust/tokio/select-loop-semantics/) · `rust/tokio`
- [async-subscription-cleanup](typescript/react/async-subscription-cleanup/) · `typescript/react`
- [render-and-subscription-cost](typescript/react/render-and-subscription-cost/) · `typescript/react`

### least-privilege

최소 권한·최소 노출·비밀 관리 — 14개

- [effective-uid-file-access](cross-cutting/infra/effective-uid-file-access/) · `cross-cutting/infra`
- [firewall-and-network-policy-layers](cross-cutting/infra/firewall-and-network-policy-layers/) · `cross-cutting/infra`
- [proxy-passthrough](cross-cutting/network/proxy-passthrough/) · `cross-cutting/network`
- [authorization-freshness-binding](cross-cutting/security/authorization-freshness-binding/) · `cross-cutting/security`
- [authorization-gate-placement](cross-cutting/security/authorization-gate-placement/) · `cross-cutting/security`
- [browser-credential-policy](cross-cutting/security/browser-credential-policy/) · `cross-cutting/security`
- [complete-mediation](cross-cutting/security/complete-mediation/) · `cross-cutting/security`
- [data-interpreted-as-syntax](cross-cutting/security/data-interpreted-as-syntax/) · `cross-cutting/security`
- [local-endpoint-hardening](cross-cutting/security/local-endpoint-hardening/) · `cross-cutting/security`
- [searchable-encryption-blind-index](cross-cutting/security/searchable-encryption-blind-index/) · `cross-cutting/security`
- [secret-ownership-least-privilege](cross-cutting/security/secret-ownership-least-privilege/) · `cross-cutting/security`
- [symlink-following-escape](cross-cutting/security/symlink-following-escape/) · `cross-cutting/security`
- [path-traversal-and-data-reality](kotlin/spring/path-traversal-and-data-reality/) · `kotlin/spring`
- [xss-escape-then-assemble](typescript/react/xss-escape-then-assemble/) · `typescript/react`

### fail-closed

판정 불가·조회 실패를 거부로 처리 — 3개

- [bind-address-loopback-vs-lan](cross-cutting/network/bind-address-loopback-vs-lan/) · `cross-cutting/network`
- [fail-closed-guard](cross-cutting/reliability/fail-closed-guard/) · `cross-cutting/reliability`
- [trust-on-first-use](cross-cutting/security/trust-on-first-use/) · `cross-cutting/security`

### race-condition

순서·동시성에 따라 결과가 달라짐 — 9개

- [aba-reusable-identifier](cross-cutting/concurrency/aba-reusable-identifier/) · `cross-cutting/concurrency`
- [capture-context-at-request-time](cross-cutting/concurrency/capture-context-at-request-time/) · `cross-cutting/concurrency`
- [critical-section-design](cross-cutting/concurrency/critical-section-design/) · `cross-cutting/concurrency`
- [out-of-order-completion](cross-cutting/concurrency/out-of-order-completion/) · `cross-cutting/concurrency`
- [single-writer-ownership](cross-cutting/concurrency/single-writer-ownership/) · `cross-cutting/concurrency`
- [snapshot-stream-cursor](cross-cutting/concurrency/snapshot-stream-cursor/) · `cross-cutting/concurrency`
- [thread-affine-object-confinement](cross-cutting/concurrency/thread-affine-object-confinement/) · `cross-cutting/concurrency`
- [monotonic-fencing](cross-cutting/distributed/monotonic-fencing/) · `cross-cutting/distributed`
- [stale-render-state](typescript/react/stale-render-state/) · `typescript/react`

### contract-drift

선언한 계약과 실제 동작의 어긋남 — 5개

- [api-contract-evolution](cross-cutting/network/api-contract-evolution/) · `cross-cutting/network`
- [serializable-capture-contract](java/serializable-capture-contract/) · `java`
- [serialization-contract-leak](kotlin/spring/serialization-contract-leak/) · `kotlin/spring`
- [response-normalization-framework-boundary](python/fastapi/response-normalization-framework-boundary/) · `python/fastapi`
- [websocket-api-contract](python/fastapi/websocket-api-contract/) · `python/fastapi`

### test-reliability

초록불이 결함 유무를 말해 주는가 — 7개

- [green-masking](cross-cutting/testing/green-masking/) · `cross-cutting/testing`
- [performance-measurement-validity](cross-cutting/testing/performance-measurement-validity/) · `cross-cutting/testing`
- [test-isolation-and-determinism](cross-cutting/testing/test-isolation-and-determinism/) · `cross-cutting/testing`
- [test-tool-default-semantics](cross-cutting/testing/test-tool-default-semantics/) · `cross-cutting/testing`
- [verification-environment-parity](cross-cutting/testing/verification-environment-parity/) · `cross-cutting/testing`
- [module-resolution-and-accidental-pass](python/module-resolution-and-accidental-pass/) · `python`
- [tree-position-semantics](typescript/react/tree-position-semantics/) · `typescript/react`

### parser-differential

검사하는 쪽과 실행하는 쪽의 해석 차이 — 3개

- [regex-is-not-a-shell-parser](cross-cutting/security/regex-is-not-a-shell-parser/) · `cross-cutting/security`
- [verify-what-you-use](cross-cutting/security/verify-what-you-use/) · `cross-cutting/security`
- [quoting-expansion-layers](shell/quoting-expansion-layers/) · `shell`

### environment-drift

실행 환경·채널마다 값·동작이 달라짐 — 3개

- [compose-variable-resolution-timing](cross-cutting/infra/compose-variable-resolution-timing/) · `cross-cutting/infra`
- [execution-context-inheritance](cross-cutting/os/execution-context-inheritance/) · `cross-cutting/os`
- [value-binding-time](cross-cutting/reliability/value-binding-time/) · `cross-cutting/reliability`

### encoding

바이트·문자·인코딩 경계 — 3개

- [cjk-vs-western-text-rules](cross-cutting/document-rendering/cjk-vs-western-text-rules/) · `cross-cutting/document-rendering`
- [uri-encoding-rules](cross-cutting/network/uri-encoding-rules/) · `cross-cutting/network`
- [charset-and-length-defaults](kotlin/charset-and-length-defaults/) · `kotlin`

### identity

같은 대상인가 — 식별자·정체성 판정 — 1개

- [identifier-ownership-and-scope](cross-cutting/data/identifier-ownership-and-scope/) · `cross-cutting/data`

### single-source-of-truth

같은 사실은 한 곳에서 파생 — 2개

- [single-source-of-truth-routing](typescript/next/single-source-of-truth-routing/) · `typescript/next`
- [theming-token-reach](typescript/react/theming-token-reach/) · `typescript/react`
