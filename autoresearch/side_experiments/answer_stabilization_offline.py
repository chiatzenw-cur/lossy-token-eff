import sys, pathlib, re, json
sys.path.insert(0,"scripts")
from grade_aime import grade
REPO=pathlib.Path("/home/chiatzen/lossy-token-eff")
pr=REPO/"prompts"/"aime24"
md=REPO/"autoresearch"/"runs"/"aime24"/"spec_casc_tok"
from openai_harmony import load_harmony_encoding, HarmonyEncodingName
enc=load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)

print(f"{'case':9} {'verd':9} {'ans':>5} {'Ltot':>7} {'Lanalysis':>9} {'last_diff_int_pos':>16} {'saveable':>9} {'save%':>6}")
print("-"*80)
tot_save=tot_len=0; tot_save_correct=tot_len_correct=0
for i in range(1,31):
    c=f"case_{i:03d}"
    hits=sorted(md.glob(f"*/{c}/seed_*"))
    if not hits: continue
    d=hits[-1]
    r=grade(d,pr)
    out=(d/"output.txt").read_text()
    ans=str(r.get("answer"))
    verd=r.get("verdict"); Ltot=r.get("output_tokens") or 0
    # split analysis vs final: find the '<|channel|>final<|message|>' marker in text
    mfin=re.search(r"<\|channel\|>final<\|message\|>", out)
    analysis = out[:mfin.start()] if mfin else out
    # token length of analysis portion (approx via harmony encode of the text)
    try: Lan=len(enc.encode(analysis, allowed_special="all"))
    except Exception: Lan=len(analysis)//4
    # find all standalone integers (0-999, AIME range) with char positions
    ints=[(m.start(), m.group()) for m in re.finditer(r"(?<![\d.])\d{1,3}(?![\d.])", analysis)]
    # last position where an integer DIFFERENT from the final answer appears
    last_diff = 0
    for pos,val in ints:
        if val != ans:
            last_diff = pos
    # convert char pos -> approx token pos (proportional)
    frac = last_diff/max(len(analysis),1)
    last_diff_tok = int(frac*Lan)
    saveable = max(0, Lan - last_diff_tok)   # tokens after the last competing integer
    pct = 100*saveable/max(Ltot,1)
    print(f"{c:9} {verd:9} {ans:>5} {Ltot:>7} {Lan:>9} {last_diff_tok:>16} {saveable:>9} {pct:>5.1f}%")
    tot_save+=saveable; tot_len+=Ltot
    if verd=="correct": tot_save_correct+=saveable; tot_len_correct+=Ltot
print("-"*80)
print(f"ALL 30:      potential tokens saved {tot_save}/{tot_len} = {100*tot_save/tot_len:.1f}% of total output")
print(f"CORRECT only: potential tokens saved {tot_save_correct}/{tot_len_correct} = {100*tot_save_correct/tot_len_correct:.1f}%")
print("\nNOTE: 'saveable' = tokens generated AFTER the last time a competing (different) integer")
print("was mentioned in the analysis channel. Optimistic upper bound on an oracle early-exit that")
print("commits the final answer as soon as it stops being contested. Char->token pos is linear-approx.")
