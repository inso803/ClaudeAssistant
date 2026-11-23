from brief.post_report import ALLOWED_CHANNEL_ID, decode_message, find_todays_brief_id


def test_allowed_channel_is_inso803_morning_briefing():
    assert ALLOWED_CHANNEL_ID == "1547445470555807794"


def test_decode_message_turns_literal_newlines_into_real_ones():
    assert decode_message("  第一行\\n第二行\\n\\n第三段 ") == "第一行\n第二行\n\n第三段"


def test_find_todays_brief_only_matches_bot_and_today():
    msgs = [
        {"id": "3", "author": {"id": "me"}, "content": "📬 Discord 回報"},
        {"id": "2", "author": {"id": "bot"}, "content": "☀️ 11/24（二）早安\n..."},
        {"id": "1", "author": {"id": "bot"}, "content": "☀️ 11/23（一）早安"},
    ]
    assert find_todays_brief_id(msgs, "bot", "11/24（") == "2"
    assert find_todays_brief_id(msgs, "bot", "11/25（") is None
