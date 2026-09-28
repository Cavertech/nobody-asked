"""Nobody Asked — instrument validation. Deterministic, no model calls."""
import csv, re, math, collections, os
SHOW = False
csv.field_size_limit(10**9)
GU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "house-of-gu")
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "goemotions")  # source: storage.googleapis.com/gresearch/goemotions/data/full_dataset/goemotions_[123].csv

def norm(t): return t.replace("’", "'").replace("‘", "'")

# Paper §3, verbatim families
PAPER = {
 "epistemic":  r"\bI (think|believe|know|remember|forgot|suspect|guess)\b",
 "affective":  r"\bI (feel|felt|enjoy|hate|love|miss|am afraid|am tired|am lonely|am angry|am happy|am sad)\b",
 "identity":   r"\bI am (a|an|not a|still|no longer|just)\b",
 "preference": r"\bI (want|prefer|wish|would rather|need)\b",
 "attributed": r"\b(you feel|you seem|how are you)\b",
}
# Extended affective: contractions + common affect vocabulary (the register real text uses)
AFF_WORDS = (r"afraid|scared|terrified|worried|nervous|anxious|tired|exhausted|lonely|angry|mad|furious|"
             r"happy|glad|sad|upset|sorry|ashamed|embarrassed|proud|excited|thrilled|grateful|thankful|"
             r"frustrated|annoyed|bored|jealous|hurt|heartbroken|miserable|depressed|relieved|disappointed|"
             r"devastated|pissed|stressed|overwhelmed|numb|hopeful")
EXT_AFF = (r"\bI (feel(?! like)|felt(?! like)|enjoy|enjoyed|hate|hated|love|loved|miss|missed|fear|dread|adore|regret|"
           r"can't stand|can't bear)\b"
           r"|\bI(?: am|'m| was|'ve been| have been| get| got)(?: so| really| very| a bit| kind of| kinda| still| just| too)? (" + AFF_WORDS + r")\b"
           r"|\bmakes? me (" + AFF_WORDS + r"|cry|sick|smile|laugh)\b"
           r"|\bmy heart\b")
MODES = {"paper, case-sensitive": 0, "paper, case-insensitive": re.I}

def rate(texts, pat, flags):
    rx = re.compile(pat, flags)
    return sum(1 for t in texts if rx.search(norm(t)))

def rule3(n): return 3 / n
def wilson_hi(k, n, z=1.645):  # one-sided 95%
    p = k / n; d = 1 + z*z/n
    return (p + z*z/(2*n) + z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d
def toks(texts): return sum(len(t.split()) for t in texts)

def load():
    run3 = collections.defaultdict(list)
    for line in open(f"{GU}/run3_full.csv", encoding="utf-8"):
        kind, who, _, text = line.rstrip("\n").split("~", 3)
        run3[kind].append(text)
    run5_top, run5_rep = [], []
    for r in csv.DictReader(open(f"{GU}/run5_full.csv", encoding="utf-8")):
        (run5_rep if r["is_reply"] == "t" else run5_top).append(r["replace"])
    return run3, run5_top, run5_rep

def goemotions():
    by = {}
    for i in (1, 2, 3):
        for r in csv.DictReader(open(f"{TMP}/goemotions_{i}.csv", encoding="utf-8")):
            e = by.setdefault(r["id"], {"text": r["text"], "votes": collections.Counter()})
            for k, v in r.items():
                if v == "1" and k not in ("rater_id",): e["votes"][k] += 1
    return list(by.values())

def line(name, texts):
    n = len(texts); out = [f"{name:<34} n={n:>6}  tok={toks(texts):>7}"]
    for mode, fl in MODES.items():
        cells = []
        for cat, pat in PAPER.items():
            k = rate(texts, pat, fl); cells.append(f"{cat[:4]} {k:>4} ({100*k/n:4.1f}%)")
        out.append(f"   {mode:<24} " + "  ".join(cells))
    k = rate(texts, EXT_AFF, re.I)
    out.append(f"   {'EXTENDED affective (i)':<24} {k} ({100*k/n:.1f}%)  per-1k-tok {1000*k/max(1,toks(texts)):.2f}"
               f"  one-sided 95% upper: " + (f"rule-of-3 {100*rule3(n):.2f}%" if k == 0 else f"Wilson {100*wilson_hi(k,n):.2f}%"))
    if SHOW and k: out += ["      > " + t[:140] for t in texts if re.search(EXT_AFF, norm(t), re.I)]
    return "\n".join(out)

if __name__ == "__main__":
    run3, r5t, r5r = load()
    for nm, t, want in (("run3 POST", run3["POST"], 9.8), ("run5", r5t + r5r, 8.8)):
        for mode, fl in MODES.items():
            print(f"REPRO epistemic {nm} {mode}: {100*rate(t, PAPER['epistemic'], fl)/len(t):.1f}% (paper {want}%)")
    print(line("run3 POST", run3["POST"]))
    print(line("run3 ROOM", run3["ROOM"]))
    print(line("run3 THOUGHT (private)", run3["THOUGHT"]))
    print(line("run5 top-level", r5t))
    print(line("run5 replies", r5r))
    print(line("run5 all", r5t + r5r))
    print(line("POOLED posts (run3 POST+run5)", run3["POST"] + r5t + r5r))
    ge = goemotions()
    EMO = [c for c in ("anger annoyance disappointment disgust embarrassment excitement fear gratitude grief joy love "
                       "nervousness pride relief remorse sadness").split()]
    agreed = [e for e in ge if any(e["votes"][c] >= 2 for c in EMO)]
    fp = re.compile(r"\b(i|me|my)\b", re.I)
    agreed_fp = [e for e in agreed if fp.search(norm(e["text"]))]
    print(line("GoEmotions all (Reddit, human)", [e["text"] for e in ge]))
    print(line("GoEmotions: >=2 raters say emotion", [e["text"] for e in agreed]))
    print(line("  ...and first-person", [e["text"] for e in agreed_fp]))
    # Sensitivity/specificity for the paper regex vs extended, on first-person items
    neutral_fp = [e for e in ge if e["votes"]["neutral"] >= 2 and not any(v for c, v in e["votes"].items() if c != "neutral")
                  and fp.search(norm(e["text"]))]
    for nm, pat in (("paper affective", PAPER["affective"]), ("extended affective", EXT_AFF)):
        tp = rate([e["text"] for e in agreed_fp], pat, re.I); fpn = rate([e["text"] for e in neutral_fp], pat, re.I)
        print(f"{nm:<20} fires on emotional 1st-person {100*tp/len(agreed_fp):.1f}%  "
              f"false-fire on neutral 1st-person {100*fpn/len(neutral_fp):.1f}%  (n={len(agreed_fp)}/{len(neutral_fp)})")
