"""Contract tests for Stage 2.1 metadata extraction."""

from unittest.mock import MagicMock, patch

import pytest
from PIL import ExifTags

from tagphy.tools.image_metadata import ImageMetadata


class TestDmsToDecimal:
    def test_converts_valid_dms(self):
        assert ImageMetadata()._dms_to_decimal((51, 2, 30)) == pytest.approx(
            51 + 2 / 60 + 30 / 3600
        )

    def test_rejects_negative_minutes_or_seconds(self):
        assert ImageMetadata()._dms_to_decimal((51, -1, 0)) is None
        assert ImageMetadata()._dms_to_decimal((51, 0, -1)) is None

    def test_rejects_malformed_dms(self):
        assert ImageMetadata()._dms_to_decimal("not-a-tuple") is None
        assert ImageMetadata()._dms_to_decimal((1, 2)) is None


class TestParseGpsToLatLon:
    def test_returns_none_for_empty_or_missing(self):
        meta = ImageMetadata()
        assert meta.parse_gps_to_lat_lon(None) is None
        assert meta.parse_gps_to_lat_lon({}) is None

    def test_parses_northern_eastern_coords(self):
        gps = {
            1: "N",
            2: (51, 2, 30),
            3: "E",
            4: (114, 4, 0),
        }
        lat, lon = ImageMetadata().parse_gps_to_lat_lon(gps)
        assert lat == pytest.approx(51 + 2 / 60 + 30 / 3600)
        assert lon == pytest.approx(114 + 4 / 60)

    def test_applies_south_and_west_refs(self):
        gps = {
            1: "S",
            2: (33, 51, 0),
            3: "W",
            4: (151, 12, 0),
        }
        lat, lon = ImageMetadata().parse_gps_to_lat_lon(gps)
        assert lat < 0
        assert lon < 0

    def test_rejects_invalid_refs(self):
        gps = {1: "X", 2: (10, 0, 0), 3: "E", 4: (20, 0, 0)}
        assert ImageMetadata().parse_gps_to_lat_lon(gps) is None

    def test_rejects_incomplete_gps_ifd(self):
        gps = {1: "N", 2: (10, 0, 0)}  # missing lon
        assert ImageMetadata().parse_gps_to_lat_lon(gps) is None

    def test_rejects_zero_zero_placeholder(self):
        gps = {1: "N", 2: (0, 0, 0), 3: "E", 4: (0, 0, 0)}
        assert ImageMetadata().parse_gps_to_lat_lon(gps) is None

    def test_rejects_out_of_range_coords(self):
        gps = {1: "N", 2: (95, 0, 0), 3: "E", 4: (10, 0, 0)}
        assert ImageMetadata().parse_gps_to_lat_lon(gps) is None


def _mock_image_with_exif(
    *,
    datetime_original=None,
    datetime_fallback=None,
    gps_info=None,
):
    image = MagicMock()
    exif = MagicMock()
    exif_ifd = {}
    if datetime_original is not None:
        exif_ifd[ExifTags.Base.DateTimeOriginal] = datetime_original

    def get_ifd(ifd_id):
        if ifd_id == ExifTags.IFD.Exif:
            return exif_ifd
        if ifd_id == ExifTags.Base.GPSInfo:
            return gps_info or {}
        return {}

    exif.get_ifd.side_effect = get_ifd
    exif.get.side_effect = lambda key, default=None: (
        datetime_fallback if key == ExifTags.Base.DateTime else default
    )
    image.getexif.return_value = exif
    return image


class TestExtractMetadata:
    @patch("tagphy.tools.image_metadata.Image.open")
    @patch("tagphy.tools.image_metadata.rg.search")
    def test_prefers_datetime_original_for_year(self, mock_search, mock_open):
        mock_search.return_value = []
        mock_open.return_value = _mock_image_with_exif(
            datetime_original="2024:06:15 12:00:00",
            datetime_fallback="2019:01:01 00:00:00",
        )

        result = ImageMetadata().extract_metadata("photo.jpg")

        assert result["year"] == "2024"
        assert "location" in result

    @patch("tagphy.tools.image_metadata.Image.open")
    @patch("tagphy.tools.image_metadata.rg.search")
    def test_falls_back_to_datetime_when_original_missing(
        self, mock_search, mock_open
    ):
        mock_search.return_value = []
        mock_open.return_value = _mock_image_with_exif(
            datetime_fallback="2021:03:04 08:00:00",
        )

        result = ImageMetadata().extract_metadata("photo.jpg")

        assert result["year"] == "2021"

    @patch("tagphy.tools.image_metadata.Image.open")
    @patch("tagphy.tools.image_metadata.rg.search")
    def test_year_none_when_no_datetime(self, mock_search, mock_open):
        mock_search.return_value = []
        mock_open.return_value = _mock_image_with_exif()

        result = ImageMetadata().extract_metadata("photo.jpg")

        assert result["year"] is None
        assert result["location"] is None
        mock_search.assert_not_called()

    @patch("tagphy.tools.image_metadata.Image.open")
    @patch("tagphy.tools.image_metadata.rg.search")
    def test_location_from_valid_gps_geocode(self, mock_search, mock_open):
        mock_search.return_value = [{"name": "Calgary", "cc": "CA"}]
        mock_open.return_value = _mock_image_with_exif(
            datetime_original="2023:01:01 00:00:00",
            gps_info={
                1: "N",
                2: (51, 2, 30),
                3: "W",
                4: (114, 4, 0),
            },
        )

        result = ImageMetadata().extract_metadata("photo.jpg")

        assert result["location"] == "Calgary, CA"
        mock_search.assert_called_once()
        coords = mock_search.call_args[0][0]
        assert coords[0] > 0
        assert coords[1] < 0

    @patch("tagphy.tools.image_metadata.Image.open")
    @patch("tagphy.tools.image_metadata.rg.search")
    def test_invalid_gps_skips_geocode(self, mock_search, mock_open):
        mock_open.return_value = _mock_image_with_exif(
            datetime_original="2023:01:01 00:00:00",
            gps_info={1: "N", 2: (0, 0, 0), 3: "E", 4: (0, 0, 0)},
        )

        result = ImageMetadata().extract_metadata("photo.jpg")

        assert result["location"] is None
        mock_search.assert_not_called()

    @patch("tagphy.tools.image_metadata.Image.open")
    def test_image_open_failure_propagates(self, mock_open):
        mock_open.side_effect = FileNotFoundError("missing")

        with pytest.raises(FileNotFoundError):
            ImageMetadata().extract_metadata("missing.jpg")
