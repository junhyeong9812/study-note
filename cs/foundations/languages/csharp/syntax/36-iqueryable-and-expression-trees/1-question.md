# csharp/syntax/36 — `IQueryable` 과 식 트리 맛보기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**`Func` 은 실행 파일, `Expression` 은 설계도 — `IQueryable` 은 설계도를 쌓다가 결과를 요구받을 때 공급자에게 통째로 넘긴다**」 한 줄로 거의 다 풀린다. **공급자에게 언제 무엇이 닿나**를 세라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. ★ ORM 은 **설치하지 않았다** — 3번의 공급자는 **직접 짠 장난감**이다.
> ★★★ **본체 창은 ① IL + ⑤ 장난감 공급자 로그다.**
> 선행 — [35번](../35-linq-grouping-joins-and-aggregation/) · [33번](../33-linq-method-syntax-and-deferred-execution/)(`AsEnumerable` · 캡처) · [28번](../28-lambdas-and-closure-capture/)(람다의 IL).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 같은 람다 · 네 메서드의 IL (예측)

```csharp
// cs36b-il.cs
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
```

- ★★★ `AsFunc` 과 `AsTree` 의 IL 에 `ldftn` 이 있나? 각각 무엇을 `call` 하나?
- ★★★ `OnEnumerable` 과 `OnQueryable` 은 각각 어느 클래스의 `Where` 를 부르나?

### 2. ★★ 식 트리를 걸어 보면 (예측)

```csharp
// cs36b-tree.cs
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
```

- ★★ `[1]` 의 노드는 몇 개이고 어떤 `NodeType` 들인가?
- ★★ `[3]`·`[4]` 줄은? `[4]` 아래 덤프에서 `Call` 노드는 어느 클래스의 어느 메서드인가?

### 3. ★★★ 장난감 공급자 — 열두 단계 (예측)

```csharp
// cs36b-toy.cs
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
```

- ★★★ 열두 단계 각각 `CreateQuery` · `Execute` 칸의 수와 결과는? 번역 칸에는 무엇이 찍히나?
- ★★ 마지막 줄의 `N / M` 은?

### 4. ★★★ 같은 본문 · `Func` 과 `Expression` (예측)

```csharp
// cs36b-ban.cs
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
```

- ★★★ 스무 칸 각각의 진단 코드는(없으면 `ok`)? 마지막 줄의 `N / M` 은?

### 5. ★ 식 트리를 손으로 (예측)

```csharp
// cs36b-form.cs
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
```

- ★ 네 줄의 출력은?

### 6. ★★★ 3번의 `[8]` (왜)

- `[8]` 을 1번의 `OnEnumerable`·`OnQueryable` 로 설명하라. **결과 값**만 보고 `[3]` 과의 차이를 잡을 수 있나?

### 7. ★★★ 3번의 `[9]`·`[10]` 과 4번 (왜)

- `IsOdd` 가 든 쿼리는 어느 줄에서 무슨 일이 일어나나? 4번의 `Expression` 열과 견주면 **막는 쪽 · 막는 때**가 어떻게 다른가?

### 8. ★★★ 3번은 무엇을 증명하고 무엇을 증명하지 못하나 (경계)

- 장난감의 `Execute` 가 하는 일은 누가 정했나? 3번에서 **`IQueryable` 계약의 모양**으로 읽어도 되는 칸과 **장난감의 규칙**일 뿐인 칸을 갈라라.
- ★ EF Core 의 번역 실패에 대해 이 문서가 말할 수 있는 것은?

### 9. ★★ 3번의 `[11]` 과 33번의 `AsEnumerable` (경계)

- [33번](../33-linq-method-syntax-and-deferred-execution/) (1)에서 `AsEnumerable` 이 돌려준 객체는 무엇이었나? 그 사실로 3번 `[11]` 을 설명하라.

### 10. ★★ 「`IQueryable` 이 DB 에서 빠르다」 (연결)

- 이 문서는 그것을 쟀나? 3번이 대신 보여 준 것은 무엇이고, 시간 차이를 재려면 무엇이 더 있어야 하나?
- ★ 3번 `[7]` 을 [33번](../33-linq-method-syntax-and-deferred-execution/) (3)의 캡처 함정과 견주면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
