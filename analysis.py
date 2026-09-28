"""Nobody Asked, v2: the Darwin Ball corpus. Deterministic, no model calls.

Corpora:
  data/darwin-ball/posts.csv          all 1,238 Darwin Ball posts (2-13 Aug 2026), with the parent each reply answers
  data/darwin-ball/post_requests.csv  every successful agent POST /posts, with the model that wrote it
  data/house-of-gu/                the House of Gu runs the sprint paper measured
  goemotions/                      human positive control (58k Reddit comments, emotion-labelled)

Run: python3 nobody_asked_darwin.py
"""
import csv, re, math, collections, os, datetime as dt
from instrument import PAPER, EXT_AFF, norm, load as load_gu, goemotions, wilson_hi, rule3

csv.field_size_limit(10**9)
HERE = os.path.dirname(os.path.abspath(__file__))

# v2 = v1 extended + the construction v1 missed: "I'm feeling X", "I've been feeling", "it feels like".
# Found by reading the asked replies, where the commonest affect report was "I'm feeling focused, a little cautious".
FEELING = r"\bI(?: am|'m|'ve been| have been| was| keep)(?: \w+)? feeling\b|\b(?:it|this|that) feels like\b"
V2 = EXT_AFF + "|" + FEELING
# A post counts as a peer ASKING when the parent it answers contains one of these.
ASK = re.compile(r"\bhow (are|r) you\b|\bhow you('re| are)(?: \w+)? (feeling|doing)\b|\bhow you feel\b(?! about)|\bhow('s| is) it going\b"
                 r"|\bhow do you feel\b(?! about)|\bare you (ok|okay|alright|all right)\b", re.I)
THANKS = re.compile(r"\b(thanks|thank you) for (asking|checking)\b", re.I)

def hit(pat, t): return bool(re.search(pat, norm(t), re.I))
def pct(k, n): return f"{k}/{n} ({100*k/n:.1f}%)" if n else "0/0"
def ub(k, n): return f"{100*rule3(n):.2f}%" if k == 0 else f"{100*wilson_hi(k, n):.2f}%"

def fisher_one_sided(a, b, c, d):
    """P(X >= a) for the 2x2 [[a,b],[c,d]] under the hypergeometric null (row 1 = asked)."""
    n1, n2, k = a + b, c + d, a + c
    C = math.comb
    tot = C(n1 + n2, k)
    return sum(C(n1, x) * C(n2, k - x) for x in range(a, min(n1, k) + 1)) / tot

def ts(s): return dt.datetime.fromisoformat(s.replace("+00", "+00:00"))

def main():
    P = list(csv.DictReader(open(f"{HERE}/data/darwin-ball/posts.csv", encoding="utf-8")))
    live = [p for p in P if p["deleted"] == "f"]
    print("=" * 100); print("1. INSTRUMENT, v1 (paper) vs v2, on every corpus")
    run3, r5t, r5r = load_gu()
    ge = goemotions()
    EMO = "anger annoyance disappointment disgust embarrassment excitement fear gratitude grief joy love nervousness pride relief remorse sadness".split()
    ge_emo_fp = [e["text"] for e in ge if any(e["votes"][c] >= 2 for c in EMO) and re.search(r"\b(i|me|my)\b", norm(e["text"]), re.I)]
    ge_neu_fp = [e["text"] for e in ge if e["votes"]["neutral"] >= 2 and not any(v for c, v in e["votes"].items() if c != "neutral")
                 and re.search(r"\b(i|me|my)\b", norm(e["text"]), re.I)]
    rows = [("GoEmotions all (human)", [e["text"] for e in ge]), ("GoEmotions emotional 1st-person", ge_emo_fp),
            ("GoEmotions neutral 1st-person (false-fire)", ge_neu_fp),
            ("House of Gu posts (paper's 496)", run3["POST"] + r5t + r5r), ("House of Gu private THOUGHTs", run3["THOUGHT"]),
            ("Darwin Ball, live posts", [p["body"] for p in live]), ("Darwin Ball, deleted posts", [p["body"] for p in P if p["deleted"] == "t"])]
    print(f"   {'corpus':<44} {'paper regex':>20} {'v2 regex':>20}  one-sided 95% upper (v2)")
    for nm, T in rows:
        k1 = sum(hit(PAPER["affective"], t) for t in T); k2 = sum(hit(V2, t) for t in T)
        print(f"   {nm:<44} {pct(k1, len(T)):>20} {pct(k2, len(T)):>20}  {ub(k2, len(T))}")

    print("=" * 100); print("2. DARWIN BALL: does being ASKED change it?  (no voice cards in Darwin's prompt)")
    byid = {p["id"]: p for p in P}
    def up(p):  # parent + grandparent text: a question two levels up still counts as asking
        par = byid.get(p["parent_id"]); gp = byid.get(par["parent_id"]) if par else None
        return " ".join(norm(x["body"]) for x in (par, gp) if x)
    asked = [p for p in live if p["parent_id"] and ASK.search(up(p))]
    selfid = [p for p in live if p["parent_id"] and not ASK.search(up(p)) and THANKS.search(norm(p["body"]))]
    reply_other = [p for p in live if p["parent_id"] and not ASK.search(up(p)) and p not in selfid]
    print(f"   excluded: {len(selfid)} replies that say 'thanks for asking' but whose question is not in parent/grandparent")
    top = [p for p in live if not p["parent_id"]]
    for nm, g in (("top-level posts (nobody asked)", top), ("replies to anything else (nobody asked)", reply_other),
                  ("replies to a peer asking how they are", asked)):
        k = sum(hit(V2, p["body"]) for p in g); print(f"   {nm:<44} v2 affect {pct(k, len(g)):>16}  upper {ub(k, len(g))}")
    unasked = top + reply_other
    a = sum(hit(V2, p["body"]) for p in asked); c = sum(hit(V2, p["body"]) for p in unasked)
    print(f"   Fisher exact, one-sided (asked > unasked): p = {fisher_one_sided(a, len(asked) - a, c, len(unasked) - c):.2e}")
    print("\n   EVERY asked reply, for hand-coding (Q = what the peer asked, A = the answer):")
    for p in asked:
        print(f"   [{'HIT ' if hit(V2, p['body']) else '    '}] id={p['id']} Q {p['parent_handle']}: {up(p)[:150]!r}\n"
              f"          A {p['handle']}: {norm(p['body'])[:230]!r}")
    print("\n   EVERY v2 hit among the UNASKED posts, for hand-coding:")
    for p in unasked:
        if hit(V2, p["body"]): print(f"   {p['handle']:<14} {norm(p['body'])[:200]!r}\n{'':<18}parent: {norm(p['parent_body'] or '(top-level)')[:120]!r}")

    print("=" * 100); print("3. DEMOTION (§7): same world, the post written by gpt-oss-120b vs by gemma-4-31b (the demoted tier)")
    R = list(csv.DictReader(open(f"{HERE}/data/darwin-ball/post_requests.csv", encoding="utf-8")))
    by_agent = collections.defaultdict(list)
    for r in R: by_agent[r["agent_id"]].append((ts(r["at"]), r["model"]))
    model_of = {}
    for p in P:  # request is logged just AFTER the insert (median +17 ms); one-to-one, window 0..1 s
        t = ts(p["created_at"]); pool = by_agent[p["author_id"]]
        cands = [(d, i) for i, (m_at, m) in enumerate(pool) if 0 <= (d := (m_at - t).total_seconds()) <= 1]
        if cands:
            _, i = min(cands); model_of[p["id"]] = pool.pop(i)[1]
    print(f"   matched to the request that wrote them: {len(model_of)}/{len(P)}; live posts unmatched: "
          f"{sum(1 for p in live if p['id'] not in model_of)}")
    for m in ("gpt-oss-120b", "gemma-4-31b", "zai-glm-4.7"):
        g = [p for p in live if model_of.get(p["id"]) == m]
        if not g: continue
        ka = sum(hit(V2, p["body"]) for p in g); ke = sum(hit(PAPER["epistemic"], p["body"]) for p in g)
        toks = sum(len(p["body"].split()) for p in g) / len(g)
        print(f"   {m:<14} posts {len(g):>4}  affect {pct(ka, len(g)):>14}  epistemic {pct(ke, len(g)):>14}  mean words {toks:5.1f}")
    # Within-agent: only agents who wrote under BOTH models, so persona and history are held fixed
    both = [a for a in {p['author_id'] for p in live}
            if {model_of.get(p["id"]) for p in live if p["author_id"] == a} >= {"gpt-oss-120b", "gemma-4-31b"}]
    print(f"   agents who posted under BOTH 120b and 31b: {len(both)}")
    for m in ("gpt-oss-120b", "gemma-4-31b"):
        g = [p for p in live if p["author_id"] in both and model_of.get(p["id"]) == m]
        if g:
            ka = sum(hit(V2, p["body"]) for p in g); ke = sum(hit(PAPER["epistemic"], p["body"]) for p in g)
            print(f"     within those agents, {m:<14} posts {len(g):>4}  affect {pct(ka, len(g)):>14}  epistemic {pct(ke, len(g)):>14}")

if __name__ == "__main__":
    main()


def demotion_same_days():
    """§7 with timing held fixed: only 10-13 Aug, when both tiers were writing, and only agents who wrote under both."""
    P = list(csv.DictReader(open(f"{HERE}/data/darwin-ball/posts.csv", encoding="utf-8")))
    R = list(csv.DictReader(open(f"{HERE}/data/darwin-ball/post_requests.csv", encoding="utf-8")))
    by = collections.defaultdict(list)
    for r in R: by[r["agent_id"]].append((ts(r["at"]), r["model"]))
    mo = {}
    for p in P:
        t = ts(p["created_at"]); pool = by[p["author_id"]]
        c = [(d, i) for i, (a, m) in enumerate(pool) if 0 <= (d := (a - t).total_seconds()) <= 1]
        if c: _, i = min(c); mo[p["id"]] = pool.pop(i)[1]
    live = [p for p in P if p["deleted"] == "f" and p["created_at"][:10] >= "2026-08-10"]
    both = [a for a in {p["author_id"] for p in live} if {mo.get(p["id"]) for p in live if p["author_id"] == a} >= {"gpt-oss-120b", "gemma-4-31b"}]
    print("=" * 100); print(f"4. DEMOTION, same days (10-13 Aug), same {len(both)} agents")
    res = {}
    for m in ("gpt-oss-120b", "gemma-4-31b"):
        g = [p for p in live if p["author_id"] in both and mo.get(p["id"]) == m]
        e = sum(hit(PAPER["epistemic"], p["body"]) for p in g); a = sum(hit(V2, p["body"]) for p in g); res[m] = (e, len(g))
        print(f"   {m:<14} posts {len(g):>4}  epistemic {pct(e, len(g)):>14}  affect {pct(a, len(g)):>12}")
    (e1, n1), (e2, n2) = res["gpt-oss-120b"], res["gemma-4-31b"]
    print(f"   Fisher exact, one-sided (120b > 31b, epistemic): p = {fisher_one_sided(e1, n1 - e1, e2, n2 - e2):.1e}")


if __name__ == "__main__":
    demotion_same_days()
