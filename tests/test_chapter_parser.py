from app.ingestion.chapter_parser import parse_chapters


def test_parse_chapters_extracts_ordered_chapters():
    text = "第一卷\n第一章 开始\n甲乙丙\n第二章 继续\n丁戊己"
    chapters = parse_chapters(text)
    assert chapters[0].chapter_idx == 1
    assert chapters[1].chapter_idx == 2


def test_parse_chapters_supports_split_titles_from_real_novel_format():
    text = (
        "初六之卷 塞上枕戈\n"
        "初六之卷\n"
        "塞上枕戈\n\n"
        "第一章 劫后梦醒世事更\n"
        "第一章\n"
        "劫后梦醒世事更\n"
        "正文甲乙丙\n\n"
        "第二章 摇红烛影忆平生（上）\n"
        "第二章\n"
        "摇红烛影忆平生（上）\n"
        "正文丁戊己\n"
    )
    chapters = parse_chapters(text)
    assert len(chapters) == 2
    assert chapters[0].title == "第一章 劫后梦醒世事更"
    assert "正文甲乙丙" in chapters[0].content
