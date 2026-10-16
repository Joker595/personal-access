{{ if ne .Type "user" }}{{ fail "user certificates only" }}{{ end }}
{{ if not .Token.sub }}{{ fail "immutable subject required" }}{{ end }}
{
  "type": "user",
  "keyId": {{ toJson .Token.sub }},
  "principals": [{{ toJson .Token.sub }}],
  "extensions": {"permit-pty": "", "permit-port-forwarding": ""},
  "criticalOptions": {}
}
