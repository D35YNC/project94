import ssl
import pytest

from project94.listener import Listener, ListenerStartError, ListenerStopError


# TODO: separate key and cert
def drop_cert(path):
    ca = """-----BEGIN CERTIFICATE-----
MIIFiTCCA3GgAwIBAgIUfqFzmGzh7bi9sBpxBXmFkN1HkBEwDQYJKoZIhvcNAQEN
BQAwVDELMAkGA1UEBhMCVFQxDDAKBgNVBAgMA1RUVDEMMAoGA1UEBwwDVFRUMQww
CgYDVQQKDANUVFQxDDAKBgNVBAsMA1RUVDENMAsGA1UEAwwEVEVTVDAeFw0yMzEx
MjcxMzQ5MjFaFw0yNjA5MTYxMzQ5MjFaMFQxCzAJBgNVBAYTAlRUMQwwCgYDVQQI
DANUVFQxDDAKBgNVBAcMA1RUVDEMMAoGA1UECgwDVFRUMQwwCgYDVQQLDANUVFQx
DTALBgNVBAMMBFRFU1QwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQCt
8Vk/gRSOdAWt0W/XFaCrRdFO4zQgMXKV1CDzAx+o0kwksHtlnCKEevDsLeGldAwI
4ykixd9cQ/9Uri/rZlgSusgDMvavQTO0psjTmaXntIkM2hrqRQIJxi51fU79Xq4B
UmASr/WqxkmZEaZG1XqJxMlOCHG2wwVlRiNv9shB2MJcXodZyfVU1v9HQcnLOVNV
DwHLn7X4NiZBe4ZTM/3f19eHOxy8rF7BYd0Om3rtZujZ8B2oSqdBlrUW0TkmMmxV
CjYVOSnEqI6y7WishHu+xZ+VhaSFIogORl0QQE8yczFYdeMGXDedZTaIWmLKNUm8
12srCpYEu8Fyas1B4yUd5+tU4aZC8lwvFauWc8ExfR/x7jYqk3fGVvVTa0+C7kGq
FRt5jc/dYb/bYDxvXjGYOKv8+Ug8Qjng+0D6H0BSpjc56AIplMcr20OphuFd2/8z
QugqLed6rm566VsnEFFxZIkx34zJkt2TjZyohw7fFiLU4jUxa2iGauI3rBbdLJII
JtnBfHXZA+uCFAIC1sxFz3JqkggWGeRmISeWuWvIePKfsCgnzI8Fawc1F5y3VPwu
rQlvNcIZ2Lc02fEn1ebjE6DJMsSW07YwPf8jIfWWrm5RPgGEyYYRiEdEOvUxdVoK
EnGStT5K5/W/XFMgdjJi8SOhrYpyRtNc7jca5HzloQIDAQABo1MwUTAdBgNVHQ4E
FgQUqqU8STvpJ0A7HonEaTOfXtow+O4wHwYDVR0jBBgwFoAUqqU8STvpJ0A7HonE
aTOfXtow+O4wDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQ0FAAOCAgEAZxiS
o8jPpMZLYOA1O6k2LrpEBuedhY84qGqRVm6dcKKYb3i1j3Uw6q7l4sldNFVz7djJ
t8FYcivAFQwFYm8Bm+dv6NyfAumiMVj3tQtB81z2/xBn+JSdpdARvb6iSG4KK0Tl
xvFada+dENgobGIOj39nV32nyfExAXssH9FS06ix/K2oInF24eEEqw6s8+oJIiXP
LJWitgejUvgZYG+Rj6AxN2ccvdiljqZidFaxeQP0vToWn5xaRIHewLXVza5X6ive
QuwFEfCKS7EQGFmqAENAu3krBb59OFFK02Woq3kLHEKNYCJPbmar3/CJKYNrvPps
pJcdwbPX93I2N+6QhQKzzesEBk0XBBZ/dPjBHZd0ObSAg8dhdNlN6v0qo1tG5osb
KStvH4jSnulIJajTicq2OjxWzETw+pMh2yAZvPeNDIjQni2QJzE8sBibLBsZdwl6
GIBfIdztQjJQJkU1EPS86lRSHc2oPmQNXepfqMDKsHHAbAkQvPixFHm+Hy3dy3Sv
SLN9LssDxWEECA5EprdEuCifSzABCya43rK17CAdQTw8kPWc/mJSNupG5nbZDRul
CefBVAXC8soK6/MkA+b80e7IDYrKu6WDlevkEmdbhYUq6DQuTEGv/eZamcq8bLli
tqodd6D/oceqeMUp6dtACLLkh1V0vHQLXcreU1g=
-----END CERTIFICATE-----
"""
    cert = """-----BEGIN CERTIFICATE-----
MIIFiTCCA3GgAwIBAgIUdvX6F1h1TEH93XKuCce4bScyHTYwDQYJKoZIhvcNAQEN
BQAwVDELMAkGA1UEBhMCVFQxDDAKBgNVBAgMA1RUVDEMMAoGA1UEBwwDVFRUMQww
CgYDVQQKDANUVFQxDDAKBgNVBAsMA1RUVDENMAsGA1UEAwwEVEVTVDAeFw0yMzEx
MjcxMzQ5MjJaFw0yNjA5MTYxMzQ5MjJaMFQxCzAJBgNVBAYTAlRUMQwwCgYDVQQI
DANUVFQxDDAKBgNVBAcMA1RUVDEMMAoGA1UECgwDVFRUMQwwCgYDVQQLDANUVFQx
DTALBgNVBAMMBFRFU1QwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQC6
t4uamaIt7iXZCx8fTwdEo3EC/uCAo6WZyJI0ciqS+T6GE0hxhprlJcRcpcIRd6oK
1s4jQsAeeZxHs1K0WJX58lP7+u7LaVlGr0wAcZFdMBnO8t7jNVrnzViEGame1Iqq
Jc8PnPrnO7RSjRM0azAoK0+SASr3iM/laM8sMnBlWlkdUu5xvVYnwt+YVhNNNLyf
YEyqqVmyy8HM9RZ8tJu9igeLTmyUld2ufeyKY1O2uMX+5oyE0x6eNpmeOZEaGWNr
vZcIfOAngcb/Z4wHD6n6sdidBG8ZYKg3EDAUErwiZTK0uYGgIMviZf2bWFzgAN5g
wp948qQu5CAewrhF0h7do0wtEzf5nRyXG28j5T8/kfI2rSjlRIyMaa7V3E0/ZcDD
RKvFdfXZ4iLAvt/Ca3bexrxzW4m5M3Y1ruSwHf3dOZDrDiscCYkFc4dava2FWcnn
NAzwBpYFi3Io/H+9HOZ1HP8G5aE9eR6cGDHQWmhzxl3Sz1F9GEeMRSJj64cRKAZP
UFAJon6kpc2qn6bs6GIkt3ixq70bs3diJ0jo549735v7alsrk3Mv9ubtE8YByFZU
NI12QdFpsEQg0giIfufyvE02fBVNp2R7DLwv1EJoqLmeWpSS4HF5qWlLtMCl9/vA
OFfkHWQF5E+PyCLniF0u71SAtD4aMR1v2MSNGTsE7QIDAQABo1MwUTAdBgNVHQ4E
FgQUUedWkBX/cpMPkEKvHGcCZ7TDG9QwHwYDVR0jBBgwFoAUUedWkBX/cpMPkEKv
HGcCZ7TDG9QwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQ0FAAOCAgEAGXms
kzeKPx+xNDLUrD2kTVaY1y9F82RpHymDAW2KXKbv4OAlP2m2iYrsDSXevKhV4K04
eG/uVQQ0owM+da4Hr8FKeIzktoNgFoQKXbYm4DU3NsqYlHSjX2xtVGq2qkqEcaeb
LtVEXKyvvmaQOm2Co5vMH3NTJyO3kCE2U7XqlOb+fo0XhY4r9ZIoCF1uBNTKz6uu
jSjEX1MUSBND9Lr7CZx/t8Rrf1dEek0KzKJkn+SsKbaVe2Yak/NfFO9/SOgMTo/B
//X5TEtu6vAV1yXqnwoKS/hwm+9cEjFxn7kIGpMQjRjno2uuYCTt30Ttu8Tj3T0r
L9xOvUNp0PuDGK7xn5b76LKpFN2IeQIvkF2AdNY74+oup4d6wS1D1zbtEJG2zX5m
/2uL6ZlFjqcTTY2qj40wz1eSNDHnRbSPpU7k+jZtoeKklP2+mUXAZZpQemJiidte
um6A/NleqlzmWeYH2wTf6HpFAHuWQD9bIJMaWR0CNuJiZH4VUL4x+FqP61XrxOLU
BqQFxY+X1eD4GZxzfQue9hDM6MTrOPA3hEXJCkMe0vxffAGgLSq2VzA50o7ZuJaU
gwWZa9q2dQRiZyKrtAFiIlXVO1Ro1QndRR3OKDbHDZMYsjYYwU5kT34adGqtYXOt
jqIsRe+PqAGHV5asQJTIWen47BSwugZas4tsuQo=
-----END CERTIFICATE-----
"""
    key = """-----BEGIN PRIVATE KEY-----
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
skhqZ7n/kpFy2Vio+fjmagtNFrv1
-----END PRIVATE KEY-----
"""
    cafile = path / "ca.pem"
    cafile.write_text(ca, encoding="utf-8")

    certfile = path / "cert.pem"
    certfile.write_text(key+cert, encoding="utf-8")

    # keyfile = path / "key.pem"
    # keyfile.write_text(key, encoding="utf-8")


def test_create():
    listener = Listener("test", "0.0.0.0", 16004, True, False, True)
    assert listener.name == "test"
    assert listener.lhost == "0.0.0.0"
    assert listener.lport == 16004
    assert listener.state == "Unknown"
    assert listener.autorun is True
    assert listener.drop_duplicates is False
    assert listener.ssl_enabled is True
    assert listener.ssl_context.verify_mode is ssl.VerifyMode.CERT_REQUIRED


def test_create_exception():
    with pytest.raises(ValueError):
        _ = Listener("test space name", "0.0.0.0", 8080)
        _ = Listener("test", "0.0.0.0", "test port error")
        _ = Listener("test", "0.0.0.0", 0xFFFFFF)
        _ = Listener("test", "0.0.0.0", -1)


def test_load_certs(tmp_path):
    listener = Listener("test", "0.0.0.0", 16004, True, False, True)
    assert listener.load_ca("/tmp/not-exists") is False
    assert listener.load_cert("/tmp/not-exists") is False
    assert listener.load_cert("/tmp/not-exists", "/tmp/not-exists") is False

    drop_cert(tmp_path)
    assert listener.load_ca(str(tmp_path / "ca.pem")) is True
    assert listener.load_cert(str(tmp_path / "cert.pem")) is True
    # assert listener.load_cert(str(tmp_path / "cert.pem"), str(tmp_path / "key.pem")) is True


def test_start_stop(tmp_path):
    listener = Listener("test", "0.0.0.0", 16004, True, False, True)
    assert listener.state == "Unknown"

    drop_cert(tmp_path)
    listener.load_ca(tmp_path / "ca.pem")
    listener.load_cert(tmp_path / "cert.pem")
    assert listener.state == "Stopped"
    listener.start()
    assert listener.state == "Running"
    listener.restart()
    assert listener.state == "Running"
    listener.stop()
    assert listener.state == "Stopped"


def test_conversion():
    d = {'name': 'test', 'lhost': '0.0.0.0', 'lport': 16004, 'ssl': True, 'ca': [], 'cert': [], 'autorun': True, 'drop_duplicates': False}
    listener = Listener("test", "0.0.0.0", 16004, True, False, True)
    assert str(listener) == "test <0.0.0.0:16004>"
    assert listener.to_dict() == d


def test_double_start_stop():
    listener = Listener("test", "0.0.0.0", 16004)
    listener.start()
    with pytest.raises(ListenerStartError):
        listener.start()
    listener.stop()
    with pytest.raises(ListenerStopError):
        listener.stop()

