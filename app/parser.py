from zipfile import ZipFile
from typing import Iterable, IO
import lxml.etree as ET


def parse_zip(io_content: IO) -> Iterable[str]:
    """ Reads an open zip and yield the string content of each XML

    :param io_content: Open ZIP
    :return: List of XML content as string
    """
    with ZipFile(io_content) as zf:
        for file in zf.namelist():
            if file.endswith('.xml'):
                with zf.open(file) as f:
                    yield file, ET.tostring(ET.parse(f), encoding=str)
