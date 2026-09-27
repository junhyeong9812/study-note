# cpp/syntax/22 — 연산자 오버로딩 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「이 줄이 컴파일되나」를 맞히는 것**이 절반이다 — 「연산자를 정의했으니 된다」로 뭉개지 말고
> **어느 자리가 변환되고 어느 자리가 안 되는가**를 따라가야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「두 컴파일러의 에러 전문」이다**(1번).
> ★ **「부적용인 창」이 둘 있다** — ASan(메모리 오류가 없다)과 어셈블리(평범한 함수 호출이라 잴 비용이 없다).
> ★★★ **이 편의 1번이 [23번](../23-three-way-comparison-spaceship/)의 급소로 이어진다** — 비교 연산자에서는 규칙이 바뀐다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 멤버 `operator+` 에 정수를 섞으면 (예측)

```cpp
/* opov01.cpp */
// operator+ 를 멤버로 둔다 — a + 1 은 되는데 1 + a 는 되나
struct Money {
    long won;
    Money(long w) : won(w) {}                        // 암묵 변환 생성자 — long 에서 Money 로
    Money operator+(const Money& o) const { return Money(won + o.won); }   // ★ 멤버
};

int main() {
    Money a(1000);
    Money b = a + a;                                 // 1. Money + Money
    Money c = a + 1;                                 // 2. Money + 정수 — 오른쪽이 변환된다
    Money d = 1 + a;                                 // 3. 정수 + Money — 왼쪽도 변환되나
    (void)b; (void)c; (void)d;
}
```

- 1\~3번 중 **어느 줄이 에러**인가?
- ★★★ 2번은 되는데 3번은 안 된다면 — **두 자리의 차이**는 무엇인가?
- ★★ 같은 연산자를 **비멤버(숨은 friend)** 로 옮기면 3번은 되나 — 그때 로그에 찍히는 첫 인자는?

### 2. ★★ 비멤버로 옮겼는데 생성자에 `explicit` 을 붙이면 (예측)

```cpp
/* opov12.cpp */
// 비멤버로 옮겼는데 생성자에 explicit 을 붙이면 — 대칭은 무엇 덕분이었나
struct Money {
    long won;
    explicit Money(long w) : won(w) {}                         // ★ 암묵 변환을 막았다
    friend Money operator+(const Money& l, const Money& r) { return Money(l.won + r.won); }
};

int main() {
    Money a(1000);
    Money b = a + a;                                 // 1. Money + Money
    Money c = a + 1;                                 // 2. Money + 정수
    Money d = 1 + a;                                 // 3. 정수 + Money
    (void)b; (void)c; (void)d;
}
```

- 1\~3번 중 **몇 줄이 에러**인가?
- ★★ 그러면 (1)의 대칭을 만든 것은 **비멤버**였나, 다른 무엇이었나?

### 3. ★★ `operator<<` 를 멤버로 두면 (예측)

```cpp
/* opov03.cpp */
// operator<< 를 멤버로 두면 — 왼쪽 피연산자가 무엇이어야 하나
#include <iostream>

struct Pt {
    int x, y;
    std::ostream& operator<<(std::ostream& os) const {        // ★ 멤버 — 왼쪽이 Pt 다
        return os << '(' << x << ", " << y << ')';
    }
};

int main() {
    Pt p{1, 2};
    p << std::cout << '\n';                    // 1. 거꾸로 쓰면 된다
#ifdef CONVENTIONAL
    std::cout << p << '\n';                    // 2. 관례대로 쓰면
#endif
}
```

- ★★ 1번(`p << std::cout`)은 컴파일되나 — 된다면 무엇이 찍히나?
- ★★ `-DCONVENTIONAL` 로 2번(`std::cout << p`)을 켜면 에러인가 — g++ 진단은 **대략 몇 줄**인가?
- ★ 그래서 `operator<<` 를 **어디에 어떤 반환 타입으로** 두나?

### 4. ★★ `operator[]` 두 벌과 C++23 deducing `this` (예측)

```cpp
/* opov05.cpp */
// C++23 「deducing this」 — operator[] 두 벌을 하나로 합친다. 이 판의 컴파일러가 받나
#include <cstdio>
#include <type_traits>

struct Row {
    int a[3]{10, 20, 30};
    template <class Self>
    auto&& operator[](this Self&& self, int i) {           // ★ 명시적 객체 매개변수
        std::printf("      Self 가 const 인가: %d\n",
                    (int)std::is_const_v<std::remove_reference_t<Self>>);
        return self.a[i];
    }
};

int main() {
    Row r;
    const Row& cr = r;
    r[0] = 99;
    int x = cr[0];
    std::printf("    x=%d\n", x);
    std::printf("    decltype(cr[0]) 가 const int& 인가: %d\n",
                (int)std::is_same_v<decltype(cr[0]), const int&>);
}
```

- ★★★ 이 파일을 **g++ 13 `-std=c++23`** · **clang 18 `-std=c++23`** · **clang 18 `-std=c++20`** 으로 던지면 각각 되나?
- ★★ 되는 판에서 `Self 가 const 인가` 는 두 호출에서 각각 무엇인가?
- ★★ `__cpp_explicit_this_parameter` 매크로는 **되는 판에서** 정의돼 있나?

### 5. ★★ 람다와 함수 객체의 크기 (예측)

```cpp
/* opov06.cpp */
// operator() 와 함수 객체 — 람다는 operator() 를 가진 이름 없는 클래스인가
#include <cstdio>
#include <string>
#include <type_traits>

struct Adder {                                   // 손으로 쓴 함수 객체
    int k;
    int operator()(int x) const { return x + k; }
};

int main() {
    int k = 5; long big = 7; std::string s = "abc";
    Adder add{k};
    auto lam0 = [](int x) { return x + 1; };             // 캡처 없음
    auto lam1 = [k](int x) { return x + k; };            // int 하나를 값으로
    auto lam2 = [&k](int x) { return x + k; };           // int 하나를 참조로
    auto lam3 = [k, big](int x) { return x + k + big; }; // int + long
    auto lam4 = [s](int x) { return x + (int)s.size(); };// string 하나를 값으로

    std::printf("(1) add(1)=%d · lam1(1)=%d · lam1.operator()(1)=%d\n", add(1), lam1(1), lam1.operator()(1));
    std::printf("(2) sizeof  Adder %zu · 캡처없음 %zu · [k] %zu · [&k] %zu · [k,big] %zu · [s] %zu\n",
                sizeof(Adder), sizeof(lam0), sizeof(lam1), sizeof(lam2), sizeof(lam3), sizeof(lam4));
    std::printf("(3) is_class<람다> %d · 캡처 없는 람다를 함수 포인터로: %d\n",
                (int)std::is_class_v<decltype(lam1)>, ((int (*)(int))lam0)(41));
    std::printf("(4) 같은 모양의 람다 둘은 같은 타입인가: %d\n",
                (int)std::is_same_v<decltype(lam1), decltype([k](int x) { return x + k; })>);
}
```

- ★★ `(2)` 의 여섯 `sizeof` 는 각각 얼마인가 — `[k,big]` 이 12 인가?
- ★ `lam1.operator()(1)` 은 컴파일되나?
- ★ `(4)` 의 같은 모양 람다 둘은 **같은 타입**인가?

### 6. ★★★ `&&` 를 오버로드한 타입으로 조건을 엮으면 (예측)

```cpp
/* opov07.cpp */
// && 를 오버로드하면 단락 평가가 사라지나 — 양쪽 피연산자에 로그를 심는다
#include <cstdio>

struct Flag {
    bool v;
    explicit operator bool() const { return v; }
};
Flag operator&&(Flag a, Flag b) { std::printf("      operator&& 본체\n"); return Flag{a.v && b.v}; }
Flag operator||(Flag a, Flag b) { std::printf("      operator|| 본체\n"); return Flag{a.v || b.v}; }

bool  left_b()  { std::printf("      왼쪽을 평가했다\n");  return false; }
bool  right_b() { std::printf("      오른쪽을 평가했다\n"); return true;  }
Flag  left_f()  { std::printf("      왼쪽을 평가했다\n");  return Flag{false}; }
Flag  right_f() { std::printf("      오른쪽을 평가했다\n"); return Flag{true};  }
Flag  yes_f()   { std::printf("      왼쪽을 평가했다\n");  return Flag{true};  }

int main() {
    std::printf("(1) 내장 &&   false && …\n");
    bool r1 = left_b() && right_b();
    std::printf("    결과 %d\n", (int)r1);
    std::printf("(2) 오버로드한 &&   Flag{false} && …\n");
    Flag r2 = left_f() && right_f();
    std::printf("    결과 %d\n", (int)r2.v);
    std::printf("(3) 오버로드한 ||   Flag{true} || …\n");
    Flag r3 = yes_f() || right_f();
    std::printf("    결과 %d\n", (int)r3.v);
}
```

- ★★★ `(1)`·`(2)`·`(3)` 에서 「**오른쪽을 평가했다**」가 찍히나?
- ★★ 찍힌다면 **왼쪽과 오른쪽 중 무엇이 먼저**인가 — 그 순서는 보장인가?
- ★ 컴파일러가 이 자리에 경고를 내나?

### 7. ★ 오버로드할 수 없는 연산자 (경계)

- ★★ `.` · `.*` · `::` · `?:` · `sizeof` 를 `operator` 뒤에 적으면 **몇 건의 에러**가 나고, `->*` 는?
- ★ g++ 가 **다섯 중 하나에만 다른 문구**를 쓴다 — 어느 것이고, 왜 그럴까?

### 8. ★★ 멤버여야만 하는 연산자 (경계)

- ★★ `=` · `[]` · `()` · `->` 를 비멤버로 선언하면? · 대조군 `operator+` 는?
- ★ g++ 가 `[]`·`()` 와 `=`·`->` 에 **다른 문구**를 쓰는 이유는 무엇으로 보이나?

### 9. ★★ `-std=c++20` 인데 C++23 문법이 통과하는 자리 (경계)

- ★★ `static int operator()(int)` 를 `-std=c++20 -Wall -Wextra -pedantic` 으로 던지면 **`cc exit`** 는?
- ★★ 그것을 막으려면 무엇을 켜야 하나 — 이 배치의 앞 편들에서 같은 모양이 몇 번 나왔나?

### 10. ★★ 멤버로 둘까 비멤버로 둘까 (왜)

- ★★★ **`+`·`<<`·`+=`·`[]`·`&&`** 각각을 어디에 두나(또는 두지 않나)?
- ★ `+` 를 `+=` 로 만드는 이유는?

### 11. 다른 주제와 잇기 (연결)

- ★★★ (1)의 「`1 + a` 가 막힌다」는 **비교 연산자**에서는 어떻게 되나 — 몇 번 주제인가?
- ★ 숨은 friend 가 찾아지는 길은 몇 번 주제의 무엇인가?
- ★ Rust 에서 같은 대칭은 어떻게 얻나 — 그 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
