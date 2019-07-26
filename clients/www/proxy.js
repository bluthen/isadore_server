//Base: https://gist.github.com/Anks/3402241


if(process.argv.length < 6) {
    console.log('Usage: '+process.argv[0]+' '+process.argv[1]+' [proxied_hostname] [proxied_port] [secure] [listen_port]');
    return;
}


var httpProxy = require('http-proxy');
var connect = require('connect');
var http = require('http');
var serveIndex = require('serve-index');
var serveStatic = require('serve-static');
var morgan = require('morgan');


var secure = true;
var prefix = '/isadore'
var listenPort = 4242;
var rpServerPort = 80;

if (secure) {
    rpServerPort = 443;
}

var rpServer = process.argv[2];
rpServerPort = parseInt(process.argv[3]);
secure = process.argv[4] == 'true';
listenPort = parseInt(process.argv[5]);

rpServer = (secure ? 'https://' : 'http://') + rpServer+":"+rpServerPort;


var endpoint = {
      target: rpServer,
      ssl: secure,
      prefix: prefix
};
var staticDir = 'src';

var index = serveIndex(staticDir, {'icons': true});
var serve = serveStatic(staticDir);

var proxy = httpProxy.createProxyServer({target: {https: (secure ? true : false)}, changeOrigin: true});
var app = connect().use(morgan('dev')).use(
    function(req, res, next) {
        if (req.url.indexOf(endpoint.prefix) === 0) {
            proxy.web(req, res, {target: rpServer, secure: (secure ? true : false)});
        } else {
            next();
        }
    }).use(serve).use(serveIndex(staticDir, {'icons': true}));
http.createServer(app).listen(listenPort);
//http.createServer(app).listen(listenPort);

console.log('Listening on http://0.0.0.0:'+listenPort);
console.log('Proxing '+prefix+' to '+ rpServer);
// http://localhost:4242/api/test will give response
// from http://your-app-domain.com/api/test 
