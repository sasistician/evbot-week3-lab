from evbot.router import classify_complexity


def test_short_factual_query_is_simple():
    assert classify_complexity("What's the range of the Model 3?") == "simple"


def test_long_query_is_complex():
    query = (
        "I'm trying to decide on a new EV for my family and want to understand "
        "how the range, charging speed, interior space, and total cost of "
        "ownership compare over a five year period before I make a decision"
    )
    assert classify_complexity(query) == "complex"


def test_comparison_keyword_is_complex():
    assert classify_complexity("Compare the Bolt and the Ioniq 5") == "complex"


def test_recommend_keyword_is_complex():
    assert classify_complexity("Which EV would you recommend for towing?") == "complex"


def test_multiple_model_mentions_is_complex():
    assert classify_complexity("Model 3 or Mach-E, same price?") == "complex"


def test_single_model_mention_is_simple():
    assert classify_complexity("How much does the Mach-E cost?") == "simple"


def test_boundary_word_count_is_simple():
    query = " ".join(["word"] * 25)
    assert classify_complexity(query) == "simple"


def test_over_boundary_word_count_is_complex():
    query = " ".join(["word"] * 26)
    assert classify_complexity(query) == "complex"
