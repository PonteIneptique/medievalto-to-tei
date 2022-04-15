from zipfile import ZipFile
from typing import Iterable, IO, Dict, TYPE_CHECKING
import lxml.etree as ET
import regex as re
from collections import defaultdict, Counter

if TYPE_CHECKING:
    from app.models import Page

__all__ = ["page_to_tei", "parse_zip", "get_all_abbreviations", "apply_abbreviations"]


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
                try:
                    with zf.open(file) as f:
                        yield file, "\n".join([
                            string.attrib["CONTENT"]
                            for string in ET.parse(f).findall("//{*}TextLine/{*}String")
                        ])
                except ET.XMLSyntaxError:
                    continue
            elif file.endswith(".txt"):
                with zf.open(file) as f:
                    yield file, f.read().decode("UTF-8")


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


_ABBR_DICT = Dict[str, Dict[str, int]]


def get_all_abbreviations(documents: Iterable[str]) -> _ABBR_DICT:
    abbrs = defaultdict(Counter)
    for doc in documents:
        for abbr, orig in _re_abbr.findall(doc):
            abbrs[_re_hyph.sub("", abbr)][orig] += 1
    return abbrs


def apply_abbreviations(pages: Iterable["Page"], abbreviations: _ABBR_DICT) -> Dict[str, _ABBR_DICT]:
    done = defaultdict(lambda: defaultdict(Counter))
    for page in pages:
        for abbr, replacements in abbreviations.items():
            if len(replacements) == 1:
                repl = list(replacements.keys())[0]
                regex = re.compile(r"([\p{Punct}\s]+)"+rf"(?<!\[)({abbr})(?!\|)"+r"([\p{Punct}\s]+)")
                nb = regex.findall(page.page_content)
                if nb:
                    done[page.page_title][abbr][repl] = len(nb)
                    page.page_content = regex.sub(rf"\g<1>[\g<2>|{repl}]\g<3>", page.page_content)
    return done
