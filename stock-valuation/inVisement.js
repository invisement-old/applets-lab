// Load all js libraries one after another


var div = document.createElement("div");
div.innerHTML = `

<!DOCTYPE html>
<html>

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

</html>

<a href="https://inVisement.com"> <img class="inVisement-logo" src="https://invisement.com/images/logo.png"> </img> </a>

<style>

.inVisement-logo {
  width: 100px;
  right: 50%;
  transform: translateX(50%);
  padding: 2px 5px;
  position: fixed;
  top: 0px;
}
html {
}
body {
  margin: 0 auto;
  padding: 5px 3px;
  max-width: 1000px;
  display: flex;
  flex-flow: row wrap;
  justify-content: center;
}
body > div, mark-down{
  padding: 5px;
  margin: 0;
  max-width: 450px;
  width: 100%;
  height: 100%;
}

js-var, em, code {
  color: darkblue;
}

</style>
`;

export default function () {

window.dataHost = 'http://127.0.0.1:8887/' //'https://data.inVisement.com/'
window.cdnHost = 'http://127.0.0.1:8887/'//'https://inVisement.com/cdn/'

document.body.append(div)

//window.customElements.define('mark-down', {extends: 'p'})
// convert all markdowns to html after imprting markdown library
fetch('https://cdnjs.cloudflare.com/ajax/libs/markdown-it/8.4.2/markdown-it.min.js')
.then(res => res.text())
.then(eval)
.then(() =>{
  var markdown = window.markdownit({html: true});
  document.querySelectorAll('mark-down')
  .forEach(md => {
    md.innerHTML = markdown.render(md.innerHTML)
  })
  document.querySelectorAll('code').forEach(code => {
    code.innerHTML = eval(code.innerHTML)
  })
  document.querySelectorAll('em').forEach(jsvar => {
    jsvar.innerHTML = window['jsvar'][jsvar.innerHTML] || jsvar.innerHTML
  })
})
};


