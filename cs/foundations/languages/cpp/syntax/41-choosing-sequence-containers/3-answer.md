# cpp/syntax/41 — 순차 컨테이너 선택 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **g++-12 (Ubuntu 12.4.0-2ubuntu1\~24.04.1) 12.4.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 이 편의 블록에는 **흔들리는 칸이 없다**(주소는 찍지 않고 비교만 했다).\
> 근거로 쓰는 것은 다음이다 — **할당 횟수 · 연속인가 · 주소가 그대로인가 · `capacity` 수열 · 이동/복사 로그 · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **할당 — `vector` 5 · `reserve` 1 · `array` 0 · `deque` 2 · 3 · 3 · `list` 16 · `forward_list` 16** · 연속 「아니오」는 **`deque` 앞 · `deque` ×200 · `list` · `forward_list`** · 주소가 바뀐 것은 **`reserve` 없는 `vector` 하나** · ★ `sizeof` 는 **`array` 만** 원소 수에 달렸다

**출력**

```bash
# seq-grid.sh
# seq-grid.sh — 컨테이너 여덟 행 × 판 넷(컴파일러 둘 × -O0/-O2). 칸 넷은 seq01.cpp 가 찍는다
rows=('1 16 vector push_back' '2 16 vector reserve(16) 뒤 push_back' '3 16 array 칸에 쓰기' '4 16 deque push_back'
      '5 16 deque push_front' '4 200 deque push_back ×200' '6 16 list push_back' '7 16 forward_list push_front')
printf '%s\t%s\t%s\t%s\t%s\n' "컨테이너 · 넣는 법" "sizeof" "operator new 횟수" "연속인가" "처음 원소 주소 그대로인가" > t.tsv
diffs=0; cells=0
for r in "${rows[@]}"; do
  set -- $r; k=$1; n=$2; shift 2; name="$*"
  ref=""
  for c in g++ clang++; do
    for o in -O0 -O2; do
      $c -std=c++20 -Wall -Wextra -pedantic $o -DC=$k -DN=$n seq01.cpp -o sx || { echo "cc 에러 $r"; exit 1; }
      got=$(./sx) || exit 1
      if [ -z "$ref" ]; then ref="$got"; printf '%s\t%s\n' "$name" "$got" >> t.tsv
      else
        d=$(paste <(printf '%s\n' "$ref" | tr '\t' '\n') <(printf '%s\n' "$got" | tr '\t' '\n') | awk -F'\t' '$1 != $2' | wc -l)
        diffs=$(( diffs + d )); cells=$(( cells + 4 ))
      fi
    done
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 5' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
echo "판 넷 중 g++ -O0 과 갈린 칸 $diffs / $cells"
rm -f sx t.tsv
```

```text
===== bash seq-grid.sh (exit=0) =====
컨테이너 · 넣는 법	sizeof	operator new 횟수	연속인가	처음 원소 주소 그대로인가
vector push_back	24	5	예	아니오
vector reserve(16) 뒤 push_back	24	1	예	예
array 칸에 쓰기	64	0	예	예
deque push_back	80	2	예	예
deque push_front	80	3	아니오	예
deque push_back ×200	80	3	아니오	예
list push_back	24	16	아니오	예
forward_list push_front	8	16	아니오	예
판 넷 중 g++ -O0 과 갈린 칸 0 / 96
```

**왜 그런가**

- ★★★ **`vector` 는 1 · 2 · 4 · 8 · 16 으로 다섯 번 이사**했다(2번의 수열) — 이사하면 처음 원소도 새 버퍼로 옮겨져 주소가 바뀐다. `reserve(16)` 은 **처음 한 번만** 잡는다.
- ★★★ **`deque` 는 칸을 끝에 덧붙인다** — 기존 칸의 원소는 안 움직인다. 16 개는 한 칸 안이라 우연히 이웃했고, 200 개는 칸을 넘어 「아니오」가 됐다.
- ★★ **`list`·`forward_list` 는 원소마다 노드를 잡는다** — 16 회 · 서로 떨어져 있다 · 아무도 안 움직인다.
- ★★ **네 판 사이 갈린 칸 0 / 96** — 이 칸들은 최적화를 타지 않는다.

### 2. ★★ **처음 0 · 1 → 2 → 4 → … → 1024 · 바뀐 횟수 11 — 세 판 한 글자도 같다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic capseq01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 capacity 0
size    1 에서 capacity    1
size    2 에서 capacity    2
size    3 에서 capacity    4
size    5 에서 capacity    8
size    9 에서 capacity   16
size   17 에서 capacity   32
size   33 에서 capacity   64
size   65 에서 capacity  128
size  129 에서 capacity  256
size  257 에서 capacity  512
size  513 에서 capacity 1024
바뀐 횟수 11
===== clang++ -std=c++20 -Wall -Wextra -pedantic capseq01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 capacity 0
size    1 에서 capacity    1
size    2 에서 capacity    2
size    3 에서 capacity    4
size    5 에서 capacity    8
size    9 에서 capacity   16
size   17 에서 capacity   32
size   33 에서 capacity   64
size   65 에서 capacity  128
size  129 에서 capacity  256
size  257 에서 capacity  512
size  513 에서 capacity 1024
바뀐 횟수 11
===== g++-12 -std=c++20 -Wall -Wextra -pedantic capseq01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 capacity 0
size    1 에서 capacity    1
size    2 에서 capacity    2
size    3 에서 capacity    4
size    5 에서 capacity    8
size    9 에서 capacity   16
size   17 에서 capacity   32
size   33 에서 capacity   64
size   65 에서 capacity  128
size  129 에서 capacity  256
size  257 에서 capacity  512
size  513 에서 capacity 1024
바뀐 횟수 11
```

**왜 그런가**

- ★★ **이 판의 libstdc++(13 · 12)는 두 배로 늘린다.** 빈 `vector` 는 할당하지 않고(0), 첫 원소에서 1 을 잡는다.
- ★ **세 판이 같은 것은 같은 구현 계열이라서**다 — 보장이 아니다(5번).

### 3. ★★★ **`NoexceptMove` — `T&&` · `move move` / `ThrowingMove` — `const T&` · `copy copy` / `MoveOnlyThrowing` — `T&&` · `move move`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic mif01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
NoexceptMove      nothrow_move=1 copyable=1 move_if_noexcept->T&& | 재할당: move move 
ThrowingMove      nothrow_move=0 copyable=1 move_if_noexcept->const T& | 재할당: copy copy 
MoveOnlyThrowing  nothrow_move=0 copyable=0 move_if_noexcept->T&& | 재할당: move move 
===== clang++ -std=c++20 -Wall -Wextra -pedantic mif01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
NoexceptMove      nothrow_move=1 copyable=1 move_if_noexcept->T&& | 재할당: move move 
ThrowingMove      nothrow_move=0 copyable=1 move_if_noexcept->const T& | 재할당: copy copy 
MoveOnlyThrowing  nothrow_move=0 copyable=0 move_if_noexcept->T&& | 재할당: move move 
```

**왜 그런가**

- ★★★ **재할당은 `move_if_noexcept` 가 돌려준 것으로 새 원소를 만든다** — `T&&` 면 이동 생성자, `const T&` 면 복사 생성자가 골라진다.
- ★★ 두 컴파일러가 같다 — **같은 libstdc++** 이기도 하지만 이 규칙은 **표준**이다.

### 4. ★★★ **말할 수 없다 — 16 개가 한 칸에 다 들어간 것뿐이다.** 같은 탐침을 **200 개**로 돌리면 「아니오」(1번의 여섯째 행)

- ★★★ cppreference 는 「**the elements of a deque are not stored contiguously**」라고 적는다. **작은 입력의 참은 근거가 아니다** — 반례 한 행이 성질을 가른다.

### 5. ★★★ **말할 수 없다 — 표준은 `push_back` 이 「분할 상환 상수(Amortized constant)」라는 것만** 약속한다. 배수는 구현의 선택이다

- ★★ 표준이 약속하는 것 둘 더 — **용량을 넘기면 재할당하고 그때 참조·이터레이터가 전부 무효** · 넘기지 않으면 **`end()` 만 무효**.
- ★ 이 머신의 세 판은 **libstdc++ 계열 하나**다 — 다른 구현의 배수는 **못 잰 것**이다.

### 6. ★★ **복사할 수 없으면 `move_if_noexcept` 가 `T&&` 를 돌려준다 — 고를 것이 이동뿐이다.** 대가는 **강한 예외 보장**이다

- ★★ 옮기는 도중 이동이 던지면 **이미 옮긴 원소는 옛 버퍼에서 빠져나간 상태**라 되돌릴 수 없다. `noexcept` 이동이거나 복사가 가능하면 이 위험이 없다(이 편은 던지는 판을 **돌리지 않았다** — 규칙에서 읽은 것).

### 7. ★★ **`deque` 는 원소를 고정 크기 칸들에 나눠 두고 끝에 칸을 덧붙인다 — 기존 칸은 안 움직인다.** `vector` 는 **한 덩어리**라 늘리려면 통째로 옮겨야 한다

- ★ 그래서 `deque` 는 **연속을 포기하고 참조 안정성을 얻었다**(1번의 두 열이 정확히 반대).

### 8. ★★ **① 연속(번호로 바로 · `data()` 로 C 에 넘김) ② 할당이 가장 적다(`reserve` 면 1 회) ③ 머리가 작다(24 바이트)** — 버릴 조건: **넣고 빼는 동안 기존 원소의 주소·참조를 들고 있어야 할 때**

- ★★ 그때는 끝에서만 넣으면 `deque`, 가운데서도 넣으면 `list`(1번의 「주소 그대로」 열).

### 9. ★ **같은 말이 아니다 — 「이웃한 주소」만 봤다.** 캐시 줄에 몇 개가 드는지 · 실제로 미스가 나는지는 **이 창이 못 본다**

- ★ 그것을 말하려면 **N 판 시간 격자**나 하드웨어 카운터가 필요하다 — 이 편은 **돌리지 않았다.**

### 10. 다른 주제와 잇기

- ★★ **17번 (3)** — `noexcept` 가 있으면 이동 · 없으면 복사(`is_nothrow_move_constructible` 1 대 0). **3번이 새로 보인 것** — 그 판정이 **`std::move_if_noexcept` 의 반환 타입**으로 보인다는 것 · **복사가 없으면 던지는 이동이어도 옮긴다**는 셋째 경우.
- ★ [Rust 38번](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/) — **「`push` 는 꽉 찼을 때만 재할당한다(보장) — 몇 배로 늘리나는 보장이 아니다(이 판은 두 배)」** — 같은 결론이다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `seq01.cpp` + `seq-grid.sh` | 여덟 행 × 컴파일러 2 × `-O0`/`-O2` | ★★★ **갈린 칸 0 / 96** · 주소가 바뀐 행 1 / 8 · 연속 아님 4 / 8 |
| `capseq01.cpp` | g++ 13 · clang 18 · g++-12 | ★★ **두 배 · 11 회 · 세 판 동일** |
| `mif01.cpp` | 두 컴파일러 | ★★★ **`T&&` · `const T&` · `T&&`** |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **두 배 · 첫 용량 1 · `sizeof` · `deque` 의 칸 크기(16 개가 한 칸)와 빈 채 할당.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **`vector` 연속 · 분할 상환 상수 · 재할당 시 참조 무효 · `deque` 양끝 삽입 참조 유지 · `list` 참조 유지 · `move_if_noexcept` 규칙.**

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — 다른 표준 라이브러리(libc++ 없음).
- **안 돌려 본 것** — **시간** · 던지는 이동의 실제 판 · `shrink_to_fit`.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **1번 격자 · 2번 수열** — 라이브러리 판이 바뀌면 할당 횟수와 배수가 움직일 수 있다.
