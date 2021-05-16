


var expand = function() {
    var children = this.parentElement.children;
    for(i = 0; i < children.length; i++)
    {
        children[i].classList.toggle("expanded")
    }
    children[1].classList.toggle("fa-plus-circle");
    children[1].classList.toggle("fa-minus-circle");
    setdropdowntitleheights()
};

loadSidebar();

function setdropdowntitleheights() {
    element = document.querySelector("#dropdowncatintro p")
    element.style.height = element.parentElement.clientHeight + 'px'

    element = document.querySelector("#dropdowncatprimitives p")
    element.style.height = element.parentElement.clientHeight + 'px'

    element = document.querySelector("#dropdowncatbuiltin p")
    element.style.height = element.parentElement.clientHeight + 'px'
}

function loadSidebar() {
    fetch("sidebar.html")
        .then((response) => response.text())
        .then((text) => {
            const otherDoc = document.implementation.createHTMLDocument("sidebar").documentElement;
            otherDoc.innerHTML = text;
            document.querySelector("#sidebar").innerHTML = otherDoc.querySelector(".sidebar").innerHTML;

            var elements = document.getElementsByClassName("toggle-dropdown");
            for (var i = 0; i < elements.length; i++) 
            {
                elements[i].addEventListener('click', expand, false);
            } 

            elements = document.getElementsByTagName('h2');

            for (var i = 0; i < elements.length; i++) 
            {
                elements[i].id = elements[i].textContent.toLowerCase().replace(/ /g,"").replaceAll('\t',"").split('\n')[1]
            } 

            dropdownParents = document.getElementsByTagName('span');

            for (var i = 0; i < dropdownParents.length; i++) 
            {
                
                dropdownName = dropdownParents[i].href = dropdownParents[i].textContent.toLowerCase().replaceAll(/ /g,"").replace('\t',"").split('\n')[1]

                dropdownParents[i].parentElement.parentElement.id = dropdownName
                dropdownParents[i].parentElement.href = dropdownName + '.html'

                dropdowns = document.querySelectorAll('#' + dropdownName + ' .dropdown-content');

                for (var j = 0; j < dropdowns.length; j++)
                {
                    dropdowns[j].href = dropdownName + '.html#' + dropdowns[j].textContent.toLowerCase().replaceAll(/ /g,"").replace('\t',"").split('\n')[1]
                } 
            } 
            
            document.querySelector('#title a').href = 'index.html'
            document.querySelector('#intro a').href = 'index.html#desc'
            if(window.location.href.indexOf("#") != -1)
            {
                document.getElementById(window.location.href.substr(window.location.href.indexOf("#")+1)).scrollIntoView();
            }
            
            setdropdowntitleheights()


        });  
}







       





