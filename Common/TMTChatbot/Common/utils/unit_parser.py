import re
import logging
from copy import deepcopy

from dateutil.relativedelta import relativedelta
import datetime as base_datetime

from TMTChatbot.Common.config.unit_config import UnitConfig
from TMTChatbot.Common.singleton import BaseSingleton
from TMTChatbot.Schema.common.data_types import DataType


class UnitParser(BaseSingleton):
    mm_re = re.compile(r'\d+[.]*\d*(mm|milimet|milimét)')
    dm_re = re.compile(r'\d+[.]*\d*(đềcimét|đềcimet|đềximét|đềximet|decimet|deximet|dm)')
    inch_re = re.compile(r'\d+[.]*\d*(inches|inch|in|\"|”)')
    cm_re = re.compile(r'\d+[.]*\d*(xentimét|centimet|centimét|xentimet|cm)')
    feet_re = re.compile(r'\d+[.]*\d*(feet|fit|foot|phít|phit|ft|′|\')')
    met_dm_re = re.compile(r'\d+[.]*\d*(met|mét|m)\d+|(met|mét|m)\d+')
    met_re = re.compile(r'\d+[.]*\d*(met|mét|m)')
    met_unit = re.compile(r'met|mét|m')

    ta_re = re.compile(r'\d+[.]*\d*tạ')
    yen_re = re.compile(r'\d+[.]*\d*yến')
    kg_re = re.compile(r'\d+[.]*\d*((([ck][iíyý]l[ôo])|kg|kí|ký|k)(gram|gam|))')
    hg_re = re.compile(r'\d+[.]*\d*(hectôgam|lạng|hectogam|hg)')
    g_re = re.compile(r'\d+[.]*\d*(gam|g|gram)')
    pound_re = re.compile(r'\d+[.]*\d*(pounds|pao|bao|pound|b|lbs|lb)')
    none_unit_re = re.compile(r'\d+[.]*\d*')

    thousand_unit_vnd_re = re.compile(r'(\d+)\s*(k|ngàn|nghìn)')
    dong_unit_vnd_re = re.compile(r'(\d+[,.]\d+)')

    weekdays_re = re.compile(r'(t|thứ)\s*([2-7]|hai|ba|tư|bốn|năm|sáu|bảy)')
    sunday_re = re.compile(r'chủ nhật|cn|cnhat|CN')

    space_re = re.compile('[-_/ ]')
    number_re = re.compile(r'\d+')

    mapping2eng = {
        r"ngày|hôm": "day",
        r"tháng": "month",
        r"năm": "year"
    }
    mapping2offset = {
        r"trước|hôm qua|vừa rồi": -1,
        r"nay|này": 0,
        r"mai|sau|tới|nữa": 1,
        r"mốt": 2,
        r"kia": 3
    }
    map_weekday2offset = {
        "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5, "sáu": 6, "bảy": 7
    }

    @classmethod
    def normalize_vnd(cls, text):
        money = 0
        thousand_vnd = cls.thousand_unit_vnd_re.search(text)
        dong_vnd = cls.dong_unit_vnd_re.search(text)
        if thousand_vnd:
            money = int(thousand_vnd.group(1)) * 1000
        elif dong_vnd:
            money_str = dong_vnd.group(1)
            money_str = re.sub(r',\.', "", money_str)
            money = int(money_str)

        return money

    @staticmethod
    def normalize_usd(text):
        pass

    @classmethod
    def normalize_int(cls, text) -> int:
        save = deepcopy(text)
        number = cls.number_re.findall(save)
        try:
            total = int(number[0])
            return total
        except Exception as e:
            # TODO wrong int parsing when input is text
            print(e)
            return text

    @classmethod
    def normalize_float(cls, text) -> float:
        save = deepcopy(text)
        save = save.lower()
        save = save.replace(',', '.')
        number = cls.none_unit_re.findall(save)
        total = float(number[0])
        return total

    @classmethod
    def normalize_kg(cls, text) -> float:
        save = deepcopy(text)
        save = save.lower()
        save = save.replace(',', '.')
        save = cls.space_re.sub('', save)
        total = 0
        ta = cls.ta_re.findall(save)
        save = cls.ta_re.sub('', save)
        if len(ta) > 0:
            total += float(ta[0][:-2]) * 100

        # yến
        yen = cls.yen_re.findall(save)
        save = cls.yen_re.sub('', save)
        if len(yen) > 0:
            total += float(yen[0][:-3]) * 10

        # kg
        kg = cls.kg_re.search(save)
        if kg:
            save = re.sub(kg.group(0), '', save)
            number = cls.none_unit_re.findall(kg.group(0))
            total += float(number[0])
        # hg
        hg = cls.hg_re.search(save)
        if hg:
            save = re.sub(hg.group(0), '', save)
            number = cls.none_unit_re.findall(hg.group(0))
            total += float(number[0]) / 10
        # gam
        g = cls.g_re.search(save)
        if g:
            save = re.sub(g.group(0), '', save)
            number = cls.none_unit_re.findall(g.group(0))
            total += float(number[0]) / 1000
        # pound
        pound = cls.pound_re.search(save)
        save = cls.pound_re.sub('', save)
        if pound:
            save = re.sub(pound.group(0), '', save)
            number = cls.none_unit_re.findall(pound.group(0))
            total += float(number[0]) * 0.45359237

        # none_unit
        none_unit = cls.none_unit_re.findall(save)
        if len(none_unit) > 0:
            total += float(none_unit[0])
        return total

    @classmethod
    def support_normalize_length(cls, text, use_meter=True) -> float:
        save = deepcopy(text)
        save = save.lower()
        save = save.replace(',', '.')
        save = cls.space_re.sub('', save)
        total: float = 0
        # millimetre
        a_z = False
        milimet = cls.mm_re.search(save)
        if milimet:
            a_z = True
            save = re.sub(milimet.group(0), '', save)
            number = cls.none_unit_re.findall(milimet.group(0))
            total += float(number[0]) / 10
        # dm
        dm = cls.dm_re.search(save)
        if dm:
            a_z = True
            save = re.sub(dm.group(0), '', save)
            number = cls.none_unit_re.findall(dm.group(0))
            total += float(number[0]) * 10
        # cm
        cm = cls.cm_re.search(save)
        if cm:
            a_z = True
            save = re.sub(cm.group(0), '', save)
            number = cls.none_unit_re.findall(cm.group(0))
            total += float(number[0])
        # Inch
        inch = cls.inch_re.search(save)
        if inch:
            a_z = True
            save = re.sub(inch.group(0), '', save)
            number = cls.none_unit_re.findall(inch.group(0))
            total += float(number[0]) * 2.54
        # feet
        feet = cls.feet_re.search(save)
        if feet:
            a_z = True
            save = re.sub(feet.group(0), '', save)
            number = cls.none_unit_re.findall(feet.group(0))
            total += float(number[0]) * 30.48
        # met
        met_dm = cls.met_dm_re.search(save)
        met = cls.met_re.search(save)
        if met_dm:
            a_z = True
            save = re.sub(met_dm.group(0), '', save)
            number = cls.met_unit.sub('.', met_dm.group(0))
            total += float(number) * 100 if float(number) * 100 > 100.0 else float(number) * 100 + 100
        elif met:
            a_z = True
            save = re.sub(met.group(0), '', save)
            number = cls.none_unit_re.findall(met.group(0))
            total += float(number[0]) * 100

        # none_unit
        none_unit = cls.none_unit_re.findall(save)
        if len(none_unit) > 0:
            if a_z:
                total += float(none_unit[0])
            else:
                if use_meter:
                    total += float(none_unit[0]) * 100
                else:
                    total += float(none_unit[0])
        if use_meter:
            return total / 100
        else:
            return total

    @classmethod
    def normalize_m(cls, text) -> float:
        return cls.support_normalize_length(text, use_meter=True)

    @classmethod
    def normalize_cm(cls, text) -> float:
        return cls.support_normalize_length(text, use_meter=False)

    @classmethod
    def normalize_datetime(cls, text):
        """
        :param text:
        :return:
        """
        today = base_datetime.date.today()
        mentioned_date = {
            "day": today.day,
            "month": today.month,
            "year": today.year
        }

        is_date_form = False
        _delta = {"days": 0, "months": 0, "years": 0}
        is_week_offset = False
        n_offset = {k: 1 for k in mentioned_date.keys()}
        n_offset = {**n_offset, "week": 1}
        # Format: ngày 26/9 || tháng 5/2023 || ngày 25 tháng 11 || 1-2-2022 || ...
        format1 = re.search("(({})\s*(\d+)\s*)+".format("|".join(cls.mapping2eng.keys()) + "|/|-|\."), text)
        if format1:
            is_date_form = True
            mentioned_time = "ngày " + text
            time_value = re.findall("({})\s*(\d+)".format("|".join(cls.mapping2eng.keys()) + "|/|-|\."), mentioned_time)
            if time_value[0][0] == "ngày":
                if len(time_value) == 1:
                    mentioned_date["day"] = int(time_value[0][1])
                elif len(time_value) == 2:
                    mentioned_date["day"] = int(time_value[0][1])
                    if "năm" == time_value[1][0]:
                        mentioned_date["year"] = int(time_value[1][1])
                    else:
                        mentioned_date["month"] = int(time_value[1][1])
                elif len(time_value) == 3:
                    mentioned_date["day"] = int(time_value[0][1])
                    mentioned_date["month"] = int(time_value[1][1])
                    mentioned_date["year"] = int(time_value[2][1])
            else:
                if len(time_value) == 2:
                    mentioned_date = {
                        "day": today.day,
                        "month": int(time_value[0][1]),
                        "year": int(time_value[1][1])
                    }
                elif len(time_value) == 1:
                    for k, v in cls.mapping2eng.items():
                        if re.search(k, time_value[0][0]):
                            mentioned_date[v] = int(time_value[0][1])
            text = text.replace(format1.group(0), "")
        # Format: 2 ngày nữa, 3 tháng sau, ...
        if re.search("(\d+)\s*({})".format("|".join(cls.mapping2eng.keys())), text):
            is_date_form = True
            time_ = re.findall("(\d+)\s*({})".format("|".join(cls.mapping2eng.keys())), text)
            value, time_unit = time_[0]
            for k, v in cls.mapping2eng.items():
                if re.search(k, time_unit):
                    # mentioned_date[v] = getattr(today, v) + int(value)
                    n_offset[v] = int(value)
        # Format day of week
        if cls.weekdays_re.search(text) or cls.sunday_re.search(text):
            is_date_form = True
            if cls.sunday_re.search(text):
                n_week = 6
                text = text.replace(cls.sunday_re.search(text).group(0), "")
            else:
                n_week = cls.weekdays_re.search(text).group(2)
                # - 2 to get offset of weekday with default monday offset = 0
                n_week = int(cls.map_weekday2offset.get(n_week, n_week)) - 2
                text = text.replace(cls.weekdays_re.search(text).group(0), "")
            _delta["days"] += n_week - today.weekday()
            if n_week <= today.weekday():
                is_week_offset = True
        # Format: 2 tuần sau, 3 tuần trước, ...
        if re.search("(\d+)\s*(tuần)", text):
            is_date_form = True
            is_week_offset = True
            n_week_offset = re.findall("(\d+)\s*tuần", text)
            n_offset["week"] = int(n_week_offset[0])

        # Format: ngày mai, tháng sau, ngày mốt, ...
        o = []
        if re.search(r"|".join(cls.mapping2offset.keys()), text):
            is_date_form = True
            unit_offset = re.findall(
                r"({})\s*({})".format("|".join(cls.mapping2eng.keys()), "|".join(cls.mapping2offset.keys())),
                text)
            week_offset = re.findall(r"(tuần)\s*({})".format("|".join(cls.mapping2offset.keys())), text)

            for unit, offset_ in unit_offset:
                _o = [f for e, f in cls.mapping2offset.items() if re.search(e, offset_)][0]
                u = [f for e, f in cls.mapping2eng.items() if re.search(e, unit)][0]
                _delta[f"{u}s"] += n_offset[u] * _o
            if week_offset:
                for unit, offset_ in week_offset:
                    o = [f for e, f in cls.mapping2offset.items() if re.search(e, offset_)]
        if is_week_offset or o:
            o = 1 if not o else o[0]
            _delta["days"] += n_offset["week"] * (o * 7)

        delta = relativedelta(**_delta)
        if not is_date_form:
            return ""
        try:
            date_ = base_datetime.date(**mentioned_date) + delta
            date_ = date_.strftime("%d/%m/%Y")
        except ValueError as err:
            logging.debug(f"Mentioned date is invalid: {err}")
            date_ = ""

        return date_

    @staticmethod
    def normalize_size(text):
        return text.upper()

    @classmethod
    def get_normalize_func(cls, data_type: DataType):
        func_name = f"normalize_{data_type.name.lower()}"
        if not hasattr(cls, func_name):
            return lambda x: x
        return getattr(cls, func_name)

    @classmethod
    def normalize(cls, text: str, ner_label: str):
        if ner_label == "size":
            return cls.normalize_size(text)
        target_unit: DataType = UnitConfig.get_target_data_type(ner_label)
        if target_unit is None:
            return text
        normalize_func = cls.get_normalize_func(target_unit)
        return normalize_func(text)


if __name__ == "__main__":
    print(UnitParser.normalize("thứ 2 tuần này", "DATE"))
