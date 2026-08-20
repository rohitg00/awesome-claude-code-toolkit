from ntxp_contacts import normalize as N


def test_strip_float_id():
    assert N.strip_float_id("696372.0") == "696372"
    assert N.strip_float_id("76177.0") == "76177"
    assert N.strip_float_id("ABC123") == "ABC123"
    assert N.strip_float_id("") == ""


def test_normalize_email():
    assert N.normalize_email("  Eric.Vaden@VadensInc.com ") == "eric.vaden@vadensinc.com"
    assert N.normalize_email("mailto:a@b.co") == "a@b.co"
    assert N.normalize_email("not an email") is None
    assert N.normalize_email("") is None


def test_normalize_phone():
    assert N.normalize_phone("(504) 529-2229") == "+15045292229"
    assert N.normalize_phone("+1 817-847-8822") == "+18178478822"
    assert N.normalize_phone("(480)855-0111") == "+14808550111"
    assert N.normalize_phone("123") is None


def test_normalize_zip():
    assert N.normalize_zip("76177.0") == "76177"
    assert N.normalize_zip("7013") == "07013"
    assert N.normalize_zip("75284-4127") == "75284-4127"
    assert N.normalize_zip("") is None


def test_normalize_state():
    assert N.normalize_state("tx") == "TX"
    assert N.normalize_state("Texas") == "TX"
    assert N.normalize_state("ZZ") is None


def test_excel_serial_date():
    # Excel serial 45292 == 2024-01-01, so 45246 == 2023-11-16.
    assert N.excel_serial_to_date("45246.5") == "2023-11-16"
    assert N.excel_serial_to_date("45292") == "2024-01-01"


def test_parse_name():
    assert N.parse_name("Charles F. Webb") == ("Charles", "F. Webb")
    assert N.parse_name("Hill Jr, Alonzo") == ("Alonzo", "Hill Jr")
    assert N.parse_name("") == (None, None)


def test_name_norm():
    assert N.name_norm("Charles", "Webb") == "charles webb"
    assert N.name_norm(None, None, "Betty L. Washington") == "betty l washington"


def test_org_name_norm():
    a = N.org_name_norm("JHL Painting Contractor Inc")
    b = N.org_name_norm("JHL Painting Contractor, Inc.")
    assert a == b == "jhl painting contractor"


def test_block_key():
    assert N.block_key("Eric", "Vaden") == "vaden|e"
    assert N.block_key(None, None, "betty washington") == "washington|b"
    # Same person blocks together; different first initials do not.
    assert N.block_key("Eric", "Vaden") == N.block_key("eric", "vaden")
    assert N.block_key("John", "Smith") != N.block_key("Mary", "Smith")
