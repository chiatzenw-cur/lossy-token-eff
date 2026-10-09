import pathlib, re, json, sys, statistics
sys.path.insert(0,"scripts")
from openai_harmony import load_harmony_encoding, HarmonyEncodingName
enc=load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
REPO=pathlib.Path(__file__).resolve().parents[2]
FINAL=re.compile(r"<\|channel\|>final<\|message\|>")
def tl(s):
    try: return len(enc.encode(s, allowed_special="all"))
    except Exception: return max(1,len(s)//4)
CATS={f"case_{i:03d}":json.load(open(REPO/"prompts"/"mtbench"/f"case_{i:03d}"/"metadata.json"))["category"] for i in range(1,81)}
order=["writing","humanities","stem","roleplay","coding","math","reasoning","extraction"]
def rows_for(method,alpha):
    d=REPO/"runs"/"mtbench"/method/alpha; per={c:[] for c in order}
    for cdir in sorted(d.glob("case_*")):
        hit=sorted(cdir.glob("seed_*"))
        if not hit: continue
        op=hit[-1]/"output.txt"
        if not op.is_file(): continue
        txt=op.read_text(); cat=CATS.get(cdir.name)
        m=FINAL.search(txt); per[cat].append(tl(txt))
    return per
configs=[("strict","strict"),("spec_casc_tok","alpha0.15"),("spec_casc_tok","alpha0.8"),
 ("mentored_dec","alpha0.75"),("cactus","alpha0.35"),("r_fuzzy","alpha0.25"),("spec_casc_opt","alpha0.05")]
base=None
print("| config | " + " | ".join(order) + " | ALL |")
print("|---|" + "--:|"*(len(order)+1))
for m,a in configs:
    per=rows_for(m,a)
    if any(len(per[c])<8 for c in order):  # incomplete
        continue
    means={c:statistics.mean(per[c]) for c in order}
    allv=statistics.mean([x for c in order for x in per[c]])
    if m=="strict":
        base=dict(means,ALL=allv)
        print(f"| **strict (abs tok)** | " + " | ".join(f"{means[c]:.0f}" for c in order) + f" | {allv:.0f} |")
        continue
    print(f"| {m}/{a} | " + " | ".join(f"{means[c]/base[c]:.2f}" for c in order) + f" | {allv/base['ALL']:.2f} |")
# reasoning % per category
print("\n| category | reasoning % (strict) | answer tok (strict) |")
print("|---|--:|--:|")
sp={c:[] for c in order}
d=REPO/"runs"/"mtbench"/"strict"/"strict"
for cdir in sorted(d.glob("case_*")):
    hit=sorted(cdir.glob("seed_*"))
    if not hit: continue
    txt=(hit[-1]/"output.txt").read_text(); cat=CATS.get(cdir.name)
    m=FINAL.search(txt)
    a=tl(txt[:m.start()]) if m else tl(txt); f=tl(txt[m.end():]) if m else 0
    sp[cat].append((a,f))
for c in order:
    a=statistics.mean(x[0] for x in sp[c]); f=statistics.mean(x[1] for x in sp[c])
    print(f"| {c} | {100*a/(a+f):.0f}% | {f:.0f} |")
