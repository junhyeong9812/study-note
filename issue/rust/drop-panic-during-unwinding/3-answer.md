# issue/rust/drop-panic-during-unwinding — 정답

태그: `test-reliability`

## 정답
<!-- 질문 1:1 대응 -->

1. **A는 그 테스트만 FAILED로 끝나고 다음 테스트가 계속 돈다. B는 프로세스 전체가 abort되어 남은 테스트가 실행되지 않고 결과 요약 줄도 나오지 않는다.**\
   B의 출력은 첫 패닉, `Drop` 안의 두 번째 패닉, 그리고 `panic in a destructor during cleanup` · `thread caused non-unwinding panic. aborting.` 다음 `signal: 6, SIGABRT`로 끝난다(rustc 1.92에서 확인).\
   `--test-threads=1`로 돌리면 B 뒤에 예정된 테스트가 한 번도 실행되지 않는 것이 보인다.

2. **되감기는 패닉 지점에서 호출한 쪽으로 거슬러 오르며 각 단계에 살아 있는 값의 `Drop`을 실행하는 과정이다. `catch_unwind`는 이 되감기를 중간에서 멈추는 지점이고, abort는 되감기 없이 프로세스를 즉시 끝내는 것이라 잡을 수 없다.**\
   `cargo test`의 기본 러너는 테스트마다 되감기를 붙잡아, 패닉한 테스트만 실패로 기록하고 나머지를 계속 돈다.\
   abort는 `Drop`을 실행하지 않고 운영체제 신호로 프로세스를 죽인다 — 러너 자신도 함께 죽는다.
   > **되감기(unwinding)** — 패닉이 스택 프레임을 하나씩 벗기며 그 프레임의 지역 값들을 drop하는 과정. 잠금 해제·카운터 복구 같은 정리가 여기서 일어난다.
   > **abort** — 프로세스를 그 자리에서 종료(SIGABRT). 소멸자도, 붙잡는 지점도 없다.

3. **되감기는 진행 중인 패닉 하나(페이로드 하나)를 위로 운반하는 장치이고, 두 번째 패닉을 함께 운반할 방법이 없기 때문이다.**\
   되감기 도중 `Drop`이 새 패닉을 일으키면 "어느 패닉을 전파할지"가 정의되지 않는다. Rust는 이 상황을 복구 불가능으로 보고 프로세스를 abort한다.\
   그래서 `Drop` 문서도 "되감기 중에 drop이 불리므로 drop 구현 안의 panic은 abort로 이어지기 쉽다"고 경고한다 — `Drop` 안에서는 패닉하지 않는 것이 관례다.

4. **다른 경로에서 이미 패닉이 나 되감는 중이고, 그 패닉의 원인이 바로 장부를 0으로 만든 상태 손상일 때다.**\
   이 사례에서는 "핀된 프레임은 내보내지 않는다"는 조건이 빠진 변이에서 일어났다. 핀된 프레임이 희생자로 뽑히자 장부가 초기화되어 카운트가 0이 됐고, 그 프레임에 새 내용을 적재하다 내부 가변 빌림이 충돌해 1차 패닉이 났다.\
   되감기가 그 프레임을 쥔 가드를 drop하자, 가드의 `Drop`이 카운트를 내리며 `count > 0` 검사에서 2차 패닉 → abort.\
   평소에는 버그를 잡아 주는 검사가, 이미 깨진 상태 위에서 정리 경로를 돌 때는 프로세스를 죽이는 방아쇠가 된다.

5. **평소(`panicking() == false`)에는 검사가 그대로 켜져 이중 해제 같은 장부 버그를 잡고, 되감는 중(`true`)에만 꺼져 1차 패닉이 온전히 전파된다.**\
   검사를 지우면 평소의 이중 해제 버그를 놓친다. 조건으로 끄면 두 목적을 다 지킨다.\
   `saturating_sub`는 0에서 멈춘다. 그냥 `-=`면 부호 없는 정수 `0 − 1`이 debug 빌드에서는 오버플로 패닉(또 `Drop` 안 패닉 → abort), release 빌드에서는 최댓값으로 감겨 그 자원이 영원히 "사용 중"으로 보인다(이 사례라면 그 프레임은 다시는 내보낼 수 없게 된다).
   > **`std::thread::panicking()`** — 현재 스레드가 패닉으로 되감는 중이면 `true`. `Drop`에서 정리 방식을 바꾸는 데 쓴다.

6. **구현을 보지 않고 쓴 테스트에 "핀 무시" 변이를 넣었더니 assert 실패가 아니라 SIGABRT로 끝났다 — 테스트가 아니라 구현의 정리 경로가 abort를 만든 것이다.**\
   테스트는 해당 호출을 `catch_unwind`로 감싸 "패닉이면 assert 실패"로 바꾸려 했지만, abort는 잡히지 않았다.\
   abort는 변이를 "검출"하긴 하지만 어느 테스트가 무엇을 잡았는지 지운다. 수정 뒤 같은 변이는 6개 테스트의 평범한 assert 실패로 보고됐다.

## 문제 구조 (추상화 코드)

### 변형 A — RAII 가드의 Drop이 불변식 검사로 2차 패닉
① 문제 코드
```rust
struct Book { pins: Vec<u32> /* ... */ }

impl Book {
    fn release(&mut self, slot: usize) {
        debug_assert!(self.pins[slot] > 0);   // 되감는 중에도 검사
        self.pins[slot] -= 1;                 // 0이면 debug 패닉 / release 감김
    }
}

struct Guard<'a> { book: &'a RefCell<Book>, slot: usize /* ... */ }

impl Drop for Guard<'_> {
    fn drop(&mut self) {
        self.book.borrow_mut().release(self.slot);   // 되감기 중 호출될 수 있다
    }
}

// 다른 경로: 손상(핀 무시)으로 이 slot의 장부가 0으로 초기화된 뒤 패닉 → 되감기 → Guard::drop → 2차 패닉 → abort
```
② 고친 코드
```rust
fn release(&mut self, slot: usize) {
    // Drop에서 불린다 — 되감는 중에 또 패닉하면 abort이므로 그때는 검사를 건너뛴다.
    debug_assert!(self.pins[slot] > 0 || std::thread::panicking(), "release of an unpinned slot");
    self.pins[slot] = self.pins[slot].saturating_sub(1);
}
```
무엇이 깨졌나: 정리 경로(`Drop`)가 정상 상태를 전제한 검사를 했고, 이미 깨진 상태에서 되감기가 그 경로를 지나며 프로세스를 죽였다.

## 검증 기록
- 2026-11-14: 사건 기록 대조·추상화(Claude 초안) — 변이(핀 무시) 시 SIGABRT, 수정 후 같은 변이가 assert 실패 6개로 바뀜을 확인. 단독 데모(일반 패닉 테스트 vs Drop 안 패닉 테스트)로 출력 문구·뒤 테스트 미실행을 rustc 1.92.0에서 확인.

## 참고
- `std::ops::Drop` 문서(패닉 시 동작): https://doc.rust-lang.org/std/ops/trait.Drop.html
- `std::thread::panicking`: https://doc.rust-lang.org/std/thread/fn.panicking.html
- `std::panic::catch_unwind`: https://doc.rust-lang.org/std/panic/fn.catch_unwind.html

## 관련 카드
- [language-semantics-traps](../language-semantics-traps/) — debug panic / release wrap 정수 오버플로. 이 카드의 `saturating_sub` 선택이 같은 함정을 Drop 맥락에서 피한다.
- [green-masking](../../cross-cutting/testing/green-masking/) — 변이로 테스트의 이빨을 확인하는 같은 축. 여기서는 변이 결과가 "검출됐지만 격리가 깨진" 형태로 나왔다.
