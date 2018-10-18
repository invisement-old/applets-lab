
var geos, tmp, path, quants, svg, tip, color, colorscale
const cdn_host = "http://127.0.01:8887/cdn/",
      data_host = "http://127.0.01:8887/data/"

const config = {
    data_file: data_host+"latest housing valuation.csv",
    id_col: 'FIPS',
    name_cols: ['County', 'State'],
    y_col: 'Total Return',
    value_cols: ['Total Return', 'Net Annual Return'],
    quant: 'scaleQuantile',
    colors: ['red', 'green'],
    number_of_colors: 7,
    legend_div: "#map-legend",
    map_div: "#main-map",
    info_table: "#info-table",
    data_type: "",
    geo_file: cdn_host+"us-counties.geo.json",
}

config.data_type = config.data_type || config.data_file.split('.').pop();

scripts = [
    "papaparse.min.js",
    "topojson.v1.min.js",
    "crossfilter.min.js",
    "d3.v3.min.js",
    "d3.tip.v0.6.3.js",
];

async function loadScripts (scripts) {
    for(let url of scripts) {
        await $.getScript(cdn_host + url)
    }
}

loadScripts(scripts).then(init)


function init () {
    path = d3.geo.path()
    quants = d3.scale.quantile()
    svg = d3.select(config.map_div).append("svg")//.attr("class", "yap-map")
    tip = d3.tip().attr('class', 'yap-tip').offset([-10,0])

    color = d3.scale.linear().domain(config['colors'].map((a,i)=>i)).interpolate(d3.interpolateHsl).range(config['colors']);

    colorscale = []
    for (var i = 0; i <= config['colors'].length - 1; i = i + (config['colors'].length - 1) / (config['number_of_colors'] - 1)) {
        colorscale.push(color(i));
    }

    dataPromise = fetch(config.data_file)
        .then(res => res.text())
        .then(text => Papa.parse(text, {header: true, dynamicTyping: true}))
        .then(papa => create_dataframe(papa.data, config.id_col))

    geoPromise = fetch(config.geo_file)
        .then(res => res.json())

    Promise.all([dataPromise, geoPromise])
        .then(results => ready(...results))

}


//// Functions ////
function ready(dataframe, geos) {
    counties_geos = topojson.feature(geos, geos.objects['counties']).features
    states_geos = topojson.feature(geos, geos.objects['states']).features

    tip.html(function(geo) {
        return config['name_cols'].map(col => dataframe.get(col).get(geo.id))
                    .filter(x=>x !== undefined)
                    .join(', ')
               + "<br>"
               + config.value_cols.map(val => val + ": " + dataframe.get(val).get(geo.id)).join('%<br>') + '%'
    });
    svg.call(tip)

    const values = [...dataframe.get(config.y_col).values()]
    values.sort(function(a, b) {
        return a - b
    });
    quants.domain(values).range(colorscale)

    svg.attr('viewBox', viewBox(counties_geos).join(' ')).attr('preserveAspectRatio', 'xMinYMin')

    draw_and_color(svg, counties_geos, dataframe.get(config.y_col))
    draw_boundries(svg, states_geos)
    draw_legend(config.legend_div, values);

    tmp = dataframe




}


function flatten_nested_geos_to_coordinates(arr) {
    const flat = [].concat(...arr);
    return flat.some(Array.isArray) ? flatten_nested_geos_to_coordinates(flat) : arr;
}


function viewBox(geos) {
    boxes = geos.map(path.bounds)
    corners = flatten_nested_geos_to_coordinates(boxes)
    corners_x = corners.map(corner=>corner[0]).filter(isFinite)
    // seperate x eletemts and filter finites
    corners_y = corners.map(corner=>corner[1]).filter(isFinite)
    // separet y elements and filter finites
    box = [Math.min(...corners_x)//x
    , Math.min(...corners_y)//y
    , Math.max(...corners_x) - Math.min(...corners_x)//width
    , Math.max(...corners_y) - Math.min(...corners_y)//height
    ]
    return box.map(Math.round)
}

function draw_and_color(svg, geo_data, yById) {
    svg
    .append("g")
    .attr("class", "border-and-fill")
    .selectAll("path")
    .data(geo_data)
    .enter()
    .append("path")
    .attr("id", function(geo) {return geo.id;})
    .attr("fill", function(geo) {return quants(yById.get(geo.id))})// fill with mapped colors
    .attr("d", path)
    .on('mouseover.tip', tip.show)
    .on('mouseout', tip.hide)
    .on('mouseover.table', info_table)
}

function info_table(geo) {
  key_value = []
  tmp.forEach((v,k) => key_value.push([k,v.get(geo.id)]))
  spans = key_value.map(x => '<span>' + x[0] +'</span>' + '<span style="position: absolute; right:1em;" >' + x[1] +'</span> <br>')

  //document.getElementById(config.info_table).innerHTML = spans.join('')
  d3.select(config.info_table).html(spans.join(''))

}


function draw_boundries(svg, geo_data) {
    svg.append("g").attr("class", "border").selectAll("path").data(geo_data).enter().append("path").attr("d", path)
}

function draw_legend(legend_div, values) {
    bar_width = 5;//in em

    var legend = d3.select(legend_div)//.attr("class", "yap-legend")
    for (var i = 0; i < colorscale.length; i++) {
        //for each color create a rect, color it, text it, style it
        legend
        .append("rect")
        .attr("style", "background-color: " + colorscale[i])
        .html(d3.quantile(values, i / colorscale.length).toFixed(1))
    };
}


function create_dataframe(d, id_col) {
    vars = Object.keys(d[0])
    const dataframe = new Map();
    //vars.splice(vars.indexOf(id_col), 1)
    for (v of vars) {
        dataframe.set(v, new Map())
    }

    for (row of d) {
        key = row[id_col]
        for (v of vars) {
            series = dataframe.get(v)
            value = row[v]
            series.set(key, value)
        }
    }
    return dataframe
}

