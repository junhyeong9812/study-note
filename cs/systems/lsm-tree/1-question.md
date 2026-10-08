# systems/lsm-tree — LSM-Tree와 RUM Conjecture — 질문

## 질문

1. (왜) B-Tree의 삽입이 왜 랜덤 쓰기를 만들고, LSM-Tree는 그 문제를 어떤 한 문장의 발상으로 피하는가?
2. (예측) LSM에서 `id=42`를 수정하고 다시 삭제한 직후, 디스크와 메모리에는 무엇이 남아 있고, 공간은 언제 실제로 회수되는가?
3. (경계) 쓰기가 편해진 대가를 누가 어떻게 치르며, Bloom filter가 답할 수 있는 것과 없는 것은 무엇인가?
4. (왜) Compaction을 "LSM의 GC"라 부르는 이유와, compaction이 순차 I/O인데도 왜 비용으로 취급하는지 설명하라. Leveled와 Size-tiered는 무엇을 맞바꾸는가?
5. (경계) RUM Conjecture로 B-Tree와 LSM-Tree를 비교하고, 어떤 워크로드에 어느 쪽을 고르는지 말하라.
6. (연결) Kafka도 append-only인데 왜 compaction도 Bloom filter도 없는가? LSM에서 무엇을 취하고 무엇을 버렸나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
