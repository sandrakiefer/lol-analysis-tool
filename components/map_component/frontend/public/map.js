var scale = 1.01,
panning = false,
pointX = 0,
pointY = 0,
start = { x: 0, y: 0 },
zoom = document.getElementById("zoom"),
map_img = document.getElementById("map_img"),
width = map_img.clientWidth,
height = map_img.clientHeight;

function setTransform() {
    if(pointX > 0) {
        pointX = 0;
    }

    var adjustedWidth = width * scale;
    if(pointX + adjustedWidth < width){
        pointX = -(adjustedWidth - width);
    }

    var adjustedHeight = height * scale;
    if(pointY + adjustedHeight < height){
        pointY = -(adjustedHeight - height);
    }
    if(pointY > 0) {
        pointY = 0;
    }
    zoom.style.transform = "translate(" + pointX + "px, " + pointY + "px) scale(" + scale + ")";
}

zoom.onmousedown = function (e) {
    e.preventDefault();
    start = { x: e.clientX - pointX, y: e.clientY - pointY };
    panning = true;
}

zoom.onmouseup = function (e) {
    panning = false;
}

zoom.onmousemove = function (e) {
    e.preventDefault();
    if (!panning) {
        return;
    }
    pointX = (e.clientX - start.x);
    pointY = (e.clientY - start.y);
    setTransform();
}

zoom.onwheel = function (e) {
    e.preventDefault();
    var xs = (e.clientX - pointX) / scale,
    ys = (e.clientY - pointY) / scale,
    delta = (e.wheelDelta ? e.wheelDelta : -e.deltaY);
    (delta > 0) ? (scale *= 1.2) : (scale /= 1.2);

    // Set scale value boundaries
    if(scale < 1){
        scale = 1;
    } else if (scale > 3) {
        scale = 3;
    }
    pointX = e.clientX - xs * scale;
    pointY = e.clientY - ys * scale;

    setTransform();
}