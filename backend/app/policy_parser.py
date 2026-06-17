from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
from zipfile import ZipFile
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class PolicyDocument:
    path: Path
    paragraphs: List[str]


def load_policy_document(path: str | Path) -> PolicyDocument:
    source = Path(path)
    with ZipFile(source) as archive:
        xml = archive.read('word/document.xml')
    root = ET.fromstring(xml)
    namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs: List[str] = []
    for paragraph in root.findall('.//w:p', namespace):
        texts = [node.text for node in paragraph.findall('.//w:t', namespace) if node.text]
        if texts:
            paragraphs.append(''.join(texts))
    return PolicyDocument(path=source, paragraphs=paragraphs)


def summarize_policy(document: PolicyDocument) -> dict:
    return {
        'source': document.path.name,
        'paragraph_count': len(document.paragraphs),
        'headings': [
            line
            for line in document.paragraphs
            if line[:1].isdigit() or line.startswith('Day 1') or line.startswith('Day 2') or line.startswith('Day 3')
        ],
    }
