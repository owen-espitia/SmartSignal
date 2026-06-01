import logging

logger = logging.getLogger(__name__)

try:
    from rpi_ws281x import PixelStrip, Color
    _MOCK = False
    logger.info("rpi_ws281x loaded — hardware mode")
except ImportError:
    _MOCK = True
    logger.warning("rpi_ws281x not found — running in mock mode (no hardware required)")

    class Color:
        def __init__(self, r: int, g: int, b: int):
            self.r, self.g, self.b = r, g, b

        def __repr__(self) -> str:
            return f"Color({self.r},{self.g},{self.b})"

    class PixelStrip:
        def __init__(self, num, pin, freq_hz, dma, invert, brightness, channel):
            self._num = num
            self._pixels: list[Color] = [Color(0, 0, 0)] * num

        def begin(self) -> None:
            logger.info("[MOCK] LED strip initialized (%d pixels)", self._num)

        def numPixels(self) -> int:
            return self._num

        def setPixelColor(self, n: int, color: Color) -> None:
            self._pixels[n] = color

        def show(self) -> None:
            logger.debug("[MOCK] show() — pixel[0]=%s", self._pixels[0])

        def setBrightness(self, brightness: int) -> None:
            logger.debug("[MOCK] setBrightness(%d)", brightness)


MAX_BRIGHTNESS = 51  # 20% of 255 — hard ceiling enforced regardless of config


class LEDController:
    def __init__(self, config: dict):
        cfg = config["led"]
        brightness = min(cfg["brightness"], MAX_BRIGHTNESS)
        self.strip = PixelStrip(
            cfg["count"],
            cfg["pin"],
            cfg["freq_hz"],
            cfg["dma"],
            cfg["invert"],
            brightness,
            cfg["channel"],
        )
        self.strip.begin()
        self.num_pixels: int = cfg["count"]

    def set_all(self, r: int, g: int, b: int) -> None:
        color = Color(r, g, b)
        for i in range(self.num_pixels):
            self.strip.setPixelColor(i, color)
        self.strip.show()

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        self.strip.setPixelColor(index, Color(r, g, b))

    def show(self) -> None:
        self.strip.show()

    def clear(self) -> None:
        self.set_all(0, 0, 0)
