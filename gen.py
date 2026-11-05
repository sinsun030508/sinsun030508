"""dark_mode.svg / light_mode.svg 생성기.

GITHUB_TOKEN(또는 ACCESS_TOKEN) 환경변수가 있으면 GraphQL API로 전체 통계를 채우고,
없으면 공개 REST API로 Repos/Stars/Commits/Followers 를 채운다(Lines of Code 는 토큰 필요). GitHub Actions(.github/workflows/update.yml)가 매일 실행한다.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from html import escape

USER = "sinsun030508"

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

# ---------------------------------------------------------------- GitHub Stats
# GITHUB_TOKEN(Actions 기본 토큰)은 공개+비공개 기여 수를 포함한 커밋 수를 주고,
# ACCESS_TOKEN(PAT, 선택)을 넣으면 비공개 저장소까지 저장소 수/코드 줄 수에 포함된다.
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
PRIV_TOKEN = os.environ.get("ACCESS_TOKEN") or TOKEN


def graphql(query, variables=None, token=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"Bearer {token or TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
    if resp.get("errors"):
        raise RuntimeError(resp["errors"])
    return resp["data"]


LOC_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      history(first: 100, author: {id: $id}, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { additions deletions }
      }
    } } }
  }
}"""


def lines_of_code(repo_names, user_id):
    add = rem = 0
    for name in repo_names:
        cursor = None
        try:
            while True:
                ref = graphql(LOC_QUERY, {"owner": USER, "name": name, "id": user_id, "cursor": cursor},
                              token=PRIV_TOKEN)["repository"]["defaultBranchRef"]
                if ref is None:  # 빈 저장소
                    break
                h = ref["target"]["history"]
                add += sum(n["additions"] for n in h["nodes"])
                rem += sum(n["deletions"] for n in h["nodes"])
                if not h["pageInfo"]["hasNextPage"]:
                    break
                cursor = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"loc {name}: {e}")
    return add, rem


def fetch_stats():
    u = graphql(f"""
    query {{
      user(login: "{USER}") {{
        id createdAt
        followers {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER) {{
          totalCount
          nodes {{ name stargazerCount isFork }}
        }}
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {{
          totalCount
        }}
      }}
    }}""", token=PRIV_TOKEN)["user"]

    # contributionsCollection 은 한 번에 1년까지만 조회 가능 → 가입 연도부터 연도별로 합산
    joined = int(u["createdAt"][:4])
    aliases = "\n".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z")'
        " { totalCommitContributions restrictedContributionsCount }"
        for y in range(joined, datetime.now(timezone.utc).year + 1)
    )
    contrib = graphql(f'query {{ user(login: "{USER}") {{ {aliases} }} }}')["user"]
    commits = sum(v["totalCommitContributions"] + v["restrictedContributionsCount"] for v in contrib.values())

    nodes = u["repositories"]["nodes"]
    add, rem = lines_of_code([n["name"] for n in nodes if not n["isFork"]], u["id"])
    return {
        "repos": u["repositories"]["totalCount"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in nodes),
        "followers": u["followers"]["totalCount"],
        "commits": commits,
        "loc_add": add,
        "loc_del": rem,
    }


def rest(url):
    """토큰이 없어도 동작하는 공개 REST API 호출 (시간당 60회 제한)."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-gen"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.loads(r.read())


def fetch_stats_rest():
    """토큰 없이 PC에서 실행할 때: 공개 데이터만으로 통계 계산 (Lines of Code 제외)."""
    api = "https://api.github.com"
    u = rest(f"{api}/users/{USER}")
    repos = rest(f"{api}/users/{USER}/repos?per_page=100&type=owner")
    s = {
        "repos": u["public_repos"],
        "contributed": None,
        "stars": sum(r["stargazers_count"] for r in repos),
        "followers": u["followers"],
        "commits": None,
        "loc_add": None,
        "loc_del": None,
    }
    try:
        s["commits"] = rest(f"{api}/search/commits?q=author:{USER}&per_page=1")["total_count"]
    except Exception as e:
        print("commits fetch failed:", e)
    return s


def get_stats():
    if TOKEN:
        try:
            s = fetch_stats()
            print("stats:", s)
            return s
        except Exception as e:
            print("GraphQL stats fetch failed:", e)
    else:
        print("GITHUB_TOKEN 없음 → 공개 REST API로 통계 조회")
    try:
        s = fetch_stats_rest()
        print("stats (REST):", s)
        return s
    except Exception as e:
        print("REST stats fetch failed:", e)
    if os.environ.get("GITHUB_ACTIONS"):
        # Actions 에서는 '-' 로 덮어쓰지 말고 실패로 끝내서 로그로 원인을 확인할 수 있게 한다
        raise SystemExit("통계를 가져오지 못했습니다.")
    return None


def kv2(k1, v1, k2, v2):
    """한 줄에 두 개의 key: value 를 ' | ' 로 나란히 표시 (전체 폭 W 유지)."""
    lw = 31
    rw = W - lw - 2  # kv() 줄과 같은 폭(W+1)
    left = [("t", ". "), ("k", k1), ("t", ":"), ("d", " " + "." * max(lw - len(k1) - len(v1) - 5, 1) + " "), ("v", v1)]
    right = [("k", k2), ("t", ":"), ("d", " " + "." * max(rw - len(k2) - len(v2) - 3, 1) + " "), ("v", v2)]
    return left + [("d", " | ")] + right


def stats_lines(s):
    s = s or {}
    n = lambda k: f"{s[k]:,}" if s.get(k) is not None else "-"
    repos = n("repos")
    if s.get("contributed") is not None:
        repos += f" {{Contributed: {s['contributed']}}}"
    loc = [("t", ". "), ("k", "Lines of Code"), ("t", ": ")]
    if s.get("loc_add") is not None:
        loc += [("v", f"{s['loc_add'] - s['loc_del']:,}"), ("d", " ( "), ("g", f"{s['loc_add']:,}++"),
                ("d", ", "), ("r", f"{s['loc_del']:,}--"), ("d", " )")]
    else:
        loc += [("v", "-")]
    return [
        [],
        sec("GitHub Stats"),
        kv2("Repos", repos, "Stars", n("stars")),
        kv2("Commits", n("commits"), "Followers", n("followers")),
        loc,
    ]


INFO += stats_lines(get_stats())

THEMES = {
    "dark":  dict(bg="#161b22", border="#30363d", t="#c9d1d9", k="#ffa657", v="#a5d6ff", d="#616e7f", h="#79c0ff", art="#c9d1d9", g="#3fb950", r="#f85149"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", t="#24292f", k="#953800", v="#0a3069", d="#c2cfde", h="#0550ae", art="#24292f", g="#1a7f37", r="#cf222e"),
}

LH, CW, FS = 20, 9.6, 16
def build(name, c):
    rows = max(len(ART), len(INFO))
    h = rows * LH + 50
    artw = max(len(l) for l in ART) * CW
    x2 = 25 + artw + 30
    w = int(x2 + W * CW + 45)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="ConsolasFallback,Consolas,\'Courier New\',monospace" font-size="{FS}px">',
           f'<style>.t{{fill:{c["t"]}}}.k{{fill:{c["k"]}}}.v{{fill:{c["v"]}}}.d{{fill:{c["d"]}}}.h{{fill:{c["h"]};font-weight:bold}}.g{{fill:{c["g"]}}}.r{{fill:{c["r"]}}}text,tspan{{white-space:pre}}</style>',
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
    open(f"{name}_mode.svg", "w", encoding="utf-8").write("\n".join(out))

for n, c in THEMES.items(): build(n, c)
