// Load all js libraries one after another
export async function initiate () {
    var jsUrls = [
    "https://cdnjs.cloudflare.com/ajax/libs/d3/5.7.0/d3.min.js", 
    "https://cdnjs.cloudflare.com/ajax/libs/PapaParse/4.6.3/papaparse.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/7.0.1/highcharts.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/7.0.1/modules/exporting.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/7.0.1/modules/export-data.js",
  ]
  for(let url of jsUrls) {
    try {
        await fetch(url).then(res => res.text()).then(eval)
    }catch(err) {}
  }
};


var highchartsDefaultOptions = {
  credits: {
    href: 'https://invisement.com',
    text: 'inVisement',
  },
  legend: {
    margin: 0,
    padding: 0,
    itemStyle: {
      fontWeight: 'normal',
      fontSize: '.8em',
    },
  },
  exporting: {
    buttons: {
      contextButton: {
        menuItems: [
          "printChart",
          "downloadPNG", 
          "downloadSVG",
          "downloadJPEG",
          "downloadPDF",
          "separator",
          "downloadCSV",
          "downloadXLS",
        ]
      },
    },
  },
}

function createDataframe (data) { //data from papaparse
  let key = 'Sector'
  let numCols = ["Expected Return", "Base Return", "Growth Potential", "Financial Position"]
  let weightCol = 'Market Cap'
  // create dataframe from parsed data that has color and value
  var data,
    colorscale = ['rgba(255,0,0,.2)', 'rgba(0,255,0,.2)'],
    coloring = num => num!=undefined && d3.scaleLinear().domain([0,.3]).range(colorscale).interpolate(d3.interpolateHsl)(num)
  var dataframe = {};
  for (let col of Object.keys(data[0])) {
    let series = new Map()
    data.forEach(row => series.set(row[key], {
      y: row[col],
      //color: coloring(row[col]),
      name: row[key],
    }))
    dataframe[col] = series
  }
  return dataframe
}









export function pieChartSectorsMarketCap (container){

  fetch("https://data.invisement.com/sectors.csv")
  .then(res => res.text())
  .then(csv => Papa.parse(csv, {
    skipEmptyLines: true,
    dynamicTyping: true,
    header: true,    
  }))
  .then(result => {
    updatePieChartOptionsByData(result.data, pieChartOptions)  
    Highcharts.chart(container, pieChartOptions) 
    console.log(Highcharts.getOptions())
  }) 

  function updatePieChartOptionsByData (csvText, pieChartOptions) {
    let dataframe = createDataframe (csvText)
    dataframe['Market Cap'].delete('Total Market')
    pieChartOptions.series = [{
      name: 'Market Cap',
      data: [...dataframe['Market Cap'].values()],
    }]
    let total = pieChartOptions.series[0].data.reduce((s,v) => s + v.y||0, 0)
    pieChartOptions.subtitle = {
      align: 'center',
      verticalAlign: 'middle',
      text: "Total Market Cap:<br/>$<b>" + Math.round(total/1e9).toLocaleString() + '</b>B',
      y: -10,
    }
  }

  var pieChartOptions = {...highchartsDefaultOptions,
    chart: {
      type: 'pie',
      //backgroundColor: 'rgba(255,255,255,1)',
    },
    title: {
      text: "Market Cap by Sector",
      style: {
        fontSize: 16,
      }
    },
    plotOptions: {
      pie: {
        innerSize: '66%',
        allowPointSelect: true,
        showInLegend: true,
        dataLabels: {
          enabled: true,
          distance: 5,
          style: {
            fontSize: '10px',        
          },
          formatter: function() {
            return '<pre>$' + Math.round(this.y/1e9) + 'B'
          }
        },
      },
    },
    tooltip: {
      formatter: function() {
        return this.key +': <b>' +Math.round(this.percentage*10)/10+'</b>%<br/>$<b>'+ Math.round(this.y/1e9) +'</b>B'
      }
    },
    legend: {
      labelFormatter: function () {
        return this.name +': <b>' +Math.round(this.percentage*10)/10+'</b>%'
      },
      padding: -10,
      itemStyle: {
        fontSize: '9px',
        fontWeight: 'normal',
      },
    },
  }
}


export function barChartSectorsReturn (container) {

  fetch("https://data.invisement.com/sectors.csv")
  .then(res => res.text())
  .then(csv => Papa.parse(csv, {
    skipEmptyLines: true,
    dynamicTyping: true,
    header: true,    
  }))
  .then(result => {
    updateBarChartOptionsByData(result.data, barChartOptions)  
    Highcharts.chart(container, barChartOptions) 
  }) 


  function updateBarChartOptionsByData (csvText, barChartOptions) {
    let dataframe = createDataframe (csvText)
    let numCols = ["Expected Return", "Base Return", "Growth Potential", "Financial Position"]
    barChartOptions.series = numCols.map(name => {return{
      name: name,
      data: [...dataframe[name].values()],
    }})

    let stacked = ['Base Return', 'Growth Potential', 'Financial Position']
    barChartOptions.series
    .filter(series => stacked.includes(series.name))
    .forEach(series => {
      series.stack = true
      series.pointPadding= .2
      series.pointPlacement= .3        
    })
    barChartOptions.series[0].pointPadding = -.5
    barChartOptions.series[0].borderColor = 'blue'
    //add color to expected value
    //barChartOptions.series[0].data.forEach(v => v['color'] = coloring(v['y']))

    //barChartOptions.series[1].color = 'darkkhaki'
    //barChartOptions.series[2].color = 'rosybrown'
    //barChartOptions.series[3].color = 'royalblue' 
  }

  var barChartOptions = {...highchartsDefaultOptions,
    "chart": {
          backgroundColor: {
              linearGradient: [0, 250, 700, 250],
              stops: [
                  [0, 'rgba(255, 0, 0, .2)'],
                  [1, 'rgb(0, 255, 0, .3)'],
              ]
          },
      "type": "bar",
      "inverted": true,
      //"polar": true,
      //styledMode: false,
    },
   "plotOptions": {
      "series": {
        allowPointSelect: true, //access through var selectedPoints = chart.getSelectedPoints()
        "stacking": 'normal',
        //"animation": true,
        "dataLabels": {
          //enabled: true,
        }
      },
    },
    "title": {
      "text": "Expected Returns for Each Sector (%)"
    },
    "subtitle": {
      //"text": ""
    },
     legend: {
          enabled: true
      },
      xAxis: {
         type: 'category',
      },

      yAxis: [{
          title: {
              text: 'Percentage'
          }
      }],
      tooltip: {
          shared: true,
          //headerFormat: '{point.series.name}<br/>',
          //pointFormat: '<b>{point.y:,.1f}</b> %',
          formatter: function() {
            return this.points.map(point => point.series.name + ': ' + '<b>'+Math.round(point.y*1000)/10+'</b> %<br/>').join('')
          }
      },
    "credits": {
      href: 'https://invisement.com',
      text: 'inVisement',
    },
    "yAxis": {
      "title": {}
    }
  }


}

