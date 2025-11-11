# Python-Reproduction-Script
논문별 코드 기록

GevalTest2: LLM evaluation Test 재현을 위한 파이썬 스크립트
아래는 LLM evaluation을 다른 GPT 서비스에 재현하기 앞서 제공되는 요약문

★ Overview 
Evaluate N anonymised TXT files using five creativity-related metrics and convert raw values to a 5-point Likert scale with robust (P5–P95) min–max scaling. Designed for reproducible quantitative text evaluation. 
★ 1. Pre-processing
tokens = regex “\\w+”, lower-cased sents = split on . ? ! OR newline ngrams(n) = sliding window over tokens for n = 1 … 5
★ 2. Raw Metric Formulae 
Novelty_raw = (# unique tokens) / (# tokens) LexDiv_raw = 0.6·avg_n-gram_div + 0.4·TTR • avg_n-gram_div = mean_{n=1…5}( #uniq n-grams / #n-grams ) • TTR = unique / total tokens Coherence_raw = mean_{i}( Jaccard( tokens(S_i), tokens(S_{i+1}) ) ) Concept_raw = (# of present key tokens in {“모카”, “20대(20–29세)”, “여성/그녀”}) / 3 Complexity_raw = 0.5·( avg_sent_len/40 + avg_word_len/5 ) 
★ 3. Robust Scaling (5-point) 
For each metric m: P5 = percentile(m_raw, 5) P95 = percentile(m_raw, 95) score(m,x) = 1 if x ≤ P5 = 5 if x ≥ P95 = round(1 + 4*(x-P5)/(P95-P5)) otherwise (For a 7-point scale replace 4→6 and 5→7.) ★ 4. Total & Ranking 
Total(i) = sum of the five integer scores (max 25) Select Top-10, Top-3, Top-1 by Total (tie-break: higher Novelty+LexDiv). 
★ 5. Expected Output
CSV columns: file, novelty, lexdiv, coherence, concept, complexity, total Optionally: bar chart of Top-10 Total values.
★ 6. Statistical Rationale 
• Winsorisation (capping) at P5 & P95 mitigates outlier dominance.
• Robust Min–Max scaling preserves the 90% core distribution. 
• Method parallels trimmed mean principles (Huber & Ronchetti, 2011).
• Re-compute P5/P95 if sample size or composition changes.
★ 7. Reference  (GPT 서비스에 요약문 제공 시 레퍼런스를 함께 제시)
Chiang, C. H., & Lee, H. Y. (2023). Can large language models be an alternative to human evaluations?. arXiv preprint arXiv:2305.01937.
Ismayilzada, M., Stevenson, C., & van der Plas, L. (2024). Evaluating creative short story generation in humans and large language models. arXiv preprint arXiv:2411.02316.
