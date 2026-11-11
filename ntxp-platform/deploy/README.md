Draft, untested compose: one image running every view behind the hub. **Not deployed.** Before use: build an image
that installs all four packages, confirm each app's `serve` flags (`ntxp serve-http`, `ntxp-contracts serve-web`,
`ntxp-apilog serve`), set `NTXP_HUB_TOKEN`, per-app DB settings, and the apilog `NTXP_APILOG_KEY`. Keep apilog's
data volume separate from the others.
