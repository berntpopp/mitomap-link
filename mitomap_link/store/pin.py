"""The one data release this application build serves (bumped by a reviewed PR).

Must equal ``container-release.json`` ``data.release_tag``/``data.digest``
(``tests/unit/test_release_contract.py`` enforces it).
"""

RELEASE_TAG = "data-mitomap-a6646827e6157779"
COMPRESSED_SHA256 = "c76206df08fc62fe9c0fea7e60e4f527e5285eadb95ebb9edd36248668d85084"
EXPANDED_SHA256 = "a6646827e6157779d0bb3988634e6aa488abf8bbeb338739a5fddf793acdaef1"
BUNDLE_URL = (
    f"https://github.com/berntpopp/mitomap-link/releases/download/{RELEASE_TAG}/mitomap.sqlite.gz"
)
