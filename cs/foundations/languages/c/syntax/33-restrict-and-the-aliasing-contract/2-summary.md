# c/syntax/33 — `restrict` 와 앨리어싱 계약: 「**겹치지 않는다는 약속 — 지키는 것은 호출자다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `restrict` 의 **형식 정의**(「그 객체가 고쳐진다면 다른 모든 접근도 그 포인터에 기반해야 하고, 어기면 UB」), 「**모든 `restrict` 를 지워도 적격한 프로그램의 뜻은 안 바뀐다**」는 문장, `memcpy` 의 「**겹치면 UB**」를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **어셈블리·종료 코드·센 수는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **최적화 수준이 결과를 바꾸는 자리는 전부 판 격자**(컴파일러 2 × `-O0`/`-O2`, 위반 호출은 × `-O0`/`-O1`/`-O2`)로 돌렸다.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — `restrict` 는 **C99 부터**다(C89 에서는 낱말째 모른다 — (1)의 판 격자). C11·C17·C23 에서 **뜻이 바뀌지 않았다.** ★ **C++ 에는 없다**((7)).
> ★★★ **재지 않은 성능 주장은 하지 않는다.** 「`restrict` 는 빠르게 한다」는 **시간으로 재지 않았다** — 이 편은 **어셈블리의 로드 수**만 센다.
> ★★ **경계** — **타입이 다른 포인터**로 같은 메모리를 읽는 규칙(엄격한 앨리어싱)은 목록의 **55번 주제**가 정본이다. 여기는 「**같은 타입의 두 포인터가 겹치느냐**」만 본다.\
> ★ **`const`** 는 [31번 형제](../31-const-and-pointer-const-placement/), **`volatile`** 은 [32번 형제](../32-what-volatile-actually-guarantees/)가 정본이다 — 이 편이 **한정자 묶음의 끝**이다. **sanitizer 사용법**은 목록의 **58번 주제**다.
> 선행 — [31번 형제](../31-const-and-pointer-const-placement/) · 목록의 **55번 주제**(아직 없다).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창 — `-O2` 어셈블리의 로드 수다.** [31번 형제](../31-const-and-pointer-const-placement/)의 `twice_read` 가 `*p` 를 **두 번** 읽던 것을, `restrict` 를 붙인 같은 함수와 나란히 센다.
★★★ 그리고 **약속을 어긴 결과는 어셈블리가 아니라 실행 값**으로만 보인다 — 그런데 그것은 **UB 의 한 판 결과**라 「**관찰**」이지 결론이 아니다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | gcc `-Wrestrict` 가 **`&x, &x` 처럼 글자로 같은 인자**만 잡는다 · 변수로 넘기면 **0건** · clang **0건**((5)) | 씀 |
| ② 실행 출력 | ★★ **약속을 어긴 호출의 값**이 최적화 수준에 따라 갈린다((3)) — UB 의 관찰 | 씀 |
| ③ sanitizer | ★★ **탐침 8칸 중 답한 칸 1** — 그 1칸도 `restrict` 를 본 것이 아니라 **`memcpy` 를 본 것**이다((4)) | 씀(거의 침묵) |
| ★★★ ④ **`-O2` 어셈블리** | ★ **본체** — `*p` 를 읽는 명령이 **2 → 1** · 루프가 **`jmp memcpy`** 로 바뀐다 | 씀 |
| ⑤ `-O0` 어셈블리 | 대조군 — `-O0` 에서는 `restrict` 가 있어도 **2 번**((1)) | 씀 |
| 시간 측정 | 「`restrict` 는 빠르게 한다」 | ★ **안 쟀다**(규칙 — 재지 않은 성능 주장 금지) |
| ★ 제5의 상태 | 「`restrict` 위반을 도구가 잡나」를 sanitizer 로 물었더니 **침묵**했다 — 그런데 **컴파일러가 루프를 `memcpy` 호출로 바꾼 판**에서만 ASan 이 **`memcpy-param-overlap`** 으로 답했다. **창을 바꿔 답한 것은 도구가 아니라 컴파일러**다 | 창을 바꿔 답함 |

★ **바꾼 창(ASan 의 `memcpy` 가로채기)이 못 보는 것** — **`memcpy` 로 번역되지 않은 위반 전부.** `twice_read_r(p, q)` 는 여덟 칸 **전부** 침묵했다.

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ASan 리포트 첫 줄의 **`==PID==`** · 스택 줄의 **주소**(`0x…`) | 실행마다 다르다 |
| 안 흔들린다 | ★★★ **어셈블리 전부** · 로드 수 격자 | 같은 컴파일러 · 같은 플래그면 같다 |
| 안 흔들린다 | ★★ **약속을 어긴 호출의 값**(`7` · `14` · 배열) | **UB 지만 이 판에서는 번역이 정해져 있어** 다시 돌려도 같다 — 그래서 「**이 판의 값**」이지 「**C 의 값**」이 아니다 |
| 안 흔들린다 | sanitizer 격자의 **「리포트 N줄」 · `run exit`** · ASan 의 **`memcpy-param-overlap`** 과 **`파일:줄`** | 같은 자리를 밟는다 |

★★ **정규화 규칙은 기본 둘(주소 · PID)뿐**이다 — 위 표의 「흔들린다」 줄과 **같은 목록**이다. 이 편 고유 규칙은 없다.

## 한눈에 — 쉽게 말하면

**`restrict` 는 「이 창구로 들어온 서류는 다른 창구로는 안 들어온다」는 접수 규정이다.**

- **규정이 없으면** — 직원은 서류 하나를 처리하다가 **옆 창구가 같은 서류를 고쳤을까 봐** 다시 확인한다. → **`restrict` 없는 `twice_read`** — `*q = 0` 뒤에 `*p` 를 **다시 읽는다**
- **규정이 있으면** — 「다른 창구로는 안 온다」니까 **처음 본 것을 믿는다.** → **`restrict`** — `*p` 를 **한 번만** 읽는다
- **그런데 손님이 같은 서류를 두 창구에 냈다면** — 규정을 어긴 것은 **손님**이다. 직원은 모른 채 **처음 본 값**으로 일한다. → **약속을 어긴 호출은 UB** — 결과는 그 판의 번역이 정한다
- **경비원은 이것을 못 본다** — 경비원은 **문(메모리 경계)만** 지킨다. → **ASan·UBSan 은 `restrict` 위반에 침묵한다**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 다시 확인한다 | `twice_read` — `[rdi]` 두 번 | ★★★ **어셈블리 — 2 번** |
| 처음 본 것을 믿는다 | `twice_read_r` — `[rdi]` 한 번 · `add eax, eax` | ★★★ **어셈블리 — 1 번** |
| 규정을 어긴 손님 | `twice_read_r(p, q)` 에 같은 `x` | ★★ **실행 값** — `-O0` `7` · `-O2` `14`(관찰) |
| 경비원 | ASan · UBSan | ★★ **8칸 중 1칸** — 그것도 `memcpy` 를 본 것 |
| 접수 규정이 적힌 서식 | `memcpy` 의 `__restrict` 매개변수 | ★★ **헤더에 적혀 있다** — `memmove` 에는 없다 |

```text
   int a = *p;  *q = 0;  int b = *p;  return a + b;          -O2 · gcc / clang 같은 모양

   const int *p, int *q                     const int *restrict p, int *restrict q
   ---------------------------------------  ---------------------------------------
   mov eax, [rdi]      ① *p                 mov eax, [rdi]      ① *p
   mov [rsi], 0        *q = 0               mov [rsi], 0        *q = 0
   add eax, [rdi]      ② ★ *p 다시           add eax, eax        ★ 다시 안 읽는다 — a + a
```

- ★★★ **이 주제는 「UB」 칸이 본체**다 — `restrict` 가 하는 일은 **「어기면 UB」라는 조건을 거는 것뿐**이다. 컴파일러는 그 조건 덕에 **어긴 경우를 고려하지 않아도 된다.**
- ★★★ 그래서 **「표준」 칸의 첫 줄이 역설적**이다 — **적격한 프로그램에서 `restrict` 를 전부 지워도 뜻이 안 바뀐다.** `restrict` 는 **어긴 프로그램에서만** 차이를 만든다.
- ★★ **「도구가 못 보는 것」이 결론**이다 — 컴파일러 경고는 **글자로 같은 인자**만, sanitizer 는 **`memcpy` 로 번역된 것**만 봤다.

> **앨리어싱(aliasing)** — 두 이름(포인터)이 **같은 메모리**를 가리키는 것. 한쪽으로 쓰면 다른 쪽으로 읽은 값이 바뀐다.\
> 예: `int x; int *p = &x, *q = &x;` 에서 `*q = 0` 은 `*p` 도 바꾼다.

> **`restrict`** — 포인터에 붙는 한정자. 「**이 포인터로 접근하는 객체가 이 블록 안에서 고쳐진다면, 그 객체의 다른 모든 접근도 이 포인터에 기반한다**」는 약속. 어기면 **UB**.\
> 예: `void copy(int *restrict d, const int *restrict s, int n);`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`restrict` 는 번역을 무엇으로 바꾸나** — 31편의 `twice_read` 를 같은 모양으로 두고 **로드 수로.**
2. ★★★ **약속을 어기면 무엇이 나오나** — 그리고 **그것이 왜 결론이 아닌가.**
3. ★★ **누가 그 약속을 지켜 주나** — 컴파일러 경고 · sanitizer · 헤더의 서명.

## 동작 방식

### (1) ★★★ 번역이 바뀐다 — `*p` 를 읽는 명령이 2 에서 1 로

**언제 쓰나** — 「두 포인터가 겹칠 수 있어서 컴파일러가 다시 읽는다」를 없애고 싶을 때. ★★★ **이 편의 본체**다.

```c
/* s33a.c */
int twice_read(const int *p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int twice_read_r(const int *restrict p, int *restrict q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int restrict_p_only(const int *restrict p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int restrict_q_only(const int *p, int *restrict q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
twice_read:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, DWORD PTR [rdi]
        ret
twice_read_r:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
restrict_p_only:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
restrict_q_only:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
twice_read:                             # @twice_read
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, dword ptr [rdi]
        ret
.Lfunc_end0:
                                        # -- End function
twice_read_r:                           # @twice_read_r
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, eax
        ret
.Lfunc_end1:
                                        # -- End function
restrict_p_only:                        # @restrict_p_only
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, eax
        ret
.Lfunc_end2:
                                        # -- End function
restrict_q_only:                        # @restrict_q_only
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, eax
        ret
.Lfunc_end3:
                                        # -- End function
```

```text
===== *p 를 읽는 명령 수 — 함수 4 × 컴파일러 2 × 최적화 2 (exit=0) =====
함수             | gcc -O0   | gcc -O2   | clang -O0 | clang -O2
twice_read       | 2 번      | 2 번      | 2 번      | 2 번     
twice_read_r     | 2 번      | 1 번      | 2 번      | 1 번     
restrict_p_only  | 2 번      | 1 번      | 2 번      | 1 번     
restrict_q_only  | 2 번      | 1 번      | 2 번      | 1 번     
(칸 = 그 함수에서 [rdi] 또는 [rax] 를 32비트 레지스터로 읽는 명령 수 — *p 를 메모리에서 읽은 횟수)
```

```text
===== gcc -std=c17 -O0 -S -masm=intel -fno-asynchronous-unwind-tables s33a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^twice_read_r:/,/ret$/p' (cc exit=0) =====
twice_read_r:
        endbr64
        push    rbp
        mov     rbp, rsp
        mov     QWORD PTR -24[rbp], rdi
        mov     QWORD PTR -32[rbp], rsi
        mov     rax, QWORD PTR -24[rbp]
        mov     eax, DWORD PTR [rax]
        mov     DWORD PTR -8[rbp], eax
        mov     rax, QWORD PTR -32[rbp]
        mov     DWORD PTR [rax], 0
        mov     rax, QWORD PTR -24[rbp]
        mov     eax, DWORD PTR [rax]
        mov     DWORD PTR -4[rbp], eax
        mov     edx, DWORD PTR -8[rbp]
        mov     eax, DWORD PTR -4[rbp]
        add     eax, edx
        pop     rbp
        ret
```

그림 해설 (한 단계씩):

- ★★★ **`twice_read` 는 네 벌 다 `*p` 를 두 번 읽는다** — [31번 형제](../31-const-and-pointer-const-placement/)가 잰 것과 같다(`mov eax, [rdi]` · `add eax, [rdi]`).
- ★★★ **`twice_read_r` 은 `-O2` 에서 한 번만 읽는다** — 두 번째 읽기가 **`add eax, eax`** 가 됐다. 「`*q = 0` 이 `*p` 를 못 바꾼다」고 **믿어도 되기** 때문이다. **두 컴파일러가 같은 모양**이다.
- ★★★ **한쪽에만 붙여도 된다** — `restrict_p_only` · `restrict_q_only` 가 **둘 다 1 번**이다. 형식 정의가 「**`p` 로 접근하는 객체가 고쳐진다면 다른 모든 접근도 `p` 에 기반해야 한다**」이므로, `p` 하나만 `restrict` 여도 `*q = 0` 이 `*p` 를 고치는 경우는 **이미 UB** 다. `q` 쪽도 마찬가지다.
- ★★ **`-O0` 에서는 `restrict` 가 아무것도 안 바꾼다** — 네 함수 다 **2 번**이다. `restrict` 는 **최적화에 쓰일 수 있는 허락**이지 **명령**이 아니다.
- ★ 이것은 **명령 수**다 — **시간은 재지 않았다.** 「한 번 읽으니 빠르다」는 **이 문서의 주장이 아니다.**

```text
===== restrict 라는 낱말 — 판 4 (-pedantic -c s33a.c) (exit=0) =====
gcc    -std=c89  cc exit=1 · 에러 3
gcc    -std=c99  cc exit=0 · 에러 0
gcc    -std=c17  cc exit=0 · 에러 0
gcc    -std=c2x  cc exit=0 · 에러 0
clang  -std=c89  cc exit=1 · 에러 10
clang  -std=c99  cc exit=0 · 에러 0
clang  -std=c17  cc exit=0 · 에러 0
clang  -std=c2x  cc exit=0 · 에러 0
```

- ★ **`-std=c89` 에서는 에러**다 — `restrict` 가 **낱말째 없다**(식별자로 읽혀 선언이 깨진다). C99 부터 키워드다.

```text
   누가 무엇을 약속하나

   함수를 쓴 쪽                                  함수를 부르는 쪽
   ----------------------------------------      ----------------------------------------
   int twice_read_r(const int *restrict p,       twice_read_r(&x, &y);   지켰다
                    int *restrict q);            twice_read_r(p, q);     p == q == &x
     "p 로 읽는 객체를 이 안에서 누가 고친다면     ★ 어겼다 — 그런데 이 줄에는
      그 접근도 p 에 기반한다"고 가정해서           아무 표시도 없다
     *p 를 한 번만 읽는다
```

비용 — **약속을 지키는 책임이 호출자에게 넘어간다.** 함수 서명만 보고는 호출자가 그 약속을 **알아볼 방법이 없다**((5)).

### (2) ★★★ 루프가 `memcpy` 호출이 된다

**언제 쓰나** — 「`restrict` 를 붙인 복사 루프를 컴파일러가 어떻게 바꾸나」를 볼 때. (3)·(4)의 **원인**이 이 절이다.

```c
/* s33b1.c */
int twice_read(const int *p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int twice_read_r(const int *restrict p, int *restrict q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

void copy_plain(int *d, const int *s, int n) {
    for (int i = 0; i < n; i++) d[i] = s[i];
}

void copy_restrict(int *restrict d, const int *restrict s, int n) {
    for (int i = 0; i < n; i++) d[i] = s[i];
}
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33b1.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^copy_plain:/,/^copy_restrict:/p' (cc exit=0) =====
copy_plain:
        endbr64
        test    edx, edx
        jle     .L4
        movsx   rdx, edx
        xor     eax, eax
        lea     rcx, 0[0+rdx*4]
.L6:
        mov     edx, DWORD PTR [rsi+rax]
        mov     DWORD PTR [rdi+rax], edx
        add     rax, 4
        cmp     rax, rcx
        jne     .L6
.L4:
        ret
copy_restrict:
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33b1.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^copy_restrict:/,$p' (cc exit=0) =====
copy_restrict:
        endbr64
        test    edx, edx
        jle     .L8
        mov     edx, edx
        sal     rdx, 2
        jmp     memcpy@PLT
.L8:
        ret
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33b1.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^copy_restrict:/,/End function/p' (cc exit=0) =====
copy_restrict:                          # @copy_restrict
# %bb.0:
        test    edx, edx
        jle     .LBB3_1
# %bb.2:
        mov     edx, edx
        shl     rdx, 2
        jmp     memcpy@PLT                      # TAILCALL
.LBB3_1:
        ret
.Lfunc_end3:
                                        # -- End function
```

```text
   void copy_*(int *d, const int *s, int n) { for (i < n) d[i] = s[i]; }     -O2

   restrict 없음 (gcc)                      restrict 있음 (gcc · clang)
   ---------------------------------------  ---------------------------------------
   .L6: mov edx, [rsi+rax]   한 칸씩        n * 4 를 계산하고
        mov [rdi+rax], edx   읽고 쓴다       jmp memcpy      ★ 루프가 사라졌다
        add rax, 4 / jne .L6                  (memcpy 의 서명도 __restrict)
```

- ★★★ **`copy_restrict` 는 두 컴파일러 다 `jmp memcpy`** 다 — 「`d` 와 `s` 가 안 겹친다」를 믿으니 **루프 전체를 `memcpy` 한 번**으로 바꿨다.
- ★★ **`copy_plain` 은 한 칸씩 읽고 쓰는 루프로 남는다**(gcc) — 겹칠 수 있으면 `memcpy` 로 못 바꾼다. 겹칠 때의 뜻이 다르기 때문이다((3)).
- ★ **`memcpy` 자체가 `restrict` 서명**이다((6)) — 컴파일러는 **약속을 약속으로 갈아 끼운 것**이다.

비용 — **어긴 호출의 결과가 이제 「라이브러리의 `memcpy` 가 겹침에 무엇을 하느냐」에 달린다.** 컴파일러의 것도 아니게 된다.

### (3) ★★★ 약속을 어기면 — 값이 판마다 갈린다(관찰)

**언제 쓰나** — 「`restrict` 를 붙였는데 호출자가 겹치게 넘기면」을 물을 때. ★★★ **이 절의 값은 전부 UB 의 한 판 결과**다.

```c
/* s33b2.c */
#include <stdio.h>

int  twice_read(const int *p, int *q);
int  twice_read_r(const int *restrict p, int *restrict q);
void copy_plain(int *d, const int *s, int n);
void copy_restrict(int *restrict d, const int *restrict s, int n);

static void show(const char *tag, const int *a) {
    printf("%-14s", tag);
    for (int i = 0; i < 8; i++) printf(" %d", a[i]);
    printf("\n");
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int x = 7, *p = &x, *q = &x;           /* 두 포인터가 같은 x */
    printf("twice_read   (p, q) = %d\n", twice_read(p, q));
    x = 7;
    printf("twice_read_r (p, q) = %d\n", twice_read_r(p, q));

    int a[8], b[8];
    for (int i = 0; i < 8; i++) a[i] = b[i] = i;
    copy_plain(a + 1, a, 7);               /* 목적지가 원본보다 한 칸 뒤 */
    copy_restrict(b + 1, b, 7);
    show("copy_plain", a);
    show("copy_restrict", b);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s33b1.c s33b2.c -o x ; ./x (cc exit=0 · run exit=0) =====
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
```

```text
===== 약속을 어긴 호출 — 같은 x 를 두 포인터로 · 겹치는 두 배열 (두 파일 모두 -std=c17 -Wall -Wextra -pedantic + 최적화 수준) (exit=0) =====
--- gcc -O0
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- gcc -O1
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- gcc -O2
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
--- clang -O0
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- clang -O1
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
--- clang -O2
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
```

그림 해설 (한 단계씩):

- ★★★ **`twice_read` 는 여섯 벌 다 `7`** 이다 — `restrict` 가 없으니 **겹쳐도 합법**이고, `7 + 0` 이 **옳은 답**이다(31편과 같다).
- ★★★ **`twice_read_r` 은 `-O0` 에서 `7`, `-O1`/`-O2` 에서 `14`** 다 — (1)의 어셈블리 그대로다. `*q = 0` 을 **쓰고도** 처음 읽은 `7` 을 **두 번 더했다.**
- ★★★ **`copy_plain` 은 여섯 벌 다 `0 0 0 0 0 0 0 0`** — 한 칸 뒤로 복사하는 루프를 **앞에서부터 한 칸씩** 돌면 `a[0]` 이 끝까지 번진다. **이것이 C 의 뜻**이다.
- ★★ **`copy_restrict` 는 판에 따라 `0 0 1 2 3 4 5 6`** 이 나온다 — gcc `-O2` · clang `-O1`/`-O2`. **(2)의 `jmp memcpy` 판**들이다. **gcc `-O1` 은 `0 0 0 …`** 이다 — 그 판은 루프를 안 바꿨다.
- ★★ **`0 0 1 2 3 4 5 6` 은 `memmove` 의 결과와 같다** — 이 glibc 의 `memcpy` 가 **겹친 영역을 `memmove` 처럼** 처리했다((6)의 격자). **그것도 관찰**이다.

★★★ **여기서 처방을 적지 않는다** — 「`-O1` 이면 안전하다」도 「`-O0` 에서 시험하라」도 틀린 말이다. **UB 가 갈리는 자리는 어디에 넣어야 갈린다는 처방이 없다**(규칙). 결론은 한 줄이다 — **어긴 호출은 뜻이 없다.**

### (4) ★★ sanitizer 는 `restrict` 를 보나 — 탐침 여덟 · 제5의 상태

**언제 쓰나** — 「ASan·UBSan 으로 돌리면 잡히겠지」라고 생각할 때.

★★★ **탐침 수를 먼저 선언한다** — 컴파일러 2 × sanitizer 2(ASan · UBSan) × 최적화 2 = **8칸**, 칸마다 **두 위반**(`twice_read_r` · `copy_restrict`)을 한 번에 돌린다.

```text
===== sanitizer 탐침 — 컴파일러 2 × sanitizer 2 × 최적화 2 (s33b1.c + s33b2.c) (exit=0) =====
gcc    address    -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
gcc    address    -O2  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 14
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
gcc    undefined  -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
gcc    undefined  -O2  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 14
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
clang  address    -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
clang  address    -O2  run exit=1   리포트 1줄 | ERROR: AddressSanitizer: memcpy-param-overlap
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 14
clang  undefined  -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
clang  undefined  -O2  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
답한 칸 1 / 8
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s33b1.c s33b2.c -o x && ./x 2>&1 >/dev/null | grep -oE '^==[0-9]+==ERROR: AddressSanitizer: [a-z-]+|^ +#1 .*|^SUMMARY: AddressSanitizer: [a-z-]+' (exit=1) =====
==487774==ERROR: AddressSanitizer: memcpy-param-overlap
    #1 0x63f49b4d1d9f in copy_restrict s33b1.c:20:38
SUMMARY: AddressSanitizer: memcpy-param-overlap
```

```text
===== sanitizer 를 켜면 copy_restrict 의 번역이 바뀌나 — 컴파일러 2 × sanitizer 3 (-std=c17 -O2 -S) (exit=0) =====
컴파일러 sanitizer (-O2)  | copy_restrict 몸통에서 memcpy 가 나오는 줄
gcc      (없음)           | 1 줄
gcc      address          | 0 줄
gcc      undefined        | 0 줄
clang    (없음)           | 1 줄
clang    address          | 2 줄
clang    undefined        | 0 줄
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -fsanitize=undefined s33b1.c s33b2.c -o x ; ./x (cc exit=0 · run exit=0) =====
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
```

그림 해설 (한 단계씩):

- ★★★ **답한 칸 1 / 8** — clang `-O2` ASan 한 칸이 **`memcpy-param-overlap`** 을 냈다. 스택의 `#1` 이 **`copy_restrict s33b1.c:20:38`** — 루프 자리다.
- ★★★ **그 1칸은 `restrict` 를 본 것이 아니다** — (2)에서 루프가 **`memcpy` 호출**이 됐고, ASan 은 **`memcpy` 를 가로채서** 겹침을 잰다. **gcc `-O2` ASan 은 같은 소스에서 침묵**했다 — 그 판은 **ASan 을 켜자 루프를 `memcpy` 로 안 바꿨다**(어셈블리 격자의 `gcc address` **0 줄** · 실행 값도 `0 0 0 …`). **UBSan 을 켜도 두 컴파일러 다 0 줄**이다.
- ★★★ **`twice_read_r(p, q)` 는 여덟 칸 전부 침묵**이다 — `memcpy` 가 없는 위반은 **어떤 칸도 못 봤다.**
- ★★ **sanitizer 가 증상을 지운 칸이 있다** — clang `-O2` UBSan 에서 `twice_read_r` 이 **`7`** 이다(맨 아래 블록). sanitizer 없는 clang `-O2` 는 `14` 였다. **같은 소스 · 같은 `-O2` 에서 플래그 하나로 값이 바뀌었으니 번역이 바뀐 것**이다. 그래서 「sanitizer 판에서 값이 맞았다」는 **아무것도 증명하지 않는다.**
```text
   restrict 위반 두 개                 ASan                          UBSan
   ------------------------------      ----------------------------  ----------------------------
   twice_read_r(p, q)                  못 본다 (8칸 중 0)              못 본다
   copy_restrict(b + 1, b, 7)          루프가 memcpy 로 바뀐 판에서만   못 본다
                                       memcpy 를 가로채 본다(1칸)
```

- ★ **「돌려 봤다 · 침묵했다」는 「없다」가 아니다** — 이 판의 두 도구는 **`restrict` 를 검사하는 기능이 없다**는 관찰이다.

### (5) ★★ 컴파일러 경고 — 글자로 같은 인자만

**언제 쓰나** — 「같은 것을 두 `restrict` 매개변수에 넘기면 컴파일러가 말해 주겠지」라고 생각할 때.

```c
/* s33d.c */
int twice_read_r(const int *restrict p, int *restrict q);

int by_address(void) {
    int x = 7;
    return twice_read_r(&x, &x);
}

int by_variables(void) {
    int x = 7, *p = &x, *q = &x;
    return twice_read_r(p, q);
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s33d.c -o /dev/null (cc exit=0) =====
s33d.c: In function ‘by_address’:
s33d.c:5:29: warning: passing argument 2 to ‘restrict’-qualified parameter aliases with argument 1 [-Wrestrict]
    5 |     return twice_read_r(&x, &x);
      |                         ~~  ^~
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s33d.c -o /dev/null (cc exit=0) =====
s33d.c: In function ‘by_address’:
s33d.c:5:29: warning: passing argument 2 to ‘restrict’-qualified parameter aliases with argument 1 [-Wrestrict]
    5 |     return twice_read_r(&x, &x);
      |                         ~~  ^~
```

```text
===== gcc -std=c17 -O2 -c s33d.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -c s33d.c -o /dev/null (cc exit=0) =====
```

- ★★★ **gcc 는 `by_address` 만 잡는다** — `twice_read_r(&x, &x)` 는 **글자로 같은 인자**라 `-Wrestrict` 가 본다. `-O0` 에서도 같고, **`-Wall` 을 빼면 0건**이다(`-Wall` 이 켠다).
- ★★★ **`by_variables` 는 경고 0건** — `p` 와 `q` 가 **둘 다 `&x`** 인데 못 본다. 값을 따라가지 않는다.
- ★★ **clang 은 둘 다 0건**이다 — `-Wall -Wextra -pedantic` 에서 **이 판의 clang 에는 대응하는 경고가 없다.**
- ★ **셋 다 `cc exit=0`** 이다 — 경고여도 **빌드는 통과**한다.

### (6) ★★ `memcpy` 와 `memmove` — 서명에 적힌 약속

**언제 쓰나** — 겹칠 수 있는 영역을 복사할 때 **둘 중 무엇을 부르나** 정할 때.

```text
===== grep -n -A1 -E '^extern void \*(memcpy|memmove) ' /usr/include/string.h | expand (exit=0) =====
43:extern void *memcpy (void *__restrict __dest, const void *__restrict __src,
44-                  size_t __n) __THROW __nonnull ((1, 2));
--
47:extern void *memmove (void *__dest, const void *__src, size_t __n)
48-     __THROW __nonnull ((1, 2));
```

```c
/* s33e.c */
#include <stdio.h>
#include <string.h>

static char a[64] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz";
static char b[64] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz";

int main(int argc, char **argv) {
    (void)argv;
    size_t n = 30 + (size_t)argc;          /* 컴파일러가 크기를 모르게 — 31 */
    memmove(a + 2, a, n);
    memcpy(b + 2, b, n);                   /* 겹친다 */
    printf("memmove : %s\n", a);
    printf("memcpy  : %s\n", b);
    printf("same?   : %s\n", strcmp(a, b) == 0 ? "yes" : "no");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s33e.c -o x ; ./x (cc exit=0 · run exit=0) =====
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
```

```text
===== 겹치는 영역에 memmove 와 memcpy — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
--- gcc -O2 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
--- clang -O0 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
--- clang -O2 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s33e.c -o x && ./x 2>&1 >/dev/null | grep -oE '^==[0-9]+==ERROR: AddressSanitizer: [a-z-]+|^ +#1 .*|^SUMMARY: AddressSanitizer: [a-z-]+' (exit=1) =====
==487989==ERROR: AddressSanitizer: memcpy-param-overlap
    #1 0x5cc438b9d288 in main s33e.c:11
SUMMARY: AddressSanitizer: memcpy-param-overlap
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s33e.c -o x && ./x 2>&1 >/dev/null | grep -oE '^==[0-9]+==ERROR: AddressSanitizer: [a-z-]+|^ +#1 .*|^SUMMARY: AddressSanitizer: [a-z-]+' (exit=1) =====
==487994==ERROR: AddressSanitizer: memcpy-param-overlap
    #1 0x59d16745a77f in main s33e.c:11:5
SUMMARY: AddressSanitizer: memcpy-param-overlap
```

```text
   memcpy (void *__restrict dest, const void *__restrict src, size_t n)
            -> "dest 와 src 가 안 겹친다"를 서명이 요구한다      겹치면 UB (표준 문장)

   memmove(void *dest,            const void *src,            size_t n)
            -> 약속이 없다                                     겹쳐도 뜻이 있다
```

- ★★★ **헤더가 약속을 서명으로 적는다** — glibc `string.h` 의 `memcpy` 두 포인터에 **`__restrict`**, `memmove` 에는 **없다.** 표준 문장도 같다 — **`memcpy` 는 겹치면 UB**, `memmove` 는 **임시 배열을 거친 것처럼** 동작한다.
- ★★★ **이 판에서는 겹친 `memcpy` 가 `memmove` 와 같은 글자를 냈다** — 네 벌 다 `same? : yes`. ★★ **이것은 이 glibc 의 관찰**이다. 다른 libc · 다른 크기 · 다른 CPU 에서 같다는 근거가 **이 문서에 없다.**
- ★★★ **ASan 은 두 컴파일러 다 `memcpy-param-overlap`** 으로 잡는다 — `s33e.c:11` 이 그 `memcpy` 줄이다. **이것이 ASan 이 겹침을 보는 유일한 경로**다((4)의 1칸과 같은 기능).

비용 — **`memmove` 는 약속이 없는 대신 겹침을 처리한다.** 「겹칠 수 있다」를 **호출자가 모르면** `memmove` 쪽이 뜻이 있는 선택이다(속도는 **재지 않았다**).

### (7) ★ C++ 에는 `restrict` 가 없다

**언제 쓰나** — C 헤더를 C++ 에서 쓰거나, C 코드를 C++ 로 옮길 때.

```cpp
// s33x.cpp
int twice_read_r(const int *restrict p, int *restrict q) {
    int a = *p;
    *q = 0;
    return a + *p;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s33x.cpp -o /dev/null (cc exit=1) =====
s33x.cpp:1:38: error: expected ‘,’ or ‘...’ before ‘p’
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                                      ^
s33x.cpp: In function ‘int twice_read_r(const int*)’:
s33x.cpp:2:14: error: ‘p’ was not declared in this scope
    2 |     int a = *p;
      |              ^
s33x.cpp:3:6: error: ‘q’ was not declared in this scope
    3 |     *q = 0;
      |      ^
s33x.cpp:1:29: warning: unused parameter ‘restrict’ [-Wunused-parameter]
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                  ~~~~~~~~~~~^~~~~~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s33x.cpp -o /dev/null (cc exit=1) =====
s33x.cpp:1:38: error: expected ')'
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                                      ^
s33x.cpp:1:17: note: to match this '('
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                 ^
s33x.cpp:2:14: error: use of undeclared identifier 'p'
    2 |     int a = *p;
      |              ^
s33x.cpp:3:6: error: use of undeclared identifier 'q'
    3 |     *q = 0;
      |      ^
s33x.cpp:4:17: error: use of undeclared identifier 'p'
    4 |     return a + *p;
      |                 ^
s33x.cpp:1:29: warning: unused parameter 'restrict' [-Wunused-parameter]
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                             ^
1 warning and 4 errors generated.
```

```cpp
// s33x2.cpp
int twice_read_r(const int *__restrict__ p, int *__restrict__ q) {
    int a = *p;
    *q = 0;
    return a + *p;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s33x2.cpp -o /dev/null (cc exit=0) =====
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s33x2.cpp -o /dev/null (cc exit=0) =====
```

```text
===== g++ -std=c++17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33x2.cpp -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
_Z12twice_read_rPKiPi:
.LFB0:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
.LFE0:
```

- ★★★ **C++17 에서 `restrict` 는 키워드가 아니다** — 두 컴파일러 다 **선언이 깨져** `cc exit=1` 이다(g++ 는 `restrict` 를 **매개변수 이름**으로 읽었다 — `unused parameter 'restrict'`).
- ★★ **`__restrict__` 는 받는다** — **`-pedantic` 에서도 경고 0건 · `cc exit=0`**(두 컴파일러). 이름에 밑줄 둘이 붙은 **구현 확장**이라 `-pedantic` 이 문제 삼지 않는다.
- ★★ **번역도 C 와 같다** — `add eax, eax`, `*p` 를 **한 번** 읽는다.
- ★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))은 `restrict` 를 **주제로 세우지 않았다**(C 쪽에 둔다고 적었다).

## 문법 — 형태와 규칙

### 형태

(1)의 `s33a.c` · (2)의 `s33b1.c` 가 이 절의 **실제로 컴파일되는 형태**다. 쓰는 자리를 한 줄씩:

| 쓴 꼴 | 자리 | 뜻 | 층 |
|---|---|---|---|
| `int *restrict p` | 매개변수 | 이 블록에서 `*p` 가 고쳐진다면 **모든 접근이 `p` 기반** | ★★★ 표준(어기면 UB) |
| `int *restrict p, int *q` | 한쪽만 | ★ **한쪽만으로도** 두 번째 읽기가 사라졌다((1)) | 표준 |
| `const int *restrict p` | 읽기 전용 쪽 | `const` 는 「내가 안 고친다」 + `restrict` 는 「남도 이 경로 밖으로 안 고친다」 | 표준 |
| `void *memcpy(void *restrict, const void *restrict, size_t)` | 라이브러리 서명 | **겹치면 UB** | ★★★ 표준 |
| `__restrict__` / `__restrict` | C++ · 헤더 | 구현 확장 | ★ 구현 정의(확장) |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| `twice_read_r(p, q)` — `p`·`q` 가 같은 `x` | 경고 0 · 값이 `7`/`14` 로 갈림 · sanitizer **8칸 침묵** | ★★★ UB | (3)·(4) |
| `twice_read_r(&x, &x)` | gcc `-Wrestrict` **경고 · `cc exit=0`** · clang 0 | ★★★ UB | (5) |
| `copy_restrict(b + 1, b, 7)` | 경고 0 · `-O2` 에서 **`memmove` 같은 값** · clang ASan `memcpy-param-overlap` 1칸 | ★★★ UB | (3)·(4) |
| 겹치는 영역에 `memcpy` | 경고 0 · 이 glibc 에서 `memmove` 와 같음 · ASan **두 컴파일러 다 잡음** | ★★★ UB | (6) |
| `-std=c89` 에서 `restrict` | **에러 · `cc exit=1`** | 판 경계(C99 부터) | (1) |
| C++ 에서 `restrict` | **에러 · `cc exit=1`** | C++ 에 없다 | (7) |

### 규칙 불릿

- ★★★ **`restrict` 는 「어기면 UB」라는 조건이다** — 컴파일러는 그 조건 덕에 **겹치는 경우를 고려하지 않는다.**
- ★★★ **적격한 프로그램에서 `restrict` 를 전부 지워도 뜻이 안 바뀐다** — 표준 문장이다. **차이는 어긴 프로그램에만** 있다.
- ★★★ **약속을 지키는 것은 호출자다** — 서명을 쓴 쪽이 아니라 **부르는 쪽**이 겹치지 않게 넘겨야 한다.
- ★★ **한쪽만 `restrict` 여도 된다** — 형식 정의가 「그 객체의 **다른 모든 접근**」을 묶는다.
- ★★ **`-O0` 에서는 번역이 안 바뀐다** — `restrict` 는 허락이지 명령이 아니다.
- ★★ **`memcpy` 는 겹치면 UB, `memmove` 는 뜻이 있다** — 서명의 `restrict` 가 그 차이를 적는다.
- ★ **C99 부터**, **C++ 에는 없다**(`__restrict__` 확장).

## 어디서 틀리나

### 1. ★★★ 「`restrict` 를 붙이면 빨라진다」

**재지 않았다** — 이 편은 **로드 수**만 셌다(2 → 1). 빨라지는지는 **시간을 재야** 아는 것이고, 그 전에 **약속이 참인지**가 먼저다.

### 2. ★★★ 「`restrict` 는 컴파일러가 검사해 주는 약속이다」

**거의 아무도 검사하지 않는다**((4)·(5)). gcc 는 **글자로 같은 인자**만, sanitizer 는 **`memcpy` 로 번역된 것**만 봤다. **어긴 호출 대부분은 경고 0 · 리포트 0 으로 돈다.**

### 3. ★★★ 「어긴 호출을 돌려 봤더니 값이 맞더라」

**`-O0` 은 `7`, `-O2` 는 `14`** 였다((3)). sanitizer 판에서는 **맞는 값이 나와 증상이 사라졌다**((4)). **맞은 판은 어떤 것도 증명하지 않는다.**

### 4. ★★ 「`const` 를 붙였으니 컴파일러가 한 번만 읽겠지」

**`const` 로는 안 된다** — [31번 형제](../31-const-and-pointer-const-placement/)가 두 번 읽었다. **「겹치지 않는다」를 말하는 한정자는 `restrict`** 다.

### 5. ★★ 「`memcpy` 로 겹치게 복사해도 되더라」

**이 glibc 판의 관찰**이다((6)). 표준은 **UB** 라고 적고, ASan 은 **잡는다.** 겹칠 수 있으면 `memmove`.

### 6. ★ 「C++ 에서도 `restrict` 를 쓰면 된다」

**에러**다((7)). `__restrict__` 는 **확장**이다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「UB」 칸이 본체**다 — `restrict` 의 뜻 전부가 「**어기면 UB**」라는 한 줄에 있다.\
★★★ **「표준」 칸은 짧다** — 형식 정의와 「지워도 뜻이 같다」 두 줄이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★ **표준** | 어느 구현에서도 같다 | ★★★ **`restrict` 의 형식 정의**(고쳐지는 객체의 모든 접근이 그 포인터 기반) · ★★ **적격한 프로그램에서 지워도 뜻이 같다** · `memcpy` 겹침 UB · `memmove` 는 겹쳐도 뜻이 있다 · C99 부터 키워드 | 표준 문장 · `twice_read` 여섯 벌 `7` · `copy_plain` 여섯 벌 `0 …` · `-std=c89` 에러 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** — `restrict` 는 선택 기능이 아니다 | — |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★ **`__restrict__`·`__restrict` 확장**(C++·헤더) · 명령 선택(`add eax, eax` · `jmp memcpy`) · ★ `-Wrestrict` 같은 경고의 **유무와 범위** | g++ `exit=0` · 어셈블리 · gcc 경고 1 · clang 0 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음**(이 편이 던진 것 중에는) | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **`restrict` 약속을 어긴 모든 접근** · **겹치는 영역의 `memcpy`** | `7`/`14` · `0 0 1 2 …` · sanitizer 1 / 8 · ASan `memcpy-param-overlap` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★ **표준** | ★ **`restrict` 가 「필요한데 빠진」 자리**는 아무도 말하지 않는다 — 빠지면 **느려질 수 있을 뿐 틀리지 않으므로** 당연하다 |
| **조건부 표준** | — |
| ★★ **구현 정의** | ★ **clang 에는 `-Wrestrict` 에 해당하는 경고가 이 판에 없다**((5)) |
| **미명시** | — |
| ★★★ **UB** | ★★★ **`restrict` 위반은 탐침 8칸 중 1칸만 답했다** — 그것도 **`memcpy` 로 번역된 위반**이다. ★★★ **`twice_read_r(p, q)` 는 경고 0 · 리포트 0 · 여덟 칸 침묵.** ★★ **sanitizer 가 번역을 바꿔 증상을 지운 칸**(clang UBSan `7`) |
| ★★ **(층을 가로지름)** | ★ **「종료 코드가 0인데 ill-formed」는 이 편에 새 항목이 없다** — `restrict` 위반은 **문법이 아니라 실행의 문제**라 전부 적격한 프로그램이다. ★★ 대신 **「종료 코드 0인데 UB」가 셋**이다(금지 사례 표의 위 세 줄) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **`restrict` 는 도구가 못 보는 약속이다** — 이 판의 도구 중 **`restrict` 자체를 보는 것은 없었다.** 남은 창은 **코드 리뷰와 서명 읽기**다.
  - ★★★ **ASan 이 답한 1칸은 우연한 창**이다 — 컴파일러가 루프를 `memcpy` 로 바꿨기 때문에 열렸고, **같은 소스의 gcc 판에서는 안 열렸다.**
  - ★★ **sanitizer 판의 「맞는 값」은 가장 위험한 근거**다 — 계측이 번역을 바꿔 증상이 사라졌다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 겹치지 않는 두 버퍼를 받는 함수 | ★★ **`restrict`** — 단 **호출자 모두가 지킨다는 것을 확인한 뒤** | 「빨라질 것 같아서」 붙이기(재지 않았다) |
| 겹칠 수도 있는 복사 | ★★★ **`memmove`** | ★★★ `memcpy`(겹치면 UB) |
| 겹치지 않는 게 확실한 복사 | ★★ `memcpy` | — |
| 「`*p` 를 다시 읽지 마라」 | ★ `restrict` 또는 **지역 변수에 한 번 받아 두기** | `const`(다시 읽는다 — 31편) |
| C++ 에서 같은 약속 | ★ `__restrict__`(확장 — **이식성 없다**) | `restrict`(에러) |
| 위반을 찾기 | ★ **리뷰** + `memcpy` 로 바뀌는 자리는 ASan | ★★ 「sanitizer 가 조용했다」로 안심하기 |

판단 규칙 두 줄.

- ★★★ **「이 함수를 부르는 모든 곳이 겹치지 않게 넘기나」를 증명할 수 없으면 붙이지 않는다** — 어긴 호출을 잡아 줄 도구가 없다.
- ★★ **라이브러리를 부를 때는 서명의 `restrict` 를 읽는다** — `memcpy` 의 두 `__restrict` 가 곧 「겹치면 안 된다」는 문서다.

## 핵심 문장

- ★★★ **`restrict` 는 「이 포인터로 접근하는 객체가 고쳐진다면 다른 접근도 전부 이 포인터 기반」이라는 약속이고, 어기면 UB 다.**
- ★★★ **31편의 `twice_read` 는 `*p` 를 두 번 읽었고, `restrict` 를 붙인 같은 함수는 `-O2` 에서 한 번(`add eax, eax`) 읽었다** — 두 컴파일러 같은 모양 · 한쪽만 붙여도 같다 · `-O0` 은 2 번.
- ★★★ **`restrict` 복사 루프는 `-O2` 에서 `jmp memcpy` 가 됐다.**
- ★★★ **약속을 어긴 호출은 `-O0` `7` · `-O2` `14` 로 갈렸다** — UB 의 관찰이지 결론이 아니다.
- ★★★ **sanitizer 탐침 8칸 중 1칸만 답했다** — 그것도 `memcpy` 로 번역된 판의 ASan `memcpy-param-overlap` 이다. clang UBSan 은 **증상까지 지웠다.**
- ★★ **gcc `-Wrestrict` 는 `&x, &x` 처럼 글자로 같은 인자만 잡고, clang 은 0건이다.**
- ★★ **`memcpy` 서명에는 `restrict` 가 있고 `memmove` 에는 없다** — 이 glibc 는 겹친 `memcpy` 를 `memmove` 처럼 처리했다(관찰).
- ★ **적격한 프로그램에서 `restrict` 를 다 지워도 뜻은 같다** — 차이는 어긴 프로그램에만 있다.

## 관련 자료

- [31번 형제 — `const` 와 포인터 const 위치](../31-const-and-pointer-const-placement/) — ★★★ **직접 선행.** `twice_read` 의 「두 번 읽기」가 이 편의 출발점이다. `const` 는 **「내가 안 고친다」**, `restrict` 는 **「이 경로 밖으로 아무도 안 고친다」**.
- [32번 형제 — `volatile` 이 실제로 보장하는 것](../32-what-volatile-actually-guarantees/) — ★★ **같은 세기 방식**(로드·스토어 수). `volatile` 은 **읽기를 늘리는 쪽**, `restrict` 는 **줄이는 쪽**이다.
- 목록의 **55번 주제** — ★★★ **경계.** **타입이 다른 두 포인터**의 앨리어싱(엄격한 앨리어싱 규칙)은 그쪽이 정본이다. 이 편은 **같은 타입**의 겹침만 본다.
- [14번 형제 — 포인터](../14-pointers-address-dereference-and-pointer-types/) — ★ 포인터 값과 가리키는 값의 구분.
- 목록의 **58번 주제** — sanitizer **사용법**의 정본.
- ★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)) — `restrict` 를 **주제로 세우지 않았다**(C 의 **33번**으로 넘겼다).

## 용어 풀이

> **앨리어싱** — 두 이름이 같은 메모리를 가리키는 것.\
> 예: `p` 와 `q` 가 둘 다 `&x`.

> **`restrict`** — 「이 포인터로 접근하는 객체가 고쳐진다면, 그 객체의 다른 접근도 전부 이 포인터 기반」이라는 한정자. 어기면 UB.\
> 예: `int *restrict d`.

> **기반한다(based on)** — 표준의 낱말. 「그 포인터를 다른 사본을 가리키게 바꾸면 이 식의 값도 바뀐다」면 그 포인터에 기반한 식이다.\
> 예: `p + 1` 은 `p` 에 기반하고, 따로 받은 `q` 는 기반하지 않는다.

> **`memcpy` / `memmove`** — 바이트 복사 함수. `memcpy` 는 **겹치면 UB**, `memmove` 는 겹쳐도 **임시 배열을 거친 것처럼** 복사한다.\
> 예: `memmove(a + 2, a, n)`.

> **`-Wrestrict`** — gcc 의 경고. 같은 인자를 두 `restrict` 매개변수에 넘기는 것을 **보이는 범위에서** 잡는다. `-Wall` 에 든다.\
> 예: `twice_read_r(&x, &x)`.

> **`memcpy-param-overlap`** — ASan 이 `memcpy` 호출을 가로채 **두 영역이 겹칠 때** 내는 리포트 이름.\
> 예: `copy_restrict` 가 `memcpy` 로 번역된 판.

> **`__restrict__`** — gcc·clang 의 확장 낱말. C++ 에서도 `restrict` 처럼 쓴다. **표준이 아니다.**\
> 예: `int *__restrict__ q`.

## 더 들어가면

- ★★ **이 glibc 의 `memcpy` 가 왜 겹침을 `memmove` 처럼 처리했나** — 구현 선택(같은 코드 경로를 쓰는지)은 **캐지 않았다.** 이 편은 결과만 관찰했다.
- ★★ **`restrict` 를 붙인 루프가 벡터화되는 판** — 이 판은 `memcpy` 호출로 바꿨다. **`-fno-builtin` 같은 플래그로 막으면** 다른 번역이 나올 것이다. ★ **던지지 않았다.**
- ★ **블록 스코프의 `restrict` 지역 포인터** — 매개변수만 던졌다. ★ **던지지 않았다.**
- ★ **gcc `-fanalyzer` · clang `--analyze`** — 이 편의 위반에 무엇을 말하나. ★ **캡처하지 않았다**(예비로 돌렸을 때 `restrict` 관련 새 경고는 없었지만 블록으로 남기지 않았으므로 근거로 쓰지 않는다).
- ★ **C23 의 `restrict` 와 배열 매개변수 `int a[restrict 10]`** — 형태만 있다. ★ **던지지 않았다.**
