import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import platform

# ✅ 한글 깨짐 방지
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# ✅ CSV 불러오기
df = pd.read_csv("saramin_developer_jobs_all.csv")

# ✅ 키워드 추출
all_keywords = []
for sectors in df['sectors'].dropna():
    for keyword in str(sectors).split(","):
        clean_keyword = keyword.strip()
        if clean_keyword and clean_keyword != "외":
            all_keywords.append(clean_keyword)

# ✅ 빈도 분석 및 시각화
keyword_counts = Counter(all_keywords)
labels, values = zip(*keyword_counts.most_common(15))

plt.figure(figsize=(10, 6))
plt.barh(labels[::-1], values[::-1])
plt.title("사람인 개발자 공고 - 직무 키워드 Top 15")
plt.xlabel("공고 수")
plt.tight_layout()
plt.show()
