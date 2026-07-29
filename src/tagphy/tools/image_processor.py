from PIL import Image, ExifTags
from typing import Any
from pillow_heif import register_heif_opener
import reverse_geocoder as rg

register_heif_opener()


class ImageMetadata:
    def extract_metadata(self, image_path: str) -> dict:
        """Extract metadata from an image. Returns the year taken and the location.

        Args:
            image_path: The path to the image to process.

        Returns:
            A dictionary containing the year taken and the location.
        """
        im = Image.open(image_path)
        exif = im.getexif()

        year_taken = None
        location = None
        # get taken time
        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        datetime_original = exif_ifd.get(ExifTags.Base.DateTimeOriginal)
        datetime_fallback = exif.get(ExifTags.Base.DateTime)

        if datetime_original:
            year_taken = datetime_original.split(":")[0]
        elif datetime_fallback:
            year_taken = datetime_fallback.split(":")[0]

        gps_info = exif.get_ifd(ExifTags.Base.GPSInfo)
        coords = self.parse_gps_to_lat_lon(gps_info)
        if coords:
            geo_info = rg.search(coords, mode=1)
            if geo_info:
                location = "".join([geo_info[0]["name"], ", ", geo_info[0]["cc"]])

        return {
            "year": year_taken,
            "location": location,
        }

    def _dms_to_decimal(self, dms: Any) -> float | None:
        """Convert EXIF (degrees, minutes, seconds) to a decimal degree magnitude."""
        try:
            degrees, minutes, seconds = dms
            degrees_f = float(degrees)
            minutes_f = float(minutes)
            seconds_f = float(seconds)
        except (TypeError, ValueError):
            return None

        if minutes_f < 0 or seconds_f < 0:
            return None

        return degrees_f + (minutes_f / 60.0) + (seconds_f / 3600.0)

    def parse_gps_to_lat_lon(
        self, gps_info: dict[int, Any] | None
    ) -> tuple[float, float] | None:
        """
        Parse a Pillow GPS IFD dict into (lat, lon) decimal degrees.

        Returns None unless latitude/longitude and their refs are present and valid.
        """
        if not gps_info:
            return None

        # EXIF GPS tags: 1=LatRef, 2=Lat, 3=LonRef, 4=Lon
        lat_ref = gps_info.get(1)
        lat_dms = gps_info.get(2)
        lon_ref = gps_info.get(3)
        lon_dms = gps_info.get(4)

        if lat_ref is None or lon_ref is None or lat_dms is None or lon_dms is None:
            return None

        try:
            lat_ref_s = str(lat_ref).strip().upper()
            lon_ref_s = str(lon_ref).strip().upper()
        except Exception:
            return None

        if lat_ref_s not in {"N", "S"} or lon_ref_s not in {"E", "W"}:
            return None

        lat = self._dms_to_decimal(lat_dms)
        lon = self._dms_to_decimal(lon_dms)
        if lat is None or lon is None:
            return None

        if lat_ref_s == "S":
            lat = -lat
        if lon_ref_s == "W":
            lon = -lon

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None

        # Common bogus placeholder
        if lat == 0.0 and lon == 0.0:
            return None

        return (lat, lon)


if __name__ == "__main__":
    meta = ImageMetadata().extract_metadata("../../../dev/5.Heic")
    print(meta)
