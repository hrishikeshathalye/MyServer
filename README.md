<h1 align="center">MyServer</h1>

<div align="center">
  :globe_with_meridians:
</div>
<div align="center">
  <strong>A minimal, multithreaded HTTP/1.1 compliant Webserver</strong>
</div>
<br />

<div align="center">
  
 [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  
 [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
 
 ![Version](https://img.shields.io/badge/version-1.0-blue])
 
<div>
  
<div align="center">
  <sub>Built by
  <a href="https://github.com/hrishikeshathalye">Hrishikesh Athalye</a> and
  <a href="https://github.com/shaunak27">Shaunak Halbe</a>  
</div>

## Table of Contents
- [Features](#features)
- [Installation And Usage](#usage)
- [Config](#config)
- [Testing](#testing)
- [Logs](#logs)
- [Acknowledgements](#config)

## Features
1. Supports 5 common HTTP methods - GET, POST, PUT, DELETE and HEAD
2. Multithreaded
3. Explicit configuration options
4. Level based logging support
5. Support for cookies
6. Automated basic testing

## Installation And Usage
1. Install all required packages using "pip3 install -r requirements.txt"
2. Start the server using "python3 server.py port_no" , where port_no can be any valid port number. Not giving a port number will cause the server socket to bind to any available port. To bind to port numbers < 1024 prefixing the command with sudo is required.
3. To stop or restart the server just type "stop" or "restart" into the terminal window where the server is running and press enter. A thread that continuously keeps waiting for input takes this input and stops/restarts the server.
4. Server configuration options are available in the myserver.conf file in the conf directory.
5. Access Log, Error Log and Post Data Logs are located in the log directory. If not already present the server will create them.
(Being a general purpose web server, default behaviout for POST is to log POST data to PostDataLog.log)

## Config
Locate the file myserver.conf in the conf directory. The meanings of the various configuration options are as follows:

1. DocumentRoot : The folder where get requests are served from and where PUT requests store data. The value against this filed will indicate the location of the document root relative to the working directory of the project.

2. ErrorPages : Custom error pages can be put into this directory, error indicating status codes (Eg: 400, 404, etc) will be sent with body as pages put in this directory. If this directory does not contain status codes for some errors, a blank body will be sent for those.

3. MaxSimultaneousConnections : Maximum number of connections that can be handled at once, connections more than this will queue and if queue size is full no connection can be made. If set to 1, the server will essentially behave like a single threaded server.

4. QueueSize : The maximum number of connections that will be queued once maximum simultaenous connections have been reached

5. RequestTimeout : Timeout for requests. Since the server is capable of handling requests made line-by-line (telnet like fashion), this indicates the maximum amount of time the server will wait before terminating the connection once inactivity is detected. The timer resets after each line typed by the client, if request is being made line-by-line. This ensures the server isn't being kept hanging by a client who has initiated a connection but is taking too long to request. 

6. ServerCloseTimeout : Timeout to wait for requests to complete once a "stop" is given. If all requests are served before this timeout, server will stop immediately. else it will wait for a maximum time specified here, if requests do not complete within this time, the server still closes the connection immediately. This takes care of hanging threads and sets a hard limit on the timeout that the server will wait for.

7. LogDir : Directory where log files are stored. (log by default)

8. ErrorLog : Name of the error log file name. (error.log by default)

9. AccessLog : Name of access log file name. (access.log by default)

10. PostDataLog :  Name of file where log of POST data is stored. (postData.log by default)

11. Log Level : Only errors of severity equal to and above this level will be logged into error.log. Can be one of - CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET (NOTSET by default)

## Components
From time to time there will arise a need to have an element in an application
hold a self-contained state or to not rerender when the application does. This
is common when using 3rd party libraries to e.g. display an interactive map or a
graph and you rely on this 3rd party library to handle modifications to the DOM.
Components come baked in to Choo for these kinds of situations. See
[nanocomponent][nanocomponent] for documentation on the component class.

```javascript
// map.js
var html = require('choo/html')
var mapboxgl = require('mapbox-gl')
var Component = require('choo/component')

module.exports = class Map extends Component {
  constructor (id, state, emit) {
    super(id)
    this.local = state.components[id] = {}
  }

  load (element) {
    this.map = new mapboxgl.Map({
      container: element,
      center: this.local.center
    })
  }

  update (center) {
    if (center.join() !== this.local.center.join()) {
      this.map.setCenter(center)
    }
    return false
  }

  createElement (center) {
    this.local.center = center
    return html`<div></div>`
  }
}
```

```javascript
// index.js
var choo = require('choo')
var html = require('choo/html')
var Map = require('./map.js')

var app = choo()
app.route('/', mainView)
app.mount('body')

function mainView (state, emit) {
  return html`
    <body>
      <button onclick=${onclick}>Where am i?</button>
      ${state.cache(Map, 'my-map').render(state.center)}
    </body>
  `

  function onclick () {
    emit('locate')
  }
}

app.use(function (state, emitter) {
  state.center = [18.0704503, 59.3244897]
  emitter.on('locate', function () {
    window.navigator.geolocation.getCurrentPosition(function (position) {
      state.center = [position.coords.longitude, position.coords.latitude]
      emitter.emit('render')
    })
  })
})
```

### Caching components
When working with stateful components, one will need to keep track of component
instances – `state.cache` does just that. The component cache is a function
which takes a component class and a unique id (`string`) as its first two
arguments. Any following arguments will be forwarded to the component constructor
together with `state` and `emit`.

The default class cache is an LRU cache (using [nanolru][nanolru]), meaning it
will only hold on to a fixed amount of class instances (`100` by default) before
starting to evict the least-recently-used instances. This behavior can be
overriden with [options](#app--chooopts).

## Optimizations
Choo is reasonably fast out of the box. But sometimes you might hit a scenario
where a particular part of the UI slows down the application, and you want to
speed it up. Here are some optimizations that are possible.

### Caching DOM elements
Sometimes we want to tell the algorithm to not evaluate certain nodes (and its
children). This can be because we're sure they haven't changed, or perhaps
because another piece of code is managing that part of the DOM tree. To achieve
this `nanomorph` evaluates the `.isSameNode()` method on nodes to determine if
they should be updated or not.

```js
var el = html`<div>node</div>`

// tell nanomorph to not compare the DOM tree if they're both divs
el.isSameNode = function (target) {
  return (target && target.nodeName && target.nodeName === 'DIV')
}
```

### Reordering lists
It's common to work with lists of elements on the DOM. Adding, removing or
reordering elements in a list can be rather expensive. To optimize this you can
add an `id` attribute to a DOM node. When reordering nodes it will compare
nodes with the same ID against each other, resulting in far fewer re-renders.
This is especially potent when coupled with DOM node caching.

```js
var el = html`
  <section>
    <div id="first">hello</div>
    <div id="second">world</div>
  </section>
`
```

### Pruning dependencies
We use the `require('assert')` module from Node core to provide helpful error
messages in development. In production you probably want to strip this using
[unassertify][unassertify].

To convert inlined HTML to valid DOM nodes we use `require('nanohtml')`. This has
overhead during runtime, so for production environments we should unwrap this
using the [nanohtml transform][nanohtml].

Setting up browserify transforms can sometimes be a bit of hassle; to make this
more convenient we recommend using [bankai build][bankai] to build your assets for production.

## FAQ
### Why is it called Choo?
Because I thought it sounded cute. All these programs talk about being
_"performant"_, _"rigid"_, _"robust"_ - I like programming to be light, fun and
non-scary. Choo embraces that.

Also imagine telling some business people you chose to rewrite something
critical for serious bizcorp using a train themed framework.
:steam_locomotive::train::train::train:

### Is it called Choo, Choo.js or...?
It's called "Choo", though we're fine if you call it "Choo-choo" or
"Chugga-chugga-choo-choo" too. The only time "choo.js" is tolerated is if /
when you shimmy like you're a locomotive.

### Does Choo use a virtual-dom?
Choo uses [nanomorph][nanomorph], which diffs real DOM nodes instead of
virtual nodes. It turns out that [browsers are actually ridiculously good at
dealing with DOM nodes][morphdom-bench], and it has the added benefit of
working with _any_ library that produces valid DOM nodes. So to put a long
answer short: we're using something even better.

### How can I support older browsers?
Template strings aren't supported in all browsers, and parsing them creates
significant overhead. To optimize we recommend running `browserify` with
[nanohtml][nanohtml] as a global transform or using [bankai][bankai] directly.
```sh
$ browserify -g nanohtml
```

### Is choo production ready?
Sure.

## API
This section provides documentation on how each function in Choo works. It's
intended to be a technical reference. If you're interested in learning choo for
the first time, consider reading through the [handbook][handbook] first
:sparkles:

### `app = choo([opts])`
Initialize a new `choo` instance. `opts` can also contain the following values:
- __opts.history:__ default: `true`. Listen for url changes through the
  history API.
- __opts.href:__ default: `true`. Handle all relative `<a
  href="<location>"></a>` clicks and call `emit('render')`
- __opts.cache:__ default: `undefined`. Override default class cache used by
  `state.cache`. Can be a a `number` (maximum number of instances in cache,
  default `100`) or an `object` with a [nanolru][nanolru]-compatible API.
- __opts.hash:__ default: `false`. Treat hashes in URLs as part of the pathname,
  transforming `/foo#bar` to `/foo/bar`. This is useful if the application is
  not mounted at the website root.

### `app.use(callback(state, emitter, app))`
Call a function and pass it a `state`, `emitter` and `app`. `emitter` is an instance
of [nanobus](https://github.com/choojs/nanobus/). You can listen to
messages by calling `emitter.on()` and emit messages by calling
`emitter.emit()`. `app` is the same Choo instance. Callbacks passed to `app.use()` are commonly referred to as
`'stores'`.

If the callback has a `.storeName` property on it, it will be used to identify
the callback during tracing.

See [#events](#events) for an overview of all events.

### `app.route(routeName, handler(state, emit))`
Register a route on the router. The handler function is passed `app.state`
and `app.emitter.emit` as arguments. Uses [nanorouter][nanorouter] under the
hood.

See [#routing](#routing) for an overview of how to use routing efficiently.

### `app.mount(selector)`
Start the application and mount it on the given `querySelector`,
the given selector can be a String or a DOM element.

In the browser, this will _replace_ the selector provided with the tree returned from `app.start()`.
If you want to add the app as a child to an element, use `app.start()` to obtain the tree and manually append it.

On the server, this will save the `selector` on the app instance.
When doing server side rendering, you can then check the `app.selector` property to see where the render result should be inserted.

Returns `this`, so you can easily export the application for server side rendering:

```js
module.exports = app.mount('body')
```

### `tree = app.start()`
Start the application. Returns a tree of DOM nodes that can be mounted using
`document.body.appendChild()`.

### `app.toString(location, [state])`
Render the application to a string. Useful for rendering on the server.

### `choo/html`
Create DOM nodes from template string literals. Exposes
[nanohtml](https://github.com/choojs/nanohtml). Can be optimized using
[nanohtml][nanohtml].

### `choo/html/raw`
Exposes [nanohtml/raw](https://github.com/shama/nanohtml#unescaping) helper for rendering raw HTML content.

## Installation
```sh
$ npm install choo
```

## See Also
- [bankai](https://github.com/choojs/bankai) - streaming asset compiler
- [stack.gl](http://stack.gl/) - open software ecosystem for WebGL
- [yo-yo](https://github.com/maxogden/yo-yo) - tiny library for modular UI
- [tachyons](https://github.com/tachyons-css/tachyons) - functional CSS for
  humans
- [sheetify](https://github.com/stackcss/sheetify) - modular CSS bundler for
  `browserify`

## Support
Creating a quality framework takes a lot of time. Unlike others frameworks,
Choo is completely independently funded. We fight for our users. This does mean
however that we also have to spend time working contracts to pay the bills.
This is where you can help: by chipping in you can ensure more time is spent
improving Choo rather than dealing with distractions.

### Sponsors
Become a sponsor and help ensure the development of independent quality
software. You can help us keep the lights on, bellies full and work days sharp
and focused on improving the state of the web. [Become a
sponsor](https://opencollective.com/choo#sponsor)

<a href="https://opencollective.com/choo/sponsor/0/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/1/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/2/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/3/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/3/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/4/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/5/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/6/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/7/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/7/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/8/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/9/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/9/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/10/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/10/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/11/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/11/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/12/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/12/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/13/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/13/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/14/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/14/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/15/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/15/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/16/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/16/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/17/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/17/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/18/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/18/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/19/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/19/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/20/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/20/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/21/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/21/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/22/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/22/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/23/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/23/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/24/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/24/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/25/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/25/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/26/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/26/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/27/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/27/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/28/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/28/avatar.svg"></a>
<a href="https://opencollective.com/choo/sponsor/29/website" target="_blank"><img src="https://opencollective.com/choo/sponsor/29/avatar.svg"></a>

### Backers
Become a backer, and buy us a coffee (or perhaps lunch?) every month or so.
[Become a backer](https://opencollective.com/choo#backer)

<a href="https://opencollective.com/choo/backer/0/website" target="_blank"><img src="https://opencollective.com/choo/backer/0/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/1/website" target="_blank"><img src="https://opencollective.com/choo/backer/1/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/2/website" target="_blank"><img src="https://opencollective.com/choo/backer/2/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/3/website" target="_blank"><img src="https://opencollective.com/choo/backer/3/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/4/website" target="_blank"><img src="https://opencollective.com/choo/backer/4/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/5/website" target="_blank"><img src="https://opencollective.com/choo/backer/5/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/6/website" target="_blank"><img src="https://opencollective.com/choo/backer/6/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/7/website" target="_blank"><img src="https://opencollective.com/choo/backer/7/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/8/website" target="_blank"><img src="https://opencollective.com/choo/backer/8/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/9/website" target="_blank"><img src="https://opencollective.com/choo/backer/9/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/10/website" target="_blank"><img src="https://opencollective.com/choo/backer/10/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/11/website" target="_blank"><img src="https://opencollective.com/choo/backer/11/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/12/website" target="_blank"><img src="https://opencollective.com/choo/backer/12/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/13/website" target="_blank"><img src="https://opencollective.com/choo/backer/13/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/14/website" target="_blank"><img src="https://opencollective.com/choo/backer/14/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/15/website" target="_blank"><img src="https://opencollective.com/choo/backer/15/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/16/website" target="_blank"><img src="https://opencollective.com/choo/backer/16/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/17/website" target="_blank"><img src="https://opencollective.com/choo/backer/17/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/18/website" target="_blank"><img src="https://opencollective.com/choo/backer/18/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/19/website" target="_blank"><img src="https://opencollective.com/choo/backer/19/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/20/website" target="_blank"><img src="https://opencollective.com/choo/backer/20/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/21/website" target="_blank"><img src="https://opencollective.com/choo/backer/21/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/22/website" target="_blank"><img src="https://opencollective.com/choo/backer/22/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/23/website" target="_blank"><img src="https://opencollective.com/choo/backer/23/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/24/website" target="_blank"><img src="https://opencollective.com/choo/backer/24/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/25/website" target="_blank"><img src="https://opencollective.com/choo/backer/25/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/26/website" target="_blank"><img src="https://opencollective.com/choo/backer/26/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/27/website" target="_blank"><img src="https://opencollective.com/choo/backer/27/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/28/website" target="_blank"><img src="https://opencollective.com/choo/backer/28/avatar.svg"></a>
<a href="https://opencollective.com/choo/backer/29/website" target="_blank"><img src="https://opencollective.com/choo/backer/29/avatar.svg"></a>

## License
[MIT](https://tldrlegal.com/license/mit-license)

[nanocomponent]: https://github.com/choojs/nanocomponent
[nanolru]: https://github.com/s3ththompson/nanolru
[bankai]: https://github.com/choojs/bankai
[nanohtml]: https://github.com/choojs/nanohtml
[browserify]: https://github.com/substack/node-browserify
[budo]: https://github.com/mattdesl/budo
[es2020]: https://github.com/yoshuawuyts/es2020
[handbook]: https://github.com/yoshuawuyts/choo-handbook
[hyperx]: https://github.com/substack/hyperx
[morphdom-bench]: https://github.com/patrick-steele-idem/morphdom#benchmarks
[nanomorph]: https://github.com/choojs/nanomorph
[nanorouter]: https://github.com/choojs/nanorouter
[yo-yo]: https://github.com/maxogden/yo-yo
[unassertify]: https://github.com/unassert-js/unassertify
[window-performance]: https://developer.mozilla.org/en-US/docs/Web/API/Performance
