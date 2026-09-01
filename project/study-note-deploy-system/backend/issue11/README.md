# issue11 — /api/suggest: 자동완성은 검색과 다른 길로

- 이슈 #22 · PR: #24 (front issue9와 쌍)

## 1. 배경·방식

자동완성의 제1요구는 **지연**(키 입력마다 호출) — 그래서 검색 파이프라인(rewrite→
BM25+kNN→RRF)을 타지 않고 **ES 단독** 별도 경로를 만든다:

```
multi_match(title^3·heading^2·content)      제목 우선, 내용도 잡음
collapse(path)                              문서당 최고 청크 1건 — 같은 문서 도배 방지
highlight(pre/post = ⟦m⟧/⟦/m⟧)              제목 전체 + 내용 90자 조각 1개
```

일치 강조를 HTML이 아닌 마커로 보내는 이유는 front issue9(주입 원천 차단) 참조.

## 2. collapse를 쓴 이유 (대안 비교)

- 대안: size를 키워 받고 backend에서 path별 dedupe — 요청·전송 낭비 + "문서당 최고
  점수 청크" 선택 로직을 직접 짜야 함.
- collapse는 ES가 **keyword 필드 기준 그룹당 최고 히트 1건**을 골라준다 — 우리
  _id 설계(path#chunk_no)와 별개로 path가 keyword 필드라 바로 성립.

## 3. 결론

스모크에서 "정렬" 입력에 portfolio 글(제목 일치)·lsm-tree(내용 일치 스니펫)가 함께
리스트업 — 제목/내용 어느 쪽 일치든 잡힌다는 요구 충족. PR #24
