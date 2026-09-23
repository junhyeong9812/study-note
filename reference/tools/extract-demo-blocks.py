#!/usr/bin/env python3
"""문서에서 `demo` 블록을 뽑아 다시 띄워 「보이는 것」이 실제로 그런지 대조한다.

왜 필요한가
-----------
`render-rules.md` 의 「쓴 사람이 직접 확인한다」는 **쓰는 동안** 확인하라는 규칙이다.
그것만으로는 **옮겨 적기 사고**가 안 걸린다 — 실제로 띄워 보고 값을 받아 놓고
문서로 옮기는 과정에서 틀리는 것. SQL 60주제에서 같은 유형이 4건 나왔고
넷 다 손으로 재배치한 블록이었다. 그래서 `extract-exec-blocks.py` 의 demo 판이 필요하다.

★ **이 도구는 「보이는 것」이 맞는지 판정하지 않는다.** 자연어라 기계가 못 읽는다.
하는 일은 **블록을 뽑아 실제로 띄우고 계산값을 덤프하는 것**까지다 —
그 덤프와 문서의 서술을 맞춰 보는 것은 사람이 한다. 판정을 자동화한 척하지 않는다.

쓰는 법
-------
    python3 extract-demo-blocks.py <문서.md ...>            # 블록 목록만
    python3 extract-demo-blocks.py --render <문서.md ...>   # 띄워서 계산값까지

`--render` 는 Chrome headless 를 쓴다. 블록에는 `<!doctype>`·`<body>` 가 없으므로
**래퍼를 붙여서** 띄운다(`render-rules.md` 에 적힌 함정 — 안 붙이면 기본 여백 때문에
실측 좌표가 문서와 어긋난다).

한계 — 이 도구가 못 보는 것
--------------------------
- **입력이 걸린 것**(`:hover`·`:focus`·`:active`)은 못 켠다. CDP 로 `Input.dispatch*` 를
  넣어야 하고, 그건 블록마다 무엇을 누를지 사람이 정해야 한다.
- **시간이 걸린 것**(전환·애니메이션)은 한 시점만 본다.
- 그래서 **「이 블록은 이 도구로 확인이 안 된다」는 목록을 같이 낸다.** 조용히 통과시키지 않는다.
"""
import re, sys, subprocess, tempfile, os, json

FENCE = re.compile(r'^```(\w+)\s+demo\s*$')
CAPTION = re.compile(r'^>\s*\*\*(보이는 것|바꿔 볼 것|실측)\*\*')
NEEDS_INPUT = re.compile(r':hover|:focus|:active|:target|transition|animation|@keyframes')

PROBE = """
<script>
var out=[];
document.querySelectorAll('*').forEach(function(el){
  if(['SCRIPT','STYLE','HEAD','HTML','PRE'].indexOf(el.tagName)>=0) return;
  var c=getComputedStyle(el), r=el.getBoundingClientRect();
  out.push([el.tagName.toLowerCase()+(el.id?'#'+el.id:'')+(el.className&&typeof el.className==='string'?'.'+el.className.trim().replace(/\\s+/g,'.'):''),
    'rect='+Math.round(r.left)+','+Math.round(r.top)+' '+Math.round(r.width)+'x'+Math.round(r.height),
    'color='+c.color,'bg='+c.backgroundColor,'display='+c.display,
    'margin='+c.marginTop+'/'+c.marginBottom].join('  '));
});
var p=document.createElement('pre');
p.id='__probe';
p.textContent='<<<BEGIN>>>\\n'+out.join('\\n')+'\\n<<<END>>>';
document.body.appendChild(p);
</script>
"""


def blocks(path):
    """`demo` 펜스와 바로 뒤의 캡션 줄들을 함께 뽑는다."""
    lines = open(path, encoding='utf-8').read().split('\n')
    out, i = [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        start, lang, body = i + 1, m.group(1), []
        i += 1
        while i < len(lines) and not lines[i].startswith('```'):
            body.append(lines[i]); i += 1
        i += 1
        caps = []
        while i < len(lines):
            if not lines[i].strip():
                i += 1; continue
            if CAPTION.match(lines[i]):
                caps.append(lines[i].strip()); i += 1
            else:
                break
        src = '\n'.join(body)
        out.append(dict(file=path, line=start, lang=lang, src=src, captions=caps,
                        needs_input=bool(NEEDS_INPUT.search(src))))
    return out


def render(b):
    doc = ('<!doctype html><meta charset="utf-8"><title>demo</title>\n'
           '<style>body{margin:0}</style>\n' + b['src'] + PROBE)
    fd, p = tempfile.mkstemp(suffix='.html'); os.write(fd, doc.encode()); os.close(fd)
    try:
        r = subprocess.run(['google-chrome', '--headless', '--disable-gpu', '--no-sandbox',
                            '--dump-dom', p], capture_output=True, text=True, timeout=60)
        m = re.search(r'&lt;&lt;&lt;BEGIN&gt;&gt;&gt;(.*?)&lt;&lt;&lt;END&gt;&gt;&gt;', r.stdout, re.S)
        if not m:
            m = re.search(r'<<<BEGIN>>>(.*?)<<<END>>>', r.stdout, re.S)
        return m.group(1).strip() if m else '(프로브 출력 없음)'
    finally:
        os.unlink(p)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--render']
    do_render = '--render' in sys.argv
    allb, no_caption, cannot = [], [], []
    for f in args:
        for b in blocks(f):
            allb.append(b)
            if not any('보이는 것' in c for c in b['captions']):
                no_caption.append(b)
            if b['needs_input']:
                cannot.append(b)
            if do_render:
                print('===== %s:%d  (%s)' % (b['file'], b['line'], b['lang']))
                for c in b['captions']:
                    print('  ' + c)
                print(render(b)); print()
    print('demo 블록 %d개' % len(allb), file=sys.stderr)
    if no_caption:
        print('★ 「보이는 것」이 없는 블록 %d개 — render-rules 가 필수로 정한다'
              % len(no_caption), file=sys.stderr)
        for b in no_caption:
            print('   %s:%d' % (b['file'], b['line']), file=sys.stderr)
    if cannot:
        print('※ 입력·시간이 걸려 이 도구로는 확인이 안 되는 블록 %d개 — 사람이 CDP 로 확인한다'
              % len(cannot), file=sys.stderr)
        for b in cannot:
            print('   %s:%d' % (b['file'], b['line']), file=sys.stderr)
    sys.exit(1 if no_caption else 0)
