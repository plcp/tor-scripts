SOURCES=\
src/header.js src/endpoint.js src/get.js src/ntor.js src/relay.js src/onion.js\
src/io.js src/post.js src/stream.js src/util.js src/api.js src/export.js

BUNDLELICENSE=LICENSE.bundle.txt
BUNDLES=\
cleanup-bundle tweetnacl-bundle sjcl-bundle lighttor-bundle\
lighttor-bundle-license tweetnacl-bundle-license sjcl-bundle-license

COMPRESSOR=./sjcl/compress/compress_with_closure.sh
