import os, re, glob
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from PyPDF2 import PdfReader


INPUT_FOLDER = r"D:\G-eval\Input"                     #text나 pdf파일로 된 평가할 문서들이 들어있는 폴더 경로 지정
OUTPUT_CSV   = r"D:\G-eval\g_eval_results2.csv"
OUTPUT_PNG   = r"D:\G-eval\g_eval_top10.png"


def read_file(path):
    if path.lower().endswith(".pdf"):
        try:
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"PDF 읽기 실패: {path} ({e})")
            return ""
    # TXT 파일인 경우
    for enc in ('utf-8','cp949','euc-kr','iso-8859-1'):
        try:
            with open(path,'r',encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return open(path,'rb').read().decode('utf-8', errors='ignore')

def split_sents(text):
    text = text.replace('\r',' ')
    return [s.strip() for s in re.split(r'[\.?!]\s+|\n+', text) if s.strip()]

def jaccard(a,b):
    return len(a&b)/len(a|b) if a and b else 0.0

def ngram_div(tokens, n_max=5):
    if not tokens: return 0.0
    ratios=[]
    for n in range(1,n_max+1):
        ngrams=list(zip(*(tokens[i:] for i in range(n))))
        total=len(ngrams)
        ratios.append(len(set(ngrams))/total if total else 0)
    return sum(ratios)/len(ratios)

paths = sorted(glob.glob(os.path.join(INPUT_FOLDER, '*.*')),
               key=lambda x: int(re.search(r'No(\d+)', x).group(1)) if re.search(r'No(\d+)', x) else 0)

if not paths:
    raise FileNotFoundError(f"No files found in {INPUT_FOLDER}")

print(f"총 {len(paths)}개 파일 감지.\n")

rows=[]
for fp in paths:
    txt = read_file(fp)
    toks = re.findall(r'\w+', txt.lower())
    tc, uc = len(toks), len(set(toks))
    novelty = uc/tc if tc else 0
    lexdiv = 0.6*ngram_div(toks)+0.4*(uc/tc if tc else 0)
    sents = split_sents(txt)
    coherence = 0.5 if len(sents)<2 else np.mean([jaccard(set(re.findall(r'\w+',a.lower())),
                                                          set(re.findall(r'\w+',b.lower())))
                                                  for a,b in zip(sents,sents[1:])])
    concept = sum(bool(re.search(p, txt)) for p in [r'모카',r'\b20\s*대|\b2[0-9]\s*세',r'여성|그녀'])/3  # 프롬프트 명령어 키워드 중심으로 입력
    avg_sent_len = tc/len(sents) if sents else 0
    avg_word_len = sum(len(t) for t in toks)/tc if tc else 0
    complexity = (avg_sent_len/40 + avg_word_len/5)/2

    rows.append(dict(file=os.path.basename(fp),
                     novelty_raw=novelty, lexdiv_raw=lexdiv,
                     coherence_raw=coherence, concept_raw=concept,
                     complexity_raw=complexity))

df = pd.DataFrame(rows)

for m in ['novelty','lexdiv','coherence','concept','complexity']:
    p5, p95 = np.percentile(df[f'{m}_raw'], 5), np.percentile(df[f'{m}_raw'], 95)
    def scale(x):
        if x <= p5: return 1
        if x >= p95: return 5
        return round(1 + 4*(x-p5)/(p95-p5))
    df[m] = df[f'{m}_raw'].apply(scale)

df['total'] = df[['novelty','lexdiv','coherence','concept','complexity']].sum(axis=1)
df_sorted = df.sort_values('total', ascending=False).reset_index(drop=True)

# 결과 저장
df_sorted.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"결과 저장 완료: {OUTPUT_CSV}")


plt.figure(figsize=(10,4))
plt.bar(df_sorted.head(10)['file'], df_sorted.head(10)['total'], color='teal')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Total (5-pt)')
plt.title('Top-10 Total Scores – Robust 5-point')
plt.tight_layout()
plt.savefig(OUTPUT_PNG)
print(f"그래프 저장: {OUTPUT_PNG}")
