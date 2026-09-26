# csharp/syntax/36 — `IQueryable` 과 식 트리 맛보기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **옵코드와 호출 대상 · `NodeType` · 공급자 로그의 수 · 스크립트가 센 「N / M」 · 진단 코드** 이다.
> ★★★ **ORM 을 설치하지 않았고 시간을 재지 않았다.** 3번의 공급자는 **직접 짠 장난감**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`AsFunc` 에만 `ldftn`**(`newobj Func`) · **`AsTree` 는 `Expression::Parameter` · `Constant` · `GreaterThan` · `Lambda`** · **`OnEnumerable` → `Enumerable::Where` · `OnQueryable` → 조립 사슬 뒤 `Queryable::Where`**

**출력**

```text
===== 소스: cs36b-il.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
public static class L {
    public static Func<int, bool> AsFunc() => x => x > 2;
    public static Expression<Func<int, bool>> AsTree() => x => x > 2;
    public static IEnumerable<int> OnEnumerable(IEnumerable<int> s) => s.Where(x => x > 2);
    public static IQueryable<int> OnQueryable(IQueryable<int> s) => s.Where(x => x > 2);
}
class Program {
    static void Main() {
        Il.Dump(typeof(L), "AsFunc");
        Il.Dump(typeof(L), "AsTree");
        Il.Dump(typeof(L), "OnEnumerable");
        Il.Dump(typeof(L), "OnQueryable");
    }
}
===== csc -optimize -r:il.dll -out:exo.dll cs36b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- L.AsFunc ---
  IL_0000: ldsfld L+<>c::<>9__0_0
  IL_0005: dup
  IL_0006: brtrue.s IL_001f
  IL_0008: pop
  IL_0009: ldsfld L+<>c::<>9
  IL_000e: ldftn L+<>c::<AsFunc>b__0_0
  IL_0014: newobj System.Func<System.Int32,System.Boolean>::.ctor
  IL_0019: dup
  IL_001a: stsfld L+<>c::<>9__0_0
  IL_001f: ret
--- L.AsTree ---
  .locals [0] System.Linq.Expressions.ParameterExpression
  IL_0000: ldtoken System.Int32
  IL_0005: call System.Type::GetTypeFromHandle
  IL_000a: ldstr "x"
  IL_000f: call System.Linq.Expressions.Expression::Parameter
  IL_0014: stloc.0
  IL_0015: ldloc.0
  IL_0016: ldc.i4.2
  IL_0017: box System.Int32
  IL_001c: ldtoken System.Int32
  IL_0021: call System.Type::GetTypeFromHandle
  IL_0026: call System.Linq.Expressions.Expression::Constant
  IL_002b: call System.Linq.Expressions.Expression::GreaterThan
  IL_0030: ldc.i4.1
  IL_0031: newarr System.Linq.Expressions.ParameterExpression
  IL_0036: dup
  IL_0037: ldc.i4.0
  IL_0038: ldloc.0
  IL_0039: stelem.ref
  IL_003a: call System.Linq.Expressions.Expression::Lambda<System.Func<System.Int32,System.Boolean>>
  IL_003f: ret
--- L.OnEnumerable ---
  IL_0000: ldarg.0
  IL_0001: ldsfld L+<>c::<>9__2_0
  IL_0006: dup
  IL_0007: brtrue.s IL_0020
  IL_0009: pop
  IL_000a: ldsfld L+<>c::<>9
  IL_000f: ldftn L+<>c::<OnEnumerable>b__2_0
  IL_0015: newobj System.Func<System.Int32,System.Boolean>::.ctor
  IL_001a: dup
  IL_001b: stsfld L+<>c::<>9__2_0
  IL_0020: call System.Linq.Enumerable::Where<System.Int32>
  IL_0025: ret
--- L.OnQueryable ---
  .locals [0] System.Linq.Expressions.ParameterExpression
  IL_0000: ldarg.0
  IL_0001: ldtoken System.Int32
  IL_0006: call System.Type::GetTypeFromHandle
  IL_000b: ldstr "x"
  IL_0010: call System.Linq.Expressions.Expression::Parameter
  IL_0015: stloc.0
  IL_0016: ldloc.0
  IL_0017: ldc.i4.2
  IL_0018: box System.Int32
  IL_001d: ldtoken System.Int32
  IL_0022: call System.Type::GetTypeFromHandle
  IL_0027: call System.Linq.Expressions.Expression::Constant
  IL_002c: call System.Linq.Expressions.Expression::GreaterThan
  IL_0031: ldc.i4.1
  IL_0032: newarr System.Linq.Expressions.ParameterExpression
  IL_0037: dup
  IL_0038: ldc.i4.0
  IL_0039: ldloc.0
  IL_003a: stelem.ref
  IL_003b: call System.Linq.Expressions.Expression::Lambda<System.Func<System.Int32,System.Boolean>>
  IL_0040: call System.Linq.Queryable::Where<System.Int32>
  IL_0045: ret
```

**왜 그런가**

- ★★★ 람다는 **목표 타입**을 따른다 — `Func<int,bool>` 이면 몸을 **메서드**로 컴파일해 주소를 담고, `Expression<Func<int,bool>>` 이면 몸을 **노드를 조립하는 호출**로 바꾼다(몸을 컴파일한 메서드가 없다).
- ★★★ `s.Where(x => x > 2)` 는 **`s` 의 정적 타입**으로 `Enumerable.Where(Func)` / `Queryable.Where(Expression)` 중 하나가 골라지고, 그것이 다시 람다의 목표 타입을 정한다.

### 2. ★★ **`[1]` 노드 다섯 — `Lambda` · `Parameter` · `GreaterThan` · `Parameter` · `Constant`** · `[3]` **``EnumerableQuery`1`` 둘** · `[4]` **`Queryable.Select` 가 뿌리, 그 아래 `Queryable.Where`**

**출력**

```text
===== 소스: cs36b-tree.cs =====
using System;
using System.Linq;
using System.Linq.Expressions;
class Program {
    static void Walk(Expression e, int d) {
        string extra = e is MethodCallExpression m ? $" · {m.Method.DeclaringType!.Name}.{m.Method.Name}" : "";
        Console.WriteLine($"{new string(' ', d * 2)}{e.NodeType} ({e.Type.Name}){extra} : {e}");
        switch (e) {
            case LambdaExpression l: foreach (var p in l.Parameters) Walk(p, d + 1); Walk(l.Body, d + 1); break;
            case BinaryExpression b: Walk(b.Left, d + 1); Walk(b.Right, d + 1); break;
            case MethodCallExpression c: foreach (var a in c.Arguments) Walk(a, d + 1); break;
            case UnaryExpression u: Walk(u.Operand, d + 1); break;
        }
    }
    static void Main() {
        Expression<Func<int, bool>> t = x => x > 2;
        Console.WriteLine($"[1] t.ToString() = {t}");
        Walk(t, 1);
        Func<int, bool> f = t.Compile();
        Console.WriteLine($"[2] t.Compile()(5) = {f(5)} · t.Compile()(1) = {f(1)}");
        var q = new[] { 1, 2, 3, 4 }.AsQueryable().Where(x => x > 2).Select(x => x * 10);
        Console.WriteLine($"[3] q 의 타입 {q.GetType().Name} · Provider {q.Provider.GetType().Name}");
        Console.WriteLine($"[4] q.Expression = {q.Expression}");
        Walk(q.Expression, 1);
        Console.WriteLine($"[5] q 를 돌리면 [{string.Join(", ", q)}]");
    }
}
===== csc -out:ex.dll cs36b-tree.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] t.ToString() = x => (x > 2)
  Lambda (Func`2) : x => (x > 2)
    Parameter (Int32) : x
    GreaterThan (Boolean) : (x > 2)
      Parameter (Int32) : x
      Constant (Int32) : 2
[2] t.Compile()(5) = True · t.Compile()(1) = False
[3] q 의 타입 EnumerableQuery`1 · Provider EnumerableQuery`1
[4] q.Expression = System.Int32[].Where(x => (x > 2)).Select(x => (x * 10))
  Call (IQueryable`1) · Queryable.Select : System.Int32[].Where(x => (x > 2)).Select(x => (x * 10))
    Call (IQueryable`1) · Queryable.Where : System.Int32[].Where(x => (x > 2))
      Constant (EnumerableQuery`1) : System.Int32[]
      Quote (Expression`1) : x => (x > 2)
        Lambda (Func`2) : x => (x > 2)
          Parameter (Int32) : x
          GreaterThan (Boolean) : (x > 2)
            Parameter (Int32) : x
            Constant (Int32) : 2
    Quote (Expression`1) : x => (x * 10)
      Lambda (Func`2) : x => (x * 10)
        Parameter (Int32) : x
        Multiply (Int32) : (x * 10)
          Parameter (Int32) : x
          Constant (Int32) : 10
[5] q 를 돌리면 [30, 40]
```

**왜 그런가**

- ★★ 식 트리는 **자료**다 — 걸어 다니며 `NodeType` 을 읽을 수 있다. `Where`·`Select` 를 이은 `IQueryable` 은 결과가 아니라 **`Call` 노드가 겹친 나무**를 들고 있고, 람다는 **`Quote`** 에 싸여 들어 있다.

### 3. ★★★ **`[1]`·`[2]`·`[9]` 는 `CreateQuery` 1 · `Execute` 0** · 나머지 아홉은 **`Execute` 1** — **Execute 가 불린 단계 9 / 12** · `[8]` 번역에 **`WHERE` 가 없다** · `[10]`·`[12]` 는 **`NotSupportedException`**

**출력**

```text
===== 소스: cs36b-toy.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;

// 장난감 공급자 — 식 트리를 SQL 비슷한 문자열로 번역하고, 번역한 조건으로만 메모리 표를 거른다.
class ToyProvider : IQueryProvider {
    public static readonly List<string> log = new();
    readonly int[] table;
    public ToyProvider(int[] table) { this.table = table; }
    public IQueryable CreateQuery(Expression e) => throw new NotSupportedException("비제네릭 CreateQuery");
    public IQueryable<T> CreateQuery<T>(Expression e) { log.Add("CreateQuery"); return new ToyQuery<T>(this, e); }
    public object Execute(Expression e) => throw new NotSupportedException("비제네릭 Execute");
    public TResult Execute<TResult>(Expression e) {
        log.Add("Execute");
        var (sql, preds, tail) = Translate(e);
        log.Add($"번역: {sql}");
        var rows = table.Where(x => preds.All(p => p(x)));
        object r = tail switch { "Count" => rows.Count(), "First" => rows.First(), _ => rows.ToList() };
        return (TResult)r;
    }
    static (string, List<Func<int, bool>>, string) Translate(Expression e) {
        var conds = new List<string>(); var preds = new List<Func<int, bool>>(); string tail = "";
        while (e is MethodCallExpression m) {
            switch (m.Method.Name) {
                case "Where":
                    var lam = (LambdaExpression)((UnaryExpression)m.Arguments[1]).Operand;
                    conds.Insert(0, Cond(lam.Body));
                    preds.Insert(0, (Func<int, bool>)lam.Compile());
                    break;
                case "Count": case "First": tail = m.Method.Name; break;
                default: throw new NotSupportedException($"번역 못 함: 연산자 {m.Method.Name}");
            }
            e = m.Arguments[0];
        }
        string select = tail == "Count" ? "COUNT(*)" : tail == "First" ? "TOP 1 x" : "x";
        string where = conds.Count == 0 ? "" : " WHERE " + string.Join(" AND ", conds);
        return ($"SELECT {select} FROM t{where}", preds, tail);
    }
    static string Cond(Expression b) => b switch {
        BinaryExpression { NodeType: ExpressionType.GreaterThan } g => $"{Cond(g.Left)} > {Cond(g.Right)}",
        BinaryExpression { NodeType: ExpressionType.LessThan } g => $"{Cond(g.Left)} < {Cond(g.Right)}",
        ParameterExpression => "x",
        ConstantExpression c => $"{c.Value}",
        MemberExpression { Expression: ConstantExpression } mm => $"{Expression.Lambda(mm).Compile().DynamicInvoke()}",
        MethodCallExpression mc => throw new NotSupportedException($"번역 못 함: 메서드 {mc.Method.DeclaringType!.Name}.{mc.Method.Name}"),
        _ => throw new NotSupportedException($"번역 못 함: 노드 {b.NodeType}"),
    };
}
class ToyQuery<T> : IQueryable<T> {
    readonly ToyProvider p;
    public ToyQuery(ToyProvider p, Expression? e = null) { this.p = p; Expression = e ?? Expression.Constant(this); }
    public Type ElementType => typeof(T);
    public Expression Expression { get; }
    public IQueryProvider Provider => p;
    public IEnumerator<T> GetEnumerator() => p.Execute<List<T>>(Expression).GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    public override string ToString() => "t";
}
class Program {
    static bool IsOdd(int x) => x % 2 == 1;
    static int steps, executed;
    static void Step(string label, Func<object?> f) {
        ToyProvider.log.Clear();
        string r;
        try {
            var v = f();
            r = v is IQueryable ? "(IQueryable)" : v is IEnumerable e ? "[" + string.Join(",", e.Cast<object>()) + "]" : $"{v}";
        }
        catch (Exception e) { r = $"{e.GetType().Name} — {e.Message}"; }
        int c = ToyProvider.log.Count(l => l == "CreateQuery"), x = ToyProvider.log.Count(l => l == "Execute");
        steps++; if (x > 0) executed++;
        string[] cells = { label, c.ToString(), x.ToString(), r, string.Join(" / ", ToyProvider.log.Where(l => l.StartsWith("번역"))) };
        if (cells.Length != 5) throw new Exception("칸 수 어긋남");
        Console.WriteLine(string.Join("\t", cells));
    }
    static void Main() {
        var db = new ToyQuery<int>(new ToyProvider(new[] { 1, 2, 3, 4, 5 }));
        IQueryable<int> q = null!;
        int min = 1;
        Console.WriteLine(string.Join("\t", "단계", "CreateQuery", "Execute", "결과", "공급자가 만든 번역"));
        Step("[1] q = db.Where(x => x > min)", () => q = db.Where(x => x > min));
        Step("[2] q = q.Where(x => x < 5)", () => q = q.Where(x => x < 5));
        Step("[3] q.ToList()", () => q.ToList());
        Step("[4] q.Count()", () => q.Count());
        Step("[5] q.First()", () => q.First());
        Step("[6] foreach (var x in q)", () => { var s = new List<int>(); foreach (var x in q) s.Add(x); return s; });
        Step("[7] min = 3; q.ToList()", () => { min = 3; return q.ToList(); });
        Step("[8] IEnumerable<int> e = db; e.Where(x => x > 1).ToList()", () => { IEnumerable<int> e = db; return e.Where(x => x > 1).ToList(); });
        Step("[9] q = db.Where(x => IsOdd(x))", () => q = db.Where(x => IsOdd(x)));
        Step("[10] q.ToList()", () => q.ToList());
        Step("[11] db.Where(x => x > 1).AsEnumerable().Where(IsOdd).ToList()", () => db.Where(x => x > 1).AsEnumerable().Where(IsOdd).ToList());
        Step("[12] db.Select(x => x * 10).ToList()", () => db.Select(x => x * 10).ToList());
        Console.WriteLine($"Execute 가 불린 단계 {executed} / {steps}");
    }
}
===== csc -nullable:enable -out:ex.dll cs36b-toy.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
단계	CreateQuery	Execute	결과	공급자가 만든 번역
[1] q = db.Where(x => x > min)	1	0	(IQueryable)	
[2] q = q.Where(x => x < 5)	1	0	(IQueryable)	
[3] q.ToList()	0	1	[2,3,4]	번역: SELECT x FROM t WHERE x > 1 AND x < 5
[4] q.Count()	0	1	3	번역: SELECT COUNT(*) FROM t WHERE x > 1 AND x < 5
[5] q.First()	0	1	2	번역: SELECT TOP 1 x FROM t WHERE x > 1 AND x < 5
[6] foreach (var x in q)	0	1	[2,3,4]	번역: SELECT x FROM t WHERE x > 1 AND x < 5
[7] min = 3; q.ToList()	0	1	[4]	번역: SELECT x FROM t WHERE x > 3 AND x < 5
[8] IEnumerable<int> e = db; e.Where(x => x > 1).ToList()	0	1	[2,3,4,5]	번역: SELECT x FROM t
[9] q = db.Where(x => IsOdd(x))	1	0	(IQueryable)	
[10] q.ToList()	0	1	NotSupportedException — 번역 못 함: 메서드 Program.IsOdd	
[11] db.Where(x => x > 1).AsEnumerable().Where(IsOdd).ToList()	1	1	[3,5]	번역: SELECT x FROM t WHERE x > 1
[12] db.Select(x => x * 10).ToList()	1	1	NotSupportedException — 번역 못 함: 연산자 Select	
Execute 가 불린 단계 9 / 12
```

**왜 그런가**

- ★★★ `Queryable.Where` 는 공급자의 **`CreateQuery`** 를 부를 뿐이다 — 결과를 요구하는 연산(`ToList` · `Count` · `First` · `foreach`)이 와야 **`Execute`** 로 식 트리 **전체**가 넘어간다. 그래서 두 `Where` 가 **한 번역문**(`WHERE x > 1 AND x < 5`)으로 합쳐지고, `Count`·`First` 까지 번역에 들어간다.
- ★★★ `[7]` 은 번역 때 **지금의 `min`** 을 읽었다 · `[8]` 은 정적 타입 `IEnumerable<int>` 라 **거르기가 메모리로** · `[11]` 은 `AsEnumerable` 앞만 번역.

### 4. ★★★ **막힌 칸 8 / 20** — `Func` 열 전부 `ok` · `Expression` 열에서 **`CS0834`·`CS0832`·`CS8072`·`CS8514`·`CS8122`·`CS8188`·`CS8143`·`CS8110`** · 보간 문자열과 `&&` 비교는 `ok`

**출력**

```text
===== 소스: cs36b-ban.cs =====
using System;
using System.Linq.Expressions;
class P {
    static int n;
    static string? s = null;
    static void M() {
        Func<int, bool> a1 = x => { return x > 2; };                        // cell 문-본문 Func
        Expression<Func<int, bool>> a2 = x => { return x > 2; };            // cell 문-본문 Expression
        Func<int, int> b1 = x => n = x;                                      // cell 대입 Func
        Expression<Func<int, int>> b2 = x => n = x;                          // cell 대입 Expression
        Func<int, int> c1 = x => s?.Length ?? 0;                             // cell 널-조건 Func
        Expression<Func<int, int>> c2 = x => s?.Length ?? 0;                 // cell 널-조건 Expression
        Func<int, int> d1 = x => x switch { 1 => 10, _ => 0 };              // cell switch-식 Func
        Expression<Func<int, int>> d2 = x => x switch { 1 => 10, _ => 0 };  // cell switch-식 Expression
        Func<int, bool> e1 = x => x is > 2;                                  // cell is-패턴 Func
        Expression<Func<int, bool>> e2 = x => x is > 2;                      // cell is-패턴 Expression
        Func<int, int> f1 = x => throw new Exception();                      // cell throw-식 Func
        Expression<Func<int, int>> f2 = x => throw new Exception();          // cell throw-식 Expression
        Func<int, (int, int)> g1 = x => (x, x);                              // cell 튜플 Func
        Expression<Func<int, (int, int)>> g2 = x => (x, x);                  // cell 튜플 Expression
        Func<int, int> h1 = x => Local(x);                                   // cell 지역-함수 Func
        Expression<Func<int, int>> h2 = x => Local(x);                       // cell 지역-함수 Expression
        Func<int, string> i1 = x => $"{x}";                                  // cell 보간-문자열 Func
        Expression<Func<int, string>> i2 = x => $"{x}";                      // cell 보간-문자열 Expression
        Func<int, bool> j1 = x => x > 2 && x < 9;                            // cell 비교-논리 Func
        Expression<Func<int, bool>> j2 = x => x > 2 && x < 9;                // cell 비교-논리 Expression
        static int Local(int v) => v;
    }
    static void Main() { }
}
===== csc -nullable:enable -out:ex.dll cs36b-ban.cs 2>&1 | sort (cc exit=1) =====
cs36b-ban.cs(10,46): error CS0832: An expression tree may not contain an assignment operator
cs36b-ban.cs(12,46): error CS8072: An expression tree lambda may not contain a null propagating operator.
cs36b-ban.cs(14,46): error CS8514: An expression tree may not contain a switch expression.
cs36b-ban.cs(16,47): error CS8122: An expression tree may not contain an 'is' pattern-matching operator.
cs36b-ban.cs(18,46): error CS8188: An expression tree may not contain a throw-expression.
cs36b-ban.cs(20,53): error CS8143: An expression tree may not contain a tuple literal.
cs36b-ban.cs(22,46): error CS8110: An expression tree may not contain a reference to a local function
cs36b-ban.cs(8,42): error CS0834: A lambda expression with a statement body cannot be converted to an expression tree
===== python3 cellgrid.py cs36b-ban.cs <위 진단> — 칸마다 진단 코드 =====
식 \ 자리           Func             Expression
문-본문             ok               CS0834
대입               ok               CS0832
널-조건             ok               CS8072
switch-식         ok               CS8514
is-패턴            ok               CS8122
throw-식          ok               CS8188
튜플               ok               CS8143
지역-함수            ok               CS8110
보간-문자열           ok               ok
비교-논리            ok               ok
막힌 칸 8 / 20
```

**왜 그런가**

- ★★★ 식 트리는 **정해진 노드 종류**로만 그릴 수 있다. 문 본문 · 대입 · `?.` · `switch` 식 · `is` 패턴 · `throw` 식 · 튜플 · 지역 함수는 **그 노드로 나타낼 수 없어** 컴파일러가 막는다. 델리게이트는 그냥 **컴파일된 코드**라 제약이 없다.

### 5. ★ **`(a, b) => (a + b) · Add · 매개변수 2` · `5` · `x => (x > 2) · True` · `3,4`**

**출력**

```text
===== 소스: cs36b-form.cs =====
using System;
using System.Linq;
using System.Linq.Expressions;

Expression<Func<int, int, int>> add = (a, b) => a + b;
Console.WriteLine($"{add} · {add.Body.NodeType} · 매개변수 {add.Parameters.Count}");
Console.WriteLine(add.Compile()(2, 3));

var p = Expression.Parameter(typeof(int), "x");
var built = Expression.Lambda<Func<int, bool>>(Expression.GreaterThan(p, Expression.Constant(2)), p);
Console.WriteLine($"{built} · {built.Compile()(3)}");
Console.WriteLine(string.Join(",", new[] { 1, 2, 3, 4 }.AsQueryable().Where(built)));
===== csc -out:ex.dll cs36b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
(a, b) => (a + b) · Add · 매개변수 2
5
x => (x > 2) · True
3,4
```

- ★ 손으로 부른 `Expression.Parameter`·`Constant`·`GreaterThan`·`Lambda` 는 1번에서 **컴파일러가 대신 쓴 사슬**과 같다 — 같은 나무(`x => (x > 2)`)가 나온다.

### 6. ★★★ **`e` 의 정적 타입이 `IEnumerable<int>` 라 `Enumerable.Where` 가 골라졌다** — 공급자는 `WHERE` 없는 트리를 받아 **표 전체**를 주고, 거르기는 **메모리에서** · **결과 값(`[2,3,4,5]`)만으로는 못 잡는다**

- ★★★ 1번의 `OnEnumerable` 과 같은 IL — 람다는 **델리게이트**가 되어 공급자가 **읽을 수 없다.** 번역문(`SELECT x FROM t`)만이 차이를 말한다. 결과가 맞으니 **테스트는 초록색**이다.

### 7. ★★★ **`[9]` 는 조용하고 `[10]` 의 `Execute` 에서 공급자가 거부** — 4번은 **컴파일러가 빌드할 때** 막는다

- ★★★ `IsOdd(x)` 는 **정적 메서드 호출 노드**로 식 트리에 **그릴 수 있다** — 그래서 컴파일도 `Where` 도 통과한다. 그 노드를 **번역할 수 있나**는 공급자의 몫이고, 공급자에게 번역을 청하는 것은 `Execute` 다. 4번의 여덟 꼴은 **그릴 수조차 없어서** 빌드 때 막힌다. **막는 쪽이 둘 · 때가 둘**이다.

### 8. ★★★ **계약의 모양** — 「`Where` 를 이을 때는 `CreateQuery` 뿐 · 결과를 요구할 때 식 트리 전체가 넘어간다 · 정적 타입이 `IEnumerable` 이면 `Queryable` 을 안 탄다」 · **장난감의 규칙** — 번역문의 모양 · 무엇을 번역하고 무엇을 거부하나 · `GetEnumerator` 에서 `Execute` 를 부르는 것 · ★ **EF Core 에 대해서는 말할 수 있는 것이 없다**

- ★★★ `Execute` 안에서 SQL 을 만들지 · 거부할지 · 메모리에서 돌릴지는 **공급자마다 다르다.** 이 문서의 공급자는 **내가** 그렇게 짰다. `CreateQuery`/`Execute` 가 **언제 불리나**는 `Queryable` 쪽 코드가 정한 것이라 장난감과 무관하게 관찰된다(★ 그것도 이 판의 구현 관찰이다).
- ★ EF Core 는 **설치하지도 문서를 열지도 않았다.** 「번역 못 하면 실행 지점에서 알린다」는 **장난감의 규칙**이지 EF Core 의 확인된 동작이 아니다 — 확인할 것으로 남는다.

### 9. ★★ **`AsEnumerable` 은 소스 그 자체를 돌려줬다(33번 `<Src>d__1`)** — 객체는 그대로이고 **정적 타입만** `IEnumerable<int>` 로 바뀌므로, 그 뒤의 `Where(IsOdd)` 가 **`Enumerable.Where`** 로 골라진다

- ★★ 앞쪽 `Where(x => x > 1)` 는 이미 식 트리에 들어가 **번역**되고(`WHERE x > 1`), `ToList` 가 `ToyQuery` 를 열거할 때 한 번 `Execute` 된다. 받아 온 `2,3,4,5` 에 `IsOdd` 가 **C# 으로** 적용되어 `[3,5]`.

### 10. ★★ **재지 않았다** — 3번이 보여 준 것은 **거르기가 어디서 일어나나**(번역문의 `WHERE` 유무 · 받아 온 행) · 시간 차이는 **실제 DB 와 원격 왕복**이 있어야 잰다 · `[7]` 은 33번 (3)과 **같은 함정** — 식 트리에 **변수**가 들어가 번역 때 읽힌다

- ★★ 이 문서에 「빠르다」는 문장이 없다. 장난감의 표는 메모리 배열이라 **거리가 없다** — 잴 것이 있어도 잴 수 없는 판이다(못 잰 것).
- ★ [33번](../33-linq-method-syntax-and-deferred-execution/) (3) — `Enumerable` 쪽은 **람다가 부를 때** 변수를 읽고, 여기서는 **공급자가 번역할 때** 읽는다. 둘 다 **정의 때가 아니다.**

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs36b-il.cs` | csc 1회(`-optimize`) · 실행 1회 | ★★★ `ldftn`·`newobj Func` 대 `Expression::…` 사슬 · `Enumerable::Where` 대 `Queryable::Where` |
| `cs36b-tree.cs` | csc 1회 · 실행 1회 | 노드 다섯 · ``EnumerableQuery`1`` · `Queryable.Select`/`Where` |
| `cs36b-toy.cs` | csc 1회 · 실행 1회 | ★★★ **Execute 가 불린 단계 9 / 12** · `[8]` `WHERE` 없음 · `[10]`·`[12]` 거부 |
| `cs36b-ban.cs` | csc 1회(`sort`) + cellgrid 1회 | ★★★ **막힌 칸 8 / 20** |
| `cs36b-form.cs` | csc 1회 · 실행 1회 | `Add` · `5` · `True` · `3,4` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12)에서만** 그렇다.

- ★★ 식 트리 람다의 **조립 사슬 모양 · 캐시 없음**(Roslyn) · `Queryable` 연산자가 `CreateQuery`/`Execute` 를 부르는 **방식** · 진단 코드 배정.

**언어·문서가 보장하는 것**(구현이 바뀌어도 같다)

- **람다의 목표 타입 변환(델리게이트 / 식 트리)** · **식 트리로 못 그리는 꼴은 컴파일 에러** · **오버로드 해석이 정적 타입을 따른다** · `IQueryProvider` 의 두 일(XML).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★★ **실제 ORM**(설치하지 않았다) · `ExpressionVisitor`.
- **못 잰 것** — ★★★ **DB 에서의 시간**(DB 가 없다) · 식 트리의 할당·`Compile()` 비용.
- **잴 것이 없는 것** — 없다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **4번** — 식 트리가 새 노드를 받아들이면(예: `?.`) 그 칸이 `ok` 로 바뀐다. **1번** 의 조립 사슬 모양 · 캐시 유무.
