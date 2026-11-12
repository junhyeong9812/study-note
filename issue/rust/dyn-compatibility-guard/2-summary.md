# issue/rust/dyn-compatibility-guard — 정리 (힌트)

## 전체 흐름

```text
[가드 없음]
  store 모듈      trait Store { ... + fn visit<F>(&self, f: F); }   ← 변경, 컴파일 ✅ (조용함)
  제네릭 사용처   fn run<T: Store>(t: &T)                            ← 컴파일 ✅
  dyn 사용처      Box<dyn Store>   (다른 모듈 · 다른 크레이트 · 아직 없음)
                     └─ 여기서 처음 E0038 💥  — 변경한 곳과 멀고, 사용처가 없으면 아예 안 남

[가드 있음]
  store 모듈      trait Store { ... + fn visit<F>(&self, f: F); }
                  const _: Option<&dyn Store> = None;   ← 정의 바로 옆에서 E0038 💥
                     │  타입 &dyn Store 를 "쓰기만" 함 — 값은 None, 구현체 불필요
                     └  컴파일 타임 상수, 이름 없음(_) → 런타임 코드 0

  확인: 일부러 제네릭 메서드를 넣는 변이 → 가드 줄에서 E0038 이 나는지 본다 → 원복
```

## 핵심 문장

- dyn 호환성은 trait 선언에 적히지 않는 성질이다 — 메서드 하나를 더하면 조용히 사라지고, `dyn`을 쓰는 곳에서만 에러가 난다.
- 제네릭 메서드는 타입마다 단형화되는 무한한 함수 족이라 vtable 한 칸에 담을 수 없다.
- `const _: Option<&dyn Trait> = None;`은 dyn 호환성을 정의 옆에서 단언하는 0비용 컴파일 타임 검사다.
- 가드는 실패할 수 있어야 증거다 — 변이(제네릭 메서드 추가)로 가드가 실제로 깨지는지 한 번 확인한다.
- 제네릭 메서드가 필요하면 `where Self: Sized`(dyn에서 그 메서드를 포기)나 확장 trait 분리로 dyn 호환성을 지킨다.
