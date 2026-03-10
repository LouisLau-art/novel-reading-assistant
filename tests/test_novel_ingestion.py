from app.ingestion.chapter_parser import parse_novel_text


def test_parse_novel_text_captures_volume_and_chapter_metadata():
    text = (
        "初六之卷 塞上枕戈\n"
        "初六之卷\n"
        "塞上枕戈\n\n"
        "第一章 劫后梦醒世事更\n"
        "第一章\n"
        "劫后梦醒世事更\n"
        "正文甲乙丙\n"
    )
    novel = parse_novel_text(text)
    assert novel.volume_title == "初六之卷 塞上枕戈"
    assert novel.chapters[0].chapter_idx == 1
    assert novel.chapters[0].volume_title == "初六之卷 塞上枕戈"
