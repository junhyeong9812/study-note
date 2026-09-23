# data — 값의 표현·해석·키

데이터 값이 저장·전달·비교·집계될 때 의미가 조용히 바뀌는 패턴이다.\
공통 원리: **표현(null·구분자·키·시간·순서)의 의미를 명시하지 않으면, 틀린 결과가 예외 없이 그럴듯한 값으로 나온다.**\
경계 입력(빈 값·중복·구분자 포함·타임존·동점)에서만 드러나므로 정상 경로 테스트로는 잡히지 않는다.

## 공통 원리

```
  입력 값 ──▶ 표현 ──▶ 비교·조인·집계·정렬 ──▶ 결과
              │
              ├─ absent = empty = 0        → 결함이 정상으로 위장
              ├─ 구분자·마커가 데이터에 등장 → 경계 붕괴
              ├─ 정규화 규칙이 지점마다 다름 → 매칭 실패
              └─ 전순서·타임존 미명시        → 비결정·어긋난 날짜
                              ▼
                  에러 없음 + 그럴듯한 오답
```

## 패턴 카드

- [absent-vs-empty](absent-vs-empty/) — "없음(absent)·비어 있음(empty)·손상·기본값·로딩 중·실패"를 같은 값(null·[]·0·"")으로 뭉개면 결함이 정상 데이터로 위장된다 — 상태를 구분해 표현하고 필수 필드는 필수로 받는다.
- [ad-hoc-parsing-of-structured-text](ad-hoc-parsing-of-structured-text/) — 주석·문자열·중첩 괄호처럼 상태가 있는 문법은 정규식·양끝 슬라이스로 파싱할 수 없다 — 틀려도 예외 없이 과대·과소 매칭하므로 상태 기계·실파서를 쓴다.
- [aggregation-semantics](aggregation-semantics/) — 집계는 의미(누적 vs 게이지, DISTINCT의 비가산성, 차원에 맞는 집계 함수)를 맞춰야 한다 — 틀려도 오류 없이 그럴듯한 수치가 나온다.
- [append-only-over-snapshot](append-only-over-snapshot/) — 시간축 없는 현재값을 복사·재전송하는 대신 append-only 이동 기록을 적재하고 소비 단계에서 합산·최신 선택하면 순서·재전송에 무관하게 구성적이다.
- [boundary-arithmetic](boundary-arithmetic/) — 오프셋·길이·0 분모·정수 overflow·비교 경계(==의 방향)·인덱스 좌표계 혼용은 대부분 입력에서 정상이다가 경계에서만 터진다 — 경계 산술을 명시 계산·검증한다.
- [byte-stream-framing](byte-stream-framing/) — 스트림·파일 읽기 경계는 줄·문자·이스케이프 시퀀스 경계와 무관하다 — 완성된 프레임만 디코드하고 상한 절단도 프레임 경계에서 한다.
- [discriminator-not-shape](discriminator-not-shape/) — 다형 레코드는 모양(shape)이 아니라 명시적 판별자(role·type·층)로 해석해야 한다 — 같은 모양의 다른 의미를 오분류한다.
- [float-nan-semantics](float-nan-semantics/) — IEEE-754 NaN은 자기 자신과 같지 않아 전동치(Eq)·== 탐지·리터럴 생성 가정을 깨뜨린다.
- [graph-traversal-invariants](graph-traversal-invariants/) — 외부 데이터로 만든 그래프·트리는 자기참조·사이클·부재 노드가 있을 수 있다 — visited 가드·깊이/개수 예산·레인 중복 방지 없이 순회·배치하면 무한 재귀·오배치가 난다.
- [heuristic-matching-false-positive](heuristic-matching-false-positive/) — 부분 문자열·접두어·이름 관례·부수 신호(ps 출력·포트)로 의미를 추정하는 휴리스틱은 경계가 없어 오탐한다 — 정확 일치·구조적 신호·영속 상태로 판정한다.
- [identifier-ownership-and-scope](identifier-ownership-and-scope/) — 식별자는 유일한 범위(네임스페이스)와 정본·발급 주체가 정해져야 키가 된다 — 외부 규칙 예측·축약·해시·상수 fallback·넓은 키는 충돌·오귀속을 만든다.
- [in-band-signaling-collision](in-band-signaling-collision/) — 구분자·마커·센티널을 데이터와 같은 채널에 두면 데이터에 등장하는 순간 경계·의미가 깨진다 — NUL 구분·이스케이프 왕복 계약·nonce·별도 채널을 쓴다.
- [input-format-detection](input-format-detection/) — 수집·렌더 대상의 형식(RSS vs Atom·구분자·다중값·코드 vs 마크다운)을 가정하지 말고 판정해야 한다 — 틀린 가정은 예외 없이 그럴듯한 잘못된 결과를 낸다.
- [key-normalization-consistency](key-normalization-consistency/) — 검사·저장·조회·조인이 같은 값을 다룰 때 정규화 규칙(대소문자·trim·콜레이션·유니코드 정규형·표기)이 한 곳이라도 다르면 매칭이 조용히 실패하거나 검사가 우회된다.
- [lookup-cost-and-indexing](lookup-cost-and-indexing/) — 조회 비용은 자료구조·인덱스가 결정한다 — 인덱스 없는 조인·upsert·선행 와일드카드·역방향 선형 탐색·해시 군집화는 입력 크기에 따라 O(n²)로 붕괴한다.
- [ordering-total-order](ordering-total-order/) — 결과 순서는 ORDER BY·전순서 키가 없으면 보장되지 않는다(동점·Set 순회·사전식 비교·분할 컷) — 결정성이 필요하면 전순서를 명시한다.
- [pagination-cursor-integrity](pagination-cursor-integrity/) — 커서 페이징은 이어받기 쿼리가 첫 쿼리와 같은 집합을 가리키고 종료·전진이 스캔한 키 윈도우에서 나와야 한다 — 아니면 가지·꼬리가 무음 유실된다.
- [time-semantics](time-semantics/) — 벽시계는 단조 ID가 아니고 날짜는 타임존에 종속되며 구간 경계는 반열린이어야 한다 — 서로 다른 시계·타임존·해상도를 섞으면 조용히 틀린다.

> 이 폴더의 메타 태그: `silent-failure`(7) · `resource-bounding`(3) · `identity`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
