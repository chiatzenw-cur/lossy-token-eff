import pathlib, re, sys, statistics, json
sys.path.insert(0,"scripts")
from openai_harmony import load_harmony_encoding, HarmonyEncodingName
enc=load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
REPO=pathlib.Path("/home/chiatzen/lossy-token-eff")
FINAL=re.compile(r"<\|channel\|>final<\|message\|>")
def tl(s):
    try: return len(enc.encode(s, allowed_special="all"))
    except Exception: return max(1,len(s)//4)
def parse_alpha(name):
    m=re.match(r"alpha(neg)?([0-9.]+)$", name)
    if not m: return None
    v=float(m.group(2))
    return -v if m.group(1) else v

DATASETS=["gsm8k","aime24","humaneval","livecodebench","longbench_v2","mtbench"]
METHODS=["mentored_dec","spec_casc_tok","spec_casc_opt","r_fuzzy","cactus"]

def scan(ds, method, adir):
    d=REPO/"runs"/ds/method/adir
    ana=[];fin=[];nofinal=0
    for cdir in sorted(d.glob("case_*")):
        hit=sorted(cdir.glob("seed_*"))
        if not hit: continue
        op=hit[-1]/"output.txt"
        if not op.is_file(): continue
        txt=op.read_text()
        m=FINAL.search(txt)
        if m: a=tl(txt[:m.start()]); f=tl(txt[m.end():])
        else: a=tl(txt); f=0; nofinal+=1
        ana.append(a); fin.append(f)
    n=len(ana)
    if n==0: return None
    return dict(n=n, ana=statistics.mean(ana), fin=statistics.mean(fin),
               tot=statistics.mean(a+f for a,f in zip(ana,fin)), nofinal=nofinal)

rows=[]
for ds in DATASETS:
    st=scan(ds,"strict","strict")
    if not st: 
        print(f"# {ds}: no strict data"); continue
    maxn=st["n"]
    for method in METHODS:
        mroot=REPO/"runs"/ds/method
        if not mroot.is_dir(): continue
        adirs=[]
        for ad in mroot.iterdir():
            if not ad.is_dir(): continue
            av=parse_alpha(ad.name)
            if av is None: continue
            adirs.append((av, ad.name))
        adirs.sort()
        # keep only points with near-full n
        good=[(av,an,r) for av,an in adirs if (r:=scan(ds,method,an)) and r["n"]>=0.8*maxn]
        if not good: continue
        gentle=good[0]; aggr=good[-1]
        for label,(av,an,r) in (("gentle",gentle),("aggr",aggr)):
            rows.append(dict(ds=ds, method=method, label=label, alpha=av, n=r["n"],
                st_ana=st["ana"], st_fin=st["fin"], st_tot=st["tot"], st_nofinal=st["nofinal"],
                ana=r["ana"], fin=r["fin"], tot=r["tot"], nofinal=r["nofinal"],
                ana_ratio=r["ana"]/st["ana"], fin_ratio=r["fin"]/st["fin"] if st["fin"] else float('nan'),
                tot_ratio=r["tot"]/st["tot"]))

# --- strict reference table ---
print("## Strict (lossless) reference — reasoning vs answer token split\n")
print("| dataset | n | reasoning tok | answer tok | total | reasoning % | runs w/o final ch |")
print("|---|--:|--:|--:|--:|--:|--:|")
seen=set()
for r in rows:
    if r["ds"] in seen: continue
    seen.add(r["ds"])
    print(f"| {r['ds']} | {r['n']} | {r['st_ana']:.0f} | {r['st_fin']:.0f} | {r['st_tot']:.0f} | {100*r['st_ana']/r['st_tot']:.0f}% | {r['st_nofinal']} |")

print("\n## Relaxation inflation — most-aggressive alpha vs strict (ratio)\n")
print("| dataset | method | α | n | reasoning ×strict | answer ×strict | total ×strict | no-final (strict→relaxed) |")
print("|---|---|--:|--:|--:|--:|--:|--:|")
for r in rows:
    if r["label"]!="aggr": continue
    print(f"| {r['ds']} | {r['method']} | {r['alpha']:g} | {r['n']} | {r['ana_ratio']:.2f} | {r['fin_ratio']:.2f} | {r['tot_ratio']:.2f} | {r['st_nofinal']}→{r['nofinal']} |")

print("\n## Gentlest alpha vs strict (ratio) — the accuracy-preserving end\n")
print("| dataset | method | α | n | reasoning ×strict | answer ×strict | total ×strict |")
print("|---|---|--:|--:|--:|--:|--:|")
for r in rows:
    if r["label"]!="gentle": continue
    print(f"| {r['ds']} | {r['method']} | {r['alpha']:g} | {r['n']} | {r['ana_ratio']:.2f} | {r['fin_ratio']:.2f} | {r['tot_ratio']:.2f} |")
