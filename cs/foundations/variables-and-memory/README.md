# 변수와 메모리 (컴퓨터사이언스 부트캠프 with 파이썬 ch.1, ch.5)

> 원고: computer_science repo의 따라 친 노트를 구조만 잡아 이관(2026-09-05). 내용 보강 없음 — 원문 유지, 오탈자만 교정.

## 목차

| 원본 파일 | 절 |
|---|---|
| chapter/chapter1.py | 1. 변수와 값 객체 / 2. 얕은 복사와 깊은 복사 |
| docs/shallow_copy.py | 2. 얕은 복사와 깊은 복사 |
| docs/deep_copy.py | 2. 얕은 복사와 깊은 복사 |
| chapter/chapter5.py | 3. 전역 변수와 지역 변수 / 4. 값에 의한 전달과 참조에 의한 전달 / 5. 파이썬의 객체 참조에 의한 전달 / 6. 레퍼런스 카운트와 인터닝 |
| chapter/chapter5-1.py | 7. 불변 객체는 함수 안에서 바꿀 수 없다 — id 실험 |
| chapter/chapter5-2.py | 8. 가변 객체 — 재할당 vs 내부 변경 |
| chapter/chapter5-3.py | 8. 가변 객체 — 재할당 vs 내부 변경 |
| chapter/chapter5-4.py | 9. 람다 함수 |

## 1. 변수와 값 객체

출처: `computer_science/chapter/chapter1.py`

파이썬에서 쓰는 변수는 이름과 값 객체로 나눠진다.

```python
num = 5
type(num)
```

진짜 신기한 점은 보통 `int num = 5` 같은 경우 num은 메모리 공간 자체를 의미하지만, 파이썬은 num이란 게 값 객체의 주소를 의미한다. 즉 5라는 값을 담고 있는 메모리 공간을 의미하는 게 아니라, 값 객체는 다른 메모리 공간에 있다.

파이썬은 PyObject라는 구조체로 이루어진 복합 객체이다. 여기에는 이 객체를 얼마나 많은 변수가 가리키고 있는지 기록한다. 즉 0이 되면 메모리에서 삭제된다.

- reference Count라는 객체 포인터를 기록
- type 정보 — 이 객체가 int인지 str인지 알려준다.
- Value — 우리가 아는 진짜 데이터 5

`a = 5, b = 5`일 경우 파이썬은 동일한 객체의 주소를 가리키며 이를 interning이라 한다.

파이썬은 참조 횟수 계산을 통해 0인 경우 그 즉시 메모리에서 삭제한다. 참조 횟수로 해결하지 못하는 케이스가 순환참조이며, 이러한 것을 해결하는 것이 가비지 컬렉션이다. A 리스트가 B를 가리키고 B가 A를 가리키는 경우입니다.

파이썬은 -5부터 **256**까지의 정수는 프로그램 시작 때 메모리에 딱 하나씩만 미리 만들어놓는다.\
단 이것은 **CPython 구현 세부사항**이지 언어가 보장하는 것이 아니다 — 다른 구현에서는 달라도 된다.\
(2026-09-21 정정: 「254」는 실측과 어긋났다. CPython 3.12.3 에서 경계를 탐색하면 -5 ~ 256 이고 C API 문서도 같다. 자세한 것은 [languages/python/syntax/02-is-vs-eq-interning](../languages/python/syntax/02-is-vs-eq-interning/))

파이썬 메모리 누수 케이스:

1. 전역변수 남용: 리스트를 전역변수로 만들어놓고 데이터를 무한히 append하면, 프로그램이 종료될 때까지 참조 카운트가 0이 되지 않아 메모리가 계속 쌓인다.
2. 캐시 오남용: 성능을 위해 딕셔너리에 데이터를 저장해두고 지우지 않으면 결국 메모리 부족.

## 2. 얕은 복사와 깊은 복사

출처: `computer_science/chapter/chapter1.py`, `computer_science/docs/shallow_copy.py`, `computer_science/docs/deep_copy.py`

1. 얕은 복사(Shallow Copy) — 얕은 복사는 리스트라는 바구니만 새로 하나 더 만드는 것. 바구니 안의 물건들은 원본과 똑같은 주소를 가리킨다. 특징으로는 가장 바깥쪽 리스트는 별개의 메모리 주소를 갖지만, 내부 요소들은 원본과 같은 객체를 공유한다.

2. 깊은 복사(Deep Copy) — 깊은 복사는 재귀적으로 모든 것을 새로 복제한다. 바구니뿐만 아니라 그 안에 들어있는 작은 바구니, 또 그 안의 물건들까지 전부 메모리의 새로운 공간에 복사본을 만든다. 특징으로는 원본과 복사본이 메모리상 완벽하게 독립한다.

파이썬은 얕은 복사를 제공하여 속도를 챙긴다.

```python
# docs/shallow_copy.py
original = [[1,2], [3,4]]
shallow = original.copy()

print(original is shallow)
# False 껍데기 포인터는 다르다.

# 하지만 내부 리스트는 같은 객체이다.
shallow[0][0] = 99
print(original)
# [[99, 2], [3, 4]]
```

```python
# docs/deep_copy.py
import copy

original = [[1, 2], [3, 4]]
deep = copy.deepcopy(original)

# 내부 리스트까지 완전히 다른 객체이다.
deep[0][0] = 99
print(original)
# [[1, 2], [3, 4]]
print(deep)
# [[99, 2], [3, 4]]
```

## 3. 전역 변수와 지역 변수

출처: `computer_science/chapter/chapter5.py`

```python
g_var = 10

def func():
    global g_var
    g_var = 20
    print("g_var = {} in function".format(g_var))
```

함수 안에서 전역 변수 g_var 값의 변경을 시도하기 위해 선언한 것은 메서드 안에 새로운 지역변수를 생성한 것이기 때문에 서로 다르다. 지역변수는 전역변수와 반대의 개념이다. 말 그대로 특정 지역에서만 접근 가능한 변수. 지역변수는 함수 바깥에서는 접근 불가능하며 함수가 호출될 때 생성되었다가 호출이 끝나면 사라지며, 전역변수를 변경하기 위해서는 특별한 문법이 필요하다. 바로 `global`이라는 메서드로 전역 메서드를 저격해야 된다.

```
g_var = 10 in before
g_var = 20 in function
g_var = 20 in after
```

그렇다면 지역변수와 메서드 내의 또다른 지역변수일 경우에는?

```python
a = 1
def outer():
    b = 2
    c = 3
    print(a, b, c)
    def inner():
        d = 4
        e = 5
        print(a, b, c, d, e)
    inner()
# 1 2 3
# 1 2 3 4 5
```

지역 변수에 접근할 수 있는 nonlocal 메서드:

```python
def outer1():
    a = 2
    b = 3

    def inner():
        nonlocal a
        a = 100
    inner()

    print("locals in outer : a = {}, b = {}".format(a, b))
# locals in outer : a = 100, b = 3
```

## 4. 값에 의한 전달과 참조에 의한 전달

출처: `computer_science/chapter/chapter5.py`

함수의 인자 전달 방식에 따라 크게 값에 의한 전달과 참조에 의한 전달로 나눈다. 파이썬은 값에 의한 전달과 참조에 의한 전달 방식을 사용하지 않으므로 설명하기 어렵지만, 함수는 메서드를 정의할 때 컴파일 시점에 자료형을 알려줘야 한다. 결국 우리가 쓰는 `{}` 이건 스코프 영역을 의미한다. 이때 x 자체를 인자로 전달하고 그 값에 밸류값을 넣고 스코프 밖으로 나왔을 때 x가 변하지 않는다. 이때 x를 값에 의한 전달 방식으로 전달했기 때문이다. 함수가 호출될 때는 메모리에 스택 프레임이 생기며, 스택 프레임은 함수의 메모리 공간 즉 지역변수가 존재하는 영역이다.

현재 C++ 코드로 보자.

```cpp
int test(int a, int b);

int main(void){
    int a = 10, b = 5;
    int res = test(a, b);
    cout << "result of test : " << res << endl;
    return 0;
}

int test(int a, int b) {
    int c = a + b;
    int d = a - b;
    return c + d;
}
```

위와 같은 코드가 있다. 즉 위에서 test가 a와 b를 받게 되면 결국 test의 스택 프레임을 보자. 스택 프레임 내에는 a, b, c, d가 존재하는 것이다. 그럼 main의 스택 프레임을 보면 a, b, res가 된다. 즉 a와 b 값이 서로 다른 스택 프레임에 존재하는 것이다. 즉 main의 스택 프레임이 쌓이고 그 위에 test의 스택 프레임이 쌓이는 것이다. 이때 이 공간은 서로 독립적인 공간으로 이 값은 복사된 값임을 알 수 있다. 이때 이처럼 값을 복사해서 전달하는 걸 값에 의한 전달이라 한다.

참조에 의한 전달:

```cpp
void change_value(int *x, int value) {
    *x = value;
    cout << "x : " << *x << " in change_value" << endl;
}

int main(void) {
    int x = 10;
    change_value(&x, 20);
    cout << "x: " << x << " in main" << endl;
    return 0;
}
```

만약 이와 같이 구조가 된다면 x = 0x1111 1111 같은 x 자체 메모리 주소로 할당되게 되어, 이 메모리 값이 해당 메서드의 스택 프레임에 들어가는 것을 알 수 있다. 즉 보낼 때 4바이트 공간 즉 메모리 주소를 보내는 것을 알 수 있다. 이렇게 인자를 변수의 참조로 전달하는 것이 참조에 의한 전달이다.

## 5. 파이썬의 객체 참조에 의한 전달

출처: `computer_science/chapter/chapter5.py`

파이썬은 객체 참조에 의한 전달을 한다. 변경 불가능한 객체를 전달할 때 — 이때 변경이 불가능한 상수 객체를 인자로 전달해보자. 주목할 점은 파이썬의 변수는 C언어처럼 변수를 메모리 공간에 값을 직접 저장하지 않는다. 변수 이름이 값 객체를 가리키는 것을 볼 수 있다. 상수 객체는 변경 불가능한 객체이다. 변수 값을 바꾼다는 의미는 변수 이름이 가리키는 메모리 공간의 값을 직접 바꾸는 게 아니라 바꾸고자 하는 상수 객체를 참조하게 되는 것이다.

```python
def change_value(x, value):
    x = value
    print("x : {} in change_value".format(x))

x = 10
change_value(x, 20)
print("x : {} in main.py".format(x))  # x : 10
```

변경 가능한 객체(list)를 전달할 때:

```python
def func1(li):
    li[0] = 'I am your father!'

def func2(li):
    li = ['I am your father!', 2, 3, 4]

li = [1, 2, 3, 4]
func1(li)
print(li)  # ['I am your father!', 2, 3, 4]

li = [1, 2, 3, 4]
func2(li)
print(li)  # [1, 2, 3, 4]
```

위 코드와 아래 코드를 비교해보면, 위는 참조한 리스트에 접근해 변경을 시도하고 아래는 다른 리스트를 메모리 공간에 새롭게 만든 다음 이를 참조해 리스트를 변경한다. 이때 보면 위는 같은 li를 참조하는 것을 알 수 있지만, 아래는 li가 메서드에 새롭게 생성한 리스트 객체를 바라보고 있는 것이다. 즉 참조하는 주소가 달라지게 된 것, 그렇기에 기존의 li가 그대로인 것이다. 변경 불가능한 객체는 값을 바꾸려면 다른 메모리 공간에 새로운 객체를 만든 다음 참조를 통해 만든 객체를 가리키게 만들 수밖에 없다. 튜플 값을 변경하려면 튜플을 만들어야 된다. 하지만 리스트는 변경이 가능하다. 이때 위는 li 자체는 참조하되 내부 0번 배열이 가리키는 위치가 변경되는 거라 리스트 자체 주소는 변경되지 않는 것. 그래서 결국 만들어진 li 자체는 프레임 스택이 사라져버리는 것이다.

즉 함수 인자로 변경 불가능 객체를 전달해 값을 변경할 수 없다. 그 이유는 함수 안에서 새 객체를 만든 다음 참조하여 바꾸려 하면 함수 호출이 끝나고 스택 프레임이 사라지면서 참조도 사라지기 때문이다. 함수 내부에서 객체를 새롭게 할당해야지만 값을 변경할 수 있는 객체는 변경 불가능 객체인 상수, 문자열, 튜플뿐이다.

리스트나 딕셔너리 같은 변경 가능 객체도 함수 안에서 새로운 객체를 만들 경우 함수 호출이 끝나면서 객체는 사라진다. 그러므로 변경 가능 객체를 인자로 전달할 때도 인자로 전달된 객체에 접근하여 변경해야만 함수를 호출한 쪽의 객체를 변경할 수 있다. 이러한 방식을 객체 참조에 의한 전달이라 한다.

변경 불가능 객체는 함수 인자로 전달해 변경할 수 없을까? — 반환해서 다시 받으면 된다.

```python
def change_value1(tu):
    tu = ('I am your father!', 2, 3, 4)
    return tu

tu = (1, 2, 3, 4)
tu = change_value1(tu)
```

## 6. 레퍼런스 카운트와 인터닝

출처: `computer_science/chapter/chapter5.py`

레퍼런스 카운트란? 메모리 영역 중에 힙이라는 공간이 있습니다. 이때 C나 C++는 이러한 힙에 할당된 메모리는 프로그래머가 직접 해제해야 된다. 하지만 자바, 파이썬, C#은 메모리를 프로그래머가 직접 관리하지 않고 언어가 스스로 해제한다. 더 이상 사용하지 않는 메모리를 언어 차원에서 해제한다는 개념을 가비지 컬렉션이라 한다. 그럼 가비지 컬렉션은 어떻게 구현할 수 있을까? 가장 단순한 형태인 mark and sweep부터 가장 빠르다고 알려진 Stop and Copy, reference Counting 등 가비지 컬렉션을 구현하는 알고리즘은 여러 개가 있고, 파이썬은 레퍼런스 카운팅으로 가비지 컬렉션을 구현한다.

여기서 레퍼런스는 참조(reference), 즉 무언가 가리킨다는 의미로 파이썬에서 변수는 값을 직접 갖는 게 아니라 상수 객체를 가리키고 있다고 했는데 이러한 개념이 바로 참조이다. 예시로 a가 10을 가리키고 이 대상의 개수가 레퍼런스 카운트 1이다. 이때 a의 참조가 10이 아닌 다른 값 객체로 바뀌면, 이때 상수 객체의 레퍼런스 카운트가 0이 되고 메모리가 해제되는 것.

```python
import sys

a = "abcde"
print(sys.getrefcount(a))
# 4294967295
```

이렇게 짧은 문자열은 파이썬이 인터닝(interning) 처리를 해서 자주 쓰일 것 같은 문자열을 미리 메모리에 올려놓고 사용한다. 그래서 2^32-1인 값이 나오는 것이고 이 객체는 삭제하지 말라는 특수한 값, 이뮤터블 객체가 된다. 이러한 문자열이나 None, True, False 같은 객체들은 참조 카운트를 아예 추적하지 않는다.

```python
print(sys.getrefcount(None))   # 4294967295
print(sys.getrefcount(True))   # 4294967295
print(sys.getrefcount("abc"))  # 4294967295

# 인터닝 안 되는 문자열은 정상 카운트
long_str = "a" * 1000
print(sys.getrefcount(long_str))  # 4294967295

n = 1000
dynamic_str = "a" * n
print(sys.getrefcount(dynamic_str))  # 2
```

여기서 `"a"*1000`이 4294967295이게 되는 이유는 컴파일 최적화 때문에, 파이썬 인터프리터가 코드 실행 전 컴파일 시점 최적화를 진행한다. 이때 상수 폴딩이라고 해서 컴파일 시점에 미리 계산된다.

```python
import dis
def test():
    return "a" * 1000
dis.dis(test)
#   8   2 RETURN_CONST   1 ('aaaa...a')  ← 1000개가 이미 완성된 상수
```

이처럼 리턴 컨스트에서 이미 1000개가 완성되어 있어서 컴파일 때 미리 만들게 된다.

## 7. 불변 객체는 함수 안에서 바꿀 수 없다 — id 실험

출처: `computer_science/chapter/chapter5-1.py`

```python
def change_string(s):
    print(f"함수 내부 변경 전: {id(s)}")  # 메인과 같은 주소
    s = "new"  # 새 객체 생성 + 지역변수 s가 새 객체를 가리킴
    print(f"함수 내부 변경 후: {id(s)}")  # 다른 주소
    return s

text = "hello"
print(f"메인 호출 전: {id(text)}")
change_string(text)
print(f"메인 호출 후: {id(text)}")
print(text)
```

```
메인 호출 전: 130150971864144
함수 내부 변경 전: 130150971864144
함수 내부 변경 후: 11749824
메인 호출 후: 130150971864144
hello
```

이걸 보면 결국 불변 객체는 값을 바꿀 수 없다. `s = "new"`는 기존 객체를 수정하는 게 아니라 새 객체를 만들어서 지역변수가 그걸 가리키게 하는 것이다. 메인의 text는 여전히 원래 객체를 가리킨다.

## 8. 가변 객체 — 재할당 vs 내부 변경

출처: `computer_science/chapter/chapter5-2.py`, `computer_science/chapter/chapter5-3.py`

```python
# chapter5-2.py
def change_list_wrong(lis):
    lst = [99, 99, 99]  # 새 객체 생성
    print(f"함수 내부: {lst}")

my_list = [1, 2, 3]
change_list_wrong(my_list)
print(my_list)  # [1, 2, 3]
```

불변 객체랑 똑같은 상황이다. 새 객체를 만들어서 지역변수를 가리키게 했으니 메인에는 영향이 없다.

```python
# chapter5-3.py
def change_list_right(lst):
    lst[0] = 99
    lst.append(4)
    print(f"함수 내부: {lst}")

my_list = [1, 2, 3]
change_list_right(my_list)
print(my_list)  # [99, 2, 3, 4]
```

결국 레퍼런스 카운트가 바뀌지 않는다면 해당 객체는 살아있고, 그에 대한 포인터가 바뀌는 내부 값 변경은 가능하다는 것을 알 수 있다.

## 9. 람다 함수

출처: `computer_science/chapter/chapter5-4.py`

```python
li = [i for i in range(1, 11)]
li.sort(key=lambda x: x % 2 == 0)
print(li)
# [1, 3, 5, 7, 9, 2, 4, 6, 8, 10]
```

이처럼 정렬 기준으로 사용하기 위해 함수를 따로 정의하는 것은 번거로운 작업이다. 람다 함수를 사용하면 매우 편리하게 정렬 기준을 제공할 수 있다. 람다 함수를 변수로 받으면서 함수 정의를 한 것처럼 사용 가능하다.

```python
f = lambda x: x ** 2
print(f(4))  # 16
print(f(5))  # 25
```

이때 람다 함수를 자세히 보면 값을 반환하는 return문이 없다. 또한 람다 함수의 몸체에는 반드시 식이 들어가야 한다.

```python
f1 = lambda li, idx: li[idx]
li = [1, 2, 3]
print(f1(li, 1))  # 2
# f2 = lambda li, idx, value: li[idx] = value  ← 문(statement)은 불가
```
