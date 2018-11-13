var cdn_host = "http://127.0.01:8887/cdn/",
      data_host = "http://127.0.01:8887/data/"

async function load_libraries () {
    libraries = [
        "papaparse.min.js",
        "topojson.v1.min.js",
        "crossfilter.min.js",
        "d3.v3.min.js",
        "d3.tip.v0.6.3.js",
        "jsoneditor-minimalist.min.js",
        "hash.js"
    ]
    for(let url of libraries) {
        await fetch(cdn_host+url).then(res => res.text()).then(eval)
    }
}
load_libraries()

data = new Hash({url, id})

function YapMap({data_url, id_col, map_div, metric_selector, dimensions, metrics, pigments, descending_metrics, geo_file}) {
    //this.data_url = data_url || data_host + "latest housing valuation.csv"
    this.id_col= id_col || 'Fips'
    this.map_div= map_div || "#yap-canvas"
    this.metric_selector= metric_selector || "#metrics" 
    this.dimensions= dimensions || ['State', 'County']
    this.metrics= metrics
    this.pigments= pigments || ['red', 'green']
    this.descending_metrics= descending_metrics
    this.geo_file= geo_file || data_host + "us-counties.geo.json"
    //data_type: "", //|| data_url.split('.').pop(),
}

YapMap.prototype.readDataFile = function (selector) {
    document.querySelector(selector).onchange = (e) => {  
        file = e.target.files[0]
        e.target.value = null // HACK: to trigger onchange when the same file is selected
        this.fileName = file.name
        var reader = new FileReader()
        reader.readAsText(file)
        //this.dataStatus = reader.readyState
        reader.onload = (e) => {
            //this.dataStatus = reader.readyState
            papa = Papa.parse(e.target.result, {dynamicTyping: true, header: true})
            this.data = arraysToDF({data: papa.data, id_col: this.id_col})
            this.draw()
        }
    }
    return this
}

YapMap.prototype.drawDataUrl = function (data_url) {
    return fetch(data_url)
        .then(res => res.text())
        .then(text => Papa.parse(text, {header: true, dynamicTyping: true}))
        .then(papa => papa.data)
        .then(data => arraysToDF({data, id_col: this.id_col}))
        .then(this.draw())
}

function arraysToDF({data, id_col}) {
    vars = Object.keys(data[0])
    let dataframe = {};
    vars.forEach(v => dataframe[v] = new Map())
    data.forEach(row => {
        id = row[id_col]
        vars.forEach(v => {
            series = dataframe[v]
            value = row[v]
            series.set(id, value)
        })
    })
    return dataframe
}


function obj (x) {
    this.x = x
}

obj.prototype.f= function (y) {
    console.log(y+this.x)
}

a = new obj(1)
b = new obj(2)


/*
function YapMap (conf) {
    config = {...config, ...conf}
    load(config)
    .then(data => yapper({...config, ...data, loc: config['map_div']}))
    .then(yap => {
        draw({...yap, y_col: yap['metrics'][0]})
        drop_down({
            elem: document.querySelector(yap['metric_selector']), 
            options: yap['metrics'], 
            func: y_col => {yap['y_col']= y_col; draw(yap)}
        })
    })
}

/// functions
async function load ({data_url, geo_file, id_col}) {
    // load libraries sequently
    for(let url of scripts) {
        await fetch(cdn_host+url).then(res => res.text()).then(eval)
    }

    var dataframe = await fetch(data_host + data_url)
        .then(res => Papa.parse(res.text(), {header: true, dynamicTyping: true}))
        .then(papa => arraysToDataframe({data: papa.data, id_col}))

    var geos = await fetch(data_host + geo_file)
        .then(res => res.json())
    
    return {geos, dataframe}
}

function yapper ({geos, dataframe, dimensions, metrics, loc}) {
    yap = {...config, dataframe}
    yap['counties_geos'] = topojson.feature(geos, geos.objects['counties']).features
    yap['states_geos'] = topojson.feature(geos, geos.objects['states']).features
    tip = d3.tip().attr('class', 'yap-tip').offset([0,0]).html(tipper({dataframe, dimensions, metrics}))

    d3.select(loc + '_draw__').remove() // for redraw clear previous one
    yap['svg'] = d3.select(loc)
        .classed("yap-canvas", true)
        .append("svg")
        .attr('id', loc.substr(1) + '_draw__')        
        .attr('viewBox', viewBox(yap['states_geos']).join(' '))
        .attr('preserveAspectRatio', 'xMinYMin')
        .call(tip)

    yap['dimensions'] = dimensions
    yap['metrics'] = metrics
    return yap
}

function draw ({svg, dataframe, counties_geos, states_geos, y_col, pigments, descending_metrics, filters}) {
    let colorscale = [...pigments]
    if (descending_metrics.includes(y_col)) colorscale.reverse()

    draw_and_color({svg, colorscale, geos: counties_geos, ranks: toQuantile(dataframe[y_col]), klass: 'border0'})
    draw_path({svg, geos: states_geos, klass: 'border1'})
}

function toQuantile (series) {
    quantiles = new Map()
    var sorted_values = [...series.values()].sort((a,b) => a-b);
    N = sorted_values.length
    series.forEach((value,key) => quantiles.set(key, sorted_values.indexOf(value)/N)) // trick: (sorted) values.indexOf(y)/N gives quantile 
    return quantiles
}

function tipper({dataframe, dimensions, metrics}) {
    return geo => dimensions.map(col => dataframe[col].get(geo.id))
        .filter(x=>x !== undefined)
        .join(', ')
    + "<br>"
    + metrics.map(val => val + ": " + dataframe[val].get(geo.id)).join('<br>')
} 

function draw_path({svg, geos, klass}) {
    let path = d3.geo.path()
    svg.append("g")
        .attr("class", klass || 'border1')
        .selectAll("path")
        .data(geos)
        .enter()
        .append("path")
        .attr("d", path)
}

function draw_and_color({svg, geos, ranks, klass, colorscale}) {
    let path = d3.geo.path()
    coloring = a => a!=undefined && d3.interpolateHsl(...colorscale)(a)
    svg.append("g")
    .attr("class", klass || "border0")
    .selectAll("path")
    .data(geos)
    .enter()
    .append("path")
    .attr("d", path)
    .attr("id", geo => geo.id)
    .attr("fill", geo => coloring(ranks.get(geo.id))) //fill with mapped colors
    .on('mouseover.tip', tip.show)
    .on('mouseout', tip.hide)
}

function arraysToDataframe({data, id_col}) {
    vars = Object.keys(data[0])
    let dataframe = {};
    vars.forEach(v => dataframe[v] = new Map())
    data.forEach(row => {
        id = row[id_col]
        vars.forEach(v => {
            series = dataframe[v]
            value = row[v]
            series.set(id, value)
        })
    })
    return dataframe
}

function viewBox(geos) {
    let path = d3.geo.path()
    boxes = geos.map(path.bounds) //get all path bounds in coordinates
    coordinates = flatten_nested_geos_to_coordinates(boxes) // flatten to get coordinates
    coordinates_x = coordinates.map(coordinate=>coordinate[0]).filter(isFinite)// seperate x eletemts and filter finites
    coordinates_y = coordinates.map(coordinate=>coordinate[1]).filter(isFinite)// separet y elements and filter finites
    box = [Math.min(...coordinates_x)//x
    , Math.min(...coordinates_y)//y
    , Math.max(...coordinates_x) - Math.min(...coordinates_x)//width
    , Math.max(...coordinates_y) - Math.min(...coordinates_y)//height
    ]
    return box.map(Math.round)
}


function flatten_nested_geos_to_coordinates(arr) {
    const flat = [].concat(...arr);
    return flat.some(Array.isArray) ? flatten_nested_geos_to_coordinates(flat) : arr;
}

function drop_down ({elem, options, func}) {
    if (elem) {
        elem.innerHTML = ''
        options.forEach(val => {
            option = document.createElement('option');
            option.text = option.value = val; 
            elem.appendChild(option)
        })
        elem.onchange = e => func(e.target.value)
    }
}


/*

//// functions for future use

function draw_legend({legend, values, colorscale}) {
    bar_width = 5;//in em
    //var legend = d3.select(legend_div).classed("yap-caption", true)
    //legend.html(y_col + "&nbsp");
    for (var i = 0; i < colorscale.length; i++) {
        //for each color create a rect, color it, text it, style it
        d3.select('#yap-legend')
        .append("rect")
        .attr("style", "background-color: " + colorscale[i])
        .html(d3.quantile(values, i / colorscale.length).toFixed(1))
    };
}

function info_table(geo) {
    key_value = []
    dataframe.forEach((v,k) => key_value.push([k,v.get(geo.id)]))
    spans = key_value.map(x => '<span>' + x[0] +'</span>' + '<span style="position: absolute; right:1em;" >' + x[1] +'</span> <br>')
    info.innerHTML = spans.join('')
}


function filter (yap) {
    filterBy = document.createElement('select')
    filterValue = document.createElement('select')

    elem = document.querySelector('#dimensions')
    elem.appendChild(filterBy)
    elem.appendChild(filterValue)

    drop_down ({elem: filterBy, options: ['filter by', ...config['dimensions']], func: dimension => {
        dim = yap['dataframe'][dimension]
        levels = ['no filter', ...new Set(dim.values())]
        drop_down({elem: filterValue, options: levels, func: level => {
            yap['filter'] = []
            dim.forEach((y, fips) => {if (dimension==y) yap['filter'].push(fips)})
            console.log(yap)
            draw(yap)
        }})
    }})
}


*/
