import pathlib, re, json, sys, statistics
sys.path.insert(0,"scripts")
from grade_aime import grade
from openai_harmony import load_harmony_encoding, HarmonyEncodingName
enc=load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
REPO=pathlib.Path("/home/chiatzen/lossy-token-eff")
pr=REPO/"prompts"/"aime24"
FINAL=re.compile(r"<\|channel\|>final<\|message\|>")
def toklen(s):
    try: return len(enc.encode(s, allowed_special="all"))
    except Exception: return max(1,len(s)//4)
print(f"{'method/alpha':22} {'n':>3} {'total':>8} {'analysis':>9} {'final':>7} {'final%':>7} {'acc':>6} {'#no_final':>9}")
print("-"*82)
root=REPO/"runs"/"aime24"
for mdir in sorted(root.iterdir()):
    if not mdir.is_dir(): continue
    for adir in sorted(mdir.iterdir()):
        if not adir.is_dir(): continue
        tot=[];ana=[];fin=[];ncorr=0;n=0;nofinal=0
        for cdir in sorted(adir.glob("case_*")):
            hit=sorted(cdir.glob("seed_*"))
            if not hit: continue
            d=hit[-1]
            op=d/"output.txt"
            if not op.is_file(): continue
            out=op.read_text()
            n+=1
            m=FINAL.search(out)
            if m:
                a=toklen(out[:m.start()]); f=toklen(out[m.end():])
            else:
                a=toklen(out); f=0; nofinal+=1
            ana.append(a); fin.append(f); tot.append(a+f)
            try:
                r=grade(d,pr)
                if r.get("verdict")=="correct": ncorr+=1
            except Exception: pass
        if not tot: continue
        mt=statistics.mean(tot); ma=statistics.mean(ana); mf=statistics.mean(fin)
        print(f"{mdir.name+'/'+adir.name:22} {n:>3} {mt:>8.0f} {ma:>9.0f} {mf:>7.0f} {100*mf/mt:>6.1f}% {ncorr}/{n:<4} {nofinal:>9}")
