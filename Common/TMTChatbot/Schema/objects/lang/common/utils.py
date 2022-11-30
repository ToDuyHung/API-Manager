import re
from string import punctuation

from nltk import ngrams

from TMTChatbot.Schema.objects.lang.common.common_phrases import (
    QUESTION_WORDS,
    BELONG_PASSIVE_WORDS,
    STOP_WORDS,
    BELONG_ACTIVE_WORDS,
    DROP_WORDS
)

question_words = [w for w in QUESTION_WORDS]
question_words.sort(key=lambda w: len(w), reverse=True)
question_words = [f" {w.replace(' ', '_')} " for w in question_words] + [f" {w} " for w in question_words]
q_re = re.compile("|".join(question_words))
img_re = re.compile("|".join([".jpg", ".JPG", ".png", ".PNG", ".svg", ".SVG"]))

SRC_ACCENT = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗ' \
             u'ỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
DST_ACCENT = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOo' \
             u'OoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'


def replace_question_mask(text, mask):
    # print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {text}||ƠƠƠƠƠƠ|||{mask}")
    text = f" {text} ".replace("_", " ")
    words = list(q_re.findall(text))
    if len(words) > 0:
        return text.replace(words[0], f" {mask} ").strip()
    return mask


def check_question_word(text):
    text = f" {text} ".replace("_", " ")
    output = len(list(q_re.findall(text))) > 0
    return output


def check_active_noun(text):
    return text.strip() not in BELONG_PASSIVE_WORDS


def check_belong_active_phrase(text):
    return text.strip() in BELONG_ACTIVE_WORDS


def check_belong_passive_phrase(text):
    return text.strip() in BELONG_PASSIVE_WORDS


def jaccard_distance(a, b, return_num=False):
    nominator = a.intersection(b)
    if return_num:
        return len(nominator)
    else:
        denominator = a.union(b)
        similarity = len(nominator) / len(denominator)
        return similarity


def text_ngram(text, n, c_mode=True):
    output = set()
    if c_mode:
        for n_gram in range(n):
            output = output.union(set(ngrams(text.lower(), n_gram + 1)))
    else:
        for n_gram in range(n):
            output = output.union(set(ngrams(text.lower().split(), n_gram + 1)))
    return output


def question_preprocess(text):
    for c in "?!":
        text = text.replace(c, " ")
    for p in punctuation:
        text = text.replace(p, f" {p} ")
    text = f" {text} "
    for drop_word in DROP_WORDS:
        text = text.replace(f" {drop_word} ", " ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


def drop_question_word(text):
    text = f" {text} "
    for word in QUESTION_WORDS:
        text = text.replace(f" là {word} ", " ").replace(f" {word} ", " ")
    return text.strip()


def drop_stop_words(text):
    text = f" {text} "
    for stop_word in STOP_WORDS:
        text = text.replace(f" {stop_word} ", " ")
    text = " ".join(text.split()).strip()
    return text


def remove_accents(input_str):
    s = ''
    input_str.encode('utf-8')
    for c in input_str:
        if c in SRC_ACCENT:
            s += DST_ACCENT[SRC_ACCENT.index(c)]
        else:
            s += c
    return s
