# 객체지향 기초 — 절차지향에서 상속·다형성까지 (컴퓨터사이언스 부트캠프 with 파이썬 ch.6~7)

> 원고: computer_science repo의 따라 친 노트를 구조만 잡아 이관(2026-09-05). 내용 보강 없음 — 원문 유지, 오탈자만 교정.

## 목차

| 원본 파일 | 절 |
|---|---|
| chapter/chapter6.py | 1. 프로그래밍 패러다임과 절차지향 |
| chapter/chapter6-1.py | 2. 함수 없이 짠 표준편차 프로그램 |
| chapter/chapter6_1/functions.py | 3. 함수로 나눈 절차지향 프로그램 |
| chapter/chapter6-2.py | 3. 함수로 나눈 절차지향 프로그램 |
| chapter/chapter6-3.py | 4. 객체지향과 캡슐화 — 딕셔너리로 객체 흉내 내기 |
| chapter/chapter6_1/class_Person.py | 5. 클래스와 메서드의 정체 |
| chapter/chapter6_1/class_A.py | 6. 클래스 멤버와 클래스 메서드 |
| chapter/chapter6_1/class_static.py | 7. classmethod vs staticmethod |
| chapter/chapter6_1/decorater.py | 8. classmethod 활용 — 팩토리·싱글톤 |
| chapter/chapter6_1/account.py | 9. Account 클래스 — 종합 예제 |
| chapter/chapter6_1/hinding.cpp | 10. 정보 은닉 — C++의 접근 제어 |
| chapter/chapter6_1/hiding.py | 11. 파이썬의 정보 은닉 — 네임 맹글링 |
| chapter/chapter6_1/hiding_property.py | 12. 프로퍼티 기법 |
| chapter/chapter6_1/statistics.py | 13. 클래스로 재구성한 성적 분석기 |
| chapter/chapter6_1/datahandler.py | 13. 클래스로 재구성한 성적 분석기 |
| chapter/chapter6_1/main.py | 13. 클래스로 재구성한 성적 분석기 |
| chapter/chapter7.py | 14. IS-A 상속 |
| chapter/chapter7-1.py | 15. HAS-A 관계 — 합성과 통합 |
| chapter/chapter7-2.py | 16. 다형성과 메서드 오버라이딩 |
| chapter/chapter7-3.py | 17. 추상 클래스 (abc) |
| chapter/chapter7-4.py | 18. Character 클래스 계층 설계 |
| chapter/chapter7-5.py | 19. 연산자 오버로딩 — `__add__`와 `__radd__` |
| chapter/chapter7-6.py | 19. 연산자 오버로딩 — `__add__`와 `__radd__` |
| chapter/chapter7/operator_overloading.py | 20. 연산자 오버로딩 레퍼런스 — dunder 메서드 전체 |

## 1. 프로그래밍 패러다임과 절차지향

출처: `computer_science/chapter/chapter6.py`

프로그래밍의 3가지: 절차 지향 프로그래밍, 객체 지향 프로그래밍, 함수형 프로그래밍이 존재하며, 프로그래밍 패러다임은 프로그래밍을 어떻게 바라볼 것인가, 어떻게 프로그래밍할 것인가에 대한 인식이나 체계라고 할 수 있다.

절차 지향 프로그래밍: "이 프로그램은 어떤 일을 하는가?"에 대한 질문에 쉽게 답할 수 있도록 함수를 사용하여 프로그래밍하는 것, 이를 절차 지향이라 한다. 절차를 의미하는 프로시저는 서브 루틴, 메서드, 함수라고 불린다.

openpyxl로 엑셀에서 데이터 읽기:

```python
from openpyxl import *

wb = load_workbook('../file/exam.xlsx')
ws = wb.active
g = ws.rows
cells = next(g)
```

rows는 데이터가 있는 모든 행을 발행자 객체로 반환. 그리고 next 함수로 첫 번째 행을 가져와 출력하면 엑셀 파일에 들어있는 셀을 확인 가능.

```python
keys = []
for cell in cells:
    keys.append(cell.value)
# ['name', 'math', 'literature', 'science']

student_data = []
for row in g:
    dic = {k: c.value for k, c in zip(keys, row)}
    # row 자체에서 꺼낸 건 Cell이라는 객체이기에 value로 꺼내야 된다.
    student_data.append(dic)
```

## 2. 함수 없이 짠 표준편차 프로그램

출처: `computer_science/chapter/chapter6-1.py`

함수를 전혀 사용하지 않고 학생들의 표준편차를 구해보자.

```python
raw_data = {}
wb = openpyxl.load_workbook("../file/exam_math.xlsx")
ws = wb.active
for name, score in ws.rows:
    raw_data[name.value] = score.value

scores = list(raw_data.values())

s = 0
for score in scores:
    s += score
avrg = round(s/len(scores), 1)

s = 0
for score in scores:
    s += (score - avrg) ** 2
variance = round(s/len(scores), 1)      # 분산
std_dev = round(math.sqrt(variance), 1) # 표준편차

if avrg < 50 and std_dev > 20:
    print("성적이 너무 저조하고 학생들의 실력 차이가 너무 크다.")
elif avrg > 50 and std_dev > 20:
    print("성적은 평균 이상이지만 학생들이 실력 차이가 크다. 주의 요망")
elif avrg < 50 and std_dev < 20:
    print("학생들의 실력 차이는 크지 않지만 성적이 너무 저조하다. 주의 요망")
elif avrg > 50 and std_dev < 20:
    print("성적도 평균 이상이고 학생들의 실력 차이도 크지 않다.")
```

## 3. 함수로 나눈 절차지향 프로그램

출처: `computer_science/chapter/chapter6_1/functions.py`, `computer_science/chapter/chapter6-2.py`

같은 프로그램을 함수로 분해한다. functions.py의 함수들:

```python
def get_data_from_excel(filename):
    """
    get_data_from_excel(filename) ->
    {"name1":"score1", "name2", "score2"...}
    엑셀 파일에서 데이터를 가져옵니다.
    반환값은 key가 학생 이름이고 value가 점수인 딕셔너리입니다.
    """
    ...

def average(scores): ...
def variance(scores, avrg): ...
def std_dev(variance): ...

def evaluateClass(avrg, total_avrg, std_dev, sd):
    """
    evaluateClass(avrg,total_avrg,std_dev,sd) -> None
    avrg: 반 성적 평균 / total_avrg: 학년 전체 성적 평균
    std_dev: 반의 표준편차 / sd: 원하는 표준 편차 기준
    """
    ...
```

사용하는 쪽(chapter6-2.py):

```python
raw_data = get_data_from_excel("../file/exam_math.xlsx")
scores = list(raw_data.values())

avrg = average(scores)
variance = variance(scores, avrg)
standard_deviation = std_dev(variance)

evaluateClass(avrg, 50, standard_deviation, 20)
```

이와 같이 다른 프로그래머가 봐도 프로그램 실행 흐름을 매우 쉽게 파악할 수 있다. 또한 함수는 어떻게 구현했는지 알 필요 없이 인터페이스만 알면 필요한 함수를 가져다 쓰면 되므로 다른 프로그램도 쉽게 작성할 수 있다.

## 4. 객체지향과 캡슐화 — 딕셔너리로 객체 흉내 내기

출처: `computer_science/chapter/chapter6-3.py`

객체를 의미하는 object는 고정된 모양이나 형태가 있어 만지거나 볼 수 있는 것이라고 정의되어 있다. 즉 "이 프로그램이 무슨 일을 하는가?"에 대한 답을 하는 절차지향과 달리, 객체 지향은 "현실 세계에 존재하는 객체(object)를 어떻게 모델링(modeling)할 것인가?"에 대한 물음에서 시작한다. 사람이나 동물 혹은 물건을 프로그램에서 어떻게 표현해야 할까요? 이게 그 물음의 첫 번째 답이다.

캡슐화: 특성을 기준으로 객체들을 분류하거나 계층을 만들 수 있다. 객체는 고유의 특성 값과 행동 혹은 기능으로 표현할 수 있다. 객체가 지니는 특성 값은 변수로 나타낼 수 있다. 행동 혹은 기능은 함수로 표현할 수 있다. 즉 현실 세계의 객체를 나타내려면 변수와 함수만 있으면 된다. 이처럼 현실 세계를 모델링하거나 프로그램을 구현하는 데 이처럼 변수와 함수를 가진 객체를 이용하는 패러다임을 객체지향 프로그래밍이라 하며, 변수와 함수를 하나의 단위로 묶는 것을 캡슐화라고 한다.

클래스 없이 딕셔너리와 함수만으로 객체를 만들어보는 실험:

```python
def person_init(name, money):
    obj = {'name': name, 'money': money}
    obj['give_money'] = Person[1]
    obj['get_money'] = Person[2]
    obj['show'] = Person[3]
    return obj

def give_money(self, other, money):
    self['money'] -= money
    other['get_money'](other, money)

def get_money(self, money):
    self['money'] += money

def show(self):
    print('{} : {}'.format(self['name'], self['money']))

Person = person_init, give_money, get_money, show

g = Person[0]('greg', 5000)
j = Person[0]('john', 2000)
g['give_money'](g, j, 2000)
```

이처럼 other 객체의 돈, 즉 변수를 변경할 때 돈을 받는 객체가 가지고 있는 특정 함수를 호출하여 변경한다. 이처럼 서로 다른 객체가 함수 호출을 통해 상호작용하여 객체의 상태가 변하는 것을 메시지 패싱이라 한다. 주요 포인트는 서로 다른 객체가 상호작용할 때 함수를 호출했다는 것과, 함수 안에서 상대의 변수를 바꾸려면 상대가 가진 특정 함수를 호출해야 된다는 점이다.

`dis.dis(lambda: g['show'](g))`로 바이트코드를 확인:

```
0  RESUME              # 함수 시작
2  LOAD_GLOBAL g       # g 객체를 스택에 로드
12 LOAD_CONST 'show'   # 문자열 'show'를 스택에 로드
14 BINARY_SUBSCR       # g['show'] 실행 → 함수 객체 꺼냄
18 LOAD_GLOBAL g       # 인자로 쓸 g를 다시 로드
28 CALL 1              # 함수 호출 (인자 1개)
36 RETURN_VALUE        # 결과 반환
```

## 5. 클래스와 메서드의 정체

출처: `computer_science/chapter/chapter6_1/class_Person.py`

클래스 이름은 첫 글자를 대문자로 하는 것이 관례. 그리고 클래스로 묶이는 변수는 프로퍼티 또는 멤버라 부른다. 객체가 가지는 멤버를 인스턴스 멤버라 한다. OOP에서는 클래스에 묶이는 함수를 행동, 멤버 함수, 메서드라 부른다. 멤버와 메서드를 합쳐 attribute(속성)라 부른다.

```python
class Person:
    def __init__(self, name, money):
        self.name = name
        self.money = money

    def give_money(self, other, money):
        self.money -= money
        other.get_money(money)

    def get_money(self, money):
        self.money += money

    def show(self):
        print('{} : {}'.format(self.name, self.money))
```

```python
print(type(Person.give_money))  # <class 'function'>
print(type(g.give_money))       # <class 'method'>
```

기본적으로 파이썬은 객체 메서드 실행 시 self로 자기 자신을 전달한다. 결국 클래스는 함수의 모음일 뿐이다. 이걸 보면 확실히 알 수 있다 — 객체의 메서드는 함수가 아닌 메서드인 것을 알 수 있다.

```python
print(g.give_money.__func__)  # <function Person.give_money at 0x77e22f8b8e00>
print(g.give_money.__self__)  # <__main__.Person object at 0x7c82cd337c80>
print(g.give_money.__func__ is Person.give_money)  # True
print(g.give_money.__self__ is g)                  # True
```

dir로 메서드의 속성을 확인. 이로써 객체에서 메서드를 호출할 때 맨 처음 인자인 self를 전달하지 않아도 되는 이유를 알 수 있다. `__func__`를 보면 Person 클래스의 give_money 메서드로 나오며, `__self__`를 확인하니 Person 객체라 나온다. 메서드 내부에 함수와 객체의 참조를 가지고 있으므로 함수에 직접 객체의 참조를 전달할 수 있기 때문이다. 객체가 멤버와 메서드를 가질 수 있는 것처럼 클래스도 멤버와 메서드를 가질 수 있다. 클래스가 가지는 멤버를 클래스 멤버라고 하고 메서드를 클래스 메서드라 한다.

## 6. 클래스 멤버와 클래스 메서드

출처: `computer_science/chapter/chapter6_1/class_A.py`

```python
class A:
    c_mem = 10

    @classmethod
    def cls_f(cls):
        print(cls.c_mem)

    def __init__(self, num):
        self.i_mem = num

    def ins_f(self):
        print(self.i_mem)
```

이처럼 c_mem을 클래스 멤버라 한다. 클래스가 가지는 멤버이며, cls_f() 메서드 위에 데코레이터 classmethod가 있다. 이를 통해 이 메서드는 클래스 메서드가 되며, 클래스 메서드는 클래스가 가진 메서드이다. 이러한 클래스 멤버와 클래스 메서드의 또 다른 특징은 객체에서도 접근하거나 호출할 수 있다는 점이다.

```python
print(A.c_mem)  # 10
A.cls_f()       # 10

a = A(20)
print(a.c_mem)  # 10
a.cls_f()       # 10
```

이렇게 객체를 통해 클래스 멤버를 호출하거나 메서드를 호출하면 객체들이 이걸 공유하게 된다는 점이다. 모든 객체가 같은 데이터를 가진다면 이를 클래스 멤버로 만들어 공유하면 된다.

## 7. classmethod vs staticmethod

출처: `computer_science/chapter/chapter6_1/class_static.py`

```python
class Animal:
    count = 0

    def __init__(self, name):
        self.name = name
        Animal.count += 1

    @classmethod
    def get_count(cls):
        print(f"{cls.__name__} 클래스: {cls.count}개")

    @staticmethod
    def get_count_static():
        print(f"Animal 클래스: {Animal.count}개")

class Dog(Animal):
    count = 0

    def __init__(self, name):
        super().__init__(name)
        Dog.count += 1
```

```python
d1 = Dog("멍멍이"); d2 = Dog("바둑이"); a1 = Animal("동물")

# === 클래스 메서드 ===
Animal.get_count()  # Animal 클래스: 3개
Dog.get_count()     # Dog 클래스: 2개  ← cls가 Dog을 가리킴

# === 스태틱 메서드 ===
Animal.get_count_static()  # Animal 클래스: 3개
Dog.get_count_static()     # Animal 클래스: 3개  ← 항상 Animal 고정
```

## 8. classmethod 활용 — 팩토리·싱글톤

출처: `computer_science/chapter/chapter6_1/decorater.py`

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    @classmethod
    def from_birth_year(cls, name, birth_year):
        age = 2026 - birth_year
        return cls(name, age)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['age'])
```

```python
p1 = Person("철수", 25)
p2 = Person.from_birth_year("영희", 2000)
p3 = Person.from_dict({'name': "민수", "age": 30})
# 이와 같이 다양한 생성자를 만들어낼 수 있다.
```

```python
class Database:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
# 이와 같이 싱글톤으로 관리할 수 있다.
```

## 9. Account 클래스 — 종합 예제

출처: `computer_science/chapter/chapter6_1/account.py`

```python
class Account:
    num_acnt = 0

    @classmethod
    def get_num_acnt(cls):
        """cls.get_num_acnt() -> integer"""
        return cls.num_acnt

    def __init__(self, name, money):
        self.user = name
        self.balance = money
        Account.num_acnt += 1

    def deposit(self, money):
        if money < 0:
            return
        self.balance += money

    def withdraw(self, money):
        if money > 0 and money <= self.balance:
            self.balance -= money
            return money
        else:
            return None

    def transfer(self, other, money):
        """
        obj.transfer(other, money) -> bool
        other : The object to interact with
        money : money the user wants to send
        return True if the balance is enough to transfer, False if not
        """
        mon = self.withdraw(money)
        if mon:
            other.deposit(money)
            return True
        else:
            return False

    def __str__(self):
        return 'user : {}, balance : {}'.format(self.user, self.balance)
```

- 인스턴스 메서드를 호출하는 방법: 1. by object `my_acnt.deposit(500)` / 2. by class `Account.deposit(my_acnt, 500)`
- 클래스 멤버에 접근하는 방법: 1. by class `Account.num_acnt` / 2. by object `my_acnt.num_acnt`
- 클래스 메서드 호출하는 방법: 1. by class `Account.get_num_acnt()` / 2. by object `my_acnt.get_num_acnt()`

메시지 패싱 실행 결과:

```
user : greg, balance : 4000
user : john, balance : 1000
transfer succeeded
user : greg, balance : 2000
user : john, balance : 3000
```

## 10. 정보 은닉 — C++의 접근 제어

출처: `computer_science/chapter/chapter6_1/hinding.cpp`

```cpp
class {
public:
    Account(String name, int money) {
        user = name;
        balance = money;
    }
    int get_balance() { return balance; }
    void set_balance(int money) {
        if (money < 0) { return; }
        balance = money;
    }
private:
    String user;
    int balance;
};
```

이처럼 C++에서 생성자 이름이 클래스 이름과 같다. 이러한 접근 제어 지시자를 통해 정보에 대한 접근을 숨길 수 있다.

my_acnt라는 객체를 생성하여 객체의 balance 멤버에 접근하면 컴파일 오류가 나오는데, 컴파일 레벨에서 숨겨진 멤버를 명시 접근하여 오류가 난 것. 이랬을 때 장점이란? 마이너스 통장이 아닌 이상 잔액이 음수가 될 수 없다. 만약 이렇게 숨기지 않았다면 음수 처리가 될 수도 있고 실수할 수도 있다. 하지만 set을 통해 데이터 변경을 한다면 이러한 실수를 줄일 수 있다. 그렇기에 원천적으로 잔고가 음수가 되는 상황을 막을 수 있다.

```cpp
int main(void) {
    Account my_acnt("greg", 5000);
    my_acnt.set_balance(-3000);
    cout << my_acnt.get_balance() << endl;
    return 0;
}
```

이렇게 하면 어차피 set_balance에서 막기 때문에 5000이 잘 나오고, OOP에서 잘된 정보 은닉은 필요한 메서드만 공개하고 나머진 숨기는 것. 멤버에 접근하거나 변경해야 될 때는 액세스 함수를 통해 변경.

## 11. 파이썬의 정보 은닉 — 네임 맹글링

출처: `computer_science/chapter/chapter6_1/hiding.py`

```python
class Account:
    def __init__(self, name, money):
        self.user = name
        self.__balance = money

    def get_balance(self):
        return self.__balance

    def set_balance(self, money):
        if money < 0:
            return
        self.__balance = money

my_acnt = Account('greg', 5000)
my_acnt.__balance = -3000
my_acnt.__bal = -2000

print(my_acnt.get_balance())
```

-3000이 나오는데(주: 원고의 관찰 기록) 정보 은닉이 불가능하다. 그래서 파이썬에서는 숨기려는 멤버 앞에 언더바(_) 두 개를 붙인다. 프로퍼티 기법을 사용한다. 우선 __를 통해 실행하면 정보 은닉이 된 것처럼 보이지만,

```python
print(my_acnt.__dict__)
# {'user': 'greg', '_Account__balance': 5000, '__balance': -3000}
```

정보가 은닉됐다면 __balance가 보이지 않아야 된다. 이상한 점은 우리가 만들지도 않은 `_Account__balance`가 존재. 클래스 안의 멤버 앞에 __를 붙이면 이 멤버는 객체를 만들 때 이름이 변하게 된다. 클래스 이름이 멤버 앞에 붙게 된다. 즉 `__balance` → `_Account__balance: 5000`으로 바뀌는 거라서 그냥 보이는 것만 그런 거고 실제 접근은 가능하다고 알 수 있다.

```python
print(my_acnt.__balance)  # -3000  이처럼 마음만 먹으면 언제든지 변경할 수 있다.
print(my_acnt.__bal)      # -2000
```

아, 그냥 객체 생성해서 포인트로 묶어버리는구나. 그리고 키-밸류로 딕셔너리로 보관하고 인스턴스 자체가 생성되네.

## 12. 프로퍼티 기법

출처: `computer_science/chapter/chapter6_1/hiding_property.py`

```python
class Account:
    def __init__(self, name, money):
        self.user = name
        self.balance = money

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, money):
        if money < 0:
            return
        self._balance = money
```

@property는 메서드를 변수처럼 쓸 수 있게 해주는 데코레이터이다.

```python
# property 없이
my_acnt.get_balance()      # 메서드 호출
my_acnt.set_balance(5000)  # 메서드 호출

# property 사용
my_acnt.balance        # 변수처럼 읽기
my_acnt.balance = 5000 # 변수처럼 쓰기
```

이게 가능해지는 구조이다.

```python
my_acnt = Account('greg', 5000)
my_acnt.balance = -3000
print(my_acnt.balance)  # 5000 (setter가 막음)

my_acnt._balance = -3000
print(my_acnt._balance)
# 하지만 결국 원천적으로 막을 수가 없다.
```

## 13. 클래스로 재구성한 성적 분석기

출처: `computer_science/chapter/chapter6_1/statistics.py`, `computer_science/chapter/chapter6_1/datahandler.py`, `computer_science/chapter/chapter6_1/main.py`

통계 연산을 Stat 클래스로 묶는다.

```python
# statistics.py
class Stat:
    def average(self, scores): ...
    def variance(self, scores, avrg): ...
    def std_dev(self, variance): ...
```

DataHandler는 Stat을 클래스 멤버로 가지고, 캐시로 연산 결과를 저장한다.

```python
# datahandler.py
class DataHandler:
    evaluator = Stat()

    @classmethod
    def get_data_from_excel(cls, filename):
        ...

    def __init__(self, filename, year_class):
        self.rawdata = DataHandler.get_data_from_excel(filename)
        self.year_class = year_class
        # 연산한 값을 저장해 두는 저장소
        # 필요할 때 연산하되
        # 이미 연산된 값이면 연산 없이 저장된 값을 반환
        self.cache = {}

    def get_average(self):
        if 'average' not in self.cache:
            self.cache['average'] = self.evaluator.average(self.get_scores())
        return self.cache.get('average')

    # get_scores / get_variance / get_standard_deviation 도 같은 캐시 패턴

    def get_evaluation(self, total_avrg, sd=20):
        print('{} 반 성적 분석 결과'.format(self.year_class))
        ...
        self.evaluate_class(total_avrg, sd)
```

사용(main.py):

```python
dh = DataHandler('../../file/exam_math.xlsx', '2-3')
dh.get_evaluation(50)
```

## 14. IS-A 상속

출처: `computer_science/chapter/chapter7.py`

IS-A는 '~은 ~의 한 종류이다'. 이러한 관계를 프로그램에서 표현할 때는 상속(inheritance)이라 부른다. 이러한 상속 관계에는 상속을 하는 클래스를 기본(base) 클래스, 부모(parent) 클래스, 슈퍼(super) 클래스라고 하며, 상속을 받는 클래스를 파생(derived) 클래스, 자식(child) 클래스, 서브(sub) 클래스라 한다.

```python
class Computer:
    def __init__(self, cpu, ram):
        self.CPU = cpu
        self.RAM = ram

    def browse(self):
        print('browse')

    def work(self):
        print('work')

class Laptop(Computer):
    # 멤버 추가
    def __init__(self, cpu, ram, battery):
        super().__init__(cpu, ram)
        self.battery = battery

    # 메서드 추가
    def move(self, to):
        print('move to {}'.format(to))
```

이렇게 하면 Laptop 클래스 이름 옆 괄호 안에 Computer가 있고, 이걸 상속한다는 의미로 즉 browse/work 메서드를 정의하지 않아도 가지고 있다고 볼 수 있다. 또한 super란 현재 클래스의 슈퍼 클래스, 즉 기본 클래스를 의미한다.

원고에는 unittest로 확인하는 테스트도 있다:

```python
class TestLaptop(unittest.TestCase):
    def test_browse(self):
        lap = Laptop('intel', 16, 'powerful')
        lap.browse()
        self.assertEqual(lap.CPU, 'intel')
        self.assertEqual(lap.RAM, 16)
        self.assertEqual(lap.battery, 'powerful')
```

## 15. HAS-A 관계 — 합성과 통합

출처: `computer_science/chapter/chapter7-1.py`

HAS-A 관계: '~이 ~을 가진다 혹은 포함한다'. 프로그램에서 HAS-A 관계는 합성(composition) 혹은 통합(aggregation)을 이용해 표현합니다. 합성과 통합은 모두 HAS-A 관계를 나타내는 방법이지만 둘 사이에는 차이점이 있다.

```python
class CPU: pass
class RAM: pass

class Computer:
    def __init__(self):
        self.cpu = CPU()
        self.ram = RAM()
```

이때 합성 관계는 컴퓨터가 폐기되면 내부 cpu와 ram도 같이 폐기되듯, 컴퓨터와 cpu/ram 객체의 생명주기가 같고 컴퓨터가 cpu를 소유하는 강한 관계를 맺고 있게 됩니다.

```python
class Gun:
    def __init__(self, kind):
        self.kind = kind

    def bang(self):
        print('bang bang!')

class Police:
    def __init__(self):
        self.gun = None

    def acquire_gun(self, gun):
        self.gun = gun

    def release_gun(self):
        gun = self.gun
        self.gun = None
        return gun

    def shoot(self):
        if self.gun:
            self.gun.bang()
        else:
            print("Unable to shoot")
```

이처럼 Police 객체가 만들어질 때 Gun 객체를 가지고 있지 않는다. 이때 별도 메서드를 통해 가지게 되는 것이다. 이걸 HAS-A 관계로, 이렇게 생명주기를 분리하는 느슨한 관계를 통합이라 한다.

```
p1 shoots
Unable to shoot

p1 shoots again
bang bang!

p1 shoots again
Unable to shoot
```

## 16. 다형성과 메서드 오버라이딩

출처: `computer_science/chapter/chapter7-2.py`

다형성(polymorphism)이란 "상속 관계에 있는 다양한 클래스의 객체에서 같은 이름의 메서드를 호출할 때, 각 객체가 서로 다르게 구현된 메서드를 호출함으로써 서로 다른 행동(behavior), 기능, 결과를 가져오는 것". 그리고 이를 구현하기 위해 파생 클래스(derived class) 안에서 상속받은 메서드를 다시 구현하는 것을 메서드 오버라이딩(method overriding)이라 한다.

```python
class CarOwner:
    def __init__(self, name):
        self.name = name

    def concentrate(self):
        print('{} can not do anything else'.format(self.name))

class Car:
    def __init__(self, owner_name):
        self.owner = CarOwner(owner_name)

    def drive(self):
        self.owner.concentrate()
        print('{} is driving now'.format(self.owner.name))

class SelfDrivingCar(Car):
    def drive(self):
        print('Car is driving by itself')
```

이처럼 drive 메서드만 다시 구현하는, 즉 파생 클래스에서 상속받은 메서드를 다시 구현하는 것을 메서드 오버라이딩이라 한다. 차 주인은 더 이상 차가 주행하는 동안 집중하지 않아도 되므로, 오버라이딩된 drive() 메서드에는 차 주인의 concentrate() 메서드를 호출하지 않는다.

즉 이처럼 같은 이름의 메서드를 호출해도 호출한 객체에 따라 다른 결과를 내는 것을 '다형성'이라 한다. 오버라이딩은 다른 행동 혹은 기능을 의미합니다. 기본 클래스 객체와 파생 클래스 객체의 여러 가지 행동(메서드)이 다르다면 IS-A 관계가 맞는지 다시 한번 검토해야 된다.

## 17. 추상 클래스 (abc)

출처: `computer_science/chapter/chapter7-3.py`

- abc 라이브러리란: Abstract Base Class의 약자이다. 파이썬에서 추상 클래스를 만들기 위한 표준 라이브러리.
- metaclass란: 클래스를 만드는 클래스, 즉 클래스의 클래스이다. 객체 = 클래스(), 클래스 = metaclass().
- ABCMeta란: 추상 클래스를 만들어주는 메타 클래스이다. 이걸 사용하면 "이 클래스는 직접 인스턴스화하면 안 되고 반드시 상속을 쓰라"고 강제할 수 있다.
- @abstractmethod란: "이 메서드는 자식 클래스에서 반드시 구현해야 해"라고 하는 데코레이터이다.

```python
from abc import *

class Animal(metaclass=ABCMeta):
    @abstractmethod
    def eat(self):
        pass

class Lion(Animal):
    def eat(self):
        print("eat meat")

class Dear(Animal):
    def eat(self):
        print('eat grass')

class Human(Animal):
    def eat(self):
        print("eat meat and grass")

animals = [Lion(), Dear(), Human()]
for animal in animals:
    animal.eat()
```

이 예제와 같이 모든 동물은 eat(먹는다)는 기본 클래스를 두지만 다들 먹는 게 다릅니다. 메서드를 호출한 쪽에서는 객체가 어떤 걸 먹는지 알 필요가 없습니다. 각각의 객체는 자신의 클래스에 오버라이딩된 메서드를 호출한다. 그런데 이때 세상에 그냥 뭔가를 먹는 동물은 없다. 이렇다면 설계자는 유저 프로그래머가 Animal 클래스 인스턴스를 애초에 못 만들게 하고 싶다. 이럴 때는 Animal 클래스를 추상 클래스(abstract class)로 만들면 된다. 추상 클래스를 상속받는 파생 클래스에서는 추상 메서드를 반드시 오버라이딩해야 된다. 그렇지 않으면 파생 클래스도 추상 클래스가 되어 인스턴스를 만들 수 없다.

## 18. Character 클래스 계층 설계

출처: `computer_science/chapter/chapter7-4.py`

클래스 계층을 설계할 때는 다음 두 가지를 고려해야 된다.

1. 공통 부분을 기본 클래스로 묶는다. 이렇게 하면 코드를 재사용할 수 있다.
2. 부모가 추상 클래스인 경우를 제외하고, 파생 클래스에서 기본 클래스의 여러 메서드를 오버라이딩한다면 파생 클래스는 만들지 않는 것이 좋다.

```python
from abc import *

class Character(metaclass=ABCMeta):
    def __init__(self, name, hp, power):
        self.name = name
        self.HP = hp
        self.power = power

    # 파생 클래스는 반드시 attack()과 get_damage() 메서드를 오버라이딩해야 된다.
    @abstractmethod
    def attack(self, other, attack_kind):
        pass

    @abstractmethod
    def get_damage(self, power, attack_kind):
        pass

    def __str__(self):
        return '{} : {}'.format(self.name, self.HP)
```

```python
class Player(Character):
    def __init__(self, name='player', hp=100, power=10, *attack_kinds):
        super().__init__(name, hp, power)
        self.skills = []
        for attack_kind in attack_kinds:
            self.skills.append(attack_kind)

    def attack(self, other, attack_kind):
        if attack_kind in self.skills:
            other.get_damage(self.power, attack_kind)

    def get_damage(self, power, attack_kind):
        """
        만약 공격 종류가 플레이어의 기술 중 하나라면
        피해가 절반으로 감소한다.
        """
        if attack_kind in self.skills:
            self.HP -= (power // 2)
        else:
            self.HP -= power
```

불과 얼음 몬스터는 모두 Character 클래스에 추가된 attack_kind 멤버를 가지고 있으며, attack() 메서드와 get_damage() 메서드는 같은 행동을 한다. 공통된 부분은 Monster라는 부모 클래스를 만들어 거기에 둔다.

```python
class Monster(Character):
    def __init__(self, name, hp, power):
        super().__init__(name, hp, power)
        self.attack_kind = 'None'

    def attack(self, other, attack_kind):
        if self.attack_kind == attack_kind:
            other.get_damage(self.power, attack_kind)

    def get_damage(self, power, attack_kind):
        """
        몬스터는 자신과 타입이 같은 공격을 당하면
        오히려 체력이 늘어납니다. 조심해서 공격하세요.
        """
        if self.attack_kind == attack_kind:
            self.HP += power
        else:
            self.HP -= power

    def get_attack_kind(self):
        return self.attack_kind

class IceMonster(Monster):
    def __init__(self, name="Ice Monster", hp=50, power=10):
        super().__init__(name, hp, power)
        self.attack_kind = "ICE"

class FireMonster(Monster):
    def __init__(self, name="Fire Monster", hp=50, power=20):
        super().__init__(name, hp, power)
        self.attack_kind = 'FIRE'

    # FireMonster만의 행동
    def fireball(self):
        print("fireball")
```

실행 시나리오: 플레이어가 ICE 공격만 가지고 있으므로 아이스 몬스터가 공격할 때는 공격력의 절반(10//2=5)만 깎이고, 파이어 몬스터가 공격할 때는 공격력이 그대로(20) 깎인다. 모든 공격이 끝난 후 플레이어의 체력은 100 - ((10//2) + 20) = 75. 공격을 받는 몬스터 객체가 어떤 몬스터인지에 따라 호출되는 메서드가 달라지고 그에 따라 결과도 달라진다.

## 19. 연산자 오버로딩 — `__add__`와 `__radd__`

출처: `computer_science/chapter/chapter7-5.py`, `computer_science/chapter/chapter7-6.py`

```python
# chapter7-5.py — 연산자 오버로딩 없이
class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

p1 = Point(2, 2)
p2 = p1 + 3
# 당연히 Point 객체와 int 사이의 연산이 불가능하다고 오류가 나온다.
```

```python
# chapter7-6.py — __add__ / __radd__ 추가
class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, n):
        x = self.x + n
        y = self.y + n
        return Point(x, y)

    def __radd__(self, n):
        x = self.x + n
        y = self.y + n
        return Point(x, y)

    def __str__(self):
        return '({x}, {y})'.format(x=self.x, y=self.y)

p1 = Point(2, 2)
p2 = p1 + 3
print(p2)  # (5, 5)
```

이때 `__add__` 메서드가 추가되었다. 이러한 언더바가 두 개씩 붙어 있는 함수는 파이썬의 예약 함수로, `__add__`도 연산자 오버라이딩을 위해 예약된 함수다. 함수 구현을 보면 객체의 x좌표와 y좌표에 인자 n을 더한 새로운 x와 y로 새로운 객체를 만들어 반환한다. 이렇게 연산자를 오버라이딩하여 +를 만나면 `p1+3`이 `p1.__add__(3)`으로 변경된다.

`3 + p1` 연산은 오류가 나오는데, 이는 객체와 숫자를 더할 때 int 자체의 add 연산자의 상호작용이기 때문이다. 그렇기에 `__radd__` 메서드를 만들어주면 연산이 잘된다.

## 20. 연산자 오버로딩 레퍼런스 — dunder 메서드 전체

출처: `computer_science/chapter/chapter7/operator_overloading.py`

파이썬 연산자 오버라이딩(Operator Overloading) — Point 클래스 하나에 문자열 표현부터 해시까지 dunder 메서드 전체를 구현해 본 레퍼런스 파일. 각 메서드의 docstring이 어떤 연산에 대응하는지 설명한다.

### 20.1 문자열 표현

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        """print() 할 때 호출"""
        return f"Point({self.x}, {self.y})"

    def __repr__(self):
        """개발자용 표현, 리스트 안에서 출력될 때 등"""
        return f"Point({self.x}, {self.y})"
```

### 20.2 산술 연산자 (Arithmetic Operators)

`+ - * / // % **` 각각에 대해 기본형(`__add__`), 반사형(`__radd__` — other + self, other가 Point가 아닐 때), 복합 할당형(`__iadd__` — self += other) 세 벌씩 구현한다. 패턴은 동일하다.

```python
    def __add__(self, other):
        """self + other"""
        if isinstance(other, Point):
            return Point(self.x + other, self.y + other)

    def __radd__(self, other):
        """other + self (other가 Point가 아닐 때)"""
        return Point(self.x + other, self.y + other)

    def __iadd__(self, other):
        """self += other"""
        if isinstance(other, Point):
            self.x += other.x
            self.y += other.y
        else:
            self.x += other
            self.y += other
        return self

    def __sub__(self, other):
        """self - other"""
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        return Point(self.x - other, self.y - other)
```

같은 3벌 패턴으로 `__mul__`/`__rmul__`/`__imul__`(self * other), `__truediv__`/`__rtruediv__`/`__itruediv__`(self / other — 실수 나눗셈), `__floordiv__`/`__rfloordiv__`/`__ifloordiv__`(self // other — 정수 나눗셈), `__mod__`/`__rmod__`/`__imod__`(self % other), `__pow__`/`__rpow__`/`__ipow__`(self ** other — 거듭제곱)를 구현한다.

### 20.3 단항 연산자

```python
    def __neg__(self):
        """-self"""
        return Point(-self.x, -self.y)

    def __pos__(self):
        """+self"""
        return Point(+self.x, +self.y)

    def __abs__(self):
        """abs(self) - 원점으로부터의 거리"""
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __invert__(self):
        """~self (비트 반전, 여기서 좌표 뒤집기로 활용)"""
        return Point(self.y, self.x)
```

### 20.4 비교 연산자

```python
    def __eq__(self, other):
        """self == other"""
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y
        return False

    def __ne__(self, other):
        """self != other"""
        return not self.__eq__(other)

    def __lt__(self, other):
        """self < other (원점으로부터 거리 비교)"""
        if isinstance(other, Point):
            return abs(self) < abs(other)
        return abs(self) < other
```

`__le__`(self <= other), `__gt__`(self > other), `__ge__`(self >= other)도 같은 거리 비교 패턴.

### 20.5 비트 연산자

`& | ^` 역시 기본형/반사형/복합 할당형 3벌 패턴(`__and__`/`__rand__`/`__iand__`, `__or__`/`__ror__`/`__ior__`, `__xor__`/`__rxor__`/`__ixor__`)으로 좌표별 비트 연산을 구현하고, 시프트는 `__lshift__`/`__rlshift__`/`__ilshift__`(self << other), `__rshift__`/`__rrshift__`/`__irshift__`(self >> other)로 구현한다.

```python
    def __and__(self, other):
        """self & other"""
        if isinstance(other, Point):
            return Point(self.x & other.x, self.y & other.y)
        return Point(self.x & other, self.y & other)

    def __lshift__(self, other):
        """self << other"""
        return Point(self.x << other, self.y << other)
```

### 20.6 타입 변환 (type Conversion)

```python
    def __int__(self):
        """int(self) - 원점으로부터 거리의 정수 값"""
        return int(abs(self))

    def __float__(self):
        """float(self) - 원점으로부터 거리"""
        return float(abs(self))

    def __bool__(self):
        """bool(self) - 원점이 아니면 True"""
        return self.x != 0 or self.y != 0

    def __complex__(self):
        """complex(self) - 복소수 변환"""
        return complex(self.x, self.y)
```

복소수란 실수+허수로 이루어진 수. a + bi — a = 실수부(real), b = 허수부(imaginary), i = 허수 단위(i² = -1). 복소수 평면과 2D 좌표계는 완전히 같은 구조이다. `3 + 4j` 같은 방식으로 표현할 수 있다. 회전이 간단해진다 — 좌표를 회전시키려면 원래 복잡한 삼각함수 계산이 필요한데, 복소수는 곱셈만으로 회전이 가능하다.

### 20.7 컨테이너 연산자

```python
    def __len__(self):
        """len(self) - 좌표 개수"""
        return 2

    def __getitem__(self, index):
        """self[index]"""
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Point index out of range")

    def __setitem__(self, index, value):
        """self[index] = value"""
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        else:
            raise IndexError("Point index out of range")

    def __contains__(self, value):
        """value in self"""
        return value == self.x or value == self.y

    def __iter__(self):
        """for item in self"""
        yield self.x
        yield self.y
```

### 20.8 호출 연산자와 해시

```python
    def __call__(self, dx=0, dy=0):
        """self(dx, dy) - 이동한 새 Point 반환"""
        return Point(self.x + dx, self.y + dy)

    def __hash__(self):
        """hash(self) - 딕셔너리 키나 set에 사용 가능하게"""
        return hash((self.x, self.y))
```

### 20.9 복소수 회전 실험

```python
import cmath

p = Point(3, 4)
c = complex(p)
# 90도 회전 (i를 곱하면 90도 회전)
rotated = c * 1j  # (-4+3j) → Point(-4, 3)
print(rotated)
# (-4+3j)

# 45도 회전
angle = cmath.exp(1j * cmath.pi/4)  # 45도 공식
rotated_45 = c * angle
print(rotated_45)
```
