# cpp/syntax/40 — `std::function`·함수 객체·호출 가능 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·역어셈블은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · GNU objdump 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · 역어셈블의 오프셋과 명령 줄 수** 다.\
> 근거로 쓰는 것은 다음이다 — **통과 칸 · `new` 횟수 · 간접 분기 0 / 1 · `cc exit`/`run exit` · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **함수 포인터 2 / 7 · `std::function` 6 / 7 · 템플릿 6 / 7 · `std::invoke` 7 / 7 — 통과 42 / 56 · 컴파일러 사이 갈린 행 0**

**출력**

```bash
# hold-grid.sh
# hold-grid.sh — 호출 가능 일곱 × 받는 자리 넷 × 컴파일러 둘. 칸에는 컴파일되면 찍힌 값, 안 되면 「에러」
calls=('1 함수 포인터' '2 캡처 없는 람다' '3 캡처 있는 람다' '4 함수 객체' '5 멤버 함수 포인터' '6 std::bind 결과' '7 move-only 람다')
recvs=('1 R(*)(Args)' '2 std::function' '3 템플릿 F&&' '4 std::invoke')
cell() {
  if ! $1 -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=$2 -DRECV=$3 hold01.cpp -o hx 2>/dev/null; then printf '에러'; return; fi
  printf '%s' "$(./hx)"
}
printf '%s\t%s\t%s\t%s\n' "호출 가능" "받는 자리" "g++" "clang++" > t.tsv
for c in "${calls[@]}"; do
  for r in "${recvs[@]}"; do
    printf '%s\t%s\t%s\t%s\n' "$c" "$r" "$(cell g++ ${c%% *} ${r%% *})" "$(cell clang++ ${c%% *} ${r%% *})" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 4' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
pass=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=4;i++) if ($i != "에러") n++ } END { print n+0 }')
split=$(tail -n +2 t.tsv | awk -F'\t' '$3 != $4' | wc -l)
for r in "${recvs[@]}"; do
  n=$(tail -n +2 t.tsv | awk -F'\t' -v r="$r" '$2 == r && $3 != "에러"' | wc -l)
  printf '받는 자리 %s — 통과 %d / %d\n' "$r" "$n" "${#calls[@]}"
done
echo "통과 칸 $pass / $(( rows * 2 )) · 컴파일러 사이 갈린 행 $split / $rows"
rm -f hx t.tsv
```

```text
===== bash hold-grid.sh (exit=0) =====
호출 가능	받는 자리	g++	clang++
1 함수 포인터	1 R(*)(Args)	42	42
1 함수 포인터	2 std::function	42	42
1 함수 포인터	3 템플릿 F&&	42	42
1 함수 포인터	4 std::invoke	42	42
2 캡처 없는 람다	1 R(*)(Args)	42	42
2 캡처 없는 람다	2 std::function	42	42
2 캡처 없는 람다	3 템플릿 F&&	42	42
2 캡처 없는 람다	4 std::invoke	42	42
3 캡처 있는 람다	1 R(*)(Args)	에러	에러
3 캡처 있는 람다	2 std::function	42	42
3 캡처 있는 람다	3 템플릿 F&&	42	42
3 캡처 있는 람다	4 std::invoke	42	42
4 함수 객체	1 R(*)(Args)	에러	에러
4 함수 객체	2 std::function	42	42
4 함수 객체	3 템플릿 F&&	42	42
4 함수 객체	4 std::invoke	42	42
5 멤버 함수 포인터	1 R(*)(Args)	에러	에러
5 멤버 함수 포인터	2 std::function	42	42
5 멤버 함수 포인터	3 템플릿 F&&	에러	에러
5 멤버 함수 포인터	4 std::invoke	42	42
6 std::bind 결과	1 R(*)(Args)	에러	에러
6 std::bind 결과	2 std::function	42	42
6 std::bind 결과	3 템플릿 F&&	42	42
6 std::bind 결과	4 std::invoke	42	42
7 move-only 람다	1 R(*)(Args)	에러	에러
7 move-only 람다	2 std::function	에러	에러
7 move-only 람다	3 템플릿 F&&	42	42
7 move-only 람다	4 std::invoke	42	42
받는 자리 1 R(*)(Args) — 통과 2 / 7
받는 자리 2 std::function — 통과 6 / 7
받는 자리 3 템플릿 F&& — 통과 6 / 7
받는 자리 4 std::invoke — 통과 7 / 7
통과 칸 42 / 56 · 컴파일러 사이 갈린 행 0 / 28
```

**왜 그런가**

- ★★★ **함수 포인터는 주소 하나** — 상태를 가진 것(캡처 · 함수 객체 · `bind` 결과 · move-only)은 **못 바뀐다.** 멤버 함수 포인터는 **타입부터 다르다**(`int (Obj::*)(int)`).
- ★★★ **`std::function` 은 복사 가능한 호출 가능 전부** — move-only 만 빠진다(39편 (4)). 멤버 함수 포인터는 **INVOKE 규칙**으로 부른다.
- ★★★ **템플릿은 타입을 가리지 않지만 몸통이 `f(o, x)`** 라 괄호로 안 불리는 멤버 함수 포인터에서 막힌다. **`std::invoke` 는 부르는 법 자체를 묶는다** — 7 / 7.
- ★★ **갈린 행 0** — 막히는 이유가 **언어 규칙**이라 두 컴파일러가 같다.

### 2. ★★ **캡처 있는 람다 → 함수 포인터는 호출 줄(43행) · 멤버 함수 포인터 → 템플릿은 템플릿 몸통(19행)** — 두 컴파일러 같다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=3 -DRECV=1 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp: In function ‘int main()’:
hold01.cpp:43:43: error: cannot convert ‘std::remove_reference<main()::<lambda(Obj&, int)>&>::type’ {aka ‘main()::<lambda(Obj&, int)>’} to ‘FnPtr’ {aka ‘int (*)(Obj&, int)’}
   43 |     std::printf("%d\n", recv_ptr(std::move(c), o, 41));
      |                                  ~~~~~~~~~^~~
      |                                           |
      |                                           std::remove_reference<main()::<lambda(Obj&, int)>&>::type {aka main()::<lambda(Obj&, int)>}
hold01.cpp:17:20: note:   initializing argument 1 of ‘int recv_ptr(FnPtr, Obj&, int)’
   17 | int recv_ptr(FnPtr f, Obj& o, int x) { return f(o, x); }
      |              ~~~~~~^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=3 -DRECV=1 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp:43:25: error: no matching function for call to 'recv_ptr'
   43 |     std::printf("%d\n", recv_ptr(std::move(c), o, 41));
      |                         ^~~~~~~~
hold01.cpp:17:5: note: candidate function not viable: no known conversion from 'typename std::remove_reference<(lambda at hold01.cpp:32:14) &>::type' (aka '(lambda at hold01.cpp:32:14)') to 'FnPtr' (aka 'int (*)(Obj &, int)') for 1st argument
   17 | int recv_ptr(FnPtr f, Obj& o, int x) { return f(o, x); }
      |     ^        ~~~~~~~
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=5 -DRECV=3 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp: In instantiation of ‘int recv_template(F&&, Obj&, int) [with F = int (Obj::*)(int)]’:
hold01.cpp:47:38:   required from here
hold01.cpp:19:70: error: must use ‘.*’ or ‘->*’ to call pointer-to-member function in ‘f (...)’, e.g. ‘(... ->* f) (...)’
   19 | template <class F> int recv_template(F&& f, Obj& o, int x) { return f(o, x); }
      |                                                                     ~^~~~~~
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=5 -DRECV=3 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp:19:69: error: called object type 'int (Obj::*)(int)' is not a function or function pointer
   19 | template <class F> int recv_template(F&& f, Obj& o, int x) { return f(o, x); }
      |                                                                     ^
hold01.cpp:47:25: note: in instantiation of function template specialization 'recv_template<int (Obj::*)(int)>' requested here
   47 |     std::printf("%d\n", recv_template(std::move(c), o, 41));
      |                         ^
1 error generated.
```

**왜 그런가**

- ★★ **앞은 오버로드 해석 단계의 실패**다 — `recv_ptr` 를 고르는 순간 **인자 변환이 없어** 호출 자리에서 멈춘다.
- ★★ **뒤는 인스턴스화 단계의 실패**다 — `recv_template<int (Obj::*)(int)>` 는 **고르는 데는 성공**했고, 몸통을 만들다 `f(o, x)` 에서 깨졌다. clang 은 그 뒤에 **`requested here` 로 47행**(호출 줄)을 알려 준다(35편의 사슬 읽기).

### 3. ★★★ **`sizeof = 32` · `new` 가 1 회인 행은 17 · 24 · 64 바이트와 `Loud` 넷 — 나머지 다섯은 0 · 복사도 담기와 같은 횟수 · 네 판 사이 갈린 줄 0**

**출력**

```bash
# sbo-grid.sh
# sbo-grid.sh — sbo01.cpp 를 컴파일러 둘 × 최적화 둘 로 빌드해 돌리고, 네 판의 줄을 견준다
out=""
for c in g++ clang++; do
  for o in -O0 -O2; do
    $c -std=c++20 -Wall -Wextra -pedantic $o sbo01.cpp -o sx || { echo "cc 에러 $c $o"; exit 1; }
    ./sx > "run$c$o.txt" || exit 1
  done
done
cat "rung++-O0.txt"
bad=$(tail -n +2 "rung++-O0.txt" | awk -F'\t' 'NF != 6' | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
lines=$(wc -l < "rung++-O0.txt")
diffs=0
for f in "rung++-O2.txt" "runclang++-O0.txt" "runclang++-O2.txt"; do
  d=$(diff "rung++-O0.txt" "$f" | grep -c '^<')
  diffs=$(( diffs + d ))
done
heap=$(tail -n +3 "rung++-O0.txt" | awk -F'\t' '$4 > 0' | wc -l)
echo "힙에 담긴 것 $heap / $(( lines - 2 )) · 판 네 개 중 g++ -O0 과 갈린 줄 $diffs / $(( lines * 3 ))"
rm -f sx run*.txt
```

```text
===== bash sbo-grid.sh (exit=0) =====
sizeof(std::function<int(int)>) = 32
담는 것	sizeof	trivially_copyable	new(담기)	new(복사)	call
함수 포인터	8	1	0	0	2
캡처 없는 람다	1	1	0	0	2
캡처 8 바이트	8	1	0	0	2
캡처 16 바이트	16	1	0	0	2
캡처 17 바이트	17	1	1	1	2
캡처 24 바이트	24	1	1	1	2
캡처 64 바이트	64	1	1	1	2
캡처 Loud(8 바이트)	8	0	1	1	2
std::ref(64 바이트 람다)	8	1	0	0	2
힙에 담긴 것 4 / 9 · 판 네 개 중 g++ -O0 과 갈린 줄 0 / 33
```

**왜 그런가**

- ★★★ **32 바이트 안에 16 바이트 칸**이 있고(이 판), 거기 들어가면 힙이 필요 없다. **17 바이트부터 넘친다.**
- ★★ **복사본도 자기 대상을 가져야** 한다 — 힙에 둔 것이면 복사할 때 **새 창고를 또 잡는다**(1 회).
- ★★ **할당 횟수는 최적화를 타지 않았다** — 네 판 동일. 다만 **두 컴파일러가 같은 libstdc++** 라 「구현이 바뀌어도 같다」는 **못 잰 것**이다.

### 4. ★★★ **`use_function` 과 `use_ptr` — 두 컴파일러 다.** `use_tpl`·`use_local` 은 두 줄로 녹았다 · ★★ `__throw_bad_function_call` 은 **`use_function` 에만, `-dr` 의 재배치 줄로만** 이름이 보인다

**출력**

```text
===== g++ -std=c++20 -O2 -c ind01.cpp -o ind.o && objdump -dr --no-show-raw-insn -C ind.o (exit=0) =====

ind.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_invoke(std::_Any_data const&, int&&)>:
   0:	endbr64
   4:	mov    (%rsi),%eax
   6:	add    %eax,%eax
   8:	ret
   9:	nopl   0x0(%rax)

0000000000000010 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)>:
  10:	endbr64
  14:	test   %edx,%edx
  16:	je     30 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)+0x20>
  18:	cmp    $0x1,%edx
  1b:	je     20 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)+0x10>
  1d:	xor    %eax,%eax
  1f:	ret
  20:	mov    %rsi,(%rdi)
  23:	xor    %eax,%eax
  25:	ret
  26:	cs nopw 0x0(%rax,%rax,1)
  30:	lea    0x0(%rip),%rax        # 37 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)+0x27>
			33: R_X86_64_PC32	.data.rel.ro-0x4
  37:	mov    %rax,(%rdi)
  3a:	xor    %eax,%eax
  3c:	ret
  3d:	nopl   (%rax)

0000000000000040 <use_tpl(int)>:
  40:	endbr64
  44:	lea    (%rdi,%rdi,1),%eax
  47:	ret
  48:	nopl   0x0(%rax,%rax,1)

0000000000000050 <use_function(std::function<int (int)> const&, int)>:
  50:	endbr64
  54:	sub    $0x18,%rsp
  58:	mov    %fs:0x28,%rax
  61:	mov    %rax,0x8(%rsp)
  66:	xor    %eax,%eax
  68:	cmpq   $0x0,0x10(%rdi)
  6d:	mov    %esi,0x4(%rsp)
  71:	je     90 <use_function(std::function<int (int)> const&, int)+0x40>
  73:	lea    0x4(%rsp),%rsi
  78:	call   *0x18(%rdi)
  7b:	mov    0x8(%rsp),%rdx
  80:	sub    %fs:0x28,%rdx
  89:	jne    a5 <use_function(std::function<int (int)> const&, int)+0x55>
  8b:	add    $0x18,%rsp
  8f:	ret
  90:	mov    0x8(%rsp),%rax
  95:	sub    %fs:0x28,%rax
  9e:	jne    a5 <use_function(std::function<int (int)> const&, int)+0x55>
  a0:	call   a5 <use_function(std::function<int (int)> const&, int)+0x55>
			a1: R_X86_64_PLT32	std::__throw_bad_function_call()-0x4
  a5:	call   aa <use_function(std::function<int (int)> const&, int)+0x5a>
			a6: R_X86_64_PLT32	__stack_chk_fail-0x4
  aa:	nopw   0x0(%rax,%rax,1)

00000000000000b0 <use_ptr(int (*)(int), int)>:
  b0:	endbr64
  b4:	mov    %rdi,%rax
  b7:	mov    %esi,%edi
  b9:	jmp    *%rax
  bb:	nopl   0x0(%rax,%rax,1)

00000000000000c0 <use_local(int)>:
  c0:	endbr64
  c4:	lea    (%rdi,%rdi,1),%eax
  c7:	ret
```

```text
===== clang++ -std=c++20 -O2 -c ind01.cpp -o ind.o && objdump -dr --no-show-raw-insn -C ind.o (exit=0) =====

ind.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <use_tpl(int)>:
   0:	lea    (%rdi,%rdi,1),%eax
   3:	ret
   4:	data16 data16 cs nopw 0x0(%rax,%rax,1)

0000000000000010 <use_function(std::function<int (int)> const&, int)>:
  10:	push   %rax
  11:	mov    %esi,0x4(%rsp)
  15:	cmpq   $0x0,0x10(%rdi)
  1a:	je     26 <use_function(std::function<int (int)> const&, int)+0x16>
  1c:	lea    0x4(%rsp),%rsi
  21:	call   *0x18(%rdi)
  24:	pop    %rcx
  25:	ret
  26:	call   2b <use_function(std::function<int (int)> const&, int)+0x1b>
			27: R_X86_64_PLT32	std::__throw_bad_function_call()-0x4
  2b:	nopl   0x0(%rax,%rax,1)

0000000000000030 <use_ptr(int (*)(int), int)>:
  30:	mov    %rdi,%rax
  33:	mov    %esi,%edi
  35:	jmp    *%rax
  37:	nopw   0x0(%rax,%rax,1)

0000000000000040 <use_local(int)>:
  40:	lea    (%rdi,%rdi,1),%eax
  43:	ret
```

```bash
# ind-grid.sh
# ind-grid.sh — ind01.cpp 의 네 함수 × 컴파일러 둘, -O2 -c. objdump -dr 로 함수 몸통마다 센다
# 칸: 간접 분기(call *·jmp *) 수 / 직접 call 수 / __throw_bad_function_call 재배치가 있나 / 명령 줄 수
funcs=(use_tpl use_function use_ptr use_local)
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "함수" "컴파일러" "간접 분기" "직접 call" "bad_function_call 재배치" "명령 줄 수" > t.tsv
for f in "${funcs[@]}"; do
  for c in g++ clang++; do
    $c -std=c++20 -O2 -c ind01.cpp -o ind.o || { echo "cc 에러"; exit 1; }
    objdump -dr --no-show-raw-insn -C ind.o > dump.txt || exit 1
    body=$(awk -v f="$f" '/^[0-9a-f]+ </ { on = ($0 ~ ("^[0-9a-f]+ <" f "\\(") && $0 !~ /\)::/); next } on' dump.txt)
    ind=$(printf '%s\n' "$body" | grep -cE '(call|jmp) +\*')
    dir=$(printf '%s\n' "$body" | grep -E 'call +[0-9a-f]+ ' | wc -l)
    thr=$(printf '%s\n' "$body" | grep -q '__throw_bad_function_call' && echo O || echo X)
    n=$(printf '%s\n' "$body" | grep -cE '^ +[0-9a-f]+:')
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$f" "$c" "$ind" "$dir" "$thr" "$n" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 6' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
ind=$(tail -n +2 t.tsv | awk -F'\t' '$3 > 0' | wc -l)
split=$(tail -n +2 t.tsv | awk -F'\t' '{ k[$1] = k[$1] "|" $3 $5 } END { for (f in k) { split(k[f], a, "|"); if (a[2] != a[3]) n++ } print n+0 }')
echo "간접 분기가 남은 칸 $ind / $rows · 간접 분기 수·재배치가 컴파일러 사이 갈린 함수 $split / $(( rows / 2 ))"
rm -f ind.o dump.txt t.tsv
```

```text
===== bash ind-grid.sh (exit=0) =====
함수	컴파일러	간접 분기	직접 call	bad_function_call 재배치	명령 줄 수
use_tpl	g++	0	0	X	4
use_tpl	clang++	0	0	X	3
use_function	g++	1	2	O	21
use_function	clang++	1	1	O	10
use_ptr	g++	1	0	X	5
use_ptr	clang++	1	0	X	4
use_local	g++	0	0	X	3
use_local	clang++	0	0	X	2
간접 분기가 남은 칸 4 / 8 · 간접 분기 수·재배치가 컴파일러 사이 갈린 함수 0 / 4
```

**왜 그런가**

- ★★★ **`use_function` 은 참조로 받은 `std::function` 이라 안에 무엇이 들었는지 모른다** — 객체의 `0x18` 자리에서 주소를 읽어 부른다(`call *0x18(%rdi)`).
- ★★ **`use_ptr` 도 대상을 모른다** — `jmp *%rax`(꼬리 호출).
- ★★★ **`use_local` 은 만든 자리와 부르는 자리가 한 함수** — 컴파일러가 대상을 알아 **간접 호출도 비었나 검사도 지웠다.**
- ★★ **`.o` 안에서 다른 함수를 부르는 `call` 은 주소가 아직 비어 있다**(g++ 판의 `60: call 65 <…+0x55>` 처럼 **바로 다음 명령의 주소**를 가리킨다) — **그 이름은 재배치(`R_X86_64_PLT32 std::__throw_bad_function_call()`)에만** 있다. `-d` 만 보면 「그런 호출 없음」으로 읽힌다.

### 5. ★★ **기본 판은 `bool(f) = 0` · `what() = bad_function_call` · `bool(f) = 0`(`run exit=0`) · `-DUNCAUGHT` 판은 `bool(f) = 0` 뒤 `terminate called after throwing an instance of 'std::bad_function_call'` · `run exit=134`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic empty01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
bool(f) = 0
잡은 예외 what() = bad_function_call
nullptr 대입 후 bool(f) = 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic empty01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
bool(f) = 0
잡은 예외 what() = bad_function_call
nullptr 대입 후 bool(f) = 0
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUNCAUGHT empty01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
bool(f) = 0
terminate called after throwing an instance of 'std::bad_function_call'
  what():  bad_function_call
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DUNCAUGHT empty01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
bool(f) = 0
terminate called after throwing an instance of 'std::bad_function_call'
  what():  bad_function_call
```

**왜 그런가**

- ★★ **비어 있는 호출은 UB 가 아니라 예외**다 — 4번의 `cmpq $0x0` 가 부를 때마다 확인한다.
- ★ **안 잡은 예외는 `std::terminate` → `abort`** — 종료 코드 134(128 + SIGABRT 6).

### 6. ★★★ **멤버 함수 포인터는 괄호로 불리지 않는다 — 객체와 `.*`/`->*` 가 필요하다.** 몸통을 `std::invoke(f, o, x)` 로 바꾸면 된다

- ★★★ **`std::invoke` 는 「부르는 규칙(INVOKE)」 그 자체**다 — 첫 인자가 멤버 포인터면 두 번째 인자를 객체로 쓰고, 아니면 괄호로 부른다. `std::function` 도 안에서 이 규칙으로 부른다.
- ★★ 1번의 넷째 열(`recv_invoke`)이 **그 고친 판**이다 — 7 / 7.

### 7. ★★ **크기만이 아니라 「trivially copyable 인가」도 본다(이 판)** — `Loud` 는 복사 생성자를 직접 써서 `trivially_copyable = 0` 이다

- ★★ libstdc++ 13 은 **작고 · 정렬이 맞고 · trivially copyable 한 것**만 안쪽 칸에 넣는다 — 칸 안의 대상은 **`std::function` 을 옮길 때 바이트째 옮겨지기** 때문이라고 읽을 수 있다(이 판의 관찰 — **표준 문장이 아니다**).
- ★ 3번 표의 `trivially_copyable` 열이 그 판별이다 — **1 이면서 16 이하인 행만 0 회.**

### 8. ★★★ **말할 수 없다 — 16 바이트 문턱은 libstdc++ 13 의 관찰이다.** 보장인 행은 **함수 포인터와 `std::ref`** 둘뿐이다

- ★★★ cppreference 가 「**small object optimization is guaranteed**」라고 적은 것은 **함수 포인터와 `std::reference_wrapper`** 다. 나머지는 「**may be constructed in dynamic allocated storage**」 — 어디서부터인지 표준이 정하지 않는다.
- ★ 이 머신의 두 컴파일러가 **같은 libstdc++** 라 「다른 구현에서는?」은 **못 잰 것**이다.

### 9. ★★ **말할 수 없다 — 한 함수 안에서 만들고 부른 판의 관찰**이다. 대상이 호출 자리에서 안 보이면(참조로 넘겨받음 · 다른 번역 단위) 무너진다

- ★★ 4번의 `use_function` 이 바로 그 판이다 — 같은 파일 · 같은 `-O2` 인데 **간접 분기 1.**
- ★ 이 편은 `-O2` 만 셌다 — 다른 최적화 수준의 역어셈블은 **근거로 싣지 않았다.**

### 10. ★★ **말할 수 없다 — 시간을 재지 않았다.** 대신 비용의 원인 둘을 결정적으로 셌다 — **`new` 횟수(3번)** 와 **간접 분기가 남았나(4번)**

- ★★ 「느린가」는 **그 두 원인이 실제 부하에서 얼마나 무거운가**에 달렸고, 그것은 **N 판 판 격자**로만 말할 수 있다(규칙 24).

### 11. 다른 주제와 잇기

- ★★ **C 식은 상태를 `void* ctx` 로 따로 넘기고, `std::function` 식은 상태가 호출 가능한 것 안에 있다.** C 식 자리에는 **캡처 없는 람다**만 들어간다(1번의 첫 열 규칙).

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ctx01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
C 식 합 = 10 · std::function 합 = 10
===== clang++ -std=c++20 -Wall -Wextra -pedantic ctx01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
C 식 합 = 10 · std::function 합 = 10
```

- ★ **`Box<dyn Fn>`** — [Rust 35번](../../../rust/syntax/35-function-pointers-and-returning-closures/) (5). 힙에 담고 트레이트 객체로 부르는 것이 **`std::function` 의 타입 소거**와 같은 자리다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `hold01.cpp` + `hold-grid.sh` | 7 × 4 × 컴파일러 2 | ★★★ **통과 42 / 56 · 갈린 행 0 / 28** |
| `hold01.cpp` 두 에러 | 두 컴파일러 | ★★ 호출 줄 43 · 몸통 19 |
| `sbo01.cpp` + `sbo-grid.sh` | 컴파일러 2 × `-O0`/`-O2` | ★★★ **`sizeof` 32 · 힙 4 / 9 · 갈린 줄 0 / 33** |
| `ind01.cpp` + `ind-grid.sh` | 컴파일러 2 · `-O2 -c` · `objdump -dr` | ★★★ **간접 분기 4 / 8 · 갈린 함수 0 / 4** |
| `empty01.cpp` · `ctx01.cpp` | 두 컴파일러 | ★★ 위 정답 |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **`sizeof = 32` · 16 바이트 문턱 · trivially copyable 조건** · **인라인 여부** · 명령 줄 수.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **담을 수 있는 것의 규칙 · 비면 `bad_function_call` · 캡처 없는 람다만 함수 포인터 · 함수 포인터·`reference_wrapper` 는 힙 없음.**

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — ★ **libc++ 의 문턱**(libc++ 없음 — 링크에서 막힌다).
- **안 돌려 본 것** — `std::move_only_function` 의 크기·문턱 · 번역 단위를 넘은 호출 · **시간**.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3번 · 4번 격자** — libstdc++ 판이 오르면 문턱이, 컴파일러 판이 오르면 인라인 칸이 움직일 수 있다.
