from app.ingestion.chapter_parser import parse_chapters


def test_parse_chapters_extracts_ordered_chapters():
    text = "第一卷\n第一章 开始\n甲乙丙\n第二章 继续\n丁戊己"
    chapters = parse_chapters(text)
    assert chapters[0].chapter_idx == 1
    assert chapters[1].chapter_idx == 2
