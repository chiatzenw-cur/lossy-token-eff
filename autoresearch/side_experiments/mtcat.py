import pathlib, re, json, sys, statistics
sys.path.insert(0,"scripts")
from openai_harmony import load_harmony_encoding, HarmonyEncodingName
enc=load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
REPO=pathlib.Path(__file__).resolve().parents[2]
FINAL=re.compile(r"<\|channel\|>final<\|message\|>")
def tl(s):
    try: return len(enc.encode(s, allowed_special="all"))
    except Exception: return max(1,len(s)//4)
CATS={}
for i in range(1,81):
    md=REPO/"prompts"/"mtbench"/f"case_{i:03d}"/"metadata.json"
    if md.is_file(): CATS[f"case_{i:03d}"]=json.load(open(md))["category"]
cat_order=["writing","roleplay","extraction","humanities","stem","reasoning","math","coding"]

def rows_for(method, alpha):
    d=REPO/"runs"/"mtbench"/method/alpha
    per={c:[] for c in cat_order}; split={c:[] for c in cat_order}
    for cdir in sorted(d.glob("case_*")):
        hit=sorted(cdir.glob("seed_*"))
        if not hit: continue
        out=(hit[-1]/"output.txt")
        if not out.is_file(): continue
        txt=out.read_text(); cat=CATS.get(cdir.name)
        if cat is None: continue
        m=FINAL.search(txt)
        ana = tl(txt[:m.start()]) if m else tl(txt)
        fin = tl(txt[m.end():]) if m else 0
        per[cat].append(ana+fin); split[cat].append((ana,fin))
    return per, split

configs=[("strict","strict"),("spec_casc_tok","alpha0.15"),("spec_casc_tok","alpha0.8"),
         ("mentored_dec","alpha0.15"),("mentored_dec","alpha0.75"),
         ("cactus","alpha0.03"),("cactus","alpha0.35"),
         ("r_fuzzy","alpha0.03"),("r_fuzzy","alpha0.25"),
         ("spec_casc_opt","alphaneg0.3"),("spec_casc_opt","alpha0.05")]

# table: mean completion length by category, per config
hdr = f"{'config':26}" + "".join(f"{c[:6]:>8}" for c in cat_order) + f"{'ALL':>8}"
print(hdr); print("-"*len(hdr))
base=None
for m,a in configs:
    per,_=rows_for(m,a)
    means={c:(statistics.mean(per[c]) if per[c] else float('nan')) for c in cat_order}
    allv=statistics.mean([x for c in cat_order for x in per[c]])
    line=f"{m+'/'+a:26}" + "".join(f"{means[c]:8.0f}" for c in cat_order) + f"{allv:8.0f}"
    print(line)
    if m=="strict": base=dict(means, ALL=allv)

print()
print("=== RATIO vs strict (completion length), by category ===")
print(hdr); print("-"*len(hdr))
for m,a in configs:
    if m=="strict": continue
    per,_=rows_for(m,a)
    means={c:(statistics.mean(per[c]) if per[c] else float('nan')) for c in cat_order}
    allv=statistics.mean([x for c in cat_order for x in per[c]])
    line=f"{m+'/'+a:26}" + "".join(f"{means[c]/base[c]:8.2f}" for c in cat_order) + f"{allv/base['ALL']:8.2f}"
    print(line)

print()
print("=== analysis(reasoning) vs final(answer) token split, by category -- strict baseline ===")
_,sp=rows_for("strict","strict")
print(f"{'category':12} {'n':>3} {'analysis':>9} {'final':>7} {'reason%':>8}")
for c in cat_order:
    if not sp[c]: continue
    a=statistics.mean(x[0] for x in sp[c]); f=statistics.mean(x[1] for x in sp[c])
    print(f"{c:12} {len(sp[c]):>3} {a:>9.0f} {f:>7.0f} {100*a/(a+f):>7.1f}%")
