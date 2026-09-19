from Components.Converter.PliExtraInfo import PliExtraInfo


class CineViewTransponderInfo(PliExtraInfo):
    """PliExtraInfo with OpenATV 8 frontend units normalized for CineView."""

    @staticmethod
    def _normalize(value):
        if value in (None, ""):
            return ""
        try:
            number = int(value)
        except (TypeError, ValueError):
            return str(value)
        if abs(number) >= 1000000:
            number //= 1000
        return str(number)

    def createFrequency(self, fedata):
        return self._normalize(fedata.get("frequency"))

    def createSymbolRate(self, fedata, feraw):
        if "DVB-T" in feraw.get("tuner_type", ""):
            bandwidth = fedata.get("bandwidth")
            return bandwidth or ""
        return self._normalize(fedata.get("symbol_rate"))
