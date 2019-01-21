/*
    Hash extands Map in JS to have functionalities similar to Python's Panda DataFrame
    Basic Usage:
    hash = new Hash ({url, metrics, dimensions, id}, initialArray)
    hash.filter((val, id) => )
    hash.map((val, id) => val)
    hash.reduce((val, id) => )
    hash.info({metrics, filter_ids, subset})
    hash.unfo({filter_ids})
    hash.clean()
    hash.info({clean: true})
    hash.reset()

Example:
var cdn_host = "http://127.0.01:8887/cdn/",
      data_host = "http://127.0.01:8887/data/"
url = data_host + "latest housing valuation.csv"
id = 'Fips'
hash = new Hash({id, url})
*/


async function load_libraries () {
    libraries = [
        "papaparse.min.js",
        //"topojson.v1.min.js",
        //"crossfilter.min.js",
        //"d3.v3.min.js",
        //"d3.tip.v0.6.3.js",
        //"jsoneditor-minimalist.min.js"
    ]
    for(let url of libraries) {
        await fetch(cdn_host+url).then(res => res.text()).then(eval)
    }
}
load_libraries()


class Hash extends Map {
    constructor ({url, text, array, id, metrics, dimensions}, arr) {
        super(arr)
        this.info({id, metrics, dimensions})
        var parser = 'fromCSV'
        if (url) {
            fetch(url)
                .then(res => res.text())
                .then(text => Papa.parse(text, {dynamicTyping: true, header: true}))
                .then(papa => this[parser](papa.data))
                return
        }
    }
}

Hash.prototype.fromCSV = function (data) {
    let id = this._.id
    console.log(id)
    data.forEach(row => {
        this.set(row[id], row)
    })
    return this
}

Hash.prototype.info = function (obj) {
    this._ = {...this._, ...obj}
    return this
}


Hash.prototype.unfo = function (keys) {
    keys.forEach(k => delete this._[k])  
    return this
}


