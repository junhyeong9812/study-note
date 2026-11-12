# issue/rust/borrow-check-evaluation-order — 정리 (힌트)

## 전체 흐름

```text
let b = &mut self.items[ self.slots[ self.slot(key) ] ];

  desugar:  IndexMut::index_mut(&mut self.items, <인덱스 식>)
                                 │                 │
  ① 가변 빌림 시작 ──────────────┘                 │   self.items 를 &mut 로 잡음
  ② 인덱스 식 평가 ───────────────────────────────┘   self.slot(key) → &self (self 전체) 를 불변으로 빌림
                                                       ▲
                     ① 의 가변 빌림이 아직 살아 있음 ──┘  → E0502 💥
                     (IndexMut 은 2단계 빌림 대상이 아님)

  비교
  v.push(v.len())            ✅  autoref 메서드 수신자 → 2단계 빌림(예약 → 인자 평가 → 활성화)
  v[v.len() - 1] = x         💥  IndexMut 경로 → 2단계 빌림 없음
  &mut self.items[self.slots[k]]   ✅  필드 단위 빌림 — items 와 slots 는 서로 다른 자리
  &mut self.items[self.slot(k)]    💥  메서드는 시그니처(&self = self 전체)로만 판단

  교정
  let id = self.slots[self.slot(key)];   // 불변 빌림은 이 문장에서 끝남
  let b  = &mut self.items[id];          // 가변 빌림은 여기서 시작
```

## 핵심 문장

- `&mut place[idx]`는 `index_mut(&mut place, idx)`다 — 가변 빌림이 인덱스 식 평가보다 먼저 잡힌다.
- 2단계 빌림은 `vec.push(vec.len())` 같은 autoref 메서드 호출 등 정해진 경우에만 적용되고, 오버로드된 `IndexMut` 인덱싱은 그 목록에 없다.
- 빌림 검사기는 메서드 본문이 아니라 시그니처를 본다 — `&self` 메서드는 실제로 한 필드만 읽어도 `self` 전체를 빌린다.
- 교정의 기본형은 "인덱스를 먼저 값으로 계산해 빌림을 끝낸 뒤 가변 빌림을 시작"이다 — 컴파일러도 "try adding a local"로 같은 처방을 제안한다.
