# rust/serde — 데이터 모델

serde의 데이터 모델과 enum 표현 방식에서 나오는 패턴이다.\
공통 원리: **직렬화 성공은 역직렬화 성공을 보장하지 않는다** — 왕복(round-trip)으로 확인한다.

## 공통 원리

```
  값 ──serialize (성공)──▶ JSON ──deserialize──▶ ?
                                    │
                                    └─ 태그 탐색용 버퍼링 → 키가 문자열로 바뀜
                                        → 정수 키 맵 실패
```

## 패턴 카드

- [serde-data-model-traps](serde-data-model-traps/) — serde internally-tagged enum은 내용을 문자열 키로 버퍼링해 정수 키 맵 역직렬화가 실패한다(쓰기는 성공) — 비문자열 키 맵은 명시 코덱으로 변환한다.
