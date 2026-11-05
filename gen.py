from html import escape

ART = r"""
        .-----------------------.
        |  $ ./start-server.sh  |
        |  > listening :8080    |
        |  > GET /api   200 OK  |
        |  > POST /api  201     |
        |  _                    |
        '-----------------------'
             _|___________|_
    .-------------------------------.
    |  [::::::::::]  [ ]  o o o     |
    |-------------------------------|
    |  [::::::::::]  [ ]  o o o     |
    |-------------------------------|
    |  [::::::::::]  [ ]  o o o     |
    '-------------------------------'
       ||                     ||
""".strip("\n").split("\n")

W = 58  # width of info column in chars

def kv(k, v):
    dots = W - len(k) - len(v) - 4
    return [("t", ". "), ("k", k), ("t", ":"), ("d", " " + "." * dots + " "), ("v", v)]

def sec(title):
    return [("t", "- "), ("h", title), ("t", " " + "-" * (W - len(title) - 3))]

INFO = [
    [("h", "sinsun030508"), ("t", "@"), ("h", "github")],
    [("t", "-" * W)],
    kv("OS", "Windows, Linux"),
    kv("Uni", "Inha Technical College"),
    kv("Major", "Computer Systems Engineering"),
    kv("Role", "Aspiring Backend Developer"),
    kv("IDE", "Eclipse, VS Code, IntelliJ IDEA"),
    [],
    kv("Languages.Programming", "Java, Python, JSP"),
    kv("Languages.Database", "SQL"),
    kv("Languages.Real", "Korean, English"),
    [],
    kv("Interests", "Server, API, Database, OOP"),
    [],
    sec("Projects"),
    kv("DnF_Battle", "OOP game system (UML/Java)"),
    kv("SungJuk", "Grade management (JSP)"),
    kv("Subway B/C", "Cost-benefit simulator"),
    [],
    sec("Contact"),
    kv("GitHub", "github.com/sinsun030508"),
    kv("Email", "sinsun030508@naver.com"),
]

THEMES = {
    "dark":  dict(bg="#161b22", border="#30363d", t="#c9d1d9", k="#ffa657", v="#a5d6ff", d="#616e7f", h="#79c0ff", art="#c9d1d9"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", t="#24292f", k="#953800", v="#0a3069", d="#c2cfde", h="#0550ae", art="#24292f"),
}

LH, CW, FS = 20, 9.6, 16
def build(name, c):
    rows = max(len(ART), len(INFO))
    h = rows * LH + 50
    artw = max(len(l) for l in ART) * CW
    x2 = 25 + artw + 30
    w = int(x2 + W * CW + 45)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="ConsolasFallback,Consolas,\'Courier New\',monospace" font-size="{FS}px">',
           f'<style>.t{{fill:{c["t"]}}}.k{{fill:{c["k"]}}}.v{{fill:{c["v"]}}}.d{{fill:{c["d"]}}}.h{{fill:{c["h"]};font-weight:bold}}text,tspan{{white-space:pre}}</style>',
           f'<rect width="{w}" height="{h}" rx="15" fill="{c["bg"]}" stroke="{c["border"]}"/>']
    top = (h - len(ART) * LH) / 2 + 14
    out.append(f'<text x="25" y="{top}" fill="{c["art"]}" class="t">')
    for i, l in enumerate(ART):
        out.append(f'<tspan x="25" y="{top + i*LH:.0f}">{escape(l)}</tspan>')
    out.append('</text>')
    out.append(f'<text x="{x2:.0f}" y="40">')
    for i, line in enumerate(INFO):
        y = 40 + i * LH
        if not line: continue
        out.append(f'<tspan x="{x2:.0f}" y="{y}">' + "".join(f'<tspan class="{cl}">{escape(s)}</tspan>' for cl, s in line) + '</tspan>')
    out.append('</text></svg>')
    open(f"{name}_mode.svg", "w").write("\n".join(out))

for n, c in THEMES.items(): build(n, c)
