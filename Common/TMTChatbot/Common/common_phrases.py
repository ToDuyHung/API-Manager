DEFAULT_QUESTION_WORD = "gì"
WHAT_QUESTION_WORDS = ["ai", "nào", "gì"]
WHAT_QUESTION_WORDS = WHAT_QUESTION_WORDS + [item[0].upper() + item[1:] for item in WHAT_QUESTION_WORDS]
WHAT_QUESTION_SUB_WORDS = ["đấy", "ấy", "đó", "vậy"]
WHAT_QUESTION_WORDS = WHAT_QUESTION_WORDS + [f"{main_w} {sub_w}"
                                             for main_w in WHAT_QUESTION_WORDS for sub_w in WHAT_QUESTION_SUB_WORDS]
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
DROP_WORDS = ["", "vậy", "thế", "á"]
DROP_SUB_WORDS = ["ạ", "em", "mày", "mạy", "shop", "ad", "admin", "t", "m", "bạn", "nha", "nhan"]
DROP_WORDS = DROP_WORDS + [f"{main_w} {sub_w}" for main_w in DROP_WORDS for sub_w in DROP_SUB_WORDS]
DROP_WORDS = [item.strip() for item in DROP_WORDS if len(item) > 0]
DROP_WORDS.sort(key=lambda w: len(w), reverse=True)

BELONG_WORDS = ["thuộc"]

ADMINISTRATIVE_WORDS = ["thôn", "xã", "huyện", "tỉnh", "phường", "thành phố"]
ADMINISTRATIVE_WORDS += [item[0].upper() + item[1:] for item in ADMINISTRATIVE_WORDS]

DESCRIBE_WORDS = ["mô tả", "tả", "miêu tả", "thế nào"]

INTENSIVE_WORDS = ["anh", "em", "trai", "gái", "nam", "nữ", "ông", "bà", "cô", "con", "chú", "đỏ", "kem", "vàng", "tím"]

INTENSIVE_WORDS += [item[0].upper() + item[1:] for item in INTENSIVE_WORDS] + [item.upper() for item in INTENSIVE_WORDS]
