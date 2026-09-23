# cs/issue/rust/serde/serde-data-model-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **역직렬화가 실패한다: `invalid type: string "1", expected u64`.** 직렬화는 `u64` 키를 JSON 객체 키(문자열 `"1"`)로 바꿔 멀쩡히 쓴다. 그러나 읽을 때는 그 문자열 키를 `u64`로 되돌리지 못한다. 실제로 프롬프트가 한 번이라도 있던 세션은 전부 디코딩에 실패했다. 쓰는 쪽(데몬)은 정상으로 보이고 읽는 쪽(클라이언트)만 깨졌다.

2. **internally tagged enum은 태그를 찾기 위해 내용을 먼저 버퍼링하기 때문이다.** `#[serde(tag = "event")]`는 태그가 객체의 어느 위치에 있어도 되게 하려고, 역직렬화 시 객체 전체를 serde의 중간 표현(`Content`)에 먼저 담는다. 그 다음 태그를 보고 알맞은 variant로 **Content에서 다시** 역직렬화한다. 첫 단계에서 JSON 객체 키 `"1"`은 이미 "문자열 값"으로 고정되어 저장되고, 두 번째 단계의 Content 역직렬화기는 그 문자열을 `u64` 키로 파싱해 주지 않는다. 평범한 struct는 이 버퍼링을 거치지 않아 문제가 없다(오래 알려진 serde 제약이며, untagged·flatten처럼 Content 버퍼를 거치는 다른 표현에도 같은 문제가 있다 — 세부 동작은 serde 버전에 따라 확인).
   > **internally tagged 표현** — enum의 variant 이름을 내용 객체 안의 한 필드(`{"event":"Delta", ...}`)로 넣는 serde 표현 방식. 태그 위치가 고정되지 않아 역직렬화에 버퍼링이 필요하다.

3. **픽스처의 트랜스크립트에 사용자 프롬프트가 없어 `entries`가 늘 빈 맵이었다.** 빈 맵은 키가 없으니 키 타입 변환이 한 번도 일어나지 않았고, 모든 단위 테스트가 통과했다. 실제 에이전트로 돌린 스모크에서 처음으로 키가 채워져 드러났다. "쓰기는 정상"이라는 사실은 발견을 더 늦춘다 — 생산자 쪽 테스트·로그는 모두 성공이라 결함이 **소비자 쪽에서만**, 그것도 데이터가 있을 때만 나타나기 때문이다. 교훈: 직렬화 계약 테스트는 **왕복(round-trip)** 으로, 그리고 **비어 있지 않은** 데이터로 해야 한다.

4. **`1, 10, 2` 순서가 되고, "바이트 불변" 주장은 거짓이다.** `BTreeMap<String, _>`은 키를 **문자열 사전순**으로 정렬하므로 `"1" < "10" < "2"`가 된다. 원래 `u64` 키는 숫자순(`1, 2, 10`)으로 방출됐으니, 타입만 바꾼 우회는 와이어에 나가는 키 순서를 바꾼다. 1차 수정이 "와이어 바이트는 그대로"라고 주장했으나 이 재정렬 때문에 거짓이었고, 2차 정정에서 바로잡았다.

5. **역직렬화: 문자열 키로 받아 명시적으로 파싱. 직렬화: 숫자 순서 그대로 방출.**
   - 역직렬화 쪽 — `BTreeMap::<String, V>::deserialize(d)?`로 받은 뒤 각 키를 `parse::<u64>()`하고, 실패하면 `serde::de::Error::custom`으로 오류를 낸다. Content 버퍼를 거쳐도 문자열 키는 문자열로 읽을 수 있으므로 이 경로가 동작한다.
   - 직렬화 쪽 — `serializer.collect_map(map.iter())`로 `u64` 맵의 **순회 순서(숫자순)**를 그대로 흘려 바이트 순서를 보존한다.
   이 코덱을 정수 키 맵 필드들에 `#[serde(with = "u64_key_map")]`로 붙였다. **이빨 있는 테스트**가 필요한 이유: 누군가 `with`를 "불필요해 보이는 어노테이션"으로 지우면 기존 픽스처로는 다시 초록불이 된다. `with` 제거 시 즉시 `invalid type: string "1"`로 실패하고, 방출 순서도 고정하는 테스트가 있어야 교정이 유지된다.
   > **필드 단위 코덱(`#[serde(with = "module")]`)** — 특정 필드만 `module::serialize`/`module::deserialize`로 변환하게 하는 serde 기능. 타입 전체를 바꾸지 않고 와이어 표현만 조정한다.

6. **JSON 파서가 맵 키를 넘길 때 키 전용 역직렬화기가 문자열을 숫자로 파싱해 준다.** JSON 객체 키는 항상 문자열이지만, 평범한 struct를 역직렬화할 때 JSON 역직렬화기는 키를 "맵 키 자리"로 알고 요청된 타입(`u64`)으로 파싱해 넘긴다. 그러나 internally tagged enum은 먼저 JSON에서 형식 중립적인 `Content`로 옮겨 담는다. 이때 키는 "문자열 값"이 되고, 두 번째 단계의 Content 역직렬화기에는 JSON의 키 파싱 규칙이 없다. 그래서 숫자 키 맵으로의 자동 변환이 일어나지 않는다. 비문자열 키 맵을 태그 enum 안에 둘 때는 **변환을 코덱으로 명시**해야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — internally tagged enum 안의 정수 키 맵 (쓰기 성공, 읽기 실패)
① 문제 코드
```rust
#[derive(Serialize, Deserialize)]
#[serde(tag = "event")]
enum Event {
    Delta { entries: BTreeMap<u64, String>, /* ... */ },   // 읽기: invalid type: string "1", expected u64
    // ...
}
// 픽스처: 프롬프트 없는 트랜스크립트 → entries 가 늘 {} → 테스트 초록
```
② 고친 코드
```rust
#[serde(tag = "event")]
enum Event {
    Delta { #[serde(with = "u64_key_map")] entries: BTreeMap<u64, String>, /* ... */ },
}

mod u64_key_map {
    pub fn serialize<S: Serializer, V: Serialize>(m: &BTreeMap<u64, V>, s: S) -> Result<S::Ok, S::Error> {
        s.collect_map(m.iter())                              // u64 순회 순서(숫자순) 그대로 방출
    }
    pub fn deserialize<'de, D: Deserializer<'de>, V: Deserialize<'de>>(d: D) -> Result<BTreeMap<u64, V>, D::Error> {
        BTreeMap::<String, V>::deserialize(d)?             // JSON처럼 맵 키가 문자열로 오는 포맷 전제
            .into_iter()
            .map(|(k, v)| k.parse::<u64>().map(|k| (k, v))
                 .map_err(|_| serde::de::Error::custom("non-numeric key")))
            .collect()
    }
}
// 테스트: 비어 있지 않은 entries 왕복 + with 제거 시 즉시 실패 + 방출 순서 1,2,10 고정
```
무엇이 깨졌나: 태그 enum의 버퍼링 경로에서 JSON의 키 파싱 규칙이 사라졌고, 빈 픽스처가 그 경로를 한 번도 실행하지 않았다.\
같은 구조: 짧은 형태 `#[serde(tag = "type")] enum Msg { X { m: BTreeMap<u64, T> } }` — 쓰기는 정상, 스모크에서만 발견(해결 기록 없음).\
같은 구조: 같은 결함과 교정(문자열 키 코덱 + 사전순 재정렬 함정)이 프로토콜 계약 문서에도 기록됨.

### 변형 B — 문자열 키로 우회하면 정렬 순서가 바뀜
① 문제 코드
```rust
Delta { entries: BTreeMap<String, String> }    // 읽기는 되지만
// 방출: {"1":..,"10":..,"2":..}  ← 사전순 — "와이어 바이트 불변" 주장이 거짓
```
② 고친 코드
```rust
Delta { #[serde(with = "u64_key_map")] entries: BTreeMap<u64, String> }   // 타입은 u64 유지, 코덱으로 순서 보존
```
무엇이 깨졌나: 키 타입이 곧 정렬 규칙이라는 점을 빼고 "읽히기만 하면 된다"로 판단했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
