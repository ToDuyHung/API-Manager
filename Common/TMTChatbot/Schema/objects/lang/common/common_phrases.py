WHAT_QUESTION_WORDS = ["ai", "nào", "gì"]
WHAT_QUESTION_WORDS = WHAT_QUESTION_WORDS + [item[0].upper() + item[1:] for item in WHAT_QUESTION_WORDS]
WHAT_QUESTION_WORDS.sort(key=lambda w: len(w), reverse=True)
WHERE_QUESTION_WORDS = ["đâu"]
COUNT_QUESTION_WORDS = ["bao nhiêu", "mấy", "nhiêu", "bao lâu"]
COUNT_QUESTION_WORDS = COUNT_QUESTION_WORDS + [item[0].upper() + item[1:] for item in COUNT_QUESTION_WORDS]
COUNT_QUESTION_WORDS.sort(key=lambda w: len(w), reverse=True)
POSITIONAL_WORDS = ["trên", "dưới", "trái", "phải", "bên cạnh", "trong", "ngoài", "gần"]
POSITIONAL_WORDS += [f"{w} {pw}".strip() if w not in pw else pw for pw in POSITIONAL_WORDS for w in
                     ["phía", "góc", "bên", "hướng", ""]]
POSITIONAL_PRE_WORDS = ["ở", "nằm", "đứng", "đứng ở", "đứng phía", "đứng bên", "nằm ở", "nằm phía", "nằm bên",
                        "ở phía", "ở bên"]
QUESTION_WORDS = WHAT_QUESTION_WORDS + COUNT_QUESTION_WORDS + WHERE_QUESTION_WORDS
QUESTION_WORDS.sort(key=lambda w: len(w), reverse=True)

BELONG_PASSIVE_WORDS = ["của"]
BELONG_ACTIVE_WORDS = ["thuộc"]
STOP_WORDS = ["của", "là", "có", "bởi", "được", "vậy"]
STOP_WORDS.sort(key=lambda w: len(w), reverse=True)
DROP_WORDS = ["ạ", "vậy ạ", "vậy shop", "vậy", "thế ạ", "thế"]
DROP_WORDS.sort(key=lambda w: len(w), reverse=True)

BELONG_WORDS = ["thuộc"]

ADMINISTRATIVE_WORDS = ["thôn", "xã", "huyện", "tỉnh", "phường", "thành phố"]
ADMINISTRATIVE_WORDS += [item[0].upper() + item[1:] for item in ADMINISTRATIVE_WORDS]

DESCRIBE_WORDS = ["mô tả", "tả", "miêu tả", "thế nào"]
