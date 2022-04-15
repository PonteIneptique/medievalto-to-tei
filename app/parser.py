from zipfile import ZipFile
from typing import Iterable, IO, Dict
import lxml.etree as ET
import re
from collections import defaultdict, Counter

__all__ = ["page_to_tei", "parse_zip"]

"""
"<choice><abbr>$1</abbr><expan>$2</expan></choice>")
.replace(/(\[[^\|\]]\]+)/gm, "<choice type=\"hyphenization\"><orig>$1</orig><corr></corr></choice>")
.replace(/•/gm, "<choice type=\"add-space\"><orig></orig><corr> </corr></choice>")
.replace(/\r?\n/g, "<lb></lb>");
"""
_re_abbr = re.compile(r"\[([^\|\]]+|[^\|\]]*\[\s+\][^\|\]]*)\|([^\]]+)\]", flags=re.MULTILINE)
_re_hyph = re.compile(r"\[([^\|\]]+)\]", flags=re.MULTILINE)
_re_adds = re.compile(r"•", flags=re.MULTILINE)
_re_new_line = re.compile(r"\r?\n", flags=re.MULTILINE)


def parse_zip(io_content: IO) -> Iterable[str]:
    """ Reads an open zip and yield the string content of each XML

    :param io_content: Open ZIP
    :return: List of XML content as string
    """
    with ZipFile(io_content) as zf:
        for file in zf.namelist():
            if file.endswith('.xml'):
                with zf.open(file) as f:
                    yield file, "\n".join([
                        string.attrib["CONTENT"]
                        for string in ET.parse(f).findall("//{*}TextLine/{*}String")
                    ])
            elif file.endswith(".txt"):
                with zf.open(file) as f:
                    yield file, f.read()


def page_to_tei(content: str) -> str:
    return _re_new_line.sub(
        "\n<lb />",
        _re_adds.sub(
            r'<choice type="add-space"><orig></orig><corr> </corr></choice>',
            _re_hyph.sub(
                r'<choice type="hyphenization"><orig>\g<1></orig><corr></corr></choice>',
                _re_abbr.sub(r"<choice><abbr>\g<1></abbr><expan>\g<2></expan></choice>", content)
            )
        )
    )


def get_all_abbreviations(documents: Iterable[str]) -> Dict[str, Dict[str, int]]:
    abbrs = defaultdict(Counter)
    for doc in documents:
        for abbr, orig in _re_abbr.findall(doc):
            abbrs[_re_hyph.sub("", abbr)][orig] += 1
    return abbrs
