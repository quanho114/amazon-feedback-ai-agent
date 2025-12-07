# 🎯 Sentiment Analysis Benchmark

## Mục đích
So sánh 4 models để chọn model tốt nhất cho sentiment analysis:
1. **Logistic Regression** (ML classical)
2. **Linear SVM** (ML classical)
3. **RoBERTa** (Deep Learning)
4. **VADER** (Rule-based)

## Cách chạy

### 1. Cài dependencies
```bash
pip install vaderSentiment scikit-learn transformers torch
```

### 2. Chạy benchmark
```bash
python scripts/run_benchmark.py
```

## Tiêu chí đánh giá

### Metrics
- **Accuracy**: Độ chính xác tổng thể
- **F1 Score**: Cân bằng giữa precision và recall
- **Speed**: Thời gian xử lý (ms/review)

### Weighted Score
```
Total Score = 50% Accuracy + 30% F1 + 20% Speed
```

## Kết quả dự kiến

| Model | Accuracy | F1 Score | Speed (ms) | Pros | Cons |
|-------|----------|----------|------------|------|------|
| **Logistic** | ~85-88% | ~0.85 | 0.5-2ms | Fast, simple, interpretable | Need training data |
| **SVM** | ~86-89% | ~0.86 | 1-3ms | High accuracy, robust | Slower than Logistic |
| **RoBERTa** | ~92-95% | ~0.93 | 100-500ms | Best accuracy | Very slow, GPU needed |
| **VADER** | ~78-82% | ~0.78 | 0.1-0.5ms | Ultra fast, no training | Lower accuracy |

## Recommendation

### Cho Production (Real-time)
- **VADER** nếu cần speed tối đa
- **Logistic/SVM** nếu cần balance speed + accuracy

### Cho Batch Processing
- **RoBERTa** nếu cần accuracy cao nhất
- **SVM** nếu cần balance tốt

### Cho Project này
Recommend: **Linear SVM** hoặc **Logistic Regression**
- Accuracy đủ tốt (~87%)
- Speed nhanh (~1-2ms)
- Dễ deploy, không cần GPU
- Có thể train trên data riêng

## Implementation

Sau khi chọn model, integrate vào `sentiment_node.py`:

```python
# Load trained model
import joblib
model = joblib.load('models/sentiment_svm.pkl')
vectorizer = joblib.load('models/tfidf_vectorizer.pkl')

# Predict
def predict_sentiment(text):
    text_vec = vectorizer.transform([text])
    prediction = model.predict(text_vec)[0]
    return prediction  # 'positive', 'negative', 'neutral'
```

## Notes

- RoBERTa được sample (500 reviews) vì quá chậm
- Ground truth labels từ Rating: 1-2★ = negative, 3★ = neutral, 4-5★ = positive
- Models được train trên 80% data, test trên 20%
- VADER không cần training, chạy trực tiếp

## Next Steps

1. ✅ Chạy benchmark
2. ⏳ Pick best model
3. ⏳ Save trained model
4. ⏳ Integrate vào `sentiment_node.py`
5. ⏳ Update API
6. ⏳ Test performance
