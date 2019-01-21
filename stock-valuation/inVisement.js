// Load all js libraries one after another

var div = document.createElement("div");
div.innerHTML = `

<!DOCTYPE html>
<html>

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src='http://127.0.0.1:8887/markdown.min.js'> </script>
</head>

</html>


<a href="https://inVisement.com"> <img class="inVisement-logo" src="https://invisement.com/images/logo.png"> </img> </a>
<a href="https://inVisement.com"> <img class="inVisement-short-logo" src="http://127.0.0.1:8887/inVisement-short-logo.png"> </img> </a>


<style>

.inVisement-short-logo {
  width: 25px;
  left: 0px;
  padding: 0;
  position: fixed;
  top: 0px;
  border-radius: 2px;
  background-color: azure;
}

.inVisement-logo {
  width: 100px;
  right: 5px;
  padding: 2px 5px;
  position: fixed;
  bottom: 5px;
  border-radius: 5px;
  background-color: azure;
  border: thick double blue;
}
html {
  background-color: rgb(240, 255, 255); 
}
body {
  margin: 5px 0;
  max-width: 1000px;
  display: flex;
  flex-flow: row wrap;
  justify-content: center;
}
body > div, markdown{
  padding: 5px;
  margin: 0;
  max-width: 450px;
  width: 100%;
  height: 100%;
}


</style>
`;

export default function () {
document.body.append(div)

// convert all markdowns to html after imprting markdown library
fetch('http://127.0.0.1:8887/markdown.min.js')
.then(res => res.text())
.then(eval)
.then(() =>{
  document.querySelectorAll('markdown')
  .forEach(md => {
    md.innerHTML = markdown.toHTML(md.innerHTML)
  })
})
};

