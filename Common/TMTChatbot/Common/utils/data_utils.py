import re
from datetime import datetime
from nltk import ngrams
from string import punctuation

from TMTChatbot.Schema.common.data_types import DataType

img_re = re.compile("|".join([".jpg", ".JPG", ".png", ".PNG", ".svg", ".SVG"]))

SRC_ACCENT = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗ' \
             u'ỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
DST_ACCENT = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOo' \
             u'OoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'


def remove_accents(input_str):
    s = ''
    input_str.encode('utf-8')
    for c in input_str:
        if c in SRC_ACCENT:
            s += DST_ACCENT[SRC_ACCENT.index(c)]
        else:
            s += c
    return s


def normalize_text(text, keep_punctuation: bool = True, keep_accents: bool = False):
    text = text.lower()
    for p in punctuation:
        if keep_punctuation:
            text = text.replace(p, f" {p} ")
        else:
            text = text.replace(p, " ")
    if not keep_accents:
        text = remove_accents(text)
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


def check_data_decorator(func):
    def wrapper(value):
        try:
            value, data_type = func(value)
            return value, data_type
        except:
            return value, DataType.NORMAL

    return wrapper


@check_data_decorator
def check_dict(value):
    if isinstance(value, dict):
        return value, DataType.DICT
    return value, DataType.NORMAL


@check_data_decorator
def check_datetime(value):
    if "T" in value:
        time_string = value.replace("+", "")
        year, month, day = [int(item) for item in time_string.split("T")[0].split("-")]
        hour, minute, second = [int(item) for item in time_string.split("T")[1].replace("Z", "").split(":")]
        if day == 0:
            day = 1
        if month == 0:
            month = 1
        value_ = datetime(year=int(year), month=int(month), day=int(day), hour=int(hour), minute=int(minute),
                          second=int(second))
        return value_, DataType.DATETIME
    else:
        return value, DataType.NORMAL


@check_data_decorator
def check_image(value):
    if len(img_re.findall(value)) > 0:
        return value, DataType.IMAGE_URL
    return value, DataType.NORMAL


@check_data_decorator
def check_number(value):
    if int(value) == float(value):
        number, d_type = int(value), DataType.INT
    else:
        number, d_type = float(value), DataType.FLOAT
    if number is not None:
        if d_type == DataType.INT and str(number) != value:
            return value, DataType.NORMAL
        else:
            return number, d_type
    return value, DataType.NORMAL


def check_data_type(value):
    for func in [check_number, check_datetime, check_image, check_dict]:
        value, data_type = func(value)
        if data_type != DataType.NORMAL:
            return value, data_type
    return value, DataType.NORMAL


def jaccard_distance(a, b, return_num=False, re_scoring_terms=None):
    if re_scoring_terms is None:
        re_scoring_terms = {}

    def calculate_total_score(candidate_set):
        return sum(1 - re_scoring_terms.get(item, 0) for item in candidate_set)

    nominator = a.intersection(b)
    if return_num:
        return calculate_total_score(nominator)
    else:
        denominator = a.union(b)
        similarity = calculate_total_score(nominator) / calculate_total_score(denominator)
        return similarity


def text_ngram(text, n, c_mode=True, keep_punctuation=True):
    output = set()
    text = normalize_text(text, keep_punctuation=keep_punctuation)
    if c_mode:
        for n_gram in range(n):
            output = output.union(set(ngrams(text.lower(), n_gram + 1)))
    else:
        for n_gram in range(n):
            output = output.union(set(ngrams(text.lower().split(), n_gram + 1)))
    return output
