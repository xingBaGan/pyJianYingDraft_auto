from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

semantic_cls = pipeline(Tasks.text_classification, 'damo/nlp_structbert_emotion-classification_chinese-base', model_revision='v1.0.0')
result = semantic_cls(input='新年快乐！')

def get_emotion(text):
    result = semantic_cls(input=text)
    max_score = max(result['scores'])
    max_index = result['scores'].index(max_score)
    return result['labels'][max_index]

print(get_emotion('横竖都是死！'))
