from app.anonymizer import Anonymizer

def test_roundtrip():
    a = Anonymizer()
    a.add_known("NAME", "Айдана Серикова")
    src = "Айдана Серикова, +7 701 123 45 67, aidana@mail.kz, ИИН 900101123456, t.me/aidana, @aidana_s"
    out = a.anonymize(src)
    for s in ["Серикова", "701", "mail.kz", "900101123456", "t.me", "aidana_s"]:
        assert s not in out, out
    assert a.restore(out) == src

def test_reply_restore():
    a = Anonymizer(); a.add_known("NAME", "Айдана")
    a.anonymize("Айдана")
    assert a.restore("[NAME_1], удобно во вторник?") == "Айдана, удобно во вторник?"
