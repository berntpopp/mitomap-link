"""The one data release this application build serves (bumped by a reviewed PR).

Must equal ``container-release.json`` ``data.release_tag``/``data.digest``
(``tests/unit/test_release_contract.py`` enforces it).
"""

RELEASE_TAG = "data-mitomap-0000000000000000"
COMPRESSED_SHA256 = "0" * 64
EXPANDED_SHA256 = "0" * 64
BUNDLE_URL = (
    f"https://github.com/berntpopp/mitomap-link/releases/download/{RELEASE_TAG}/mitomap.sqlite.gz"
)
