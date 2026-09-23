# cs/issue/rust/serde/serde-data-model-traps — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[쓰기]  Event::Delta { entries: {1:"a", 2:"b", 10:"c"} }
          └▶ {"event":"Delta","entries":{"1":"a","2":"b","10":"c"}}      ✓ 성공 (u64 키 → 문자열)

[읽기 — 평범한 struct]
   JSON 파서가 키 "1" 을 맵 키 역직렬화기로 직접 전달 → u64 로 파싱   ✓

[읽기 — internally tagged enum]
   ① "event" 태그가 어디 있을지 모름 → 객체 전체를 중간 버퍼(Content)에 적재
      이때 키 "1" 은 그냥 문자열 값으로 저장됨
   ② 태그 확인 후 Content 에서 Delta 를 다시 역직렬화
      Content 의 문자열 키 → u64 요구                                  💥 invalid type: string "1", expected u64

[발견이 늦은 이유]  픽스처에 프롬프트가 없어 entries 가 늘 빈 맵 · 쓰기는 정상이라 생산자 쪽은 멀쩡
[1차 우회의 함정]   BTreeMap<String,_>  → 키 사전순 정렬 "1","10","2"                💥 바이트 순서 변경
[교정]  #[serde(with = "u64_key_map")]
          de: BTreeMap<String,V> 로 받아 key.parse::<u64>() (실패 시 custom 에러)
          ser: collect_map 으로 u64 순회 순서 그대로 방출
        테스트: with 제거 시 즉시 실패 + 방출 순서 고정
```

## 핵심 문장

- internally tagged enum은 태그를 찾으려고 내용을 **중간 버퍼(Content)에 먼저 담는다** — 이 경로에서는 JSON 문자열 키가 숫자 키로 복원되지 않는다.
- 그래서 **쓰기는 성공하고 읽기만 실패**한다 — 생산자 쪽 테스트는 초록불이다.
- 비문자열 키 맵은 **명시 코덱**으로 문자열 키 ↔ 숫자 키를 변환한다.
- 문자열 키 맵으로 우회하면 **정렬 순서가 사전순으로 바뀐다** — "바이트 불변" 주장이 깨진다.
- 픽스처가 빈 컬렉션만 가지면 이 부류의 결함은 **실데이터 스모크**에서야 드러난다.
