function togglVisibility(elemID) {
    var curElem = document.getElementById(elemID);
    console.log(curElem)
    // Toggle visibility
    let display = (curElem.style.display === 'none') ? 'block' : 'none';
    curElem.style.display = display;
    var elem = event.target;
    let prefix = (curElem.style.display === 'none') ? 'Show' : 'Hide';
    elem.innerHTML = prefix + elem.innerHTML.substring(4);
}

document.addEventListener('DOMContentLoaded', function () {
    var disqusThread = document.getElementById('disqus_thread');
    disqusThread.style.display = 'none';
    var backlinks = document.getElementById('backlinks');
    backlinks.style.display = 'none';
});