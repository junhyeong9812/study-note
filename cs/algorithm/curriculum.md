# 알고리즘 — `cs/algorithm/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §3에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 12 · 원고 있음 1 · 초안(Claude) 30 · 검수 완료 0

> **번호 = 권장 학습 순서**(2026-09-28 재번호). 기존 노트 폴더(`algorithm/01~30`)는 원래 번호 그대로 — 노트 링크 칸이 대응. 🔧 칸 = "쓰이는 곳".

## 3.0 기초 (2026-09-28 — 기초판은 독립 leaf, 심화 leaf가 선행으로 링크)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `algorithm-basics` | 알고리즘 기초판 — 빅오·분할 상환, 선형/이진 탐색, 버블·퀵 정렬을 한 편에 | 필수 | 원고 있음 | [../foundations/algorithm-basics](../foundations/algorithm-basics/) |

## 3.1 분석·기초

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 02 | `asymptotic-analysis` | 빅오·최악/평균·분할상환 | 필수 | 미작성 | — |
| 03 | `recursion` | 재귀 = 귀납의 코드. 기저·축소·꼬리 재귀 | 필수 | 미작성 | — |

## 3.2 정렬·탐색

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `binary-search` | 불변식으로 구간 절반 | 필수 | 초안(Claude) | [06-binary-search](06-binary-search/) |
| 05 | `elementary-sort` | 선택·삽입·버블 | 필수 | 초안(Claude) | [01-elementary-sort](01-elementary-sort/) |
| 06 | `merge-sort` | 분할정복·안정 정렬 | 필수 | 초안(Claude) | [02-merge-sort](02-merge-sort/) |
| 07 | `quick-sort` | 분할·피벗 | 필수 | 초안(Claude) | [03-quick-sort](03-quick-sort/) |
| 08 | `heap-sort` | 제자리 O(n log n) | 권장 | 초안(Claude) | [04-heap-sort](04-heap-sort/) |
| 09 | `sorting-in-practice` | 안정성·비교자 계약·TimSort·다중 키 | 필수 | 미작성 | — |
| 10 | `non-comparison-sort` | 계수·기수 정렬 | 권장 | 초안(Claude) | [05-non-comparison-sort](05-non-comparison-sort/) |
| 11 | `external-sort-and-k-way-merge` | 메모리보다 큰 데이터 정렬, k-way 병합 | 권장 | 미작성 | — |
| 12 | `hash-functions` | 좋은 해시의 조건·유니버설 해싱·SipHash, 암호/비암호 구분 | 권장 | 미작성 | — |

## 3.3 기법

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 13 | `prefix-sum` | 누적합으로 구간 합 O(1) | 필수 | 초안(Claude) | [10-prefix-sum](10-prefix-sum/) |
| 14 | `two-pointers` | 정렬 전제 양 끝 수렴 | 필수 | 초안(Claude) | [08-two-pointers](08-two-pointers/) |
| 15 | `sliding-window` | 고정/가변 창 | 필수 | 초안(Claude) | [09-sliding-window](09-sliding-window/) |
| 16 | `parametric-search` | 최적화 → 결정 문제 + 이진 탐색 | 권장 | 초안(Claude) | [07-parametric-search](07-parametric-search/) |
| 23 | `greedy` | 국소 최적 선택과 교환 논증 | 필수 | 초안(Claude) | [23-greedy](23-greedy/) |
| 24 | `divide-conquer` | 분할정복·마스터 정리 | 필수 | 초안(Claude) | [24-divide-conquer](24-divide-conquer/) |
| 25 | `dp-basics` | 최적 부분 구조 + 중복 부분 문제 | 필수 | 초안(Claude) | [21-dp-basics](21-dp-basics/) |
| 26 | `dp-advanced` | 비트마스크·구간·트리 DP | 심화 | 초안(Claude) | [22-dp-advanced](22-dp-advanced/) |
| 27 | `backtracking` | 가지치기 전수 탐색 | 권장 | 초안(Claude) | [13-backtracking](13-backtracking/) |
| 32 | `bit-manipulation` | 비트 트릭·마스크 | 권장 | 초안(Claude) | [29-bit-manipulation](29-bit-manipulation/) |
| 38 | `sweeping` | 이벤트 정렬 후 스윕 | 심화 | 초안(Claude) | [30-sweeping](30-sweeping/) |

## 3.4 그래프

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 17 | `bfs` | 레벨 순회·최단 홉 | 필수 | 초안(Claude) | [11-bfs](11-bfs/) |
| 18 | `dfs` | 깊이 순회·색칠·위상정렬 | 필수 | 초안(Claude) | [12-dfs](12-dfs/) |
| 19 | `dijkstra` | 음이 아닌 가중치 최단 경로 | 필수 | 초안(Claude) | [14-dijkstra](14-dijkstra/) |
| 20 | `bellman-floyd` | 벨만-포드·플로이드 | 권장 | 초안(Claude) | [15-bellman-floyd](15-bellman-floyd/) |
| 21 | `scc` | 강연결요소(Tarjan·Kosaraju) | 권장 | 초안(Claude) | [18-scc](18-scc/) |
| 22 | `mst` | 크루스칼·프림 | 권장 | 초안(Claude) | [17-mst](17-mst/) |
| 35 | `euler-path` | 모든 간선 한 번 | 심화 | 초안(Claude) | [16-euler-path](16-euler-path/) |
| 36 | `network-flow` | 최대 유량·이분 매칭 | 심화 | 초안(Claude) | [19-network-flow](19-network-flow/) |
| 37 | `a-star` | 휴리스틱 최단 경로 | 심화 | 초안(Claude) | [20-a-star](20-a-star/) |

## 3.5 문자열·수론

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 28 | `string-matching` | KMP 실패 함수 | 권장 | 초안(Claude) | [25-string-matching](25-string-matching/) |
| 29 | `string-hashing` | 롤링 해시(Rabin-Karp) | 권장 | 초안(Claude) | [27-string-hashing](27-string-hashing/) |
| 30 | `aho-corasick` | 다중 패턴 오토마톤 | 심화 | 초안(Claude) | [26-aho-corasick](26-aho-corasick/) |
| 31 | `number-theory` | 소수·GCD·모듈러 역원 | 권장 | 초안(Claude) | [28-number-theory](28-number-theory/) |

## 3.6 확률·계산 이론

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 39 | `randomized-algorithms` | 라스베이거스·몬테카를로, 기대 복잡도 | 심화 | 미작성 | — |
| 40 | `complexity-p-np` | P·NP·NP완전·환원·근사 | 권장 | 미작성 | — |
| 41 | `computability-and-halting` | 정지 문제·라이스 정리 | 심화 | 미작성 | — |

## 3.6b 압축 알고리즘 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 33 | `lossless-compression-lz77-huffman` | LZ77(슬라이딩 윈도 역참조) + 허프만 부호 = DEFLATE, 압축 한계 | 필수 | 미작성 | — |
| 34 | `modern-codecs-lz4-zstd-brotli` | 속도↔비율 절충, 딕셔너리 압축, 엔트로피 부호(ANS/FSE), 프레임·스트리밍 압축 | 권장 | 미작성 | — |

## 3.7 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 42 | `alg-symptom-index` | 역색인: 데이터 늘자 타임아웃(복잡도), 정렬 계약 예외, 재귀 스택 오버플로, 정규식 CPU 100%, 이진 탐색 무한 루프 | 필수 | 미작성 | — |
| 43 | `alg-incidents` | 실사건: JDK 이진 탐색 오버플로(Bloch 2006) · Stack Overflow 정규식 장애(2016-07-20) · Cloudflare WAF 정규식 백트래킹 전역 CPU 100%(2019-07-02) | 권장 | 미작성 | — |
