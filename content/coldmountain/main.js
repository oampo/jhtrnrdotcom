var ColdMountain = function() {
    this.canvas = $("canvas")[0];
    this.context = this.canvas.getContext("2d");
    $(window).on("resize", this.draw.bind(this));
};

ColdMountain.prototype.setup = function() {
    this.lineWidth = Math.random(0, 3);
    this.spread = Math.random() * 2 + 2;
    this.numberOfTriangles = Math.random() * 512 + 128;

    this.topXPositions = [];
    for (var i=0; i<this.numberOfTriangles; i++) {
        this.topXPositions.push(Math.random() * 2 - 1);
    }
};

ColdMountain.prototype.draw = function() {
    if (this.canvas.width != this.canvas.offsetWidth ||
        this.canvas.height != this.canvas.offsetHeight) {
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
    }
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);

    this.context.save();
    this.context.translate(this.canvas.width / 2, 0);
    this.context.lineWidth = this.lineWidth;
    var size = Math.min(this.canvas.width, this.canvas.height);
    for (var i=0; i<this.numberOfTriangles; i++) {
        var triangleSize = (i / this.numberOfTriangles) * size;
        triangleSize = size - triangleSize;
        var topX = this.topXPositions[i] * triangleSize / this.spread;
        var grey = Math.floor(i / this.numberOfTriangles * 255);
        grey = 255 - grey;
        var alpha = (255 - grey) / 255;
        this.context.fillStyle = "rgba(" + grey + ", " + grey + ", "+ grey + ", " + alpha + ")";
        this.context.beginPath();
        this.context.moveTo(topX, triangleSize);
        this.context.lineTo(-triangleSize / 2, this.canvas.height);
        this.context.lineTo(triangleSize / 2, this.canvas.height);
        this.context.lineTo(topX, triangleSize);
        this.context.closePath();
        this.context.stroke();
        this.context.fill();
    }
    this.context.restore();
};

$(document).ready(function() {
    var coldMountain = new ColdMountain();
    coldMountain.setup();
    coldMountain.draw();
});
