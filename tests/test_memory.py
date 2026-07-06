from evbot import memory


def test_append_and_retrieve_turn(tmp_path):
    db_path = str(tmp_path / "memory.db")
    memory.append_turn("s1", "user", "What's the range of the Model 3?", db_path=db_path)
    memory.append_turn("s1", "assistant", "About 272 miles.", db_path=db_path)

    turns = memory.get_recent_turns("s1", n=6, db_path=db_path)

    assert [t.role for t in turns] == ["user", "assistant"]
    assert turns[0].content == "What's the range of the Model 3?"


def test_recent_turns_respects_limit(tmp_path):
    db_path = str(tmp_path / "memory.db")
    for i in range(10):
        memory.append_turn("s1", "user", f"message {i}", db_path=db_path)

    turns = memory.get_recent_turns("s1", n=3, db_path=db_path)

    assert len(turns) == 3
    assert turns[-1].content == "message 9"


def test_sessions_are_isolated(tmp_path):
    db_path = str(tmp_path / "memory.db")
    memory.append_turn("s1", "user", "s1 message", db_path=db_path)
    memory.append_turn("s2", "user", "s2 message", db_path=db_path)

    s1_turns = memory.get_recent_turns("s1", db_path=db_path)
    s2_turns = memory.get_recent_turns("s2", db_path=db_path)

    assert len(s1_turns) == 1
    assert len(s2_turns) == 1
    assert s1_turns[0].content == "s1 message"


def test_persists_across_new_connections(tmp_path):
    db_path = str(tmp_path / "memory.db")
    memory.append_turn("s1", "user", "hello", db_path=db_path)

    turns = memory.get_recent_turns("s1", db_path=db_path)

    assert len(turns) == 1
